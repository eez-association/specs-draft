# 13. Rollup1 & the General Model

v0 is a deliberate subset. This chapter specifies the **general EEZ execution model** that v0
restricts, and the **Rollup1** target that lifts v0's trust assumptions. Material here is the
forward direction, not v0-normative.

## 13.1 General execution model

The execution machinery of §5 generalizes from "one L1→L2 call, one return" to arbitrary
bidirectional, multi-call, reentrant cross-chain interactions. The additional structures, all
already present in the contracts (§5.1), are unused in v0:

- **Reentrancy — `expectedL1ToL2Calls` (`ExpectedL1ToL2Call`).** A successful reentrant cross-chain
  call (the destination calls back into the source mid-execution) is pre-resolved as a nested
  action: `{ crossChainCallHash, callCount, returnData }`. A single global cursor walks the entry's
  flat `L2ToL1Calls`; the **partition invariant** holds:
  `entry.callCount + Σ expectedL1ToL2Calls[i].callCount == L2ToL1Calls.length`. Reentrant frames are
  bracketed in the rolling hash by `NESTED_BEGIN (3)` / `NESTED_END (4)`.
- **Reverting-call lookups — `LookupCall` with `failed = true`.** Proven cross-chain **reads**
  (`STATICCALL`, `failed = false`, resolved via `staticCallLookup`, must not mutate state) are
  **already part of v0** (§3.5, §5.3). The general-model extension is the *reverting* lookup: an
  intentionally-reverting cross-chain call is looked up — not executed on the mutating path — with
  `failed = true`, and replays by reverting with the cached data (resolved via the reentrant
  fallback or the top-level miss path). The `LookupCall` type carries the call and its precomputed
  result, matched by `crossChainCallHash` plus the cursor coordinate; read sub-calls are checked
  against the lookup's own rolling hash.
- **`revertSpan`.** Forces the state effects of a span of otherwise-successful calls to be rolled
  back at the protocol layer (the processor self-calls a context that always reverts, carrying the
  cursors and rolling hash out in the revert payload). For forced reverts only; a
  naturally-reverting call uses `revertSpan = 0`.
- **Cross-rollup routing — `destinationRollupId`.** Entries route to per-rollup queues, enabling
  synchronous composition across more than one L2 and L2→L1 (outbound) flows, not just L1→L2.

## 13.2 Rollup1

Rollup1 is the end goal: a permissionless, based, ZK-proven EEZ chain. Each axis replaces a v0
trust assumption; the interfaces are designed so the replacement is local.

- **Sequencing: centralized → based.** Ordering derives from L1 proposers rather than a single
  operator, with preconfirmations for fast UX. The operator role (§2) becomes an open,
  L1-driven block-building role; multiple parties may post batches for one L2 in one L1 block,
  which is what makes batch **chaining** and the no-post-block-state-change rule relevant (§12.3).
- **Settlement: multisig → ZK validity proof.** The N-of-M attestation (§8) is replaced by a
  succinct validity proof of the state-transition function, verified on L1. The
  `verify(proof, publicInputsHash)` interface is unchanged, so the proof system swaps without
  touching the rest of the protocol; re-derivation becomes a redundancy check rather than the
  load-bearing safety backstop.
- **Validator set: small permissioned → large permissionless, BLS.** A large open signer set with
  BLS-aggregated signatures (one aggregate verification regardless of set size) replaces the small
  ECDSA multisig. The cost tradeoff is in [Appendix B](B-gas-cost-analysis.md).
- **Liveness: operator-dependent → L1 force-inclusion + trustless exit.** An L1 force-inclusion
  inbox and a permissionless exit path remove v0's censorship/no-exit limitation (§12.1): a stalled
  or hostile operator can no longer freeze funds.
- **Composability: L1→L2-single-return → full bidirectional/synchronous.** The general model
  (§13.1) is enabled, generalized across many based EEZ chains composing synchronously.

The inbound system transaction is already the deterministic, unsigned **type-`0x7E`** envelope in
v0 (§3.4), so following is key-free and ready for the permissionless setting.

---

*End of the specification body. Appendices: [A](A-reference.md) (constants, formulae, glossary,
errors), [B](B-gas-cost-analysis.md) (gas & cost analysis), [C](C-open-questions.md) (open
questions), [D](D-wire-formats.md) (byte-exact wire formats & conformance vectors).*
