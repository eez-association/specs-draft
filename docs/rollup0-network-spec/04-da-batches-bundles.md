# 4. Data Availability, Batches, and Ethereum Bundles

This chapter defines Rollup0 rules layered on `eez-evm@0.2-draft`. It does not redefine EEZ tuple
layouts or hashes.

## 4.1 Calldata DA

Rollup0 publishes one complete calldata payload:

```text
payload = 0x00 || rlp([blockTxCounts, transactions, l2Entries])
```

`batch.blobIndices` MUST be empty. Producers, validators, and followers MUST reject a nonempty list
before decoding `callData`. Version 0.2 defines no Rollup0 blob codec or fallback DA channel.

| Field | RLP shape | Meaning |
|---|---|---|
| `blockTxCounts` | list of canonical unsigned integers | one user-transaction count per Rollup0 block |
| `transactions` | list of byte strings | complete signed EIP-2718 user envelopes in block-major order |
| `l2Entries` | list of byte strings | complete ABI encodings of the selected `eez-evm@0.2-draft` L2 execution objects needed to reconstruct system transactions |

The `l2Entries` objects use the L2 tuple family in
[EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md). A decoder MUST NOT decode them as the L1
`ExecutionEntry` tuple family. The two sides have different layouts.

### Strict Decoder

A decoder MUST enforce:

1. The payload is nonempty and starts with tag `0x00`.
2. The bytes after the tag contain exactly one canonical RLP item and no trailing byte.
3. The item is exactly a three-element list and each element is a list.
4. `blockTxCounts` is nonempty.
5. Each count is canonical-minimal, has no leading zero, and is at most `65535`.
6. The checked sum of counts equals `len(transactions)`.
7. Every transaction item is a byte string containing exactly one complete supported signed
   EIP-2718 envelope and no trailing byte.
8. Every `l2Entries` item is a byte string containing exactly one complete canonical ABI value of
   the expected L2 tuple type.
9. The exact sidecar count and order match the effects and system transactions selected under
   Appendix C.
10. Missing, extra, reordered, duplicated, or field-mismatched sidecar entries invalidate the
    candidate.

The outer decoder may initially expose opaque transaction and entry bytes. Candidate validation
MUST complete every inner check before proving, signing, submission, or derivation.

### Sidecar Correspondence

For each supported cross-network effect, the sidecar contains the exact L2 execution object used by
the deterministic system-transaction builder. The following data MUST match the corresponding EEZ
candidate data:

- call hash and direction;
- static/failed mode, which are both fixed to `false` by this profile;
- target, value, calldata, source, and source rollup ID;
- call and lookup arrays;
- call counts and ordering;
- return data and rolling hash; and
- every nested table, which MUST be empty in the Rollup0 flat-call profile.

The sidecar does not carry Rollup0 `StateDelta` values. Those values belong to the L1 batch and are
validated separately under §4.3.

A validator MUST derive both the L1 batch object and L2 sidecar object from the same independently
executed effect. Equality of hashes supplied by a composer is insufficient.

## 4.2 Cursor-Derived Range

Let `cursor_block` be the last Rollup0 block accepted from preceding canonical Ethereum history, or
the activated genesis block before the first candidate. The candidate MUST name its exact height,
block hash, and state root. In the arithmetic below, `cursor = cursor_block.number`. Let
`E = (e_number, e_hash, e_timestamp)` be the authenticated Ethereum proof-context header selected
under §2.3, and let:

```text
T       = target_height(E)
n       = len(blockTxCounts)
first   = cursor + 1
sync    = cursor + n
range   = (cursor, sync]
```

All arithmetic MUST be checked. A candidate range is admissible only when:

```text
n = sync - cursor = len(blockTxCounts)
cursor < sync <= T
(T - sync) mod K = 0
1 <= n <= N_max
```

`sync = T` selects the current target. `sync < T` selects a catch-up endpoint stepped back from
`T` by whole `K` intervals. If `T <= cursor`, no positive candidate is admissible for `E`.
`N_max` is the activated consensus range bound. The producer-side catch-up value `C` does not
replace it.

The first count belongs to `first`; the last belongs to `sync`. Counts include transported user
transactions only. Reconstructed system transactions are not counted.

