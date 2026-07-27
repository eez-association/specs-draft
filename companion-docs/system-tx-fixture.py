#!/usr/bin/env python3
"""
Reproduce the Rollup0 v0 signed-system-transaction vectors from Appendix C.

Requires:

    python3 -m pip install eth-abi eth-keys eth-utils rlp

The mixed Sync-block example builds, in canonical order:

1. a zero-value `loadExecutionTable` legacy transaction at nonce N; and
2. a value-bearing `executeIncomingCrossChainCall` legacy transaction at N + 1.

The consuming outbound user transaction belongs between them in a real block but is
not part of this system-transaction fixture. Both system envelopes are EIP-155
legacy RLP with no EIP-2718 type byte. The public test private key is 1 and MUST
NOT be used by a deployment.
"""

from dataclasses import dataclass

from eth_abi import encode
from eth_keys import keys
from eth_utils import keccak
import rlp


PRIVATE_KEY = bytes.fromhex("00" * 31 + "01")
CHAIN_ID = 1
PARENT_NONCE = 7
GAS_PRICE = 1_000_000_000
GAS_LIMIT = 2_000_000
EEZL2 = bytes.fromhex("4200000000000000000000000000000000000007")

THIS_ROLLUP_ID = 1
DESTINATION = bytes.fromhex("00" * 19 + "aa")
VALUE = 1
DATA = bytes.fromhex("010203")
SOURCE_ADDRESS = bytes.fromhex("00" * 19 + "bb")
SOURCE_ROLLUP_ID = 0
RETURN_DATA = b""

EXPECTED_SYSTEM_ADDRESS = "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf"
EXPECTED_INBOUND_HASH = (
    "1f284e30e41e175a4f638c727e4b370c580a647426312a0c290593ee6ae63899"
)
EXPECTED_INBOUND_ROLLING_HASH = (
    "68676dacdc339269dad7302dad8697771c8c23d92fa956992dc881fce33e0764"
)

# Filled with byte-exact values printed by this fixture. Keeping them here turns
# the document example into a regression test rather than a sample generator.
EXPECTED_OUTBOUND = {
    "call_hash": "8a96fd707d43c792dc3998ec6cc2df864750a72ca333e0c6b43b19bb8f137f9a",
    "selector": "59683c8b",
    "calldata_length": 516,
    "calldata_hash": "01eaeccabea6f657b4b8491fb612a46358117dfb43c5f6463d7fae57f8e392bc",
    "signing_hash": "5cecb66a0f6ca11e249d9cd2df56b5edffd4874ee5af8d3b574b2968cd98543a",
    "v": 37,
    "r": "7a5aac2b70cfbf7d88e3909ecc9e3a820c272d5dbeb46f0a30a378f2058a3722",
    "s": "006bbb8a2516452791caf3e1012934d306c1b647af6a4affb83bd5f8a723885d",
    "raw_length": 620,
    "tx_hash": "2e6768b4b7c3c8864d0142699bdfccc23c28de47d431a51962bfc29110b97b68",
}
EXPECTED_INBOUND = {
    "selector": "eb494246",
    "calldata_length": 1028,
    "calldata_hash": "67d2a716201823cca90b4fe8501f259092af46e369bc354ae992d1e8ff5cb4e5",
    "signing_hash": "27a83de4679bed813a7c8ef5f748de7fe128fc8f2a45565292c084252265d73f",
    "v": 37,
    "r": "e69384d342a71ecebb1c75226ad803e483f34bb48e2f3702503769e36b2a07bb",
    "s": "0404757fa64da4c22c0727e8dea0b9984d75f520c207c32ac479e2a3a7fc87f2",
    "raw_length": 1133,
    "tx_hash": "f22f620d60f898285607a2a52f80beb4f07f6dc4a408afb231c97bf979e02632",
}


CROSS_CHAIN_CALL_TYPE = "(address,uint256,bytes,address,uint256,uint256)"
OUTGOING_CALL_TYPE = "(bytes32,uint256,bytes)"
NESTED_LOOKUP_TYPE = (
    "(bytes32,bytes,bool,uint64,uint64,uint64,"
    f"{CROSS_CHAIN_CALL_TYPE}[],{OUTGOING_CALL_TYPE}[],uint256,bytes32)"
)
ENTRY_TYPE = (
    f"(bytes32,{CROSS_CHAIN_CALL_TYPE}[],{OUTGOING_CALL_TYPE}[],"
    f"{NESTED_LOOKUP_TYPE}[],uint256,bytes,bytes32)"
)
TOP_LOOKUP_TYPE = (
    f"(bytes32,bytes,bool,{CROSS_CHAIN_CALL_TYPE}[],{OUTGOING_CALL_TYPE}[],"
    f"{NESTED_LOOKUP_TYPE}[],uint256,bytes32)"
)
LOAD_SIGNATURE = f"loadExecutionTable({ENTRY_TYPE}[],{TOP_LOOKUP_TYPE}[])"
INBOUND_SIGNATURE = (
    "executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,"
    f"{ENTRY_TYPE}[],{TOP_LOOKUP_TYPE}[])"
)


