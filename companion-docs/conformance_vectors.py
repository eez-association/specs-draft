#!/usr/bin/env python3
"""Build the deterministic EEZ and Rollup0 companion conformance manifest.

The suites are deliberately separate:

* ``eez-framework-current`` describes the current EEZ contract framework.
* ``rollup0-v0-contract`` describes the older contract binding selected by
  Rollup0 v0.
* The Rollup0 codec, system-transaction, genesis, and timing suites describe
  network-profile behavior that is not authored by either contract checkout.

The executable Solidity fixtures remain the authority for compiler-output
values such as ``type(CrossChainProxy).creationCode``. This module recomputes
portable hashes and selectors and records those Solidity-derived values with
their exact provenance.
"""

from __future__ import annotations

from typing import Any

from eth_abi import encode as abi_encode
from eth_utils import keccak


EEZ_REVISION = "3a6ca65c4858792fc3a143d34c5484877ef8f68c"
ROLLUP0_CONTRACT_REVISION = "5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba"
ROLLUP0_EXECUTION_REVISION = "00b3e75872fcc0c374d3b12a01933d732d317e4c"

TARGET = "0x00000000000000000000000000000000deadbeef"
SOURCE = "0x0000000000000000000000000000000000c0ffee"
MANAGER = "0x00000000000000000000000000000000000ee200"

EEZ_POST_SIGNATURE = (
    "postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,"
    "bytes,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,uint256,bytes)[],(bytes32,uint256,bytes,bool,uint64,"
    "uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[],"
    "(bytes32,uint256,bytes,bool,(bool,address,uint256,bytes,address,uint256,"
    "uint256)[],(bytes32,uint256,uint256,bytes)[],(bytes32,uint256,bytes,bool,"
    "uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32,"
    "(uint256,bytes32)[])[],uint256,uint256,address[],(uint256,uint64[])[],"
    "uint256[],bytes,bytes[],uint64))"
)
EEZ_LOAD_SIGNATURE = (
    "loadExecutionTable((bytes32,(bool,address,uint256,bytes,address,uint256,"
    "uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,"
    "uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],"
    "(bytes32,bytes,bool,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])"
)
EEZ_INBOUND_SIGNATURE = (
    "executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,"
    "(bytes32,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],"
    "(bytes32,bytes,bool,(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(bool,address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])"
)

