# 10. Derivation and Following

While its blobs remain available, each Rollup0 anchor publishes enough data on Ethereum for a
follower to reconstruct the selected range without trusting a composer. EEZ also retains the exact
settled Rollup0 block hash. A follower derives each interval's RANDAO value from the canonical
Ethereum execution block immediately preceding that interval's starting Sync timestamp; anchor
inclusion does not select the value.

## 10.1 Canonical Input

A follower starts from the production Rollup0 genesis and the selected EEZ deployment on Ethereum.
It processes relevant Ethereum blocks, transactions, receipts, and logs in canonical order:

```text
(blockNumber, transactionIndex, logIndex)
```

RPC response order is not consensus order. The follower authenticates each Ethereum header,
transaction, receipt, contract address, and Rollup0 identifier before using it.

`BatchPosted` locates a candidate publication. `L2ExecutionPerformed.newState` carries a Rollup0
block hash despite its legacy EEZ field name. The event identifies an individual commitment update,
but does not by itself prove the complete selected action prefix. The follower accepts both events
only from the selected EEZ deployment and derives the endpoint by replay.

## 10.2 Derivation

For each applicable candidate, the follower:

1. authenticates the successful settlement transaction, its receipt, and relevant retained logs
   in the canonical Ethereum block, and records its current Rollup0 cursor as `Hparent`;
2. decodes the EEZ batch from the settlement calldata, validates the Rollup0 V1 batch profile, and
   resolves its blob indices to the transaction's versioned blob hashes;
3. obtains the referenced blob sidecars and verifies each blob, KZG proof, commitment, versioned
   hash, and position against the canonical Ethereum transaction and beacon block;
4. decodes the Rollup0 DA payload from those authenticated blobs;
5. reconstructs the candidate domain defined in Appendix D from the configured Rollup0 identities
   and canonical Ethereum context, and verifies every context-dependent Rollup0 field against it;
6. recovers every block boundary, pure-L2 transaction, protocol-transaction input, and ordered
   action-manifest entry from the selected blobs;
7. verifies that `Hparent` is the EEZ commitment immediately before settlement and that the first
   reconstructed block directly extends the header authenticated by `Hparent`, then reconstructs
   every later header from its parent under Chapter 4;
8. executes the terminal block's pure-L2 prefix and verifies `H[0]` and `R0`;
9. processes retained `ExecutionConsumed` and `L2ExecutionPerformed` logs after
   `submitCandidate`; for each successful action, it verifies the expected call hash, Rollup0 ID,
   zero-based successful-entry queue position, and resulting `H[k]` in order, then derives the
   successful-action count `k`;
10. reconstructs and executes the protocol transaction for each of those `k` successful actions
   from its authenticated settlement context, manifest index, call hash, and EEZ entry, deriving
   `B[k]`, `H[k]`, and `R[k]`;
11. recomputes every state, transaction, receipt, header, and block-hash commitment required for the
   selected endpoint;
12. checks whether the terminal timestamp makes the candidate a live or catch-up anchor, applies
   the corresponding action rules, and independently applies Chapter 4's interval RANDAO rule;
13. compares the executed endpoint with canonical settlement evidence; and
14. commits the accepted range and advances its cursor.

The follower MUST reject missing, reordered, or malformed data required to reconstruct the selected
endpoint. It does not need the signed bytes of proposed triggers that were not included on
Ethereum, because those triggers consumed no result and caused no Rollup0 transition. It MUST NOT
trust a candidate's claimed endpoint without replaying the canonical actions that selected it.

Successful canonical execution through the active settlement wrapper establishes that EEZ verified
the proof or signatures under the on-chain policy active at that transaction position. An ordinary
Rollup0 follower does not repeat that authorization check against historical proof-system contract
state. It MUST still independently execute the selected Rollup0 data and halt if the resulting
blocks or commitments disagree with canonical EEZ evidence. An auditing implementation MAY replay
the relevant Ethereum execution and independently reverify the historical proof or signatures.

For every reconstructed interval after Sync timestamp `T`, the follower authenticates the canonical
Ethereum header `P(T)` with the greatest timestamp strictly less than `T` and copies
`P(T).prevRandao` into all six Rollup0 headers in the interval. It performs this derivation whether
or not `T` has an Ethereum block and whether or not an anchor was accepted. A candidate spanning
several intervals can therefore contain different interval seeds, all derived from canonical
Ethereum history rather than from candidate inclusion.

## 10.3 Standard Block and State Synchronization

Rollup0 does not require peers to retain historical blobs. A follower can bootstrap from normal
Rollup0 execution-layer peers:

1. read the Rollup0 commitment `H` from EEZ at a finalized Ethereum block;
2. fetch through the standard `eth` protocol the Rollup0 header whose hash is exactly `H`;
3. verify the header hash and take its EVM `stateRoot` as `R`;
4. obtain complete execution state through the standard `snap` protocol and verify it against `R`,
   including contract bytecode against each account's `codeHash`, or execute the complete block
   history; and
5. fetch required headers, bodies, and receipts through `eth` and verify their parent links and
   header commitments. Execute every post-checkpoint block; only a full sync re-executes the
   pre-checkpoint history.

