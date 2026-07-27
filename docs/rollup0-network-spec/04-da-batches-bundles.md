# 4. Data Availability, Batches, and Gnosis Bundles

This chapter defines the Rollup0 v0 DA payload, batch selection, settlement evidence, and Chiado
bundle. EEZ defines reusable execution and proof concepts. Rollup0 owns the rules in this chapter.
Appendix E pins the historical `5c51e02` ABI and hashes.

## 4.1 Active DA channel

Rollup0 v0 publishes the complete payload in `postAndVerifyBatch.callData`:

```text
payload := 0x00 || rlp([blockTxCounts, transactions, l2_entries])
```

Tag `0x00` calldata is the only active channel. `batch.blobIndices` MUST be empty. Producers,
validators, live followers, and catch-up followers MUST reject a v0 batch with a nonempty
`blobIndices` list before decoding `callData`. No blob tag, packing rule, sidecar rule, or
calldata-versus-blob selector is active. Adding one requires a new profile version.

| Field | RLP shape | Meaning |
|---|---|---|
| `blockTxCounts` | list of byte strings | one canonical-minimal `uint16` user-transaction count for each produced L2 block |
| `transactions` | list of byte strings | complete signed EIP-2718 user-transaction envelopes in block-major order |
| `l2_entries` | list of byte strings | complete ABI encodings of producing derivation-form L1-shape `ExecutionEntry` values: outbound entries first, then inbound entries; §4.1.2 defines their exact relation to `batch.entries` |

### 4.1.1 Strict decoding

A decoder MUST enforce all of the following:

1. The payload is nonempty and starts with `0x00`.
2. The bytes after the tag contain exactly one canonical RLP item and no trailing bytes.
3. The item is a three-element list, and each element is itself a list.
4. `blockTxCounts` is nonempty. Each item is a canonical-minimal unsigned integer with no leading
   zero and a value at most `65535`. Integer zero is the empty RLP string.
5. `sum(blockTxCounts) == len(transactions)`.
6. Every transaction item is a byte string. During replay it MUST decode as exactly one complete
   supported signed envelope with no trailing bytes.
7. Every entry item is a byte string. It MUST decode from the entire item as exactly one
   `5c51e02` L1-shape `ExecutionEntry`.
8. `l2_entries` contains exactly one item for every producing entry in `batch.entries`, in the
   same order and with the transformation in §4.1.2. The state-anchor entry is absent.
9. `l2_entries` MUST be empty if and only if `batch.entries` contains only the state anchor.
   A follower MUST NOT reconstruct a missing sidecar from `batch.entries`.

The codec treats transaction and entry bytes as opaque only at the outer RLP layer. Signature,
chain, nonce, fee, balance, ABI, execution, and reserved-sender checks remain mandatory during
derivation. Appendix B separates the outer-codec vector from the strict end-to-end decoder vector.

### 4.1.2 Sidecar correspondence

Let `r` be the selected Rollup0 rollup ID, let `B = batch.entries`, and let `S` be the decoded
`l2_entries` sequence. A valid v0 batch has:

```text
B = [anchor, O_chain[0], ..., O_chain[o-1], I_chain[0], ..., I_chain[i-1]]
S = [        O_da[0],    ..., O_da[o-1],    I_da[0],    ..., I_da[i-1]]

transientExecutionEntryCount = 1 + o
transientLookupCallCount      = 0
l1ToL2lookupCalls             = []
len(S)                        = len(B) - 1 = o + i
```

`B` MUST be nonempty. The anchor has no sidecar counterpart. It has
`proxyEntryHash = bytes32(0)`, `destinationRollupId = r`, empty call and expected-call arrays,
`callCount = 0`, empty `returnData`, `rollingHash = bytes32(0)`, and exactly one state delta for
`r`. With producing entries, that delta is
`(r, header(cursor).stateRoot, header(sync-1).stateRoot, 0)`. In an anchor-only batch, its
`newState` is instead `header(sync).stateRoot`.

