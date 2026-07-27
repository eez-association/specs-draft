#!/usr/bin/env python3
"""Build the deterministic Rollup0-v0 conformance manifest.

Contract-authored values are pinned to
sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba.
Codec and system-transaction values are pinned to
eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c.

The current EEZ framework uses a different 3a6ca65 binding and a separate
corpus. Its values MUST NOT be substituted here.
"""

from __future__ import annotations

from typing import Any

from eth_abi import encode as abi_encode
from eth_keys import keys
from eth_utils import keccak
import rlp


CONTRACT_REVISION = "5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba"
EXECUTION_REVISION = "00b3e75872fcc0c374d3b12a01933d732d317e4c"

POST_SIGNATURE = (
    "postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,"
    "uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,"
    "bytes,bytes32)[],(bytes32,uint256,bytes,bool,(address,uint256,bytes,address,"
    "uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,"
    "uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32,"
    "(uint256,bytes32)[])[],uint256,uint256,address[],(uint256,uint64[])[],"
    "bytes32,uint256[],bytes,bytes[],uint64))"
)
LOAD_SIGNATURE = (
    "loadExecutionTable((bytes32,(address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,"
    "uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,"
    "bytes32)[])"
)
INBOUND_SIGNATURE = (
    "executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,"
    "(bytes32,(address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,"
    "uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,"
    "bytes32)[])"
)

BATCH_POSTED_EVENT = "BatchPosted(uint256)"
L2_EXECUTION_PERFORMED_EVENT = "L2ExecutionPerformed(uint256,bytes32)"
IMMEDIATE_ENTRY_SKIPPED_EVENT = "ImmediateEntrySkipped(uint256,bytes)"
EXECUTION_CONSUMED_EVENT = "ExecutionConsumed(bytes32,uint256,uint256)"

ZERO_BYTES32 = "0x" + "00" * 32
SYSTEM_TX_FIXTURE_PRIVATE_KEY = "0x" + "00" * 31 + "01"
DEV_SYSTEM_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)
DEV_SYSTEM_ADDRESS = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"

DA_PAYLOAD = (
    "00f885c20201f85e"
    "9e02f8650180808094000000000000000000000000000000000000dead80c0"
    "9e02f8650180018094000000000000000000000000000000000000beef80c0"
    "9f02f865018002809400000000000000000000000000000000000000cafe80c0"
    "e1a000000000000000000000000000000000000000000000000000000000deadbeef"
)

STATE_DELTA_TYPE = "(uint256,bytes32,bytes32,int256)"
CROSS_CHAIN_CALL_TYPE = "(address,uint256,bytes,address,uint256,uint256)"
EXPECTED_OUTGOING_TYPE = "(bytes32,uint256,bytes)"
EXPECTED_LOOKUP_TYPE = (
    "(bytes32,bytes,bool,uint64,uint64,uint64,"
    f"{CROSS_CHAIN_CALL_TYPE}[],{EXPECTED_OUTGOING_TYPE}[],uint256,bytes32)"
)
L1_EXECUTION_ENTRY_TYPE = (
    f"({STATE_DELTA_TYPE}[],bytes32,uint256,{CROSS_CHAIN_CALL_TYPE}[],"
    f"{EXPECTED_OUTGOING_TYPE}[],{EXPECTED_LOOKUP_TYPE}[],uint256,bytes,bytes32)"
)

