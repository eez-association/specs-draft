# 6. Derivation and Following

Rollup0 publishes the data needed to reconstruct accepted L2 state from canonical Ethereum
history. Derivation detects inconsistency and defines local unsafe, safe, and finalized views. It
does not reverse an EEZ-accepted state root and does not create a fraud-proof exit.

## 6.1 Canonical Ethereum input

A follower MUST authenticate:

- the activated Rollup0 profile and protocol version;
- the Rollup0 genesis commitment;
- canonical Ethereum headers and finality;
- the EEZ, manager, and proof-system deployment tuple; and
- the system-transaction rules in Appendix C.

Starting at the activated deployment block, the follower scans relevant transactions and logs in
canonical order:

```text
(blockNumber, transactionIndex, logIndex)
```

RPC response order is not consensus order. For each occurrence, the follower fetches the
transaction and receipt from the authenticated canonical block, verifies the transaction hash and
index, decodes the complete `postAndVerifyBatch` calldata, and applies §4.5. A log from another
contract, rollup ID, transaction, or orphaned block has no authority.

The transaction hash is the deduplication key. Equal calldata or roots in distinct transactions do
not make the transactions equal.

## 6.2 Range and Candidate Selection

Let `cursor_block` be the highest derived L2 block accepted from settled history, or the activated
genesis block before the first transition. Authenticate its height, block hash, and state root. In
the arithmetic below, `cursor = cursor_block.number`. For a strict DA payload with
`n = len(blockTxCounts) > 0`:

```text
first = cursor + 1
sync  = cursor + n
range = (cursor, sync]
```

All arithmetic is checked. The candidate's named parent height, block hash, and state root MUST
equal `cursor_block` exactly. Let `A = cursor_block.stateRoot`. A rich candidate uses an `A -> Z`
anchor. An anchor-only candidate uses its sole `A -> F` delta.

The follower MUST also enforce every §4.2 range condition against the candidate's authenticated
Ethereum proof-context header `E`: `sync <= target_height(E)`, the endpoint residue is a whole
`K` interval behind that target, and `n <= N_max`. The formulas above do not by themselves make a
range admissible.

Several valid sibling candidates MAY name the same exact parent identity. Validators and provers MUST
evaluate every supported candidate that is valid under the active profile, regardless of producer
identity, and MAY sign several siblings. Candidate signatures do not select a winner.

The first applicable transition in canonical Ethereum transaction order wins. After it advances
the Rollup0 cursor, later siblings with the old parent identity are stale even when their parent
root equals the new cursor root. A stale, reverted, invalid, or non-applying attempt does not
advance the cursor. A later applicable candidate starts at the current cursor identity.

## 6.3 Deterministic Reconstruction

Decode the tag-`0x00` payload under §4.1 and partition its transaction list using
`blockTxCounts`. Each count covers user transactions only. System transactions are reconstructed
under Appendix C.

The sidecar MUST preserve the complete order and multiplicity of every derivation entry. A
follower MUST NOT infer missing entries, reorder a mixed list, or substitute a call-empty
on-chain representation for data required by L2 execution.

First reconstruct and execute every nonterminal block. Let `S_pre` be the resulting pre-Sync
state. Using the exact terminal block environment, build an empty-body Sync prefix on `S_pre`,
apply every mandatory pre-execution state change, and execute no transaction. Its state root is
`Z`. This computation is required even when no effect applies.

### 6.3.1 Exact applied prefix

For a rich candidate, first validate the complete claimed chain:

```text
anchor:     A -> Z
effect[0]:  Z -> R[0]
effect[k]:  R[k-1] -> R[k]
```

Classify the anchor and each potential effect from its own receipt-bound evidence. Each position
has one result:

- applied, with the state root produced by that exact effect; or
- not applied: an immediate entry has its exact ordered `ImmediateEntrySkipped` occurrence, or an
  authenticated exact deferred trigger has a status-`0` receipt.

A successful deferred trigger requires the exact surviving `ExecutionConsumed` and
`L2ExecutionPerformed` occurrences for its queue item. Missing events in a successful receipt are
invalid evidence, not an inferred non-application. Internal revert data and logs removed by a
status-`0` transaction are not consensus evidence.

If the anchor is not applied, the candidate advances no block. If the anchor is applied, the
effect results MUST select exactly the first `q` effects for one `0 <= q <= m`. An applied result
after a non-applied result, missing evidence, ambiguous effect attribution, or evidence taken from
another transaction invalidates the candidate. Equal root values remain valid when exact effect
indices and receipt occurrences preserve their order and multiplicity. A client MUST NOT
deduplicate effects by root value.

