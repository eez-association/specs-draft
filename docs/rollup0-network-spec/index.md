# Rollup0 Network Specification

**The first EEZ rollup profile, settled on Gnosis Chiado**

| | |
|---|---|
| **Profile ID** | `rollup0-chiado` |
| **Protocol** | `rollup0-v0` |
| **Profile version** | `0.1-draft` |
| **Status** | Development profile; no production activation record exists |
| **EEZ framework** | [`eez-framework@0.1-draft`](../eez-protocol-spec/index.md) |
| **EVM compatibility binding** | `eez-evm@0.1-rollup0`, pinned to `5c51e02`; not `eez-evm@0.2-draft` |
| **Settlement host** | [Gnosis Chiado Rollup0 compatibility host profile](../gnosis-chain-eez-spec/index.md), `gnosis-chain-eez-chiado-rollup0@0.1-draft`, EIP-155 chain ID `10200` |
| **L2 execution** | Standard Ethereum EVM; the development template activates forks through Osaka |
| **Sequencing** | One permissioned operator |
| **Data availability** | Tag-`0x00` calldata only; `blobIndices=[]`; configured, key-gated replay |
| **Cross-chain scope** | One flat call per accepted entry in either L1↔L2 direction |

Rollup0 is the L2 implemented by `eez-rollup0`. Gnosis Chain is its settlement host, not another
name for the L2. This profile selects the Chiado testnet. It does not specify a Gnosis Chain
mainnet deployment or an Ethereum-mainnet Rollup0 deployment.

The profile uses the reusable EEZ framework but does not use the current
`eez-evm@0.2-draft` ABI. Its contracts, hashes, selectors, and proxy init code are the distinct
`eez-evm@0.1-rollup0` compatibility binding in [§0](00-protocol-version.md) and
[Appendix E](E-compatibility-binding.md). Implementations MUST NOT mix those editions.

## Normative precedence

The protocol manifest in §0 and the profile in §1 are the entry points for every Rollup0 v0
implementation. Appendix E is the self-contained normative transcription of the selected
compatibility binding and controls its ABI and wire surfaces. The EEZ framework controls reusable
framework concepts and the network-profile contract, but its current 0.2 ABI chapters and vectors
do not override Appendix E. The exact selected Gnosis host profile controls Chiado identity,
finality, deployment identity, and atomic inclusion; the remaining L2 choices belong to this
specification.

[§0.3](00-protocol-version.md#03-conflict-precedence) defines the complete source and
transcription precedence. A discrepancy across these supposedly disjoint surfaces is a release
blocker. A client MUST NOT resolve it by following a newer repository, the current EEZ binding, or
an address from the other Gnosis host profile.

## Abstract

Rollup0 synchronously composes contracts across Chiado and its L2. A composer simulates a
cross-chain interaction, builds the corresponding L2 blocks and EEZ batch, and submits settlement
through an all-or-nothing Chiado bundle. The L2 supports one flat inbound L1→L2 call or outbound
L2→L1 call per accepted entry. Multi-call and reentrant cross-chain execution are not enabled.

Rollup0 v0 represents L2 system operations as ordinary signed legacy EIP-155 transactions from a
prefunded `SYSTEM_ADDRESS`. A cross-chain deriver therefore needs the same private key to reproduce
transaction bytes. This key dependency is a documented development limitation and production
activation blocker, not a permissionless-following claim.

The Chiado timing profile has nominal 5-second host slots and 1-second L2 blocks. A steady slot has
three Live blocks, one pre-built Future block, and one Sync block. Actual production follows
observed canonical Chiado heads and includes explicit catch-up, missed-target, rollback, and
full-header validation rules.

## Conformance status

This profile is a development target, not a production-conforming network. The authoritative
Rollup0 blocker sets are in [§1.4](01-profile.md#14-completion-status) and
[§8](08-limitations.md); the activation-record and system-key blocker is summarized in
[§0.5](00-protocol-version.md#05-current-activation-blocker). The selected Gnosis host profile has
separate `GC-R0-*` blockers in the
[host deployment chapter](../gnosis-chain-eez-spec/02-deployment.md#22-release-blockers).
Production conformance requires both blocker sets to be empty.

## Implementation reading order

The first five steps prevent a client from silently selecting the wrong binding or host:

1. [Protocol Version & Compatibility](00-protocol-version.md)
2. [Network Profile](01-profile.md)
3. EEZ [Scope & Conformance](../eez-protocol-spec/01-scope-conformance.md),
   [Architecture](../eez-protocol-spec/02-architecture.md), and
   [Required Network Profile](../eez-protocol-spec/07-network-profile.md)
4. [Appendix E: Rollup0 v0 Compatibility Binding](E-compatibility-binding.md), not the current EEZ
   0.2 binding chapters or vectors
5. Gnosis Chain [Host Profile](../gnosis-chain-eez-spec/01-host-profile.md) and
   [Deployment & Release Blockers](../gnosis-chain-eez-spec/02-deployment.md), selecting
   `gnosis-chain-eez-chiado-rollup0@0.1-draft`
6. [Timing, Slot Production & Header Rules](02-block-production.md)
7. [The Composer](03-composer.md)
8. [Data Availability, Batches & Gnosis Bundles](04-da-batches-bundles.md)
9. [Cross-Chain Flows](05-l1-to-l2.md)
10. [Derivation and Following](06-derivation-following.md)
11. [Gas, Limits, and Economics](07-gas-economics.md)
12. [Limitations and Release Blockers](08-limitations.md)
13. [Security and Trust Model](09-security-trust-model.md)

[Future Design: Rollup1](10-future-design.md) and
[Gas & Cost Analysis](A-gas-cost-analysis.md) are informative.

Normative appendices:

- [Appendix B: DA Codec Vector](B-da-codec.md)
- [Appendix C: Signed System Transactions](C-system-transactions.md)
- [Appendix D: Genesis, Network Identity & Block Validity](D-genesis-validity.md)
- [Appendix E: Rollup0 v0 Compatibility Binding](E-compatibility-binding.md), required in step 4

The machine-readable Rollup0 v0 conformance corpus and verifier are under
[`fixtures/`](fixtures/conformance-vectors.json). They are pinned to the `5c51e02` compatibility
binding and are separate from the current EEZ `3a6ca65` framework vectors.

[Return to the specification set](../index.md).
