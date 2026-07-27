# EEZ Specifications

This site contains three separately versioned specifications. Each has its own owner, scope,
conformance target, and navigation section.

| Specification | Owns |
|---|---|
| [EEZ Framework Specification](eez-protocol-spec/index.md) | Implementation-independent cross-chain behavior, the versioned EVM binding, wire formats, conformance vectors, and the required network-profile schema. |
| [Rollup0 Network Specification](rollup0-network-spec/index.md) | The Rollup0 L2 identity, compatibility binding, execution, sequencing, data availability, proof policy, derivation, economics, and settlement-host selection. |
| [Gnosis Chain EEZ Network Specification](gnosis-chain-eez-spec/index.md) | The Chiado host-chain identity and finality rules, shared EEZ deployment identity, and required atomic-inclusion capability. It does not own Rollup0 configuration. |

The dependency direction is:

```text
Rollup0 Network Specification ──pins──> EEZ Framework Specification
             │
             └──selects──> Gnosis Chain EEZ Network Specification
                                      │
                                      └──pins──> EEZ Framework Specification
```

“Rollup0” names the L2 network. “Gnosis Chain” names its settlement-network family; the current
implementation target is the Chiado testnet. They are not aliases. No specification on this site
combines the two identities or assigns the current Rollup0 implementation an Ethereum settlement
target.

The normative framework and rollup identities in this edition are
`eez-framework@0.1-draft` and `rollup0-chiado@0.1-draft`. The Gnosis Chain specification
publishes two binding-specific host profiles:
`gnosis-chain-eez-chiado@0.1-draft` for `eez-evm@0.2-draft`, and
`gnosis-chain-eez-chiado-rollup0@0.1-draft` for Rollup0's
`eez-evm@0.1-rollup0` compatibility binding. Repository names, branches, and commit hashes are
implementation or test-vector provenance; they are not substitutes for these specification and
profile identifiers.

Rollup0 v0 selects the Rollup0 compatibility host profile. It does not select the current
`eez-evm@0.2-draft` host profile. A client MUST NOT mix their deployments, ABI layouts, selectors,
hashes, or conformance vectors.

## Normative precedence

An implementation starts from an exact network-profile ID and version. That profile selects one
EEZ framework edition, one EVM-binding edition, and, for a rollup, one exact settlement-host
profile. “Latest,” a repository `HEAD`, and an unversioned deployment name are not selectors.

The selected EVM-binding specification controls contract ABIs, tuple layouts, selectors, hash
preimages, proxy code, and binding-specific state machines. For `eez-evm@0.2-draft`, those rules
are in the EEZ Framework Specification. For `eez-evm@0.1-rollup0`, they are in Rollup0
[§0](rollup0-network-spec/00-protocol-version.md) and
[Appendix E](rollup0-network-spec/E-compatibility-binding.md); the current 0.2 binding is not a
fallback.

The Rollup0 specification controls Rollup0 L2 behavior and the exact Rollup0 profile. The selected
Gnosis Chain host profile controls Chiado identity, consensus/finality, its binding-specific
`EEZ` deployment, and the atomic-inclusion trust boundary. These ownership surfaces are disjoint.
A contradiction between them is a release blocker and MUST NOT be resolved by choosing whichever
document or implementation is newer. Rollup0's detailed source and transcription precedence is in
[§0.3](rollup0-network-spec/00-protocol-version.md#03-conflict-precedence).

## Implementation entry paths

To reimplement a Rollup0 v0 client without relying on an implementation repository or older
combined documentation:

1. Read Rollup0 [§0](rollup0-network-spec/00-protocol-version.md) and
   [§1](rollup0-network-spec/01-profile.md) to pin the protocol, profile, binding, and host.
2. Read the EEZ [scope](eez-protocol-spec/01-scope-conformance.md),
   [architecture](eez-protocol-spec/02-architecture.md), and
   [network-profile contract](eez-protocol-spec/07-network-profile.md) for the reusable framework
   layer.
3. Read Rollup0 [Appendix E](rollup0-network-spec/E-compatibility-binding.md) for the exact
   compatibility ABI and wire behavior. Do not substitute the EEZ 0.2 binding chapters or vectors.
4. Read the Gnosis Chain [host profile](gnosis-chain-eez-spec/01-host-profile.md) and
   [deployment blockers](gnosis-chain-eez-spec/02-deployment.md), selecting
   `gnosis-chain-eez-chiado-rollup0@0.1-draft`.
5. Continue through Rollup0 §§2–9 and its normative appendices and conformance corpus in the order
   listed on the [Rollup0 overview](rollup0-network-spec/index.md).

To implement the current `eez-evm@0.2-draft` binding, follow the
[EEZ Framework reading order](eez-protocol-spec/index.md#reading-order). A Chiado deployment also
requires `gnosis-chain-eez-chiado@0.1-draft`; the host profile alone does not supply the
consumer-rollup choices required by the EEZ network-profile schema.

All three specifications are drafts. A field marked `release-blocker` has no authoritative
production value in the repositories reviewed for this edition and MUST be fixed before a
production profile can claim conformance.
