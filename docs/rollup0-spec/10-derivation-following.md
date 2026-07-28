# 10. Derivation and Following

Rollup0 publishes enough data on Ethereum for a follower to reconstruct the selected Rollup0 chain
without trusting a composer.

## 10.1 Canonical Input

A follower starts from the production Rollup0 genesis and the selected EEZ deployment on Ethereum.
It processes relevant Ethereum blocks, transactions, receipts, and logs in canonical order:

```text
(blockNumber, transactionIndex, logIndex)
```

RPC response order is not consensus order. The follower authenticates each Ethereum header,
transaction, receipt, contract address, and Rollup0 identifier before using it.

`BatchPosted` locates a candidate publication. `L2ExecutionPerformed` identifies individual
Rollup0 state updates, but does not by itself identify the selected `B[k]`. The follower accepts
both events only from the selected EEZ deployment and derives the endpoint by replay.

## 10.2 Derivation

For each applicable candidate, the follower:

1. verifies that `fromBlock` and the candidate pre-state match its Ethereum-confirmed Rollup0 head;
2. decodes the EEZ batch and Rollup0 DA payload;
3. recovers every block boundary, pure-L2 transaction, and intended Ethereum trigger from the
   selected blobs;
4. reconstructs each header from its parent under Chapter 4;
5. executes the terminal block's pure-L2 prefix and verifies `R0`;
6. reconstructs and executes every `B[i]` from the EEZ entries and failed lookups;
7. replays the ordered Ethereum triggers and derives the processed action prefix from their
   execution, receipts, and retained EEZ logs;
8. recomputes every state, transaction, receipt, and header commitment for that prefix;
9. compares the executed endpoint with canonical settlement evidence; and
10. commits the accepted range and advances its cursor.

The follower MUST reject missing, extra, reordered, or malformed transactions and sidecar data. It
MUST NOT trust a candidate's claimed endpoint without replay.

## 10.3 Competing Candidates

The follower processes settlements in canonical Ethereum transaction order. After one candidate
advances the cursor, a sibling for the old parent is stale. A stale sibling does not create a
Rollup0 block range.

If an EEZ entry is not consumed, the follower validates replay against the last state root that
canonical settlement actually applied, not against a claimed full-candidate endpoint. It preserves
log order and multiplicity; it does not infer the prefix from an unordered set of matching roots.

The pure-L2 prefix remains part of `B[0]` even when no synchronous action is processed. A caught
Rollup0 revert can advance the action prefix without changing the state root. The exact prefix
index, not the state root alone, selects the terminal block variant.

The duplicate-call rule in Chapter 7 must be resolved before followers can assign two identical
calls to exact Ethereum transactions.

## 10.4 Unsafe, Safe, and Finalized

- **Unsafe:** locally executed but not selected by canonical Ethereum settlement.
- **Safe:** reconstructed and verified from canonical Ethereum settlement.
- **Finalized:** safe and included in finalized Ethereum history.

A proof, validator signature, candidate announcement, or local execution result cannot make a
Rollup0 block safe by itself.

## 10.5 Ethereum Reorganizations

On an Ethereum reorganization, a follower:

1. finds the canonical common ancestor;
2. removes candidate evidence from orphaned Ethereum blocks;
3. retreats the safe and finalized Rollup0 views to the last surviving endpoint;
4. discards conflicting unsafe descendants; and
5. derives the replacement Ethereum branch in order.

!!! note "TO BE DEFINED"
    A reorganization beyond retained history or a displacement of finalized Ethereum settlement
    requires an authenticated recovery decision. The automatic history bound and recovery
    authority are not yet selected.

## 10.6 Invalid Canonical Data

If canonical Ethereum data cannot be reconciled with the selected EEZ and Rollup0 rules, the
follower MUST halt. It MUST NOT guess a missing transaction, repair an ambiguous candidate, or
substitute a matching state-root value from another action.

---

*Next: [Chapter 11, Gas and Economics](11-gas-economics.md).*
