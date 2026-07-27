# Companion Material

This directory contains review records, executable fixtures, and generated
conformance data. It is informative. The normative specifications are:

- [EEZ Framework](../docs/eez-protocol-spec/index.md)
- [Rollup0 Network](../docs/rollup0-network-spec/index.md)
- [Gnosis Chain EEZ Profile](../docs/gnosis-chain-eez-spec/index.md)

## Conformance suites

The generated corpus keeps independently versioned sources separate:

| Suite | Selected source | Executable cross-check |
|---|---|---|
| EEZ framework | `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` | `wire-vectors-eez-current.s.sol` |
| Rollup0 v0 contract binding | `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` | `wire-vectors-rollup0-v0.s.sol` |
| Rollup0 execution, codec, and system transactions | `eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c` | Python and Rust fixtures |
| Rollup0 genesis, timing, and header rules | Rollup0 network profile | Python fixtures |

The EEZ and Rollup0 Solidity fixtures are not interchangeable. Compiler-output
values, struct layouts, and selectors differ between the two selected contract
revisions.

Create an isolated environment and run the complete companion check:

```console
python3 -m venv .venv-conformance
. .venv-conformance/bin/activate
python3 -m pip install -r companion-docs/conformance-requirements.txt
python3 companion-docs/verify-conformance.py
```

Regenerate the checked-in JSON corpus after an intentional fixture change:

```console
python3 companion-docs/verify-conformance.py --write
python3 companion-docs/verify-conformance.py
```

Cross-check compiler-authored vectors by copying the matching Solidity fixture
to `script/WireVectors.s.sol` in its selected checkout:

```console
# eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c
forge script script/WireVectors.s.sol --offline -vv

# sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba
forge script script/WireVectors.s.sol -vvv
```

The active Rollup0 system transaction is a signed legacy EIP-155 transaction.
Type `0x7E` is future design material only.