The activated applied-prefix safety mechanism MUST prevent the Ethereum operation from completing
with a hole in this sequence, including when consecutive roots are equal. Follower detection after
canonical inclusion is not prevention. If canonical history nevertheless contains an applied
effect after a non-applied anchor or effect, the history violates the activated profile and the
follower MUST halt.

The selected endpoint is:

```text
q = 0: endpoint = Z
q > 0: endpoint = R[q-1]
```

For an anchor-only candidate, validate its sole `A -> F` delta. The range advances to `F` only
when exact evidence shows that delta applied. Anchor-only settlement has no effect-prefix split.

A collapsed final-root set is not sufficient: siblings and distinct effects can produce equal
roots, and an immediate effect can skip before a later transaction executes. Historical clients
that reduced results to per-block root membership are unsafe.

### 6.3.2 Transaction placement

For a rich candidate, reconstruct each complete effect group from the sidecar and its matching DA
user transaction. The full candidate body is:

```text
G[0] || G[1] || ... || G[m-1]
```

For selected effect count `q`, the derived Sync body is exactly:

```text
B(q) = G[0] || G[1] || ... || G[q-1]
B(0) = []
```

The follower MUST NOT append a user transaction from an omitted outbound group or any unrelated
Sync user transaction. The repaired body's user count is the number of outbound groups among the
first `q` effects; it is not necessarily the original final `blockTxCounts` value.
An omitted user transaction is not part of the derived chain. A producer MAY return it to a local
pool only after checking canonical replacement receipts.

For an anchor-only candidate, the Sync body is the complete ordered user list `U` transported for
that block. It is not truncated because there is no effect prefix.

An intermediate block MUST NOT contain a transaction from the reserved system sender. The Sync
block MUST contain only the system transactions constructed by Appendix C at their required
positions. A rich Sync body MUST contain no transaction outside its effect groups.

### 6.3.3 Execution and commit

From the authenticated parent, the follower:

1. reconstructs and executes every nonterminal block in order;
2. constructs the terminal Sync environment under §2.4 and independently computes `Z`;
3. validates the complete claimed delta chain for the candidate form;
4. authenticates settlement evidence and selects no range, an anchor-only body, or rich effect
   count `q`;
5. for a selected rich range, rebuilds the terminal block with exactly `B(q)` from the same
   pre-Sync parent and environment;
6. for a selected anchor-only range, rebuilds the terminal block with exactly `U`;
7. recomputes every receipt, trie root, gas field, and complete sealed terminal header;
8. requires the rebuilt endpoint to equal `Z` for rich `q = 0`, `R[q-1]` for rich `q > 0`, or
   `F` for anchor-only settlement; and
9. commits the complete range and advances the cursor height, block hash, and state root to the
   selected Sync block atomically.

For `q = m`, the rich terminal body is the full candidate body. For `q < m`, the follower MUST
derive a new repaired terminal header from `B(q)`. It MUST NOT reuse the full candidate's
transaction root, receipt root, gas fields, state root, block hash, or body. The nonterminal
blocks remain unchanged.

A local-block fast path is valid only when ancestry, the complete ordered body, execution result,
and every header field match. Transaction-only or final-root-only comparison is insufficient.

## 6.4 Invalid Data and Execution

Reject the whole candidate range for any of these conditions:

- nonempty `blobIndices`;
- an empty payload, unknown tag, noncanonical RLP, trailing bytes, wrong shape, empty count list,
  count overflow, or count-sum mismatch;
- an ABI object that is malformed or not consumed completely;
- a missing, extra, reordered, or field-mismatched sidecar item;
- a transaction item that is not exactly one supported signed envelope;
- an invalid chain ID, signature, nonce, fee, balance, intrinsic gas, or block-validity condition;
- an unauthorized or misplaced system transaction;
- an entry/user cardinality or order mismatch;
- a range that fails any authenticated proof-context, target, residue, or `N_max` condition in
  §4.2;
- a rich Sync user transaction outside an effect group;
- an `A`, `Z`, `R[k]`, or `F` mismatch;
- inability to construct the exact system transaction;
- a parent, header, body, receipt, or endpoint mismatch; or
- incomplete, reordered, reused, cross-candidate, non-prefix, or ambiguous settlement evidence.

Rollback all tentative work and leave the cursor unchanged. A persistent error in canonical
history halts derivation. A valid EVM transaction whose call reverts remains part of the block.

## 6.5 Reorganizations