At state root `R`, the EIP-2935 history contract authenticates `H`'s parent block hash. This gives
the follower an additional check on the parent chain, but it does not authenticate `H` itself: the
system call records the parent before the block's transactions execute. The block hash stored by
EEZ remains the exact safe-head checkpoint; the state root taken from that header remains the state
synchronization target.

Peer announcements and peer majority do not determine canonicality. The follower supplies the
settled, safe, and finalized fork-choice checkpoints from canonical Ethereum settlement. Peers are
untrusted data sources.

!!! warning "AVAILABILITY: normal pruning rules apply"
    A block hash authenticates data but does not make it available. A pruned peer does not need to
    serve old bodies, receipts, or historical states. Historical RPC therefore depends on ordinary
    Rollup0 archive nodes, as it does on Ethereum; those nodes archive normal chain data, not blob
    sidecars.

## 10.4 Competing Candidates

The follower processes settlements in canonical Ethereum transaction order. After one candidate
advances the cursor, a sibling for the old parent is stale. A stale sibling does not create a
Rollup0 block range.

If an EEZ entry is not consumed, the follower validates replay against the last block-hash
commitment that canonical settlement actually applied, not against a claimed full-candidate
endpoint. It preserves log order and multiplicity; it does not infer the prefix from an unordered
set of matching hashes.

The pure-L2 prefix remains part of `B[0]` even when no synchronous action is processed. A caught
Rollup0 revert does not create another Rollup0 block variant or change `H[k]` or `R[k]`. Because it
cannot be followed by a successful action, a Rollup0 follower may ignore whether it occurred.

Followers assign calls to ordered manifest positions, not to proposed transaction hashes. Two
identical call hashes are resolved by the successful EEZ queue position: the first matching
canonical call performs the first position, and the cursor advances before the next can execute.

## 10.5 Unsafe, Safe, and Finalized

- **Unsafe:** valid locally executed blocks not yet selected by canonical Ethereum settlement. A
  block enters the shared unsafe view only with an Appendix D producer signature. Rollup0 permits
  any producer key; followers may apply local identity-based selection policy.
- **Safe:** reconstructed and verified from canonical Ethereum settlement.
- **Finalized:** safe and included in finalized Ethereum history.

A proof, validator signature, candidate announcement, or local execution result cannot make a
Rollup0 block safe by itself. An unsafe producer signature authenticates who announced the block;
it does not prove candidate validity, confer settlement priority, or prevent a different valid
range from becoming safe through canonical Ethereum.

## 10.6 Ethereum Reorganizations

On an Ethereum reorganization, a follower:

1. finds the canonical common ancestor;
2. halts for authenticated recovery if the replacement branch conflicts with its finalized
   Ethereum checkpoint or any Rollup0 endpoint finalized through it;
3. removes candidate evidence from orphaned, non-finalized Ethereum blocks;
4. retreats the safe Rollup0 view to the last surviving endpoint while leaving the finalized view
   unchanged;
5. recomputes each affected interval's RANDAO value from its preceding canonical Ethereum block;
6. removes or revalidates unsafe descendants against that cursor and the recomputed values; and
7. derives the replacement Ethereum branch in order.

A follower may retain removed branches as noncanonical data. A block containing a protocol
transaction derived from an orphaned settlement context cannot become current merely by being
relabeled unsafe; it requires a new candidate context and newly derived protocol transaction. A
pure-L2 range from an orphaned candidate may be revalidated from the restored cursor under the
current timestamp, seed, transaction, and state rules. If it still forms a valid local continuation,
the node may adopt it as unsafe or use it in a newly signed candidate. Only canonical Ethereum
settlement can make either range safe again.

The finalized Rollup0 view never retreats during an ordinary Ethereum reorganization. Rollup0
finality is inherited from Ethereum finality. A branch that excludes a finalized Rollup0
settlement is therefore an Ethereum finality violation and follows the authenticated recovery rule,
not automatic reorganization handling.

There is no separate Rollup0 maximum for an ordinary non-finalized Ethereum reorganization. A
follower MUST retain, or be able to recover, enough data to restart from its latest finalized
Ethereum checkpoint and derive the canonical branch. Exceeding a node's locally retained history
is a synchronization problem, not permission to select another branch.

!!! danger "FINALITY FAILURE: recovery requires a community hardfork"
    If canonical Ethereum displaces a finalized Rollup0 settlement, or finalized canonical data
    cannot be reconciled with the Rollup0 rules, the node halts. Initial Rollup0 defines no manager,
    multisig, or other in-protocol authority that can make the conflicting history valid. Recovery
    requires a community-coordinated hardfork that specifies a new authenticated checkpoint and
    any associated state or protocol changes.

    The generic EEZ manager's `setStateRoot` escape power does not by itself authorize that
    recovery for Rollup0 followers. An out-of-protocol use changes Ethereum-side EEZ state, but
    followers still halt unless a community hardfork explicitly adopts the resulting checkpoint.

## 10.7 Invalid Canonical Data

If canonical Ethereum data cannot be reconciled with the selected EEZ and Rollup0 rules, the
follower MUST halt. It MUST NOT guess a missing transaction, repair an ambiguous candidate, or
substitute a matching block-hash commitment from another action.

---

*Next: [Chapter 11, Gas and Economics](11-gas-economics.md).*
