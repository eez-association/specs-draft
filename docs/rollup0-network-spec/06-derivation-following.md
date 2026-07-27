# 6. Derivation and Following

Publishing replay data is a Rollup0 choice, not an EEZ requirement. Rollup0 v0 derivation is
key-gated: byte-identical reconstruction of signed legacy system transactions requires the
configured `SYSTEM_ADDRESS` private key. Chiado data alone is insufficient for a permissionless
follower.

Derivation detects disagreement and defines a local safe view. It is not a fraud proof, does not
reverse an EEZ-accepted root, and does not create a trustless exit.

## 6.1 Canonical input and index

A follower MUST first authenticate:

- the Rollup0 activation record and protocol version;
- the L2 genesis artifact and hash under Appendix D;
- the Chiado chain identity and canonical headers;
- the EEZ, manager, proof-system, and rollup deployment tuple; and
- the system signer and key required by Appendix C.

It scans `BatchPosted` logs from the selected EEZ deployment block in bounded chunks. Before
processing, it sorts results by:

```text
(blockNumber, transactionIndex, logIndex)
```

RPC return order is not canonical order. For every occurrence, it fetches the exact transaction
from the authenticated canonical block, verifies its hash and index, ABI-decodes the
`postAndVerifyBatch` calldata, obtains the receipts for the submitted bundle, and applies §4.5.
An event from another address, rollup, transaction, or orphaned block has no authority.

The post transaction hash is the historical/live deduplication key. A duplicate observation of the
same canonical transaction is processed once. A distinct transaction remains distinct even when
its calldata, roots, or user transactions equal an earlier transaction. Canonical origin and
payload decoding are checked before a duplicate can be ignored.

## 6.2 Cursor and range selection

Let `cursor` be the highest L2 block accepted from preceding settled history, or the configured
genesis block before the first batch. For a strictly decoded payload with
`n = len(blockTxCounts) > 0`, derive:

```text
first = cursor + 1
sync  = cursor + n
range = (cursor, sync]
```

All arithmetic is checked. The first relevant state delta for the followed rollup MUST start at
`header(cursor).stateRoot`. The cursor advances only after the complete candidate range passes
reconstruction, full-header validation, and endpoint comparison.

An attempt with no applied state delta, an invalid attempt, or an ambiguous attempt does not
consume a range. A later advancing batch starts at the same cursor. Several advancing batches in
one Chiado block are processed in transaction/log order, and each starts from the cursor left by
the preceding accepted batch.

## 6.3 Deterministic reconstruction

Decode `callData` under §4.1 and partition `transactions` by `blockTxCounts`. Every partition
except the last is that block's complete ordered user list. The last partition, `syncUsers`, is
the Sync block's ordered user list and MAY be nonempty.

### 6.3.1 Entry sidecar

Validate the exact sidecar-to-batch transformation in §4.1.2 before reconstruction. The sidecar is
mandatory whenever the batch has a producing entry. The on-chain inbound form is call-empty and
cannot replace the populated derivation form, including for a zero-value call.

Let:

```text
o        = transientExecutionEntryCount - 1
entries  = decoded l2_entries
outbound = entries[0:o]
inbound  = entries[o:len(entries)]
```

The subtraction is checked. Require every outbound entry to have `proxyEntryHash == 0`, every
inbound entry to have a nonzero `proxyEntryHash`, and the complete field correspondence in
§4.1.2. A follower MUST NOT partition and reorder an arbitrary mixed list, infer a missing item,
or fall back to `batch.entries`.

### 6.3.2 Exact applied prefix

Use the per-index, occurrence-preserving settlement classification from §4.5. Do not derive the
classification from an `L2ExecutionPerformed` count or root list: repeated roots cannot identify
which immediate index skipped, and each deferred result belongs to one exact rider receipt.
Evidence from another transaction or batch cannot be reused.

Require the classified sequence `[anchor, outbound..., inbound...]` to contain one leading run of
applied outcomes followed by zero or more not-applied outcomes. If an applied outcome follows a
not-applied outcome, the result has a hole and the whole candidate range is invalid. Let `a` be
the number of applied producing entries after an applied anchor. Require
`0 <= a <= len(entries)` and select exactly `entries[0:a]`; do not select by root value. If the
anchor is not applied, require every producing entry to be not applied and set `a = 0`.