For a rich candidate, the final Sync count MUST equal the number of outbound effect groups. The
corresponding final-block items in `transactions` MUST be exactly the consuming user transaction
from each outbound group, in effect-group order. An inbound-only rich candidate therefore has a
zero final count. No unrelated Sync user transaction is permitted.

For an anchor-only candidate, the final Sync count MAY be nonzero. Its final-block items are the
complete ordered ordinary user body `U` defined in §3.3.

The batch does not obtain authority over this range merely by carrying `n` counts. Its exact named
parent MUST equal `cursor_block`, its first Rollup0 state precondition MUST equal
`cursor_block.stateRoot`, replay MUST cover exactly `n`
blocks, and the final applicable state delta MUST equal the replayed Sync root.

Candidates in one Ethereum block are processed in canonical transaction order. Each applicable
candidate starts from the cursor left by preceding applicable candidates. A stale sibling does not
consume a range.

## 4.3 Per-Effect State Deltas

The EEZ binding defines the L1 `ExecutionEntry` and `StateDelta` encodings. Rollup0 uses the
symbols and prefix construction from §3.3:

```text
A    = header(cursor).stateRoot
Z    = root([])
R[k] = root(G[0] || ... || G[k])
```

`Z` is the state after all nonterminal blocks and the terminal Sync block's mandatory
pre-execution changes, with no Sync transaction executed. It MUST NOT be replaced by the
pre-Sync parent root.

A rich candidate with `m > 0` effects MUST carry this Rollup0 chain:

```text
anchor          = (rollupId, A,      Z,    0)
effect[0]       = (rollupId, Z,      R[0], etherDelta[0])
effect[k], k>0  = (rollupId, R[k-1], R[k], etherDelta[k])
```

The anchor MUST precede every effect entry. Each effect entry has exactly one Rollup0 delta at its
execution position. Each `etherDelta[k]` MUST match only that effect's exact cross-network value
movement. The last `R[m-1]` MUST equal the full rich Sync root.

An anchor-only candidate has no effect entry. For its complete ordinary Sync user body `U`, let
`F = root(U)`. It MUST carry exactly one Rollup0 delta:

```text
anchor-only = (rollupId, A, F, 0)
```

An empty anchor-only Sync body has `F = Z`. A nonempty anchor-only body is allowed, but none of its
transactions can require an EEZ effect entry.

Every validator MUST recompute `Z` and every `R[k]` by sequentially executing the corresponding
body prefix on the same pre-Sync parent and with the same terminal block environment. It MUST NOT
execute one prefix as a child block of another prefix. It MUST reject a candidate that copies the
final Sync root into an earlier delta. That historical construction is unsafe because it can
commit state from a later effect before the corresponding Ethereum-side action has occurred.

### Rollup0 Batch Restrictions

In addition to all EEZ structural rules:

- `blobIndices` is empty;
- top-level and nested lookup arrays are empty;
- static, failed, nested, reentrant, and multi-call effects are absent;
- every participating Rollup0 proof-system assignment satisfies the activated membership and
  threshold;
- `blockNumber` is the explicit recent Ethereum proof-context block selected under §2.3; and
- transient execution and lookup counts equal the exact activated routing construction.

`eez-evm@0.2-draft` does not include the transient routing counts or submitter identity in its proof
public-input hash. A validator MUST authenticate the complete submitted batch bytes, including
those counts, and the activation MUST select an external mitigation that prevents proof reuse
across another routing choice or submitter context. The mitigation is unresolved and blocks
production.

## 4.4 Ethereum Bundle

The candidate identifies an exact ordered list:

```text
bundle = [postAndVerifyBatch, trigger[0], ..., trigger[i-1]]
```

For the `i` inbound effects in the candidate, `trigger[j]` is the one exact Ethereum transaction
that attempts to consume inbound effect `j`. Each inbound effect MUST have a distinct trigger, and
one trigger MUST NOT produce more than one inbound effect for the candidate. The transactions
appear in inbound-effect order. A candidate with no inbound effect uses the one-transaction bundle.

Production candidate-range `N_max`, effect-count, total bundle-byte, and gas limits are unresolved.
The current composer drains at most three held transactions into a candidate bundle by default;
`EEZ_MAX_USER_TXS_PER_BUNDLE` can change that limit. The held pool itself has no three-transaction
admission cap. This implementation default is not a production capacity selection.

