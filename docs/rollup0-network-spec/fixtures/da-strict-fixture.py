#!/usr/bin/env python3
"""Verify the complete Rollup0 DA decoder and sidecar correspondence vector."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from eth_abi import decode as abi_decode
from eth_abi import encode as abi_encode
from eth_keys import keys
from eth_utils import keccak
import rlp

from conformance_vectors import (
    L1_EXECUTION_ENTRY_TYPE,
    strict_da_material,
)


FIXTURES = Path(__file__).resolve().parent
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
I256_MAX = (1 << 255) - 1


def load_outer_codec():
    path = FIXTURES / "da-rlp-fixture.py"
    spec = importlib.util.spec_from_file_location("rollup0_da_outer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def uint(raw: bytes, name: str) -> int:
    if not isinstance(raw, bytes):
        raise ValueError(f"{name} is not an RLP byte string")
    if raw and raw[0] == 0:
        raise ValueError(f"{name} has a non-canonical leading zero")
    return int.from_bytes(raw, "big")


def decode_signed_type2(raw: bytes) -> dict[str, object]:
    if not raw or raw[0] != 0x02:
        raise ValueError("transaction is not a type-2 envelope")
    try:
        fields = rlp.decode(raw[1:], strict=True)
    except rlp.DecodingError as exc:
        raise ValueError(f"invalid type-2 RLP: {exc}") from exc
    if not isinstance(fields, list) or len(fields) != 12:
        raise ValueError("type-2 transaction must contain exactly 12 fields")
    if b"\x02" + rlp.encode(fields) != raw:
        raise ValueError("transaction has trailing or non-canonical bytes")

    chain_id = uint(fields[0], "chainId")
    nonce = uint(fields[1], "nonce")
    max_priority_fee = uint(fields[2], "maxPriorityFeePerGas")
    max_fee = uint(fields[3], "maxFeePerGas")
    gas_limit = uint(fields[4], "gasLimit")
    to = fields[5]
    value = uint(fields[6], "value")
    data = fields[7]
    access_list = fields[8]
    y_parity = uint(fields[9], "yParity")
    r = uint(fields[10], "r")
    s = uint(fields[11], "s")

    if not isinstance(to, bytes) or len(to) != 20:
        raise ValueError("type-2 destination must be 20 bytes")
    if not isinstance(data, bytes) or not isinstance(access_list, list):
        raise ValueError("invalid type-2 data or access list")
    if y_parity not in (0, 1) or not (0 < r < SECP256K1_N) or not (0 < s <= SECP256K1_N // 2):
        raise ValueError("invalid or non-canonical secp256k1 signature")

    signing_fields = fields[:9]
    signing_hash = keccak(b"\x02" + rlp.encode(signing_fields))
    signature = keys.Signature(vrs=(y_parity, r, s))
    try:
        sender = signature.recover_public_key_from_msg_hash(signing_hash).to_checksum_address()
    except Exception as exc:
        raise ValueError(f"cannot recover transaction signer: {exc}") from exc

    return {
        "chain_id": chain_id,
        "nonce": nonce,
        "max_priority_fee": max_priority_fee,
        "max_fee": max_fee,
        "gas_limit": gas_limit,
        "to": to,
        "value": value,
        "data": data,
        "access_list": access_list,
        "sender": sender.lower(),
        "signing_hash": signing_hash,
    }


def decode_entry(raw: bytes):
    try:
        decoded = abi_decode([L1_EXECUTION_ENTRY_TYPE], raw)
    except Exception as exc:
        raise ValueError(f"invalid L1 ExecutionEntry ABI: {exc}") from exc
    if len(decoded) != 1 or abi_encode([L1_EXECUTION_ENTRY_TYPE], decoded) != raw:
        raise ValueError("entry has trailing or non-canonical ABI bytes")
    return decoded[0]


def successful_one_call_fold(return_data: bytes) -> bytes:
    value = keccak(bytes(32) + b"\x01" + (1).to_bytes(32, "big"))
    return keccak(value + b"\x02" + (1).to_bytes(32, "big") + b"\x01" + return_data)


def validate_anchor(anchor, rollup_id: int) -> tuple[bytes, bytes]:
    (
        deltas,
        proxy,
        destination,
        calls,
        expected,
        lookups,
        count,
        return_data,
        rolling,
    ) = anchor
    if (
        len(deltas) != 1
        or proxy != bytes(32)
        or destination != rollup_id
        or calls
        or expected
        or lookups
        or count != 0
        or return_data
        or rolling != bytes(32)
    ):
        raise ValueError("invalid state-anchor shape")
    delta_rollup, current_state, new_state, ether_delta = deltas[0]
    if delta_rollup != rollup_id or ether_delta != 0:
        raise ValueError("invalid state-anchor delta")
    return current_state, new_state


def validate_outbound_pair(sidecar, on_chain, rollup_id: int) -> None:
    (
        side_deltas,
        side_proxy,
        side_destination,
        side_calls,
        side_expected,
        side_lookups,
        side_count,
        side_return,
        side_rolling,
    ) = sidecar
    (
        chain_deltas,
        chain_proxy,
        chain_destination,
        chain_calls,
        chain_expected,
        chain_lookups,
        chain_count,
        chain_return,
        chain_rolling,
    ) = on_chain

    if side_deltas or len(chain_deltas) != 1:
        raise ValueError("outbound stateDelta cardinality mismatch")
    if side_proxy != bytes(32) or chain_proxy != bytes(32):
        raise ValueError("outbound proxyEntryHash mismatch")
    if side_destination != rollup_id or chain_destination != rollup_id:
        raise ValueError("outbound destinationRollupId mismatch")
    if len(side_calls) != 1 or side_calls != chain_calls:
        raise ValueError("outbound call transformation mismatch")
    if side_expected or side_lookups or chain_expected or chain_lookups:
        raise ValueError("flat outbound entry has an expected call or lookup")
    if side_count != 1 or chain_count != 1:
        raise ValueError("outbound callCount mismatch")
    if side_return != chain_return or side_rolling != chain_rolling:
        raise ValueError("outbound returnData or rollingHash mismatch")

    _, value, _, _, source_rollup, revert_span = side_calls[0]
    if value > I256_MAX:
        raise ValueError("outbound value exceeds type(int256).max")
    if source_rollup != rollup_id or revert_span != 0:
        raise ValueError("outbound sourceRollupId or revertSpan mismatch")
    if side_rolling != successful_one_call_fold(side_return):
        raise ValueError("outbound rollingHash is not the successful one-call fold")

    delta_rollup, _, _, ether_delta = chain_deltas[0]
    if delta_rollup != rollup_id or ether_delta != -value:
        raise ValueError("outbound StateDelta rollup or etherDelta mismatch")


def validate_inbound_pair(sidecar, on_chain, rollup_id: int) -> None:
    (
        side_deltas,
        side_proxy,
        side_destination,
        side_calls,
        side_expected,
        side_lookups,
        side_count,
        side_return,
        side_rolling,
    ) = sidecar
    (
        chain_deltas,
        chain_proxy,
        chain_destination,
        chain_calls,
        chain_expected,
        chain_lookups,
        chain_count,
        chain_return,
        chain_rolling,
    ) = on_chain

    if side_deltas or len(chain_deltas) != 1:
        raise ValueError("inbound stateDelta cardinality mismatch")
    if side_destination != rollup_id or chain_destination != rollup_id:
        raise ValueError("inbound destinationRollupId mismatch")
    if side_proxy == bytes(32) or side_proxy != chain_proxy:
        raise ValueError("inbound proxyEntryHash mismatch")
    if len(side_calls) != 1 or chain_calls:
        raise ValueError("inbound populated/lean call transformation mismatch")
    if side_expected or side_lookups or chain_expected or chain_lookups:
        raise ValueError("flat inbound entry has an expected call or lookup")
    if side_count != 1 or chain_count != 0:
        raise ValueError("inbound callCount transformation mismatch")
    if side_return != chain_return or chain_rolling != bytes(32):
        raise ValueError("inbound returnData or lean rollingHash mismatch")

    target, value, data, source, source_rollup, revert_span = side_calls[0]
    if value > I256_MAX:
        raise ValueError("inbound value exceeds type(int256).max")
    if source_rollup != 0 or revert_span != 0:
        raise ValueError("inbound sourceRollupId or revertSpan mismatch")
    expected_proxy = keccak(
        abi_encode(
            ["uint256", "address", "uint256", "bytes", "address", "uint256"],
            [rollup_id, target, value, data, source, source_rollup],
        )
    )
    if side_proxy != expected_proxy:
        raise ValueError("inbound call preimage does not match proxyEntryHash")
    if side_rolling != successful_one_call_fold(side_return):
        raise ValueError("inbound rollingHash is not the successful one-call fold")

    delta_rollup, _, _, ether_delta = chain_deltas[0]
    if delta_rollup != rollup_id or ether_delta != value:
        raise ValueError("inbound StateDelta rollup or etherDelta mismatch")


def validate_batch_sidecar(batch_entries, sidecar_entries, transient_count: int) -> None:
    if not batch_entries:
        raise ValueError("batch.entries is empty")
    if len(sidecar_entries) != len(batch_entries) - 1:
        raise ValueError("sidecar cardinality does not match producing entries")
    if transient_count < 1 or transient_count > len(batch_entries):
        raise ValueError("invalid transientExecutionEntryCount")

    rollup_id = batch_entries[0][2]
    _, previous_new_state = validate_anchor(batch_entries[0], rollup_id)
    if sidecar_entries:
        final_state = batch_entries[-1][0][0][2]
        for entry in batch_entries[1:]:
            if len(entry[0]) != 1:
                raise ValueError("producing entry must have exactly one stateDelta")
            delta_rollup, current_state, new_state, _ = entry[0][0]
            if delta_rollup != rollup_id or current_state != previous_new_state:
                raise ValueError("producing stateDelta chain mismatch")
            if new_state != final_state:
                raise ValueError("producing entry does not end at the Sync root")
            previous_new_state = new_state

    outbound_count = transient_count - 1
    for index, (sidecar, on_chain) in enumerate(
        zip(sidecar_entries, batch_entries[1:], strict=True)
    ):
        if index < outbound_count:
            validate_outbound_pair(sidecar, on_chain, rollup_id)
        else:
            validate_inbound_pair(sidecar, on_chain, rollup_id)


def expect_rejected(name: str, function, *args) -> None:
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError(f"malformed strict fixture accepted: {name}")


def main() -> None:
    vector = strict_da_material()
    outer = load_outer_codec()
    counts, transactions, entries = outer.decode_payload(vector["payload"])
    assert counts == vector["block_tx_counts"] == [0, 1]
    assert transactions == [vector["transaction"]]
    assert entries == [
        vector["outbound_sidecar_abi"],
        vector["inbound_sidecar_abi"],
    ]

    transaction = decode_signed_type2(transactions[0])
    assert transaction["chain_id"] == 1
    assert transaction["nonce"] == 0
    assert transaction["max_priority_fee"] == 1_000_000_000
    assert transaction["max_fee"] == 2_000_000_000
    assert transaction["gas_limit"] == 21_000
    assert transaction["value"] == 1
    assert transaction["data"] == b""
    assert transaction["access_list"] == []
    assert transaction["sender"] == vector["user_address"]
    assert transaction["signing_hash"] == vector["transaction_signing_hash"]

    anchor = decode_entry(vector["anchor_abi"])
    outbound_sidecar = decode_entry(entries[0])
    inbound_sidecar = decode_entry(entries[1])
    outbound_on_chain = decode_entry(vector["outbound_on_chain_abi"])
    inbound_on_chain = decode_entry(vector["inbound_on_chain_abi"])
    validate_batch_sidecar(
        [anchor, outbound_on_chain, inbound_on_chain],
        [outbound_sidecar, inbound_sidecar],
        2,
    )

    oversized_call = list(inbound_sidecar[3][0])
    oversized_call[1] = 1 << 255
    oversized_sidecar = list(inbound_sidecar)
    oversized_sidecar[3] = (tuple(oversized_call),)
    expect_rejected(
        "inbound value above int256",
        validate_inbound_pair,
        tuple(oversized_sidecar),
        inbound_on_chain,
        1,
    )
    expect_rejected(
        "missing mandatory sidecar",
        validate_batch_sidecar,
        [anchor, outbound_on_chain, inbound_on_chain],
        [],
        2,
    )
    expect_rejected(
        "opaque outer transaction",
        decode_signed_type2,
        bytes.fromhex("02f8650180808094000000000000000000000000000000000000dead80c0"),
    )
    expect_rejected(
        "opaque outer entry",
        decode_entry,
        bytes.fromhex("00" * 28 + "deadbeef"),
    )

    print("strict payload         =", len(vector["payload"]), "bytes")
    print("signed type-2 user tx  = OK; sender", vector["user_address"])
    print("L1 entry ABI           = OK; full canonical consumption")
    print("sidecar correspondence = OK; anchor + outbound + populated/lean inbound")
    print("semantic rejection     = 4 negative cases OK")


if __name__ == "__main__":
    main()