@dataclass(frozen=True)
class SignedVector:
    calldata: bytes
    signing_preimage: bytes
    signing_hash: bytes
    v: int
    r: int
    s: int
    raw_transaction: bytes
    tx_hash: bytes


def uint256(value: int) -> bytes:
    return value.to_bytes(32, "big")


def cross_chain_call_hash(
    target_rollup: int,
    target: bytes,
    value: int,
    data: bytes,
    source: bytes,
    source_rollup: int,
) -> bytes:
    return keccak(
        encode(
            ["uint256", "address", "uint256", "bytes", "address", "uint256"],
            [target_rollup, target, value, data, source, source_rollup],
        )
    )


def build_outbound_calldata() -> tuple[bytes, bytes]:
    call_hash = cross_chain_call_hash(
        0,
        DESTINATION,
        VALUE,
        DATA,
        SOURCE_ADDRESS,
        THIS_ROLLUP_ID,
    )
    entry = (
        call_hash,
        [],  # incomingCalls
        [],  # expectedOutgoingCalls
        [],  # expectedLookups
        0,  # callCount
        RETURN_DATA,
        bytes(32),  # rollingHash
    )
    selector = keccak(text=LOAD_SIGNATURE)[:4]
    calldata = selector + encode(
        [f"{ENTRY_TYPE}[]", f"{TOP_LOOKUP_TYPE}[]"],
        [[entry], []],
    )
    return calldata, call_hash


def build_inbound_calldata() -> tuple[bytes, bytes, bytes]:
    call_hash = cross_chain_call_hash(
        THIS_ROLLUP_ID,
        DESTINATION,
        VALUE,
        DATA,
        SOURCE_ADDRESS,
        SOURCE_ROLLUP_ID,
    )
    rolling_hash = keccak(bytes(32) + b"\x01" + uint256(1))
    rolling_hash = keccak(
        rolling_hash + b"\x02" + uint256(1) + b"\x01" + RETURN_DATA
    )
    incoming_call = (
        DESTINATION,
        VALUE,
        DATA,
        SOURCE_ADDRESS,
        SOURCE_ROLLUP_ID,
        0,  # revertSpan
    )
    entry = (
        call_hash,
        [incoming_call],
        [],  # expectedOutgoingCalls
        [],  # expectedLookups
        1,  # callCount
        RETURN_DATA,
        rolling_hash,
    )
    selector = keccak(text=INBOUND_SIGNATURE)[:4]
    calldata = selector + encode(
        [
            "address",
            "uint256",
            "bytes",
            "address",
            "uint256",
            f"{ENTRY_TYPE}[]",
            f"{TOP_LOOKUP_TYPE}[]",
        ],
        [
            DESTINATION,
            VALUE,
            DATA,
            SOURCE_ADDRESS,
            SOURCE_ROLLUP_ID,
            [entry],
            [],  # lookupCalls
        ],
    )
    return calldata, call_hash, rolling_hash


def sign_legacy(nonce: int, value: int, calldata: bytes) -> SignedVector:
    unsigned_fields = [
        nonce,
        GAS_PRICE,
        GAS_LIMIT,
        EEZL2,
        value,
        calldata,
        CHAIN_ID,
        0,
        0,
    ]
    signing_preimage = rlp.encode(unsigned_fields)
    signing_hash = keccak(signing_preimage)
    signature = keys.PrivateKey(PRIVATE_KEY).sign_msg_hash(signing_hash)
    v = 35 + 2 * CHAIN_ID + signature.v
    raw_transaction = rlp.encode(
        [
            nonce,
            GAS_PRICE,
            GAS_LIMIT,
            EEZL2,
            value,
            calldata,
            v,
            signature.r,
            signature.s,
        ]
    )
    return SignedVector(
        calldata=calldata,
        signing_preimage=signing_preimage,
        signing_hash=signing_hash,
        v=v,
        r=signature.r,
        s=signature.s,
        raw_transaction=raw_transaction,
        tx_hash=keccak(raw_transaction),
    )