STRICT_USER_PRIVATE_KEY = bytes.fromhex(
    "59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)
STRICT_USER_ADDRESS = "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"
STRICT_USER_TRANSACTION = bytes.fromhex(
    "02f86a0180843b9aca00847735940082520894"
    "deaddeaddeaddeaddeaddeaddeaddeaddeaddead"
    "0180c080"
    "a0668dfa684438e0375cec52d8a90d6f6e78ec32d102393d531b25e4d64a0eabdc"
    "a040a3c124983eb3e41843412cc4dbfe55f3d0e027a604da44efdce755d8a1ceed"
)
STRICT_EXPECTED = {
    "transaction_hash": "4a66440cef6634433ea49dc021463f7c8641172f07eef6c7d82656b4855a9ddd",
    "transaction_signing_hash": "f7e9fa783d27a79a6fe5399e9406c8f3c9062cb6848ca14d88b299f33a4561aa",
    "inbound_proxy_entry_hash": "afe7b73c7bec87333fb3594b35452a9b143619a285117740a95590d6496e55dc",
    "rolling_hash": "68676dacdc339269dad7302dad8697771c8c23d92fa956992dc881fce33e0764",
    "anchor_abi_length": 608,
    "anchor_abi_hash": "81cebf9728ca3e2018685bb550de57dcef4e6f8c461f2f2d4cc98178375bd55e",
    "outbound_sidecar_abi_length": 736,
    "outbound_sidecar_abi_hash": "862afd3d25faa565ccffbb6711982614e6d45dd6dfb82a07e94a62aeb5e8ffdf",
    "outbound_on_chain_abi_length": 864,
    "outbound_on_chain_abi_hash": "09ebd1a454f8024f1ce6e9620783a6a98be03684dfbf7f3d7644705b9768e74d",
    "inbound_sidecar_abi_length": 736,
    "inbound_sidecar_abi_hash": "cfc659cb45a43048b23db1cb0482c9f0461e5817776e063a7f09839056593776",
    "inbound_on_chain_abi_length": 608,
    "inbound_on_chain_abi_hash": "4bbd9222b8a278e1cb15d98ded88aa37d62193ef1d643aa1efc6698df3df877d",
    "payload_length": 1601,
    "payload_hash": "179bdc0defb0e2a4979efa52123be6cee63c6b86eefb121ea5bddca974e48e5f",
}


def selector(signature: str) -> str:
    return "0x" + keccak(text=signature)[:4].hex()


def checked_selector(signature: str, expected: str) -> dict[str, str]:
    actual = selector(signature)
    if actual != expected:
        raise AssertionError(f"selector drift: {actual} != {expected}")
    return {"signature": signature, "selector": actual}


def checked_event_topic(signature: str, expected: str) -> str:
    actual = "0x" + keccak(text=signature).hex()
    if actual != expected:
        raise AssertionError(f"event topic drift for {signature}: {actual} != {expected}")
    return actual


def uint256_topic(value: int) -> str:
    if not 0 <= value < 2**256:
        raise ValueError("uint256 topic value out of range")
    return "0x" + value.to_bytes(32, "big").hex()


def settlement_event_manifest() -> dict[str, Any]:
    """Build exact log vectors and outcome-prefix acceptance cases."""

    topic0 = {
        "batch_posted": checked_event_topic(
            BATCH_POSTED_EVENT,
            "0xd6f8d71ce42a799b91f399271f4b0e91f85eb87fac7bb2cedd4b3a52fad36182",
        ),
        "l2_execution_performed": checked_event_topic(
            L2_EXECUTION_PERFORMED_EVENT,
            "0x0133f662c29e67eedfc9b53c0c1f657b30ebaf9748094d09fa4659d769dd4f78",
        ),
        "immediate_entry_skipped": checked_event_topic(
            IMMEDIATE_ENTRY_SKIPPED_EVENT,
            "0x62cc6fa8d0d1b1170559640dfa2d36932712a5d761c0924ea23aabf3b602cb3c",
        ),
        "execution_consumed": checked_event_topic(
            EXECUTION_CONSUMED_EVENT,
            "0x207e371295f3ff0efe443424ce128c96f8ecea6a25636fc38ad7c222c446699c",
        ),
    }
    rollup_id = 1
    sync_root = bytes.fromhex("33" * 32)
    inbound_hash = bytes.fromhex(STRICT_EXPECTED["inbound_proxy_entry_hash"])
    revert_data = bytes.fromhex("deadbeef")
    queue_index = 7

    def prefix_length(outcomes: list[bool]) -> int | None:
        first_not_applied = next(
            (index for index, applied in enumerate(outcomes) if not applied),
            len(outcomes),
        )
        if any(outcomes[first_not_applied:]):
            return None
        return first_not_applied

    cases: list[dict[str, Any]] = []
    for name, entry_order, outcomes in (
        (
            "full_prefix",
            ["anchor", "outbound", "inbound"],
            [True, True, True],
        ),
        (
            "proper_prefix",
            ["anchor", "outbound", "inbound"],
            [True, True, False],
        ),
        (
            "anchor_only",
            ["anchor", "outbound", "inbound"],
            [True, False, False],
        ),
        (
            "none_applied",
            ["anchor", "outbound", "inbound"],
            [False, False, False],
        ),
        (
            "immediate_hole",
            ["anchor", "outbound[0]", "outbound[1]", "outbound[2]"],
            [True, True, False, True],
        ),
    ):
        length = prefix_length(outcomes)
        cases.append(
            {
                "name": name,
                "entry_order": entry_order,
                "outcomes": ["applied" if value else "not_applied" for value in outcomes],
                "valid_prefix": length is not None,
                "applied_prefix_length": length,
            }
        )

    if [case["valid_prefix"] for case in cases] != [True, True, True, True, False]:
        raise AssertionError("settlement prefix classification drift")

    return {
        "events": {
            "batch_posted": {
                "signature": BATCH_POSTED_EVENT,
                "topics": [topic0["batch_posted"], uint256_topic(1)],
                "data": "0x",
            },
            "l2_execution_performed": {
                "signature": L2_EXECUTION_PERFORMED_EVENT,
                "topics": [topic0["l2_execution_performed"], uint256_topic(rollup_id)],
                "data": "0x" + sync_root.hex(),
            },
            "immediate_entry_skipped": {
                "signature": IMMEDIATE_ENTRY_SKIPPED_EVENT,
                "topics": [topic0["immediate_entry_skipped"], uint256_topic(1)],
                "data": "0x" + abi_encode(["bytes"], [revert_data]).hex(),
            },
            "execution_consumed": {
                "signature": EXECUTION_CONSUMED_EVENT,
                "topics": [
                    topic0["execution_consumed"],
                    "0x" + inbound_hash.hex(),
                    uint256_topic(rollup_id),
                    uint256_topic(queue_index),
                ],
                "data": "0x",
            },
        },
        "ordered_outcome_cases": cases,
        "rule": (
            "Classify every immediate index and inbound rider from its exact receipt; "
            "only one leading applied run is valid."
        ),
    }


def portable_vectors() -> dict[str, str]:
    action = keccak(
        abi_encode(
            ["uint256", "address", "uint256", "bytes", "address", "uint256"],
            [
                1,
                "0x00000000000000000000000000000000deadbeef",
                10**18,
                bytes.fromhex("deadbeef"),
                "0x0000000000000000000000000000000000c0ffee",
                0,
            ],
        )
    )
    after_begin = keccak(bytes(32) + b"\x01" + (1).to_bytes(32, "big"))
    after_end = keccak(
        after_begin + b"\x02" + (1).to_bytes(32, "big") + b"\x01\x01"
    )
    result = {
        "cross_chain_call_hash": "0x" + action.hex(),
        "rolling_hash_after_call_begin": "0x" + after_begin.hex(),
        "rolling_hash_after_call_end": "0x" + after_end.hex(),
    }
    if result["cross_chain_call_hash"] != (
        "0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2"
    ):
        raise AssertionError("cross-chain call hash drift")
    return result


def strict_da_material() -> dict[str, Any]:
    """Build the strict DA vector and its corresponding on-chain entry pair."""

    private_key = keys.PrivateKey(STRICT_USER_PRIVATE_KEY)
    unsigned_transaction = [
        1,  # chainId
        0,  # nonce
        1_000_000_000,  # maxPriorityFeePerGas
        2_000_000_000,  # maxFeePerGas
        21_000,
        bytes.fromhex("deaddeaddeaddeaddeaddeaddeaddeaddeaddead"),
        1,
        b"",
        [],  # accessList
    ]
    signing_hash = keccak(b"\x02" + rlp.encode(unsigned_transaction))
    signature = private_key.sign_msg_hash(signing_hash)
    transaction = b"\x02" + rlp.encode(
        unsigned_transaction + [signature.v, signature.r, signature.s]
    )
    if transaction != STRICT_USER_TRANSACTION:
        raise AssertionError("strict DA user transaction drift")

    rollup_id = 1
    inbound_target = bytes.fromhex("4200000000000000000000000000000000000008")
    inbound_source = bytes.fromhex("00000000000000000000000000000000000000bb")
    outbound_target = bytes.fromhex("00000000000000000000000000000000000000aa")
    outbound_source = bytes.fromhex(STRICT_USER_ADDRESS[2:])
    value = 1
    data = b""
    return_data = b""

    inbound_proxy_entry_hash = keccak(
        abi_encode(
            ["uint256", "address", "uint256", "bytes", "address", "uint256"],
            [rollup_id, inbound_target, value, data, inbound_source, 0],
        )
    )
    rolling_hash = keccak(bytes(32) + b"\x01" + (1).to_bytes(32, "big"))
    rolling_hash = keccak(
        rolling_hash + b"\x02" + (1).to_bytes(32, "big") + b"\x01" + return_data
    )
    outbound_outer = (
        outbound_target,
        value,
        data,
        outbound_source,
        rollup_id,
        0,
    )
    inbound_outer = (inbound_target, value, data, inbound_source, 0, 0)

    cursor_root = bytes.fromhex("11" * 32)
    parent_root = bytes.fromhex("22" * 32)
    sync_root = bytes.fromhex("33" * 32)
    anchor = (
        [(rollup_id, cursor_root, parent_root, 0)],
        bytes(32),
        rollup_id,
        [],
        [],
        [],
        0,
        b"",
        bytes(32),
    )
    outbound_sidecar = (
        [],
        bytes(32),
        rollup_id,
        [outbound_outer],
        [],
        [],
        1,
        return_data,
        rolling_hash,
    )
    outbound_on_chain = (
        [(rollup_id, parent_root, sync_root, -value)],
        bytes(32),
        rollup_id,
        [outbound_outer],
        [],
        [],
        1,
        return_data,
        rolling_hash,
    )
    inbound_sidecar = (
        [],
        inbound_proxy_entry_hash,
        rollup_id,
        [inbound_outer],
        [],
        [],
        1,
        return_data,
        rolling_hash,
    )
    inbound_on_chain = (
        [(rollup_id, sync_root, sync_root, value)],
        inbound_proxy_entry_hash,
        rollup_id,
        [],
        [],
        [],
        0,
        return_data,
        bytes(32),
    )

    anchor_abi = abi_encode([L1_EXECUTION_ENTRY_TYPE], [anchor])
    outbound_sidecar_abi = abi_encode([L1_EXECUTION_ENTRY_TYPE], [outbound_sidecar])
    outbound_on_chain_abi = abi_encode([L1_EXECUTION_ENTRY_TYPE], [outbound_on_chain])
    inbound_sidecar_abi = abi_encode([L1_EXECUTION_ENTRY_TYPE], [inbound_sidecar])
    inbound_on_chain_abi = abi_encode([L1_EXECUTION_ENTRY_TYPE], [inbound_on_chain])
    payload = b"\x00" + rlp.encode(
        [
            [b"", b"\x01"],  # [0, 1]: final Sync block contains one user tx
            [transaction],
            [outbound_sidecar_abi, inbound_sidecar_abi],
        ]
    )

    actual = {
        "transaction_hash": keccak(transaction).hex(),
        "transaction_signing_hash": signing_hash.hex(),
        "inbound_proxy_entry_hash": inbound_proxy_entry_hash.hex(),
        "rolling_hash": rolling_hash.hex(),
        "anchor_abi_length": len(anchor_abi),
        "anchor_abi_hash": keccak(anchor_abi).hex(),
        "outbound_sidecar_abi_length": len(outbound_sidecar_abi),
        "outbound_sidecar_abi_hash": keccak(outbound_sidecar_abi).hex(),
        "outbound_on_chain_abi_length": len(outbound_on_chain_abi),
        "outbound_on_chain_abi_hash": keccak(outbound_on_chain_abi).hex(),
        "inbound_sidecar_abi_length": len(inbound_sidecar_abi),
        "inbound_sidecar_abi_hash": keccak(inbound_sidecar_abi).hex(),
        "inbound_on_chain_abi_length": len(inbound_on_chain_abi),
        "inbound_on_chain_abi_hash": keccak(inbound_on_chain_abi).hex(),
        "payload_length": len(payload),
        "payload_hash": keccak(payload).hex(),
    }
    if actual != STRICT_EXPECTED:
        raise AssertionError(f"strict DA vector drift: {actual!r}")
    if private_key.public_key.to_checksum_address().lower() != STRICT_USER_ADDRESS:
        raise AssertionError("strict DA user address drift")

    return {
        "block_tx_counts": [0, 1],
        "transaction": transaction,
        "transaction_signing_hash": signing_hash,
        "user_address": STRICT_USER_ADDRESS,
        "anchor": anchor,
        "anchor_abi": anchor_abi,
        "outbound_sidecar": outbound_sidecar,
        "outbound_sidecar_abi": outbound_sidecar_abi,
        "outbound_on_chain": outbound_on_chain,
        "outbound_on_chain_abi": outbound_on_chain_abi,
        "inbound_sidecar": inbound_sidecar,
        "inbound_sidecar_abi": inbound_sidecar_abi,
        "inbound_on_chain": inbound_on_chain,
        "inbound_on_chain_abi": inbound_on_chain_abi,
        "inbound_proxy_entry_hash": inbound_proxy_entry_hash,
        "rolling_hash": rolling_hash,
        "payload": payload,
        "transient_execution_entry_count": 2,
        "transient_lookup_call_count": 0,
    }


def strict_da_manifest() -> dict[str, Any]:
    vector = strict_da_material()
    transaction = vector["transaction"]
    payload = vector["payload"]
    return {
        "fixture": "da-strict-fixture.py",
        "block_tx_counts": vector["block_tx_counts"],
        "sync_block_user_transaction_count": 1,
        "transactions": [
            {
                "type": "0x02",
                "chain_id": 1,
                "sender": vector["user_address"],
                "nonce": 0,
                "raw": "0x" + transaction.hex(),
                "raw_length": len(transaction),
                "signing_hash": "0x" + vector["transaction_signing_hash"].hex(),
                "transaction_hash": "0x" + keccak(transaction).hex(),
            }
        ],
        "l2_entries": [
            {
                "direction": "outbound",
                "abi": "0x" + vector["outbound_sidecar_abi"].hex(),
                "abi_length": len(vector["outbound_sidecar_abi"]),
                "abi_hash": "0x" + keccak(vector["outbound_sidecar_abi"]).hex(),
                "proxy_entry_hash": "0x" + bytes(32).hex(),
                "rolling_hash": "0x" + vector["rolling_hash"].hex(),
            },
            {
                "direction": "inbound",
                "abi": "0x" + vector["inbound_sidecar_abi"].hex(),
                "abi_length": len(vector["inbound_sidecar_abi"]),
                "abi_hash": "0x" + keccak(vector["inbound_sidecar_abi"]).hex(),
                "proxy_entry_hash": "0x"
                + vector["inbound_proxy_entry_hash"].hex(),
                "rolling_hash": "0x" + vector["rolling_hash"].hex(),
            }
        ],
        "corresponding_batch": {
            "entry_order": ["anchor", "outbound", "inbound"],
            "anchor_abi": "0x" + vector["anchor_abi"].hex(),
            "anchor_abi_hash": "0x" + keccak(vector["anchor_abi"]).hex(),
            "outbound_on_chain_abi": "0x" + vector["outbound_on_chain_abi"].hex(),
            "outbound_on_chain_abi_hash": "0x"
            + keccak(vector["outbound_on_chain_abi"]).hex(),
            "inbound_on_chain_abi": "0x" + vector["inbound_on_chain_abi"].hex(),
            "inbound_on_chain_abi_hash": "0x"
            + keccak(vector["inbound_on_chain_abi"]).hex(),
            "transient_execution_entry_count": vector[
                "transient_execution_entry_count"
            ],
            "transient_lookup_call_count": vector["transient_lookup_call_count"],
            "cross_proof_system_interactions": ZERO_BYTES32,
        },
        "payload": "0x" + payload.hex(),
        "payload_length": len(payload),
        "payload_hash": "0x" + keccak(payload).hex(),
    }


def fixture_document() -> dict[str, Any]:
    da_raw = bytes.fromhex(DA_PAYLOAD)
    development_private_key = keys.PrivateKey(
        bytes.fromhex(DEV_SYSTEM_PRIVATE_KEY.removeprefix("0x"))
    )
    derived_development_address = (
        development_private_key.public_key.to_checksum_address().lower()
    )
    if derived_development_address != DEV_SYSTEM_ADDRESS:
        raise AssertionError("development system identity drift")
    settlement = settlement_event_manifest()
    return {
        "format": "rollup0-v0-conformance-v3",
        "protocol": "rollup0-v0",
        "warning": (
            "This corpus is the Rollup0 5c51e02 compatibility binding. "
            "The EEZ 3a6ca65 framework corpus is separate."
        ),
        "sources": {
            "contract_binding": {
                "repository": "https://github.com/eez-association/sync-rollups-protocol",
                "revision": CONTRACT_REVISION,
            },
            "execution_and_codec": {
                "repository": "https://github.com/eez-association/eez-rollup0",
                "revision": EXECUTION_REVISION,
            },
        },
        "contract": {
            "solidity_fixture": "wire-vectors.s.sol",
            "portable": portable_vectors(),
            "compiler_derived": {
                "l1_execution_entry_hash": (
                    "0x0daea58ce2cc9573afca8e0d65214a534a31d70deba38062ae3026bd0ebc171e"
                ),
                "proxy_creation_code_length": 1111,
                "proxy_creation_code_hash": (
                    "0x0a2e4d916da3a258d274e03e75d9236477f377b91173aa46c9bde942adfb660c"
                ),
                "proxy_init_code_hash": (
                    "0x1f9d5a077e0d412d378cb6dab69a46400ad1d04d34817760a89ecbdff0b39561"
                ),
                "proxy_address": "0xaa1096867f5756db3f25f514708af546ee99e757",
            },
            "selectors": {
                "post_and_verify_batch": checked_selector(
                    POST_SIGNATURE, "0x8b1a095a"
                ),
                "load_execution_table": checked_selector(
                    LOAD_SIGNATURE, "0x59683c8b"
                ),
                "execute_incoming_cross_chain_call": checked_selector(
                    INBOUND_SIGNATURE, "0xeb494246"
                ),
                "get_timestamp_and_block_hash": checked_selector(
                    "getTimestampAndBlockHash(uint64)", "0x6db96461"
                ),
            },
            "events": settlement["events"],
            "rollup0_batch_constants": {
                "cross_proof_system_interactions": ZERO_BYTES32,
            },
        },
        "data_availability": {
            "channel": "callData",
            "tag": "0x00",
            "blob_indices": [],
            "outer_codec_vector": {
                "fixture": "da-rlp-fixture.py",
                "block_tx_counts": [2, 1],
                "sync_block_user_transaction_count": 1,
                "payload": "0x" + DA_PAYLOAD,
                "payload_length": len(da_raw),
                "payload_hash": "0x" + keccak(da_raw).hex(),
                "negative_case_count": 10,
                "inner_items": "opaque and not valid derivation inputs",
            },
            "strict_decoder_vector": strict_da_manifest(),
        },
        "system_transactions": {
            "fixture": "system-tx-fixture.py",
            "rust_cross_check": "system-tx-vector.rs",
            "envelope": "signed-legacy-eip155",
            "fixture_identity_scope": "fixture-only; not the development genesis identity",
            "fixture_private_key": SYSTEM_TX_FIXTURE_PRIVATE_KEY,
            "system_address": "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf",
            "development_profile_identity": {
                "private_key": DEV_SYSTEM_PRIVATE_KEY,
                "system_address": derived_development_address,
            },
            "gas_limit": 2000000,
            "gas_price_wei": 1000000000,
            "outbound": {
                "selector": "0x59683c8b",
                "raw_length": 620,
                "transaction_hash": (
                    "0x2e6768b4b7c3c8864d0142699bdfccc23c28de47d431a51962bfc29110b97b68"
                ),
            },
            "inbound": {
                "selector": "0xeb494246",
                "raw_length": 1133,
                "transaction_hash": (
                    "0xf22f620d60f898285607a2a52f80beb4f07f6dc4a408afb231c97bf979e02632"
                ),
            },
        },
        "settlement_attribution": {
            "fixture": "conformance_vectors.py",
            "ordered_outcome_cases": settlement["ordered_outcome_cases"],
            "rule": settlement["rule"],
        },
        "genesis": {
            "fixture": "genesis-hash-fixture.py",
            "artifact_sha256": (
                "0xfb1ca15108f3fa320471d344ac24c55925bd88d2ce57cdbfd2d069ced2e94ef6"
            ),
            "development_state_root": (
                "0xd381d828f650845aa890778c74ad2de245f5b3f2a24763f243e19a6bafb4fec5"
            ),
            "development_genesis_hash": (
                "0xcc2334a5f46d86829de4f761b295ee171731bdde1dcb20be6e2ccb6d504a0b56"
            ),
        },
        "timing_and_headers": {
            "fixture": "timing-header-fixture.py",
            "catchup_cap": 300,
            "block_gas_limit": 30000000,
            "eip1559_elasticity": 2,
            "eip1559_base_fee_change_denominator": 8,
            "genesis_base_fee_wei": 1000000000,
            "beneficiary": "0x0000000000000000000000000000000000000000",
        },
    }