Every transaction MUST pass:

- canonical envelope and signature validation;
- Ethereum chain ID and replay-protection checks;
- nonce, intrinsic gas, fee, balance, and block-gas checks;
- sequential simulation after every preceding bundle element; and
- exact correspondence to the candidate's EEZ effects.

The activated relay/builder MUST include all transactions in exact order at consecutive transaction
indices in one selected canonical Ethereum block, or include none. No transaction or call that can
replace or consume the selected queue may be interleaved. The mechanism MUST NOT allow a trigger
transaction to be dropped. A validly included trigger whose EEZ consumption call reverts is a
non-applied effect under §4.5; its status-`0` receipt is sufficient evidence after the exact trigger
is authenticated. Internal revert data and reverted logs are not required. The failed receipt does
not excuse a missing, reordered, or unrelated trigger. The selected inclusion mechanism MUST bind
this behavior explicitly. Public-mempool sequential submission does not meet this rule.

The production builder or atomic-inclusion mechanism, target semantics, fee
funding, and failure behavior are release blockers. Candidate submission and
relay remain permissionless: the inclusion mechanism cannot create a composer
or relayer allowlist.

## 4.5 Canonical Settlement Evidence

Settlement is derived from canonical Ethereum blocks, transactions, receipts, and ordered log
occurrences. A follower MUST NOT infer settlement from `BatchPosted` alone or from a set of state
root values found somewhere in a block.

For each included candidate:

1. Authenticate the canonical Ethereum header, block number, hash, and required timestamp
   constraints.
2. Locate the exact post transaction by hash and transaction index.
3. Locate every claimed trigger at the next exact index in bundle order.
4. Require the post receipt to succeed.
5. Within each receipt, preserve log order and duplicate occurrences.
6. Accept only logs from the activated EEZ address and selected rollup ID.
7. Require the exact `BatchPosted` occurrence defined by the EEZ binding.
8. Classify the anchor from the ordered success or skip event that belongs to its exact index.
9. Classify every immediate effect by the ordered success or skip event that belongs to its exact
   index.
10. Classify every deferred effect from the exact trigger receipt and ordered consumption and
    state events that identify its queue item. An authenticated status-`0` receipt classifies that
    exact trigger as non-applied; a successful receipt requires the exact surviving consumption and
    state events to classify it as applied.
11. Require a rich result to be either no applied anchor and no applied effect, or the applied
    anchor followed by exactly the first `q` effects, for one `0 <= q <= m`.
12. Require the final applied occurrence to equal `Z` when `q = 0`, or `R[q-1]` when `q > 0`.
13. Require an anchor-only result to be either unapplied or its sole `A -> F` delta applied.

Receipt boundaries, transaction indices, log indices, event kind, effect index, queue cursor, and
duplicate multiplicity are consensus inputs. Root equality is not a substitute.

### Competing Candidates

After evidence is authenticated, process candidate posts in canonical Ethereum transaction order:

- if the candidate's exact parent height, block hash, and state root equal the current cursor
  identity, validate and apply its unique selected endpoint;
- if any parent-identity field differs, classify the candidate as stale and do not advance, even
  when its state root equals the current root;
- after an applicable candidate advances, use the selected endpoint height, hash, and root as the
  cursor for the next transaction; and
- never choose a candidate by composer identity, local arrival time, or proof arrival time.

If the rich anchor does not apply, no part of the range advances. If it applies, `q = 0` is a
valid zero-effect settlement and `0 < q < m` is a proper effect prefix. Either case selects the
deterministic repaired Sync block under §6. A hole, ambiguous occurrence, wrong transaction, or
reused event invalidates the candidate.

## 4.6 Failure

A submitted candidate remains pending until canonical evidence proves it applicable, stale,
expired, or invalid. A local timeout cannot manufacture a canonical verdict.

On failure, the composer MAY roll back its local unsafe candidate and requeue transactions.
It MUST first re-read the canonical cursor so that a stale local verdict cannot undo a competing
candidate already accepted by Ethereum ordering.

---

*Next: [§5 Cross-Network Flows](05-l1-to-l2.md).*
