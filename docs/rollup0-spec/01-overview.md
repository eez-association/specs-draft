# 1. Overview & Scope

**EEZ** is a cross-chain protocol: a set of L1/L2 contracts and a settlement rule that let a
contract on one chain call a contract on another and receive the result **within a single L1
block**. **Rollup0** (on **Gnosis Chain**, "GC") is the first chain built on EEZ. This document
specifies the protocol — the behavior and interfaces an independent client team must implement.
It is implementation-agnostic: it defines *what* a conforming client does, not *how*.

## 1.1 EEZ vs Rollup0/GC

- **EEZ** — the general protocol (cross-chain contracts + the execution/settlement model). It
  fixes only what every EEZ chain must agree on.
- **Rollup0/GC** — one chain that makes deliberate **choices** on top of EEZ. Where a property is
  a Rollup0/GC choice rather than an EEZ requirement, this spec says so explicitly.

## 1.2 v0 scope

Rollup0 v0 (GC launch) is intentionally narrow:

- **Cross-chain direction:** **L1→L2 only, single return value.** An L1 contract executes
  (including nested L1 calls), makes **exactly one** state-mutating call into L2 (where arbitrary
  state changes and nested calls may occur), receives **one** return value, and resumes on L1.
  Proven cross-chain **reads** (`STATICCALL`, resolved as lookups, §3.5) are also part of v0.
  Synchronous L2→L1 is **not** in v0 (§10).
- **Block cadence:** L2 block time **2 s**; **6 L2 blocks per L1 block** — **5 pure-L2 blocks
  followed by one Sync block** (the last block of the slot, carrying the cross-chain delivery and
  sharing its L1 block's timestamp). No proof-window (§4).
- **Settlement:** a **permissioned N-of-M** validator set — N independent single-signer proof
  systems — attesting each batch (§8).
- **Sequencing:** a **single, centralized, permissioned** operator (§2, §6). **Liveness depends
  on this operator; safety does not** (§8, §10).
- **Data availability:** Rollup0/GC publishes the full data needed to re-derive the L2 from L1
  alone (§10). This is a Rollup0/GC **choice**, not an EEZ requirement.

The full EEZ execution model is more general (bidirectional, multi-call, reentrant). v0 exercises
only the subset above; the general model is specified in [§13](13-rollup1-general-model.md) as the
Rollup1 target.

## 1.3 Conventions

Key words (MUST/SHOULD/MAY) carry their usual normative meaning. Terms are defined at first use; a
glossary and the full constant/formula set are in [Appendix A](A-reference.md), and byte-exact wire
formats with conformance vectors are in [Appendix D](D-wire-formats.md).

---

*Next: [§2 Architecture](02-architecture.md).*