Every `S[k]` has empty `stateDeltas`, `destinationRollupId = r`, empty
`expectedL1ToL2Calls`, and empty `expectedLookups`. Every `B[k+1]` has exactly one state delta for
`r`. The first producing delta starts at the anchor's `newState`; later deltas start at the
preceding producing delta's `newState`. Every producing delta ends at
`header(sync).stateRoot`.

The paired fields MUST satisfy this table. "Equal" means byte-for-byte equality of the decoded
field, including array order and multiplicity.

| Field | Outbound pair `O_da[k]`, `O_chain[k]` | Inbound pair `I_da[k]`, `I_chain[k]` |
|---|---|---|
| `stateDeltas` | DA empty; chain has the delta above | DA empty; chain has the delta above |
| `proxyEntryHash` | zero in both | the same nonzero `H_in` in both |
| `destinationRollupId` | `r` in both | `r` in both |
| `l2ToL1Calls` | equal, exactly one `outer` | DA is exactly `[outer]`; chain is empty |
| `expectedL1ToL2Calls` | empty in both | empty in both |
| `expectedLookups` | empty in both | empty in both |
| `callCount` | `1` in both | DA is `1`; chain is `0` |
| `returnData` | equal | equal |
| `rollingHash` | equal to the successful one-call fold | DA has the successful one-call fold; chain is zero |
| producing `etherDelta` | `-int256(outer.value)` | `+int256(outer.value)` |

For every `outer`, `revertSpan = 0` and `outer.value <= type(int256).max`. An outbound `outer` has
`sourceRollupId = r`. An inbound `outer` has `sourceRollupId = MAINNET_ROLLUP_ID = 0`, and:

```text
H_in = keccak256(abi.encode(
    r,
    outer.targetAddress,
    outer.value,
    outer.data,
    outer.sourceAddress,
    outer.sourceRollupId
))
```

The successful one-call fold is
`CALL_END(CALL_BEGIN(bytes32(0), 1), 1, true, returnData)` under the compatibility binding.
Zero-value producing deltas use `etherDelta = 0`.

The sidecar and on-chain entry are deliberately not ABI-equal. In particular, the populated
inbound DA entry carries the call parameters needed for L2 delivery, while the on-chain deferred
entry is lean and commits those parameters through `H_in`. A validator or follower MUST perform
the field-by-field comparison above before it uses an entry or interprets an applied prefix.
Missing, extra, reordered, duplicate-lost, or mismatched entries invalidate the whole range. The
`callData` commitment alone does not establish this correspondence.

### 4.1.3 Sync-block count

The final count belongs to the Sync block and MAY be nonzero. It counts transported user
transactions, not reconstructed system transactions. For `O` outbound entries and `U` remaining
Sync users, the final count is `O + U`.

The canonical fixture uses:

```text
blockTxCounts = [2, 1]
```

It covers two blocks, and the final Sync block has one user transaction. A client that requires a
trailing zero does not implement Rollup0 v0.

## 4.2 Cursor-derived range

Let `cursor` be the highest L2 block accepted from preceding canonical settlement history, or the
configured genesis block before the first batch. Let `n = len(blockTxCounts)`. Because `n > 0`:

```text
range_parent = cursor
first_block  = cursor + 1
sync_block   = cursor + n
range        = (cursor, sync_block]
```

Compatibility code and older prose may call `cursor` `fromBlock` and `sync_block` `toBlock`.
Under that notation, `blockTxCounts[i]` belongs to `fromBlock + 1 + i` and
`len(blockTxCounts) == toBlock - fromBlock`.

Neither height is encoded in the DA payload, and the `5c51e02` proof fold does not independently
commit to L2 block numbers. Position is established operationally by the settled cursor and state
chain: the first relevant `currentState` MUST equal `header(cursor).stateRoot`, replay MUST cover
exactly `n` blocks, and the selected applied endpoint MUST equal the replayed Sync root. A losing,
unsettled, malformed, or ambiguous post does not advance the cursor.

Batches in one Chiado block are processed in canonical transaction and log order. Each advancing
batch starts from the cursor left by the previous accepted batch. Nominal slot width `K` is not a
range validity condition; deferred posting and catch-up can cover another positive length.