def assert_expected(
    vector: SignedVector,
    expected: dict[str, object],
    *,
    call_hash: bytes | None = None,
) -> None:
    # Empty placeholders are used only while regenerating a vector deliberately.
    # The committed fixture requires every expected value to be populated.
    assert all(value not in ("", 0) for value in expected.values())
    if call_hash is not None:
        assert call_hash.hex() == expected["call_hash"]
    assert vector.calldata[:4].hex() == expected["selector"]
    assert len(vector.calldata) == expected["calldata_length"]
    assert keccak(vector.calldata).hex() == expected["calldata_hash"]
    assert vector.signing_hash.hex() == expected["signing_hash"]
    assert vector.v == expected["v"]
    assert f"{vector.r:064x}" == expected["r"]
    assert f"{vector.s:064x}" == expected["s"]
    assert len(vector.raw_transaction) == expected["raw_length"]
    assert vector.tx_hash.hex() == expected["tx_hash"]


def decode_and_recover(
    vector: SignedVector,
    *,
    nonce: int,
    value: int,
) -> str:
    decoded = rlp.decode(vector.raw_transaction)
    assert len(decoded) == 9
    assert int.from_bytes(decoded[0], "big") == nonce
    assert int.from_bytes(decoded[1], "big") == GAS_PRICE
    assert int.from_bytes(decoded[2], "big") == GAS_LIMIT
    assert decoded[3] == EEZL2
    assert int.from_bytes(decoded[4], "big") == value
    assert decoded[5] == vector.calldata
    encoded_v = int.from_bytes(decoded[6], "big")
    encoded_chain_id = (encoded_v - 35) // 2
    parity = (encoded_v - 35) % 2
    assert encoded_chain_id == CHAIN_ID
    recovered = keys.Signature(
        vrs=(
            parity,
            int.from_bytes(decoded[7], "big"),
            int.from_bytes(decoded[8], "big"),
        )
    ).recover_public_key_from_msg_hash(vector.signing_hash)
    return recovered.to_checksum_address().lower()


def print_vector(label: str, vector: SignedVector) -> None:
    print(f"{label} calldata         = 0x{vector.calldata.hex()}")
    print(f"{label} calldata length  = {len(vector.calldata)} bytes")
    print(f"{label} calldata hash    = 0x{keccak(vector.calldata).hex()}")
    print(f"{label} signing preimage = 0x{vector.signing_preimage.hex()}")
    print(f"{label} signing hash     = 0x{vector.signing_hash.hex()}")
    print(f"{label} v, r, s          = {vector.v} 0x{vector.r:064x} 0x{vector.s:064x}")
    print(f"{label} raw transaction  = 0x{vector.raw_transaction.hex()}")
    print(f"{label} raw length       = {len(vector.raw_transaction)} bytes")
    print(f"{label} transaction hash = 0x{vector.tx_hash.hex()}")


def main() -> None:
    private_key = keys.PrivateKey(PRIVATE_KEY)
    assert private_key.public_key.to_checksum_address().lower() == EXPECTED_SYSTEM_ADDRESS

    outbound_calldata, outbound_hash = build_outbound_calldata()
    inbound_calldata, inbound_hash, inbound_rolling_hash = build_inbound_calldata()
    assert inbound_hash.hex() == EXPECTED_INBOUND_HASH
    assert inbound_rolling_hash.hex() == EXPECTED_INBOUND_ROLLING_HASH

    outbound = sign_legacy(PARENT_NONCE, 0, outbound_calldata)
    inbound = sign_legacy(PARENT_NONCE + 1, VALUE, inbound_calldata)

    print("system address      = " + EXPECTED_SYSTEM_ADDRESS)
    print("outbound call hash  = 0x" + outbound_hash.hex())
    print("inbound call hash   = 0x" + inbound_hash.hex())
    print("inbound rolling hash= 0x" + inbound_rolling_hash.hex())
    print_vector("outbound", outbound)
    print_vector("inbound ", inbound)

    # These assertions intentionally follow printing so a deliberate vector
    # regeneration exposes every replacement value in one run.
    assert_expected(outbound, EXPECTED_OUTBOUND, call_hash=outbound_hash)
    assert_expected(inbound, EXPECTED_INBOUND)
    assert (
        decode_and_recover(outbound, nonce=PARENT_NONCE, value=0)
        == EXPECTED_SYSTEM_ADDRESS
    )
    assert (
        decode_and_recover(inbound, nonce=PARENT_NONCE + 1, value=VALUE)
        == EXPECTED_SYSTEM_ADDRESS
    )
    print("decode/recovery     = OK (both transactions)")


if __name__ == "__main__":
    main()
