# Companion Material

This directory contains informative implementation evidence, executable
fixtures, historical reviews, and comparative material. It is not normative.
The normative specifications are:

- [EEZ Framework](../docs/eez-protocol-spec/index.md)
- [Rollup0 Network](../docs/rollup0-network-spec/index.md)
- [Gnosis Chain EEZ Network](../docs/gnosis-chain-eez-spec/index.md)

## Source categories

Do not combine the following categories:

| Category | Selected source | Meaning |
|---|---|---|
| Normative EEZ binding | `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` | The `eez-evm@0.2-draft` ABI, wire formats, and compiler-derived vectors selected by both network specifications. |
| Reviewed Rollup0 implementation | `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` | Evidence for current node behavior and known deviations. It is not a protocol selector. |
| Recorded Rollup0 contract submodule | `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` | The older binding recorded by the reviewed Rollup0 implementation. Its difference from the selected binding is a release blocker. |
| Historical execution fixtures | `eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c` | Reproducible codec and signed-system-transaction snapshots retained for regression analysis. They do not define the current network profile. |

The active network specifications select the first row. The other rows document
implementation history. In particular, the `rollup0-v0-contract` suite and
`wire-vectors-rollup0-v0.s.sol` MUST NOT be used to implement
`eez-evm@0.2-draft`.

Rollup0 and Gnosis Chain are separate EEZ execution networks. Both production
networks settle on Ethereum. Chiado appears only in development profiles.
Rollup0 uses validity-only, open candidate admission. Gnosis Chain additionally
requires an authorized composer signature. No adjacent implementation reviewed
for this edition implements the Gnosis Chain authorization rule.

## Conformance checks

Create an isolated environment and run the companion checks:

```console
python3 -m venv .venv-conformance
. .venv-conformance/bin/activate
python3 -m pip install -r companion-docs/conformance-requirements.txt
python3 companion-docs/verify-conformance.py
```

Regenerate the checked-in JSON corpus only after an intentional fixture change:

```console
python3 companion-docs/verify-conformance.py --write
python3 companion-docs/verify-conformance.py
```

Cross-check compiler-authored vectors against the exact matching checkout:

```console
# Run from the rollup0-spec repository root.
test "$(git -C ../eez-core-protocol rev-parse HEAD)" = \
  3a6ca65c4858792fc3a143d34c5484877ef8f68c
cp companion-docs/wire-vectors-eez-current.s.sol \
  ../eez-core-protocol/script/WireVectors.s.sol
(cd ../eez-core-protocol && forge script script/WireVectors.s.sol --offline -vv)

# Historical implementation-binding diagnostic only
test "$(git -C ../eez-rollup0/sync-rollups-protocol rev-parse HEAD)" = \
  5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba
cp companion-docs/wire-vectors-rollup0-v0.s.sol \
  ../eez-rollup0/sync-rollups-protocol/script/WireVectors.s.sol
(cd ../eez-rollup0/sync-rollups-protocol && forge script script/WireVectors.s.sol -vvv)
```

The historical Rollup0 fixture uses a signed legacy EIP-155 system
transaction. The production system-transaction authorization method is an
unresolved network-profile blocker. Type `0x7E` remains future design material.
