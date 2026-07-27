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

`BatchPosted` locates a candidate publication. `L2ExecutionPerformed` identifies an applied
Rollup0 endpoint. The follower accepts both only from the selected EEZ deployment.

## 10.2 Derivation

For each applicable candidate, the follower:

1. verifies that `fromBlock` and the candidate pre-state match its Ethereum-confirmed Rollup0 head;
2. decodes the EEZ batch and Rollup0 DA payload;
3. partitions the user transactions using `blockTxCounts`;
4. reconstructs each header from its parent under Chapter 4;
5. reconstructs the Sync system transaction from the EEZ entries and Rollup0 rules;
6. executes every block in order;
7. recomputes every state, transaction, receipt, and header commitment;
8. compares the executed endpoint with canonical settlement evidence; and
9. commits the complete accepted range and advances its cursor.

The follower MUST reject missing, extra, reordered, or malformed transactions and sidecar data. It
MUST NOT trust a candidate's claimed endpoint without replay.

## 10.3 Competing Candidates

The follower processes settlements in canonical Ethereum transaction order. After one candidate
advances the cursor, a sibling for the old parent is stale. A stale sibling does not create a
Rollup0 block range.

If an EEZ entry is not consumed, the follower validates replay against the last state root that
canonical settlement actually applied, not against a claimed full-candidate endpoint.

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

A reorganization beyond retained history or a displacement of finalized Ethereum settlement
requires an authenticated recovery decision. The automatic history bound and recovery authority
are not yet defined.

## 10.6 Invalid Canonical Data

If canonical Ethereum data cannot be reconciled with the selected EEZ and Rollup0 rules, the
follower MUST halt. It MUST NOT guess a missing transaction, repair an ambiguous candidate, or
substitute a matching state-root value from another effect.

---

*Next: [Chapter 11, Gas and Economics](11-gas-economics.md).*