ROLLUP0_POST_SIGNATURE = (
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
ROLLUP0_LOAD_SIGNATURE = (
    "loadExecutionTable((bytes32,(address,uint256,bytes,address,uint256,uint256)[],"
    "(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,"
    "(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],"
    "(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,"
    "uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,"
    "bytes32)[])"
)
ROLLUP0_INBOUND_SIGNATURE = (
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

DA_PAYLOAD = (
    "00f885c20201f85e"
    "9e02f8650180808094000000000000000000000000000000000000dead80c0"
    "9e02f8650180018094000000000000000000000000000000000000beef80c0"
    "9f02f865018002809400000000000000000000000000000000000000cafe80c0"
    "e1a000000000000000000000000000000000000000000000000000000000deadbeef"
)


def _selector(signature: str) -> str:
    return "0x" + keccak(text=signature)[:4].hex()


def _portable_vectors() -> dict[str, str]:
    action = keccak(
        abi_encode(
            ["uint256", "address", "uint256", "bytes", "address", "uint256"],
            [1, TARGET, 10**18, bytes.fromhex("deadbeef"), SOURCE, 0],
        )
    )
    after_begin = keccak(bytes(32) + bytes([1]) + (1).to_bytes(32, "big"))
    after_end = keccak(
        after_begin
        + bytes([2])
        + (1).to_bytes(32, "big")
        + b"\x01"
        + b"\x01"
    )
    return {
        "cross_chain_call_hash": "0x" + action.hex(),
        "rolling_hash_after_call_begin": "0x" + after_begin.hex(),
        "rolling_hash_after_call_end": "0x" + after_end.hex(),
    }


def _selectors(items: dict[str, tuple[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name, (signature, expected) in items.items():
        actual = _selector(signature)
        if actual != expected:
            raise AssertionError(
                f"{name} selector drift: computed {actual}, expected {expected}"
            )
        result[name] = {"signature": signature, "selector": actual}
    return result


def fixture_document() -> dict[str, Any]:
    """Return the canonical JSON-serializable companion corpus."""

    portable = _portable_vectors()
    expected_action = (
        "0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2"
    )
    if portable["cross_chain_call_hash"] != expected_action:
        raise AssertionError("portable cross-chain call hash drift")

    da_raw = bytes.fromhex(DA_PAYLOAD)
    return {
        "format": "eez-companion-conformance-v1",
        "warning": (
            "Suites have independent provenance. Do not substitute the EEZ "
            "framework checkout for the Rollup0 v0 contract binding."
        ),
        "suites": {
            "eez-framework-current": {
                "repository": "https://github.com/eez-association/eez-core-protocol",
                "revision": EEZ_REVISION,
                "solidity_fixture": "companion-docs/wire-vectors-eez-current.s.sol",
                "portable": portable,
                "contract_derived": {
                    "l1_execution_entry_hash": (
                        "0x51e1632383c7841fd9e2a174163aed36834896ede9a3d2f4936e1e67801bec71"
                    ),
                    "l1_lookup_hash": (
                        "0x85be8606cad0ae3cb989136c5b255fe107c1b93f36b086538a041f5f70185b57"
                    ),
                    "l2_execution_entry_hash": (
                        "0x3308472f724b8141fe223e74d2ab939d2e0bd8668aaa25c21c8b611af0dec0fa"
                    ),
                    "public_inputs_hash": (
                        "0xe265e1c1fbc52c560558b76be4ede800269f90a65b7065c3e0ffc9baadb83076"
                    ),
                    "proxy_creation_code_length": 1111,
                    "proxy_creation_code_hash": (
                        "0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8"
                    ),
                    "proxy_init_code_hash": (
                        "0x7045969eb5c85c24a087914cfde032ebaa277996f1a2ea343a2b7d92af3e7c4b"
                    ),
                    "proxy_address": "0xc5dc78b57986585780dc0c44b99a94888522e50c",
                },
                "selectors": _selectors(
                    {
                        "post_and_verify_batch": (
                            EEZ_POST_SIGNATURE,
                            "0xd1fc6b5a",
                        ),
                        "load_execution_table": (
                            EEZ_LOAD_SIGNATURE,
                            "0xc1b4427c",
                        ),
                        "execute_incoming_cross_chain_call": (
                            EEZ_INBOUND_SIGNATURE,
                            "0xf882a0ad",
                        ),
                    }
                ),
            },
            "rollup0-v0-contract": {
                "repository": "https://github.com/eez-association/sync-rollups-protocol",
                "revision": ROLLUP0_CONTRACT_REVISION,
                "solidity_fixture": "companion-docs/wire-vectors-rollup0-v0.s.sol",
                "portable": portable,
                "contract_derived": {
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
                "selectors": _selectors(
                    {
                        "post_and_verify_batch": (
                            ROLLUP0_POST_SIGNATURE,
                            "0x8b1a095a",
                        ),
                        "load_execution_table": (
                            ROLLUP0_LOAD_SIGNATURE,
                            "0x59683c8b",
                        ),
                        "execute_incoming_cross_chain_call": (
                            ROLLUP0_INBOUND_SIGNATURE,
                            "0xeb494246",
                        ),
                        "get_timestamp_and_block_hash": (
                            "getTimestampAndBlockHash(uint64)",
                            "0x6db96461",
                        ),
                    }
                ),
            },
            "rollup0-v0-da": {
                "repository": "https://github.com/eez-association/eez-rollup0",
                "revision": ROLLUP0_EXECUTION_REVISION,
                "fixture": "companion-docs/da-rlp-fixture.py",
                "tag": "0x00",
                "block_tx_counts": [2, 1],
                "sync_block_user_transaction_count": 1,
                "payload": "0x" + DA_PAYLOAD,
                "payload_length": len(da_raw),
                "payload_hash": "0x" + keccak(da_raw).hex(),
                "negative_case_count": 10,
            },
            "rollup0-v0-system-transactions": {
                "repository": "https://github.com/eez-association/eez-rollup0",
                "revision": ROLLUP0_EXECUTION_REVISION,
                "fixture": "companion-docs/system-tx-fixture.py",
                "envelope": "signed-legacy-eip155",
                "system_address": "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf",
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
            "rollup0-v0-genesis": {
                "fixture": "companion-docs/genesis-hash-fixture.py",
                "profile_fixture": (
                    "docs/rollup0-network-spec/fixtures/genesis-validation-vector.json"
                ),
                "development_fixture": (
                    "docs/rollup0-network-spec/fixtures/genesis-dev.json"
                ),
            },
            "rollup0-v0-timing-and-headers": {
                "fixture": "companion-docs/timing-header-fixture.py",
                "catchup_cap": 300,
                "sync_composition_rule": (
                    "a Sync block is last and can contain a nonzero user-transaction count"
                ),
            },
        },
    }
