# The Rollup0 Protocol Specification

**An EVM rollup with synchronous L1↔L2 composability.**

| | |
|---|---|
| **Status** | Draft / normative-intent. Client-agnostic; written to let independent client teams build conforming implementations. |
| **Settlement target** | Ethereum L1 (**12 s blocks**); Rollup0 and GC deploy on Ethereum. Test devnets may use a faster L1 (e.g. 5 s). |
| **Execution** | Cancun-equivalent Ethereum EVM (no custom opcodes or precompiles). |
| **v0 sequencing** | Single permissioned operator. L1 is the source of truth; the chain is re-derivable by anyone from L1 alone. |
| **v0 settlement** | A permissioned validator set (ECDSA *N*-of-*M* attestation over the batch's public-inputs hash). |
| **v0 composability** | Synchronous **L1→L2** with a single return value (the general bidirectional model is §13). |
| **Successor** | **Rollup1** — the permissionless, based, ZK-proven target (§13). |

---

## Abstract

Rollup0 is a Layer-2 rollup whose distinguishing property is **synchronous cross-chain
composability**: an L1 contract and an L2 contract can call into one another with the calls and
their results settling **atomically within a single L1 block** — more ambitious than the
asynchronous, two-transaction message-passing of deployed rollup stacks today, and the organizing
constraint behind nearly every design decision here.

A single off-chain **composer** observes a cross-chain intent, simulates the whole interaction
across both chains, and packs the result into a self-describing **batch**. That batch is posted to
L1 inside an all-or-nothing **bundle** alongside the user's own L1 transactions, so the entire
interaction lands — or fails — together. State is **committed optimistically on L2 and reconciled
against L1**: L1 is the sole source of truth, and any **follower** can re-derive the exact L2 chain
from L1 data without trusting the operator. Safety therefore does not depend on the operator; only
liveness does.

**EEZ vs Rollup0/GC.** *EEZ* is the general cross-chain protocol (contracts + execution/settlement
model). *Rollup0 / GC* is the first chain built on it, with deliberate v0 choices (centralized
operator, multisig settlement, L1→L2-only composability, full data availability). Choices labelled a
*Rollup0/GC choice* are specific to this chain, not EEZ requirements.

This specification is **self-contained and client-agnostic**: it specifies *what* a conforming
implementation must do, not *how* any particular client does it. Implementation guidance, the
adversarial threat model, related-work comparisons, and the blob DA format live in companion
documents outside this spec.

---

## Reading order

1. **[Overview & Scope](01-overview.md)** — EEZ vs Rollup0/GC, the v0 subset, conventions.
2. **[Architecture](02-architecture.md)** — the three roles and the on-chain contracts.
3. **[EVM, Proxy & System Tx](03-evm-proxy-systemtx.md)** — execution environment, cross-chain proxies, the inbound system transaction.
4. **[Block Production & Headers](04-block-production.md)** — header fields and the 6-block sync slot.
5. **[Execution Model](05-execution-model.md)** — the v0 cross-chain execution core: entries, rolling hash, verification.
6. **[The Composer](06-composer.md)** — the off-chain role, specified by behaviour and requirements.
7. **[DA, Batches & Bundles](07-da-batches-bundles.md)** — payload grammar, the batch, the L1 bundle.
8. **[Proving & Settlement](08-proving-settlement.md)** — the validator-set attestation and the public-inputs fold.
9. **[L1 → L2 Flow](09-l1-to-l2.md)** — the end-to-end synchronous-call journey.
10. **[Derivation & Following](10-derivation-following.md)** — re-deriving the chain from L1.
11. **[Gas & Economics](11-gas-economics.md)** — limits, fees, settlement and DA cost.
12. **[Open Issues & Limitations](12-open-issues.md)** — accepted v0 limitations and parameters to pin.
13. **[Rollup1 & the General Model](13-rollup1-general-model.md)** — the forward direction.

**Appendices:** [A — Reference](A-reference.md) (constants, formulae, glossary, errors) ·
[B — Gas & Cost Analysis](B-gas-cost-analysis.md) · [C — Open Questions](C-open-questions.md) ·
[D — Wire Formats & Conformance Vectors](D-wire-formats.md) *(the normative byte-exact encodings)*.