On an Ethereum reorganization with common ancestor `E_common`, the follower:

1. removes indexed attempts above `E_common`;
2. resets the cursor to the last surviving accepted endpoint;
3. reduces safe and finalized labels to surviving endpoints;
4. moves the local canonical L2 head to that cursor;
5. restores eligible unsafe user transactions only after checking replacement-branch receipts;
   and
6. derives the replacement branch in canonical order.

Startup validation MUST produce the same result when a notification was missed. Orphaned
transactions, receipts, logs, roots, and payloads have no authority.

Automatic common-ancestor discovery is an implementation limit, not an EEZ rule. A reorganization
beyond that limit, or displacement of finalized Ethereum settlement, requires an authenticated
recovery decision and consistent repair of both the Ethereum index and L2 database.

## 6.6 Unsafe, Safe, and Finalized

- **Unsafe** means valid local execution that has not yet been selected by canonical Ethereum
  settlement.
- **Safe** means deterministic replay from canonical Ethereum evidence reached and fully validated
  the block.
- **Finalized** means safe and contained in finalized Ethereum history.

`finalized` MUST NOT exceed `safe`. Candidate publication, proof signatures, `BatchPosted`, or a
matching root without exact effect attribution cannot advance either label.

An unsafe candidate above safe is compatible only when its available ancestry reaches the exact
safe hash. Missing ancestry is unverifiable. It MAY remain an unsafe sync target within an
implementation bound, but it cannot move safe or finalized and MUST yield to canonical
derivation.

## 6.7 Startup and live operation

A live subscription does not replace a canonical scan. A follower catches up, subscribes, and
rescans the subscription gap. On lag, incomplete lookup, or inconsistent provider data, it
rescans canonical history. Historical and live paths MUST apply identical decoding, receipt,
ordering, and replay rules.

## 6.8 Current implementation deviations

The behavior examined at
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` does not yet
conform to this chapter:

- it has no production activation record or profile authentication;
- it does not explicitly establish canonical log order;
- some paths fetch a transaction by block and index without authenticating the expected hash;
- settlement attribution reduces roots to per-block `HashSet` membership, losing order,
  multiplicity, receipt boundaries, `ImmediateEntrySkipped`, and `ExecutionConsumed`;
- settlement has no enforceable commitment to the exact current cursor height and block hash, so
  equal-root stale siblings remain applicable to the EEZ root check;
- no enforceable applied-prefix guard prevents a later effect from applying after a caught
  immediate-entry failure; equal consecutive roots make this failure reachable;
- the composer can derive several inbound effects from one held Ethereum transaction while adding
  that transaction to the bundle only once, violating the required distinct trigger per effect;
- the codec accepts an empty count list, trailing body data, and a zero-length no-op;
- selected `eez-evm@0.2-draft` restrictions, including empty `blobIndices` and exact L1/L2 tuple
  use, are not enforced consistently;
- sidecar lookup can fall back to incomplete on-chain data and can partition or reorder entries;
- `crates/eez-composer/src/composer.rs::prepare_post_batch_raw` anchors a rich candidate from `A` to the
  pre-Sync parent root instead of `Z`; although
  `crates/eez-composer/src/local/build.rs::sync_block_pair_roots` correctly includes the pre-execution
  changes in `R[0]`, the resulting parent-to-`R[0]` stitch incorrectly assigns those changes to
  the first effect;
- `crates/eez-deriver/src/deriver.rs::reconcile_batch_blocks` truncates effect entries by
  `settled_count` but appends the remaining final-block user transactions; a prefix that omits an
  outbound effect therefore retains that effect's user transaction instead of rebuilding exactly
  `B(q)`;
- transaction and ABI decoders do not always prove complete input consumption;
- multi-block replay commits incrementally instead of atomically;
- the local fast path compares transactions without validating every sealed block field;
- a missing system key can cause a pure-user fallback instead of a deterministic failure;
- the reserved system sender rule is not enforced by every follower path;
- unverifiable unsafe ancestry can be forwarded up to an implementation bound; and
- automatic reorganization lookup retains at most 62 settlement-block hashes by default, so a
  depth-62 reorganization can already lack a retained common ancestor.

The checked-in contract gitlink is
`5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`, not the selected binding evidence
`3a6ca65c4858792fc3a143d34c5484877ef8f68c`. Updating and revalidating that dependency is a release
blocker. These deviations are implementation defects, not alternate protocol rules.

---

*Next: [§7 Gas, Limits, and Economics](07-gas-economics.md).*
