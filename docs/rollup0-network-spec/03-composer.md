# 3. The Composer

The composer is the permissioned Rollup0 operator function that turns held cross-chain intents
and ordinary L2 transactions into a candidate Sync block and a Gnosis Chain settlement bundle.
The reusable execution and settlement semantics are defined by the
[EEZ Framework](../eez-protocol-spec/index.md). This chapter defines Rollup0's orchestration.

## 3.1 Inputs

For an observed canonical Chiado head `A = (n, hash, t)`, the composer receives:

- the canonical unsafe L2 parent selected under §2;
- the last L1-confirmed L2 cursor;
- ordered held intents for a flat, single call in either the L1-to-L2 or L2-to-L1 direction;
- an ordered candidate list of L2 user transactions;
- the `rollup0-v0` chain, contract, timing, and signer configuration; and
- the exact target `(n + 1, sync_time)` derived under §2.4.

The composer MUST use one consistent snapshot of those inputs. A changed L2 parent, confirmed
cursor, Chiado anchor, protocol version, or deployment identity makes the attempt stale.

## 3.2 Lifecycle

For each eligible, caught-up, non-late steady Sync trigger, the composer MUST:

1. Simulate every admitted flat interaction across both chains under the EEZ execution rules.
   Feed each destination return value back to its source execution and record the call, return
   data, state deltas, ether delta, and rolling-hash contribution. An attempt can admit at most
   three Chiado source transactions under §4.4.
2. Reject an interaction that requires nesting, reentrancy, more than one cross-chain call within
   that interaction, or another behavior outside the Rollup0 profile.
3. Build the exact L2 transaction sequence in Appendix C. Each outbound call contributes a
   signed load transaction immediately before its paired L2 user transaction. Inbound calls
   contribute signed delivery transactions after all outbound pairs. Remaining user transactions
   follow the inbound deliveries.
4. Execute that sequence against the selected parent and construct all 23 header fields under
   §2.6. Commit only if the parent is still canonical.
5. Encode the full positive range from the L1-confirmed cursor to the new endpoint under §4.
   `blockTxCounts` partitions transported user transactions; it does not count reconstructed
   system transactions.
6. Build the EEZ batch and proofs using the exact ABI and hashes in Appendix E. Set
   `batch.blockNumber = n` and `batch.crossProofSystemInteractions = bytes32(0)`, so the proof
   context binds `blockhash(n)` and the Rollup0 proof-domain field is deterministic. Do not use
   either legacy context sentinel, and do not accept a nonzero cross-proof-system field.
7. Submit the exact ordered bundle
   `[postAndVerifyBatch, inbound source transactions...]` for Chiado block `n + 1`, with minimum
   and maximum timestamp equal to `sync_time`. Include zero to three riders in their surviving FIFO
   and deferred-entry order, exactly one rider for every inbound batch entry. The one-element
   `[postAndVerifyBatch]` form is valid for empty, outbound-only, catch-up, or fully filtered work.
8. Authenticate the canonical block and every submitted transaction and receipt. Attribute
   settlement only from the per-index immediate outcomes and receipt-bound deferred-consumption
   pairs in §4.5. Preserve transaction boundaries, order, and multiplicity. Keep the batch in
   flight until derivation reaches its uniquely selected endpoint.
9. On failure, use the rollback, requeue, poison-attempt, and retry state machine in §2.5.

A late trigger, catch-up trigger, stale parent, or unresolved earlier submission MUST NOT drain
held intents. It can still produce a cross-chain-empty structural or ordinary Sync block as
specified in §2.

## 3.3 Conformance requirements

A conforming composer MUST satisfy:

- **Faithful execution.** Every recorded result, state delta, ether delta, and rolling hash MUST
  equal an independent replay under the EEZ Framework.
- **Simulation equivalence.** Simulation MUST use the same fork rules, gas accounting, contract
  bytecode, call context, and value accounting as settlement and L2 replay.
- **Determinism.** The same authenticated genesis, parent, DA input, sidecar entries, and system
  signer MUST produce byte-identical transactions, receipts, and headers.
- **Atomic inclusion.** The complete conditional list
  `[postAndVerifyBatch, inbound source transactions...]` MUST land in its exact order at the target
  or none of its transactions can count as the intended atomic bundle. An attempt with no riders
  still requires the post transaction to land at that target.
- **Serialized settlement.** At most one submitted batch can exist above the confirmed cursor.
- **Published derivation data.** The DA payload MUST contain every user transaction and L1-shape
  execution-entry sidecar needed by a configured follower. The signed system envelopes are
  reconstructed, not transported.

The last requirement is a Rollup0 network choice, not an EEZ Framework requirement. Because v0
followers need the shared system private key to reconstruct valid signatures, it does not provide
permissionless derivation.

## 3.4 Non-guarantees

`rollup0-v0` has one centralized, permissioned operator. It provides no censorship-resistance or
transaction-ordering guarantee. Operator failure can halt progress. The shared signing key,
prefunded signer, atomic-relay dependency, and optimistic rollback path are explicit limitations
in §8.

---

*Next: [§4 Data Availability, Batches & Gnosis Bundles](04-da-batches-bundles.md).*