The state anchor is first, followed by outbound and then inbound producing entries. When the
evidence identifies the unique prefix:

```text
appliedProducing = entries[0:a]
outboundApplied  = entries[0:min(a, o)]
inboundApplied   = entries[o:a] when a > o, otherwise []
O                = outboundApplied
I                = inboundApplied
```

The applied sequence MUST be a prefix of `[anchor, outbound..., inbound...]`. It MUST NOT contain
an inbound entry before an unapplied outbound entry, skip an occurrence, reuse a duplicate root,
or include an occurrence not attributable to the exact bundle. No applied anchor means no cursor
advancement. Ambiguous or non-prefix evidence is a derivation error.

### 6.3.3 Sync transaction order

Require `len(syncUsers) >= len(O)`. Pair `O[j]` with `syncUsers[j]` in order. Starting with the
system nonce from the reconstructed Sync parent state, build and sign:

```text
load(O[0]), syncUsers[0],
load(O[1]), syncUsers[1],
...,
load(O[len(O)-1]), syncUsers[len(O)-1],
deliver(I[0]), deliver(I[1]), ...,
syncUsers[len(O)], syncUsers[len(O)+1], ...
```

Each load appears immediately before its consuming outbound user transaction. Loading all
outbound entries at the head is invalid. All inbound deliveries follow the outbound pairs and
preserve entry order. Users not paired with an applied outbound entry remain at the tail in their
original order; partial settlement does not silently remove transported transactions.

Appendix C defines both signed legacy envelopes, nonce progression, calldata, value, gas,
signature, receipt, and failure behavior. A follower MUST NOT skip a system transaction,
substitute a signature, alter a nonce, or synthesize type `0x7E`.

Intermediate blocks in the range MUST NOT contain a transaction from `SYSTEM_ADDRESS`. Therefore
the Sync nonce is determined by the authenticated parent state and preceding reconstruction. A
missing key, signer mismatch, or nonce overflow invalidates the range.

### 6.3.4 Block and endpoint checks

From the authenticated range parent, the follower:

1. reconstructs every transaction list;
2. builds every execution environment and all 23 header fields under §2;
3. executes each block in order;
4. validates the complete sealed header and body for every locally reusable block;
5. compares the final state root with the last exact applied occurrence selected under §4.5; and
6. commits the whole range and advances the cursor atomically.

A local-block fast path is allowed only when ancestry, complete ordered transactions, execution
result, and every sealed header/body field match. After the first mismatch, all later blocks in
the range are rebuilt on the new ancestry. Transaction-only or final-state-only comparison is not
conformance.

For a full settlement, the endpoint MUST equal the intended rich Sync block. For an unambiguous
proper prefix, the reconstructed endpoint is the canonical repaired Sync block. The operator's
richer optimistic block and its unsafe descendants are replaced. If replay does not produce the
exact selected root, the follower restores its pre-range head and cursor and halts.

## 6.4 Invalid data and execution

The following invalidate the whole candidate range:

- nonempty `blobIndices`;
- an empty payload, unknown tag, malformed or noncanonical RLP, trailing bytes, wrong list shape,
  empty count list, noncanonical count integer, `uint16` overflow, or count-sum mismatch;
- a malformed or trailing ABI sidecar item;
- an empty, missing, extra, reordered, or field-mismatched sidecar relative to `batch.entries`;
- a transaction byte string that is not one complete supported signed envelope;
- an invalid signature, chain, nonce, fee, intrinsic gas, balance, or other block-validity rule;
- an unexpected intermediate transaction from `SYSTEM_ADDRESS`;
- an entry/user cardinality or order mismatch;
- inability to construct an exact system transaction;
- a cursor pre-state, header, body, receipt, or selected endpoint mismatch; or
- missing, reordered, extra, cross-batch, reused, non-prefix, or ambiguous settlement evidence.

