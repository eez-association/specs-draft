# 10. Derivation & Following

**Re-derivability is a Rollup0/GC choice** (§6 R6): the chain publishes enough data that any party
can reconstruct the **byte-identical** L2 chain from L1 alone, without trusting the operator. EEZ
does not require this; Rollup0/GC provides it.

## 10.1 Derivation

From L1 alone, a deriver rebuilds the L2 chain:

1. Read each `BatchPosted` and the associated `L2ExecutionPerformed(rollupId, newState)` (§8).
2. Fetch the batch's DA payload and decode it (§7.1) into per-block user transactions and the
   L2-shape entries.
3. For each L2 block in `[fromBlock+1 … toBlock]` (range recovered from on-chain state, §7.2):
   reconstruct the header by the §4 rules, re-execute the user transactions, and — for the Sync
   block — reconstruct and prepend the system transactions deterministically from the batch's
   entries (§3.4).
4. Commit the rebuilt blocks.

Because the deriver uses the same rules and inputs as the operator, the rebuilt chain is
byte-identical — unless the operator deviated, in which case derivation detects it (§10.3).

## 10.2 Safe / finalized

A follower derives the **safe** and **finalized** L2 views from L1: a block is safe once its batch
has landed, finalized once that L1 block is finalized. The operator may run an **unsafe** head
ahead of L1; a follower advances safe/finalized only from L1, never from the operator's word.

## 10.3 Equivocation and divergence

A follower MUST reject any operator-published head that does not descend from the L1-confirmed safe
head. If a follower's re-derived state root for a settled batch disagrees with the on-chain
`L2ExecutionPerformed` root, derivation **halts** rather than adopting the bad head — the
attestation can advance the on-chain root, but re-derivation makes a wrong advancement detectable
and non-canonical to honest participants (§8.6). Under **partial consumption** (an entry left
unconsumed), the deriver validates its replay against the *actual* settled endpoint (the last
applied `newState`), not a claimed full-range endpoint.

## 10.4 L1 reorgs

The L1 is the source of truth, so an L1 reorg moves the L2. On a reorg, the deriver retreats the L2
to the highest L2 block whose batch survives at the L1 common ancestor, then re-derives forward; a
batch's on-chain L1-block binding lets a deriver re-check a record's canonicality even across a
missed reorg notification. A reorg deeper than L1 finality is outside the protocol's automatic
recovery and halts pending operator intervention (§12).

## 10.5 L2 → L1 (not in v0)

Synchronous L2→L1 — an L2-originated call into L1 within one interaction — is **not in v0**. v0 is
L1→L2 only (§1.2, §9). L2-originated messages and withdrawals are a general-model capability (§13);
any v0 withdrawal path is a separate, asynchronous mechanism outside this specification.

---

*Next: [§11 Gas, Limits & Economics](11-gas-economics.md).*
