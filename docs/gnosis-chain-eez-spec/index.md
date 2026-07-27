# Gnosis Chain EEZ Network Specification

**Chiado EEZ settlement-host network profiles**

| | |
|---|---|
| **Status** | Both host profiles are development drafts; neither is production conforming |
| **Current environment** | Gnosis Chiado testnet, EIP-155 chain ID `10200` |
| **EEZ framework** | [`eez-framework@0.1-draft`](../eez-protocol-spec/index.md) |
| **Role** | Identifies Chiado and an edition-specific L1 `EEZ` deployment and specifies the host finality, governance, and atomic-inclusion trust boundary |
| **Nominal slot** | 5 seconds |
| **Minimum EVM fork** | Chiado Dencun activation at timestamp `1706724940`; later compatible forks are permitted |
| **Gas and fee rules** | Canonical Chiado execution-header and chain-configuration rules |
| **Native asset** | Chiado xDAI |

These are Gnosis-specific profiles of the EEZ settlement-host role. They are separate from the
[Rollup0 Network Specification](../rollup0-network-spec/index.md): Gnosis Chiado supplies the EVM
and consensus in which Rollup0 batches settle, while Rollup0 supplies the L2 execution network.
Per-rollup IDs, managers, proof systems, sequencing, DA, and derivation remain owned by each
consumer network profile even when their contracts and data reside on Chiado.

The reviewed implementations support **Chiado**. This draft does not assert that an EEZ deployment
exists on Gnosis Chain mainnet, does not identify Gnosis Chain as Rollup0, and assigns no
recursive EEZ settlement target to either host profile.

The following machine-readable profiles share the Chiado consensus choices but select different
and non-interchangeable EEZ EVM bindings and deployments:

| Profile | EVM binding | Consumer | Release blockers |
|---|---|---|---|
| [`gnosis-chain-eez-chiado@0.1-draft`](network-profile.json) | `eez-evm@0.2-draft` | Current-binding EEZ consumers | `GC-DEPLOYMENT`, `GC-GENESIS`, `GC-ATOMIC-INCLUSION`, `GC-UPGRADES` |
| [`gnosis-chain-eez-chiado-rollup0@0.1-draft`](network-profile-rollup0.json) | `eez-evm@0.1-rollup0` | Rollup0 v0 | `GC-R0-DEPLOYMENT`, `GC-R0-GENESIS`, `GC-R0-ATOMIC-INCLUSION`, `GC-R0-UPGRADES` |

A consumer MUST select one exact profile ID and version. A deployment record, contract address, or
release-blocker resolution from one profile MUST NOT satisfy the other profile. The complete
blocker conditions are normative in [§2.2](02-deployment.md#22-release-blockers).

## Normative precedence

The consumer's exact profile selection determines which row applies. The selected EVM-binding
specification controls the `EEZ` ABI and binding behavior. This specification controls only
Chiado identity, consensus/finality, the binding-specific host deployment, host governance, and
the atomic-inclusion trust boundary. The consuming rollup profile controls its rollup ID,
manager, proof systems, sequencing, DA, and derivation.

These ownership surfaces do not override one another. A mismatch in binding version, deployment
identity, or supposedly shared field is a release blocker; a client MUST NOT fall back to the
other host profile. Rollup0 v0 uses its
[compatibility binding](../rollup0-network-spec/E-compatibility-binding.md), while a current
`eez-evm@0.2-draft` consumer uses the binding in the
[EEZ Framework Specification](../eez-protocol-spec/index.md#edition-boundary).

## Reading order

After the consumer selects one exact profile ID and binding edition, read:

1. The selected binding specification: the
   [current EEZ binding](../eez-protocol-spec/index.md#reading-order) or the Rollup0
   [compatibility binding](../rollup0-network-spec/E-compatibility-binding.md)
2. [Host Profile](01-host-profile.md)
3. [Deployment & Release Blockers](02-deployment.md)
4. [Security & Trust Model](03-security-trust-model.md)

Reusable framework semantics remain in the
[EEZ Framework Specification](../eez-protocol-spec/index.md). Binding-specific ABI rules remain in
the exact selected binding specification identified above.

[Return to the specification set](../index.md).
