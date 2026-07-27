# EEZ Framework Specification

**Implementation-independent cross-chain framework and versioned EVM binding**

| | |
|---|---|
| **Specification ID** | `eez-framework` |
| **Specification version** | `0.1-draft` |
| **EVM binding ID and version** | `eez-evm@0.2-draft` |
| **Minimum execution fork** | Cancun-compatible `TLOAD`, `TSTORE`, `MCOPY`, and `BLOBHASH` |
| **Status** | Draft, normative intent |
| **Scope** | Reusable EEZ contract behavior, EVM call binding, ABI/wire encodings, and network-profile requirements |
| **Out of scope** | Any network's timing, candidate-admission policy, DA, proof-policy selection, addresses, genesis, fee policy, or Ethereum environment and deployment |

EEZ is a framework for precomputing cross-chain execution, committing that execution to a batch,
verifying the batch through network-selected proof systems, and replaying the committed result
through deterministic cross-chain proxies. The EVM binding defines the `EEZ` settlement contract,
the `EEZL2` execution manager, distinct L1 and L2 execution objects, replay state machines,
proof-input hashing, and canonical ABI encodings.

A network does not conform merely by implementing these contracts. It MUST publish a
[network profile](07-network-profile.md) that selects every deployment-dependent behavior and
pins `eez-framework@0.1-draft` plus an exact compatible EVM-binding edition. This document's
binding edition is `eez-evm@0.2-draft`.

This binding does not include the transient prefix counts or batch submitter in proof public
inputs. A production execution-network profile cannot select it without the versioned external
routing mitigation required by §7.5.

This document is the normative EEZ surface. No implementation repository or source commit is
normative. [Appendix B](B-wire-formats.md) records the source snapshot used to produce this
edition's conformance vectors so that the evidence can be reproduced. Rollup0-specific constraints
are in the separate [Rollup0 Network Specification](../rollup0-network-spec/index.md), and Gnosis
Chain-specific constraints are in the separate
[Gnosis Chain EEZ Network Specification](../gnosis-chain-eez-spec/index.md). Rollup0 and Gnosis
Chain are peer EEZ execution networks. Neither network hosts or inherits the other. Reentrancy,
static and failed lookups, forced rollback, and distinct side-specific tuple families are current
behavior of this binding; each network profile decides which interaction shapes it supports.

## Edition boundary

This document publishes the reusable `eez-framework@0.1-draft` layer together with one concrete
binding, `eez-evm@0.2-draft`. The exact ABIs, tuple layouts, selectors, hashes, proxy code, and
binding-specific state machines in §§3–5 and Appendices A–B belong to that 0.2 binding. A profile
that selects a different binding does not inherit those wire surfaces merely because it selects
the same framework edition.

Both peer network specifications select this edition. A disagreement between this binding and a
network profile is a release blocker, not permission to combine rules.

## Reading order

For a client implementing `eez-evm@0.2-draft`, read:

1. [Scope & Conformance](01-scope-conformance.md)
2. [Architecture](02-architecture.md)
3. [EVM Binding, Cross-Chain Proxy & Delivery](03-evm-binding.md)
4. [Execution Model](04-execution-model.md)
5. [Proving & Settlement](05-proving-settlement.md)
6. [Security & Trust Model](06-security-model.md)
7. [Required Network Profile](07-network-profile.md)

Appendices: [Protocol Reference](A-reference.md) ·
[Wire Formats & Conformance Vectors](B-wire-formats.md) ·
[Protocol Open Questions](C-open-questions.md).

[Return to the specification set](../index.md).