## 4.3 Batch fields

`postAndVerifyBatch` receives one compatibility-bound batch:

```solidity
struct ProofSystemBatchPerVerificationEntries {
    ExecutionEntry[]           entries;
    LookupCall[]               l1ToL2lookupCalls;
    uint256                    transientExecutionEntryCount;
    uint256                    transientLookupCallCount;
    address[]                  proofSystems;
    RollupIdWithProofSystems[] rollupIdsWithProofSystems;
    bytes32                    crossProofSystemInteractions;
    uint256[]                  blobIndices;       // MUST be empty in v0
    bytes                      callData;          // §4.1 payload
    bytes[]                    proofs;
    uint64                     blockNumber;       // explicit past Chiado proof context
}
```

The contract treats `callData` as opaque and folds its hash into the proof public inputs.
Validators and followers enforce the codec.

Rollup0 v0 fixes `crossProofSystemInteractions = bytes32(0)`. The compatibility contract accepts
an arbitrary `bytes32` and commits it to the shared public input, but Rollup0 does not define any
cross-proof-system interaction or another value for this field. Producers MUST set it to zero;
validators and followers MUST reject a nonzero value. Defining another value requires a new
Rollup0 protocol version.

The compatibility public-input hash commits to the entry and lookup hashes but omits
`transientExecutionEntryCount` and `transientLookupCallCount`. Those counts affect which prefixes
use transient routing and which state is published or retained. A proof over the remaining fields
does not authenticate either count. Validators MUST bind their attestation decision to the exact
submitted batch calldata, including both counts, and deployments MUST apply the restrictions in
§9.4. A proof cannot be treated as reusable across count variants.

For a rich attempt scheduled from observed Chiado head `(N, H, T)`, `batch.blockNumber` MUST be
`N`. It MUST NOT be zero, `uint64.max`, or the future inclusion target. The operator and validators
MUST authenticate `H`, and the manager MUST return the compatibility-bound context for N.

The v0 entry order is:

```text
[state anchor, outbound entries..., inbound entries...]
```

`transientExecutionEntryCount` is one plus the outbound-entry count. Partial settlement is
interpreted only against this order and exact event occurrences under §4.5.

## 4.4 Bundle construction

The producer admits at most three Chiado source transactions per attempt. After decoding,
ordinary source-chain validation, and sequential simulation against the state established by the
preceding bundle elements, it constructs:

```text
bundle = [postAndVerifyBatch_tx, inbound_user_tx[0], ..., inbound_user_tx[P-1]]
P = i
0 <= P <= 3
```

There is exactly one rider for each inbound batch/sidecar entry and no rider without an inbound
entry. Rider `j` corresponds to `I_chain[j]` and `I_da[j]`. The batch transaction is first. In the
canonical Chiado block, rider `j` MUST be the transaction at
`transactionIndex(postAndVerifyBatch_tx) + 1 + j`. Riders are the surviving inbound source
transactions in their original FIFO and deferred-entry order, with no unrelated transaction
inserted. Outbound L2 users are in the Sync block and DA payload, never in the Chiado bundle. The
one-element form (`P = i = 0`) is valid for empty, outbound-only, catch-up, or fully filtered work.

Every rider MUST pass signature, chain, nonce, intrinsic-gas, fee, maximum-balance, and sequential
simulation checks. A deterministic invalid rider is excluded with its dependent higher-nonce
suffix. A transient validation failure cannot authorize an unvalidated rich bundle.

## 4.5 Atomicity and canonical settlement evidence

A conforming production relay MUST include the submitted raw transactions all or none, in their
exact order, in one Chiado block at the requested block number and Sync timestamp. It MUST NOT use
an allowed-revert or droppable-rider list. Sequential public-mempool submission and the development
bundle shim do not provide this property and MUST fail closed outside explicit development mode.

The EVM does not roll back `postAndVerifyBatch` when a later transaction fails. Relay atomicity is
therefore a trust assumption, not an EEZ contract guarantee. The proof digest also does not commit
to the rider transaction hashes or bundle membership. Validators MUST inspect the intended raw
transaction list and order before attesting.