The follower MUST NOT skip, rewrite, partially accept, or guess around the error. Tentative blocks
are rolled back and the safe cursor remains unchanged. A persistent error in canonical history
halts derivation for operator intervention, even when validators attested the post.

A valid user transaction whose EVM call reverts is not malformed. It remains in position,
increments its nonce, pays gas, produces a status-`0` receipt, and contributes to the block result.

## 6.5 Unsafe, safe, and finalized views

The operator feed controls only the unsafe view. A follower labels a block:

- **safe** only after canonical settlement evidence is authenticated, deterministic replay reaches
  it, and the complete block matches; and
- **finalized** only when it is safe and its containing Chiado block is finalized.

`finalized` MUST NOT exceed `safe`. `BatchPosted` alone, a matching root from another occurrence,
or operator publication cannot advance either label.

Relative to `(safeNumber, safeHash)`, an unsafe candidate below safe is rejected. A candidate at
safe must have the exact safe hash. A candidate above safe is compatible only when its available
ancestry reaches that hash. Missing ancestry is unverifiable, not compatible; it may be used as an
unsafe sync target but cannot move safe/finalized and must yield to later canonical derivation.

## 6.6 Startup and live resynchronization

At startup, validate stored Chiado block hashes and retreat orphaned index records before scanning
forward. Start from the first unindexed canonical block or the selected deployment block. For each
post, apply §§4.5 and 6.1-6.5 sequentially.

A live subscription does not replace the scan. Catch up, subscribe, then rescan the subscription
gap. On lag, disconnect, incomplete transaction lookup, or inconsistent provider data, rescan
canonical history. Live and historical paths MUST make the same decision for the same post and
update their in-memory deduplication set after each accepted transaction.

Catch-up posts may use the one-element bundle and cover every unposted L2 block through a new Sync
block. They use the same positive range, strict decoding, receipt selection, replay, and endpoint
rules.

## 6.7 Chiado reorgs and optimistic recovery

When Chiado has a canonical reorg with common ancestor A:

1. remove indexed attempts whose inclusion block is above A;
2. reset the cursor to the last surviving accepted endpoint, or genesis when none survives;
3. reduce safe and finalized to surviving endpoints;
4. move the local canonical L2 head to that cursor;
5. restore eligible optimistic source transactions in original FIFO order only when the exact
   transaction has no canonical receipt on the replacement branch; and
6. derive the new canonical Chiado branch in order.

Startup hash validation produces the same result when a notification was missed. Orphaned roots,
payloads, receipts, and events have no authority. Production remains quiescent until cursor and
local head agree.

Only one rich attempt may be unresolved. Dropped-attempt recovery and derivation use one
reconciliation lock and re-read the cursor before rollback. If derivation already reached the
attempt's Sync height, a stale failure verdict MUST NOT requeue its users or roll back its state.
If an unambiguous prefix settled, canonical derivation wins and replaces the optimistic rich Sync
block with the repaired block from §6.3.

A common ancestor deeper than the configured automatic history, or displacement of finalized
Chiado settlement, halts automatic recovery. Operators MUST quiesce production, authenticate a
recovery point, repair the L1 index and L2 database consistently, and publish the decision before
restart. The protocol does not authorize silently retaining an orphaned safe head.

## 6.8 Current implementation blockers

The imported Rollup0 client still has release-blocking deviations:

- the source codec accepts an empty count list and does not enforce every strict outer-RLP rule;
- live/catch-up paths do not independently reject nonempty `blobIndices`;
- scanning and settlement attribution can discard order and duplicate multiplicity by reducing
  roots to per-block sets;
- candidate riders are not all simulated sequentially;
- the public-mempool and development bundle fallbacks are not atomic;
- multi-block replay is committed one block at a time instead of transactionally;
- the local-block fast path does not authenticate every sealed header/body field;
- automatic common-ancestor discovery is bounded (default 62 Chiado blocks);
- shallow-reorg recovery lacks full canonical-receipt parity with dropped-attempt recovery; and
- unverifiable unsafe ancestry is forwarded up to an implementation bound without establishing
  safe compatibility.

These are implementation defects, not alternate protocol behavior.

---

*Next: [§7 Gas, Limits, and Economics](07-gas-economics.md).*
