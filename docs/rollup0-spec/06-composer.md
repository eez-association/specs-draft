# 6. The Composer

The composer is the operator function that turns a cross-chain intent into a settled interaction.
This chapter specifies **what** it must do and the requirements it must uphold; the mechanisms it
uses to do so are not part of the protocol.

## 6.1 Lifecycle

For each cross-chain intent, once per sync slot, the composer:

1. **Observes** the intent — an L1 transaction whose execution calls a cross-chain proxy (§3.2).
2. **Simulates** the whole interaction across both chains: it executes the L1 side, and where the
   L1 execution calls a proxy it resolves that call by simulating the destination (the one L2 call,
   in v0), feeding the L2 return value back so the L1 execution continues as if the call were
   local. It records every cross-chain call and its result.
3. **Builds the batch** — folds the recorded interaction into execution entries with their state
   deltas, return data, and rolling hash (§5), and assembles the data-availability payload (§7).
4. **Commits the Sync block** on L2 (§4.4) — system transactions delivering the inbound call,
   then the slot's user transactions.
5. **Posts to L1** the batch together with the triggering L1 transaction as one all-or-nothing
   bundle (§7), targeting the slot's L1 block.
6. **Reconciles** against L1: if the bundle lands, the Sync block is confirmed; if it does not,
   the composer rolls the Sync block back (§4.4). L1 is the source of truth.

## 6.2 Requirements

A conforming composer (and the resulting batch) MUST satisfy:

- **R1 — Faithful, provable batch.** The batch is a provable record of a *correct* cross-chain
  execution: every recorded call's result is what a correct re-execution yields, every entry's
  `stateDeltas` are its true state transition, and the rolling hash binds the on-chain replay to
  the recorded execution (§5). A validator signs only after confirming this (§8).
- **R2 — Simulation ≡ on-chain replay.** The results the composer records MUST equal what the
  on-chain replay produces; otherwise settlement reverts (`RollingHashMismatch` /
  `StateRootMismatch` / `EtherDeltaMismatch`, §5.4). The simulation environment MUST therefore
  match on-chain execution semantics (including gas accounting).
- **R3 — Determinism.** The composer and any follower MUST build byte-identical L2 blocks from the
  same inputs (§4, §10). The composer MUST introduce no block content that is not either a
  published user transaction or a deterministically-reconstructible system transaction.
- **R4 — All-or-nothing bundle.** The `postAndVerifyBatch` transaction and the triggering L1
  transaction MUST land together in one L1 block, or not at all — this is the basis of the
  synchronous L1↔L2 guarantee (§7).
- **R5 — Optimistic rollback.** An optimistically-committed Sync block whose bundle does not land
  MUST be rolled back; the L2 keeps only what L1 confirms (§4.4).
- **R6 — Data availability (Rollup0/GC choice).** Rollup0/GC publishes enough data that any party
  can re-derive the byte-identical L2 chain from L1 alone (§7, §10). *This is a Rollup0/GC choice,
  not an EEZ requirement* — EEZ does not mandate data availability.

## 6.3 Non-guarantees (v0)

v0 has a **single, centralized, permissioned** operator. It makes **no transaction-ordering or
censorship-resistance guarantee**: the operator chooses ordering, and liveness depends on it. A
hostile or unavailable operator can halt or censor (§12). Safety does not depend on the operator
(§5.4, §8, §10).

---

*Next: [§7 Data Availability, Batches & L1 Bundles](07-da-batches-bundles.md).*