Settlement is determined from canonical receipts, not from `BatchPosted` alone and not from a set
of roots observed somewhere in the inclusion block:

1. Authenticate the canonical Chiado block, requested number, hash, and timestamp.
2. Let `p` be the post transaction index. Require enough transactions to exist in the same block
   and identify rider `j` as canonical transaction `p + 1 + j` for every `0 <= j < i`.
   Authenticate the post and those riders by hash and index. An interposed transaction, a missing
   rider, or an additional claimed rider is invalid.
3. Read each receipt in that order and require the post receipt to have status `1`. Within a
   receipt, preserve `logIndex`.
4. Accept only logs emitted by the selected EEZ address and, where indexed, the selected rollup ID.
5. Require exactly one `BatchPosted` occurrence in the post receipt. It MUST follow all immediate
   outcome logs, and its indexed `rollupCount` MUST equal
   `len(batch.rollupIdsWithProofSystems)`.
6. Let `m = transientExecutionEntryCount = 1 + o`. Classify immediate indices `0..m-1` from the
   post receipt. After filtering by emitter and selected rollup, the next relevant log for each
   index MUST be exactly one of:
   - `L2ExecutionPerformed(r, expectedNewState)`, which classifies that index as applied; or
   - `ImmediateEntrySkipped(index, revertData)`, which classifies that index as not applied.
   A skip index MUST equal the next unclassified index. Missing, duplicate, out-of-range, or
   reordered classifications are invalid. The revert payload is diagnostic and MUST NOT be used
   to change this classification.
7. Classify inbound index `j` from the receipt of rider `j`. An applied rider has status `1` and
   exactly one ordered pair
   `ExecutionConsumed(H_in[j], r, queueIndex)` then
   `L2ExecutionPerformed(r, expectedNewState[j])`, with no extra selected-rollup consumption or
   state-delta occurrence. A rider with no retained pair is not applied. A partial pair, a
   mismatched hash or rollup ID, reversed order, or extra pair is invalid. `queueIndex` is the
   contract's persistent per-rollup queue cursor, not a batch-relative index. Let `q` be the
   authenticated next cursor after the post receipt and before the first rider. An applied rider
   MUST report `queueIndex = q`, and queue item `q` MUST be that rider's `I_chain[j]`; then set
   `q = q + 1`. A not-applied rider leaves `q` unchanged. A reused or jumped cursor is invalid.
8. Concatenate the classified outcomes in batch order
   `[anchor, outbound..., inbound...]`. Every applied outcome MUST precede every not-applied
   outcome. An applied outcome after the first not-applied outcome is a non-prefix hole and
   invalidates the range, even when all emitted roots have the same value. The applied prefix
   length is the number of leading applied outcomes.

Appendix E.9 fixes the event topic hashes, indexed fields, and data encodings. Receipt status,
transaction boundary, `logIndex`, event kind, and indexed skip/consumption data are consensus
inputs to attribution. Counting `L2ExecutionPerformed` logs alone is invalid because Rollup0
entries can deliberately repeat the Sync root.

The full batch settles only when the final attributable occurrence equals the intended Sync root.
If no state delta applied, the cursor does not advance. An unambiguous proper prefix selects the
deterministic repaired Sync block in §6.3. Ambiguous evidence halts derivation at the previous safe
head. A follower MUST NOT infer a prefix by root membership, deepest matching value, or a
per-Chiado-block `HashSet`.

## 4.6 Observation and failure

A submitted attempt remains pending until canonical evidence proves settlement or proves that the
exact target cannot contain it. Receipt success alone is insufficient. Observation MUST validate
the inclusion number, canonical hash, target timestamp, transaction order, EEZ address, events,
and selected endpoint.

If the attempt does not land, §2.5 governs optimistic rollback and held-transaction recovery. A
stale failure verdict cannot undo a Sync height already reached by canonical derivation. Final
safe/finalized advancement and Chiado reorg handling are in §6.

---

*Next: [§5 Cross-Chain Flows](05-l1-to-l2.md).*
