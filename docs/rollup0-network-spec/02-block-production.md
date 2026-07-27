# 2. Timing, Slot Production & Header Rules

This chapter defines the Rollup0 v0 production schedule and the header rules used by the
sequencer, Sync-block composer, and deriver. Sections 2.1-2.8 are **normative**. Section 2.9 is
informative and contains worked vectors. In this chapter, "L1" means the configured Gnosis
Chain settlement host. The initial `rollup0-v0` deployment uses Chiado.

The schedule is a total state machine over an ordered input trace: the timing configuration, L2
genesis and current heads, observed canonical L1 heads, timer events, the wall-clock sample used
for the lateness check, and ordered transaction inputs. For every valid configuration and input
state, the rules below return a block sequence, an explicit no-op, or an explicit error. They do
not assume that L1 produces a block at every nominal slot.

## 2.1 Timing configuration

Each Rollup0 network MUST pin these unsigned integer millisecond values. The names in the second
column are the current implementation's environment variables; the symbols are the protocol
names.

| Symbol | Configuration name | Meaning |
|---|---|---|
| `D1` | `EEZ_L1_BLOCK_TIME_MS` | nominal L1 block interval |
| `D2` | `EEZ_L2_BLOCK_TIME_MS` | L2 block interval |
| `P` | `EEZ_PROOF_TIME_MS` | worst-case composition/proof budget used by the lateness test |
| `S` | `EEZ_SUBMISSION_SLACK_MS` | required relay lead time before the target L1 slot |

`D1`, `D2`, and `P` MUST be greater than zero. `S` MAY be zero. A node MUST reject the
configuration at startup unless all of the following hold:

```
D2 mod 1000 = 0
D1 mod D2 = 0
K = D1 / D2
K >= 2
P + S < D1
P + S <= (K - 1) * D2
```

Each raw value MUST fit in `uint32`. The additions and products MUST be checked; overflow is an
invalid configuration. `D2 mod 1000 = 0` is required because EVM header timestamps are integral
seconds. Because `D1` is an integer multiple of `D2`, `D1` and the derived trigger offset are also
whole seconds. `K` is therefore an integral **nominal slot width**, not a fixed batch length and
not a claim that one L1 block arrives every `D1`.

`rollup0-v0` pins:

```
(D1, D2, P, S) = (5000, 1000, 500, 1300) ms
K = 5
```

Timing parameters are network/version configuration. Changing one on an existing chain requires a
declared protocol activation; an operator MUST NOT change them as a local runtime preference.
An implementation default other than the values above is not conforming unless a later activated
profile pins that default. Standalone, no-L1 mode is outside the Rollup0 network protocol.

## 2.2 Live, Future, and Sync composition

Let:

```
B = P + S
Q = ceil(B / D2)
F = Q - 1
L = K - F - 1 = K - Q
O = D1 - (F + 1) * D2 = D1 - Q * D2
submission_deadline_offset = D1 - S
```

The validity conditions in §2.1 guarantee `Q >= 1`, `F >= 0`, `L >= 1`, and `O >= D2`.
A nominal steady slot contains:

```
L Live blocks || F Future blocks || 1 Sync block
```

- A **Live block** is produced on the ordinary wall-clock cadence.
- A **Future block** is pre-built at the proof-window trigger. Its timestamp follows the same
  parent rule as every other block, but is normally ahead of wall clock when constructed.
- A **Sync block** terminates a steady or catch-up production chunk. Only a caught-up, non-late
  steady Sync block with no unresolved earlier submitted batch is eligible to drain held
  cross-chain intents.

These kinds are production labels; they are not encoded in the block header. Live and Future
blocks use the ordinary transaction pool. A rich Sync block contains the deterministic
cross-chain and user-transaction sequence in [Appendix C](C-system-transactions.md). A structural,
late, or deferred Sync block has no cross-chain content; a pool-built one can still contain
ordinary L2 transactions. A submitted endpoint can contain system transactions and remaining user
transactions, so its `blockTxCounts` value can be nonzero. The DA count is the number of
transported user transactions only; reconstructed system transactions are not counted. An earlier
pool-built Sync label can appear as an ordinary user-transaction block inside a later range
(§2.4 and §4.1).

The trigger opens `O` after an observed L1 head. Because `Q * D2 >= P + S`, beginning the
Future/Sync composition at that trigger reserves at least `P` for composition/proving and `S` for
relay submission before the predicted next L1 slot. There is therefore a real proof window in v0;
the old fixed “5 Live + Sync, no proof window” layout is not a protocol rule.

## 2.3 Observed-L1-head scheduler

Let `g` be the L2 genesis timestamp in Unix seconds and let `d1 = D1 / 1000`,
`d2 = D2 / 1000`, and `o = O / 1000`. An **observed L1 head** is a canonical-head event
`A = (n, hash, t)`, where `n` is its L1 block number, `hash` is its block hash, and `t` is its
actual Unix timestamp in seconds. For each observed head, compute:

```
trigger_at(A)          = t + o
proposed_sync_time(A)  = t + d1
target_height(A)       = floor(
    saturating_sub(proposed_sync_time(A), g) / d2
)
target_l1_block(A)     = n + 1
```

The additions MUST be checked in `uint64`. An overflow makes that observation unusable: the node
MUST emit no event from it and MUST surface an error. Only the subtraction before division
saturates, so a proposed time at or before genesis maps to height zero. No milliseconds are
silently inserted into a header: `trigger_at`, `proposed_sync_time`, `g`, and all header
timestamps are seconds.

The scheduler MUST retain the latest `target_height` for Live ticks and arm one pending trigger.
If another canonical L1 head is observed before that pending trigger is emitted, the new head
**supersedes** the pending head: replace the pending trigger and do not emit the old one. A later
trigger catches up any skipped L2 height. Events processed at the same instant are ordered by the
scheduler's receive order; that order is part of the input trace.

Before the first L1 head, an L1-anchored sequencer MUST NOT produce Live blocks. Afterwards, a
timer delayed at `D2` intervals proposes at most one Live block per tick. Missed-tick behavior is
**Delay**: after a delayed tick, cadence resumes one `D2` later rather than emitting a burst. The
tick uses the latest target height and produces only while the L2 head is below that target's
Live-region end (§2.4). A tick MAY be dropped when the scheduler queue is full; the Sync trigger
fills any missing Live blocks. A missed timer tick therefore changes when a block is built, not
the deterministic height or timestamp of the eventual suffix.

The scheduler MUST NOT invent L1 heads for missed L1 consensus slots. A missed slot appears only
as a larger timestamp gap between two observed heads. Likewise, an irregular or off-grid L1
timestamp is used as observed; the floor in `target_height` makes the height calculation total.
The L1 block hash identifies the canonical observation and is used by L1-reorg processing, but it
does not enter a v0 L2 header field.

!!! warning "Current boundary-arithmetic gap (informative)"

    The current Rust scheduler uses ordinary `uint64` addition for `t + o`, `t + d1`, and
    `n + 1`, while header builders use saturating addition for parent timestamps. Those operations
    agree with this specification for ordinary Unix timestamps but not at the `uint64` boundary.
    They must become checked errors before boundary behavior is conforming.

## 2.4 Total per-trigger production function

Let:

- `H` be the current L2 head number;
- `T` be the trigger's `target_height`;
- `C = 300` be the maximum number of blocks in one catch-up chunk;
- `F`, `L`, and `K` be from §2.2; and
- `ceil_div(x, y) = floor((x + y - 1) / y)` for `x > 0`, and `0` for `x = 0`.

All subtraction below is saturating. The sequencer MUST compute:

```text
composition(H, T):
    if H >= T:
        return Idle

    live_end = T - (F + 1)

    if H < live_end:
        live_needed = live_end - H
        if live_needed <= L:
            return Slot(live = live_needed, future = F)

        gap = T - H
        steps_back = ceil_div(max(gap - C, 0), K)
        snap = steps_back * K
        terminal = T - snap
        if snap >= T or terminal <= H:
            return Idle
        return Catchup(live = terminal - H - 1)

    in_future = H - live_end
    return Slot(live = 0, future = max(F - in_future, 0))
```

The result is applied as follows:

| Result | Blocks produced |
|---|---|
| `Idle` | none |
| `Slot(live, future)` | `live` Live, then `future` Future, then one Sync |
| `Catchup(live)` | `live` Live, then one structural Sync; no Future blocks |

The terminal height of a catch-up chunk has the same residue modulo `K` as `T`; a chunk never
contains more than `C` blocks. Catch-up ignores the steady-state speculative-depth cap so a
dropped batch cannot permanently freeze recovery. A catch-up Sync block MUST NOT drain held
cross-chain intents. The current submitter may send a minimal, cross-chain-empty batch for that
terminal using an unpinned `NextBlock` target. In the current implementation, `NextBlock` resolves
at send time to the observed L1 tip plus two blocks; this is an operational submission offset, not
part of `K` or the exact rich-settlement rule.

For a `Slot` result, the sequencer MUST check the configured speculative-depth bound before every
block. When `unsafe_head - L1_confirmed_head >= max_speculative_depth`, it stops the current
trigger before producing the next block. The default bound is 64; a configured value of zero
disables it. The next tick or trigger recomputes from the new heads. Catch-up is still bounded by
`C`.

Each commit snapshots the selected parent. If derivation or recovery changes the canonical parent
before the commit is accepted, the commit is stale: the sequencer MUST stop the current trigger
without building on the stale parent and retry from the current head on a later event. Other
recoverable production errors likewise leave already-accepted prefix blocks in place and cause a
later event to recompute the remaining suffix.

### Parent and settlement anchors

The protocol uses five distinct anchor roles. They MUST NOT be substituted for one another:

| Anchor | Source | What it fixes |
|---|---|---|
| scheduling anchor | observed canonical L1 head `A = (n, hash, t)` | `trigger_at`, `T`, and the proposed target `(n + 1, t + d1)` |
| proof-context anchor | `A` for a rich batch; an explicitly sampled canonical pre-target L1 block for a minimal batch | non-zero `batch.blockNumber` and the block hash folded into `publicInputsHash` |
| construction parent | current canonical unsafe L2 head immediately before each commit | `parentHash`, `number`, `timestamp`, parent-derived fee/blob fields, and pre-state |
| batch-range anchor | L1-confirmed L2 cursor `c` and its canonical header | `fromBlock = c` and the batch's initial `currentState = header(c).stateRoot` |
| settlement anchor | the submitted endpoint Sync block `e` plus the L1 inclusion | `toBlock = e.number`, final `newState = e.stateRoot`, and, for a rich batch, exact L1 block number and timestamp |

For a rich batch anchored by `A`, `batch.blockNumber` MUST equal `n`, and the proof fold MUST use
`hash = blockhash(n)` as returned by every rollup manager
([Appendix E](E-compatibility-binding.md)). The reference manager's
timestamp component for an explicit past block is zero; the exact L1 timestamp is enforced
separately by the settlement target and receipt validation. `batch.blockNumber` MUST NOT be the
future inclusion target `n + 1`, whose block hash is unavailable during execution of that block.
The legacy `0` no-context sentinel and `uint64.max` latest-context sentinel MUST NOT be used by a
production batch. A minimal unpinned batch MUST bind an explicitly sampled canonical block that
precedes its chosen inclusion target and remains inside the L1 block-hash availability window.

The Sync composer MUST build on the full construction-parent header supplied by the sequencer, not
on a separately sampled “latest” header. The commit MUST compare the built block's `parentHash`
with the then-current unsafe head under the sequencing/derivation lock. The deriver selects the
same parent as block `i - 1` on the canonical range it is reconstructing.

### Sync timestamp and lateness

After the Live/Future suffix, derive the actual Sync timestamp from its parent:

```
sync_time = parent.timestamp + d2
```

`proposed_sync_time(A)` is a scheduling prediction only. If it differs from `sync_time` because
the genesis grid or L1 timestamp is irregular, the sequencer MUST use `sync_time` and MUST NOT
alter the parent cadence to force equality. A rich attempt is then pinned to `sync_time`, not to
the prediction. If L1 block `n + 1` does not have that exact timestamp, the attempt cannot settle.
Persistent phase misalignment between `g` and the settlement chain can therefore preserve
deterministic L2 production while preventing rich settlement; a production network MUST choose a
genesis/timing profile whose normal L1 slot timestamps align to the `d2` grid.

For a steady Sync block, sample wall clock `now_ms` immediately before rich composition:

```
sync_ms     = saturating_mul(sync_time, 1000)
ready_ms    = saturating_add(now_ms, P)
deadline_ms = saturating_sub(sync_ms, S)
late        = ready_ms > deadline_ms
```

Equality is on time. If `late` is true, the sequencer MUST commit a Sync block without held
cross-chain content and leave those intents queued for a later steady slot. If it is false, the
composer targets exactly `(target_l1_block(A), sync_time)`. A conforming relay includes the whole
bundle only in L1 block `n + 1` with that timestamp, or drops it. The operator MUST verify the
receipt's actual L1 block number, that block's canonical hash and timestamp, and the settlement
event before declaring success; relay behavior alone is not evidence. Thus a missed or
timestamp-drifted L1 target cannot settle a Sync block against a different L1 time.

Any previously submitted batch above the L1-confirmed L2 cursor—Pending, observer-Settled, or
Failed—prevents another submission. In that case cadence continues with a cross-chain-empty Sync
block. Only the deriver cursor reaching the earlier endpoint, or serialized failed-batch recovery,
reopens the gate. The next successful batch covers the accumulated unconfirmed range.

### Batch ranges

For the range notation used on the wire, `fromBlock = c` is the last L1-confirmed L2 block, the
first produced block is `c + 1`, and `toBlock = e.number` is the submitted Sync endpoint. Thus:

```
range             = (fromBlock, toBlock]
block_count       = toBlock - fromBlock
blockTxCounts.len = block_count
```

All additions/subtractions MUST be checked, `toBlock > fromBlock`, and the endpoint state root
MUST equal the final state applied on L1. The length is **not required to equal `K`**. Catch-up,
superseded triggers, deferred slots, an unresolved prior bundle, and failed submission can all
make a later batch span fewer or more than `K` blocks. `C = 300` caps one catch-up production
chunk; it does not cap an accumulated unconfirmed batch range. A deriver MUST accept any positive
range that satisfies the DA grammar, header rules, and state-transition checks; it MUST NOT
enforce `toBlock - fromBlock == K`.

Earlier structural Sync labels in a multi-slot range do not require special replay treatment:
because a label is not in the header and those blocks have no cross-chain content, they replay as
ordinary blocks. The batch endpoint is the block at which the batch's reconstructed system
transactions, if any, are applied.

For the rollup's settlement state-delta chain, the first `currentState` MUST be
`header(c).stateRoot`. The leading immediate delta advances that root to the construction parent
of endpoint `e`, `header(e - 1).stateRoot`; subsequent deltas chain exactly
`currentState[j] = newState[j - 1]`, and the last delta for the rollup MUST end at
`header(e).stateRoot`. A minimal batch consists of the leading immediate delta only, with its
`newState` set to the empty Sync endpoint root. These state anchors and the DA block-count range
MUST be derived from the same cursor snapshot.

The current deriver silently ignores a decoded payload whose `blockTxCounts` list is empty. That
is an implementation conformance gap: the positive-range rule above requires explicit rejection,
not a successful no-op.

## 2.5 Submission, rollback, and retry

A rich Sync block is committed to the unsafe L2 head before its exact-target L1 bundle resolves.
Minimal, cross-chain-empty batches have no optimistic cross-chain effects, but use the same
submission ledger. The operator MUST allow only one submitted batch above the L1-confirmed L2
cursor per rollup. Settlement requires all of:

- the `postAndVerifyBatch` receipt;
- canonical inclusion at the batch's submitted target, including exact block number and timestamp
  for a rich batch; and
- the complete receipt-bound, per-index classification in §4.5, whose final applied
  `L2ExecutionPerformed(rollupId, endpoint.stateRoot)` occurrence matches the endpoint.

A matching final root without the required skip and consumption attribution is not settlement.

The operator MUST apply these transitions:

1. **Pending.** Keep the Sync block unsafe and emit no later batch. Transient receipt or head-read
   failures remain Pending; they are not proof of failure.
2. **Settled.** Keep the ledger entry until the deriver's L1-confirmed cursor reaches its Sync
   height. The cursor is stronger evidence than the background observer.
3. **Failed.** Record the failure, but perform no chain mutation in the observer task. At the next
   Sync trigger, serialize recovery with sequencing and derivation and re-read the confirmed
   cursor.
4. **Stale failure.** If that cursor has reached the failed Sync height, discard the failure
   verdict; the L1-confirmed result wins.
5. **Rollback.** Otherwise, if the failed batch carried held transactions and its Sync block or a
   descendant is canonical, move the unsafe head to the recorded parent of the failed Sync block.
   This discards the failed block **and all of its unsafe descendants**, not only the one Sync
   block. A cross-chain-empty minimal batch has no optimistic L2 effects and needs no such
   rollback.
6. **Retry.** Requeue unburned held transactions at the front in original order. A transaction
   with an L1 receipt is not requeued. A timestamp-pinned target that L1 skipped, changed to
   another timestamp, or cannot report is retried without increasing its poison-attempt counter;
   another dropped attempt increments it. At three failed attempts, evict that transaction and
   every higher nonce in the same `(sender, direction)` nonce chain.
7. **Recovery failure.** If the reorg itself fails, restore the Failed ledger entry, keep the
   one-in-flight gate closed, and retry at the next Sync trigger.

The trigger that performs a rollback yields without rebuilding on the retreated parent. Its
pre-recovery parent snapshot is stale. A later trigger runs §2.4, normally enters Catchup, and
restores the parent-derived timestamp chain before cross-chain composition resumes.

On an L1 reorg, the deriver MUST retreat safe and unsafe L2 to the highest batch that survives at
the L1 common ancestor, then replay the new canonical L1 history (§6.4). Transactions from
settled optimistic batches rolled out by that reorg are requeued. A newly observed canonical L1
head then replaces any un-fired scheduler target under §2.3.

!!! danger "Current implementation limitation — release blocker (informative)"

    The current Rust deriver commits a multi-block replay one block at a time and does not restore
    its pre-replay head if a later block in the same range fails. It retries a resynchronization on
    the next L1 event, but the intervening half-replayed head violates the atomic recovery rule
    above. Transactional replay or an explicit pre-loop rollback is required before this behavior
    can be considered release-safe; this specification change does not resolve that implementation
    blocker.

!!! warning "Current exact-target and observation gaps (informative)"

    The current relay request sets the exact block number and equal minimum/maximum timestamps, but
    the receipt observer does not post-validate the receipt's block number, canonical block hash,
    or block timestamp. It accepts any inclusion block if the final-state event matches. In
    addition, the fallback for an RPC without `eth_sendBundle` sends transactions to the public
    mempool in order and cannot preserve either bundle atomicity or an exact target. Those paths do
    not satisfy this section and remain deployment/conformance blockers.

    The live composer also leaves `batch.blockNumber = 0`, so the on-chain manager returns the
    legacy `(timestamp, blockHash) = (0, 0)` context instead of binding the observed scheduling
    head. Although the Rust ABI now calls `getTimestampAndBlockHash(uint64)` correctly, the rich
    proof/context anchor above is not wired into the submitted batch.

    Receipt and head RPC errors are retried while Pending. The current observer has no independent
    timeout for a target-tip RPC that remains unavailable, so such an outage can hold the
    one-in-flight gate indefinitely. This is a liveness limitation, not permission to guess a
    failure verdict.

## 2.6 Header construction

All construction paths MUST use the same parent, ordered transaction list, chain specification,
and execution environment. Let `target = parent.timestamp + d2`. The generic payload-attribute
builder defensively computes:

```
timestamp = max(parent.timestamp + 1, target)
```

where additions are checked. Because `d2 >= 1`, a valid Rollup0 parent makes this exactly
`parent.timestamp + d2`. This clamp prevents a caller-proposed timestamp from violating strict
monotonicity; it does **not** permit a canonical Rollup0 block to use a different cadence. The
manual Sync builder and deriver use the same parent-derived timestamp directly. If the checked
addition overflows, construction MUST return an error and MUST NOT emit a block.

The execution header has the following 23 fields. JSON aliases are shown where they differ from
the Rust field name. No field is left to builder policy.

| Header field | Rollup0 v0 construction |
|---|---|
| `parentHash` | selected parent's hash |
| `ommersHash` / `sha3Uncles` | `0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347`, the Keccak hash of RLP `[]` |
| `beneficiary` / `miner` | `0x0000000000000000000000000000000000000000` |
| `stateRoot` | post-state root after all active-fork pre-execution changes, ordered transactions, and post-execution changes |
| `transactionsRoot` | canonical indexed-trie root of the exact EIP-2718 transaction envelopes in body order |
| `receiptsRoot` | canonical indexed-trie root of the corresponding typed receipts |
| `logsBloom` | bloom over the logs in those receipts |
| `difficulty` | `0` |
| `number` | `parent.number + 1`, checked for `uint64` overflow |
| `gasLimit` | `30_000_000` |
| `gasUsed` | cumulative gas used by execution, with `0 <= gasUsed <= gasLimit` |
| `timestamp` | `parent.timestamp + d2`, checked for `uint64` overflow |
| `extraData` | empty byte string (`0x`) |
| `mixHash` / `prevRandao` | `bytes32(0)`; `prevRandao` is the payload-attribute alias; see §2.8 |
| `nonce` | `0x0000000000000000`, the post-Merge beacon nonce |
| `baseFeePerGas` | present; the EIP-1559 next-block value derived from the parent and the network's pinned parameters |
| `withdrawalsRoot` | canonical root of an empty withdrawals list; the body withdrawals value is present and empty |
| `blobGasUsed` | execution-derived total blob gas used by included type-3 transactions; it is not assumed to be zero |
| `excessBlobGas` | canonical next-block value derived from the parent under the active EIP-4844/EIP-7691 blob parameters |
| `parentBeaconBlockRoot` | `bytes32(0)` |
| `requestsHash` | absent before Prague; when Prague is active, the EIP-7685 hash of execution-produced requests |
| `blockAccessListHash` | absent (`None`); the v0 chain schedule does not activate the fork that requires it |
| `slotNumber` | absent (`None`); the v0 chain schedule does not activate Amsterdam |

The table describes the 23-field logical header model. Ethereum header RLP omits absent optional
suffix fields; it does not encode them as empty values. Under the selected Osaka development
schedule, `requestsHash` is present while `blockAccessListHash` and `slotNumber` are absent.
The canonical v0 header therefore contains **21 RLP list items**. A 23-item encoding with empty
placeholders is invalid.

The body ommers list MUST be empty. The body withdrawals list MUST be present and empty. The
transaction body is the exact ordered list selected under Appendix C and §4.1. An empty
transactions or receipts trie has root
`0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421`;
the empty withdrawals root has the same value. A zero-log block has an all-zero 256-byte bloom.

For `baseFeePerGas`, let the network's pinned elasticity be `E`, change denominator be `D`,
`targetGas = parent.gasLimit / E`, `p = parent.baseFeePerGas`, and `u = parent.gasUsed`. Since
London is active throughout v0:

```
if u == targetGas:
    baseFeePerGas = p
if u > targetGas:
    baseFeePerGas = p + max(floor(p * (u - targetGas) / targetGas / D), 1)
if u < targetGas:
    baseFeePerGas = p - floor(p * (targetGas - u) / targetGas / D)
```

All operations use the canonical EIP-1559 integer order and checked intermediate arithmetic. The
network profile MUST pin `E`, `D`, and the genesis base fee. `excessBlobGas` similarly uses the
canonical next-block function and the blob target/update fraction from the active, pinned chain
schedule; a client MUST NOT substitute local fee-market parameters.

When Prague is active, execution requests are grouped with their one-byte request type, each type
appears at most once, empty groups are omitted, and groups are ordered by type. Then:

```
requestsHash = sha256(sha256(request_0) || ... || sha256(request_m))
```

For no requests this is
`0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Before Prague the field MUST be absent, not the empty hash.

A deployment MUST pin one fork schedule and genesis. It MUST NOT activate a fork unless the
sequencer pool builder, manual Sync builder, Engine API validator, and deriver implement identical
body, execution, and header-field rules. The current development `genesis.json` activates London,
Shanghai, Cancun, Prague, and Osaka from genesis; that implementation fact does not by itself pin
a production network profile. Activating a header field that v0 requires absent, including
`blockAccessListHash` or `slotNumber`, requires a versioned specification change.

The zero beneficiary is the currently implemented fee-recipient rule on all three construction
paths. A non-zero operator or vault recipient is a future, versioned change; it is not a
deployment-local choice (§7.2).

## 2.7 Header validation

A validator or deriver MUST validate construction independently of the scheduler label:

1. Decode the body and header canonically. Reject malformed typed transactions, non-canonical RLP,
   an optional-field gap, a non-empty ommers list, a non-empty withdrawals list, or a
   fork-controlled field whose presence does not match §2.6 and the pinned activation schedule.
2. Select the expected canonical parent and require exact `parentHash`. Compute `parent.number + 1`
   and `parent.timestamp + d2` with checked `uint64` arithmetic and require exact `number` and
   `timestamp`. A proposed L1 time, local wall clock, production label, or batch length cannot
   override the timestamp; Future blocks have no wall-clock exception or additional wall-clock
   validity test.
3. Require the exact fixed `ommersHash`, beneficiary, `gasLimit`, `extraData`, `difficulty`,
   `mixHash`, `nonce`, `parentBeaconBlockRoot`, absent `blockAccessListHash`, and absent
   `slotNumber`. Require the exact empty-withdrawals root and body.
4. Recompute and require `baseFeePerGas` and `excessBlobGas` from the parent and pinned chain
   parameters. Validate every blob transaction, commitment/versioned hash, per-transaction blob
   count, and block blob-gas limit, then require `blobGasUsed` to equal the execution total.
5. Validate every transaction envelope, type, signature, chain ID, sender nonce, intrinsic gas,
   fee constraints, and block-gas fit. For a batch endpoint, reconstruct the exact outbound-load,
   paired user, inbound-delivery, and remaining-user sequence under Appendix C. For every earlier
   block, use exactly its DA user-transaction partition in order. Do not count reconstructed
   system transactions in `blockTxCounts`.
6. Starting from the selected parent's state, apply all active-fork pre-execution changes,
   execute the ordered transactions, and apply all post-execution changes. Recompute and require
   the exact `stateRoot`, `transactionsRoot`, `receiptsRoot`, `logsBloom`, `gasUsed`, and
   `requestsHash`; require receipt cumulative gas to end at `gasUsed` and require
   `gasUsed <= gasLimit`.
7. Canonically RLP-encode the present header prefix and omit absent optional suffix fields. The
   selected schedule has 21 RLP items: it includes `requestsHash` and omits
   `blockAccessListHash` and `slotNumber`. Compute `keccak256(header_rlp)` and require the
   advertised/sealed block hash. If a block already exists locally at that height, require the
   complete sealed header and body to equal this reconstruction; transaction-list equality or
   endpoint-state-root equality alone is insufficient.

Any mismatch invalidates that block and the entire settled batch range. The deriver MUST leave its
confirmed cursor and canonical pre-range head unchanged on rejection.

!!! danger "Current full-header validation gap — release blocker (informative)"

    The current Rust deriver's local-block fast path compares transaction bytes, and its
    batch-boundary check compares the first parent link. It does not compare every reconstructed
    intermediate header field before reusing those blocks. A matching final state root does not
    authenticate timestamps, fee/blob fields, receipts roots, or other intermediate headers.
    Full sealed-header/body comparison (or unconditional deterministic replay) is required before
    the fast path conforms to this section.

## 2.8 `prev_randao`: v0 and a future version

Rollup0 v0 MUST set `prev_randao` (`mixHash`) to `bytes32(0)` in **every** L2 block. It is not
derived from an L1 head or Sync-slot anchor. Contracts reading the `PREVRANDAO` opcode therefore
receive zero, and MUST NOT use it for randomness. Applications requiring adversary-resistant
randomness must use a VRF, commit-reveal, or another application-level construction.

An L1-derived `prev_randao` is design intent for a future protocol version only. That version must
pin the source L1 field and block, behavior across missed/reorged L1 slots, activation boundary,
and the data needed for byte-identical derivation. No implementation may begin using an L1 value
without that versioned rule and simultaneous activation in every construction/validation path.

## 2.9 Informative edge-case vectors

These examples are non-normative calculations of the preceding rules. Millisecond values are
shown as `(D1, D2, P, S)`.

| Vector | Inputs | Derived result |
|---|---|---|
| 12-second profile | `(12000, 2000, 4000, 1500)` | `K=6`, `F=2`, `L=3`, `O=6000`, deadline offset `10500` |
| Current Chiado profile | `(5000, 1000, 500, 1300)` | `K=5`, `F=1`, `L=3`, `O=3000`, deadline offset `3700` |
| Exact budget multiple | `(12000, 2000, 3500, 500)` | `P+S=4000`, so `F=1`, not 2; `L=4`, `O=8000` |
| Smallest valid slot | `(4000, 2000, 1500, 100)` | `K=2`, `F=0`, `L=1`, `O=2000` |

For the 12-second profile, `composition(0, 6) = Slot(3, 2)`,
`composition(5, 6) = Slot(0, 0)`, and `composition(6, 6) = Idle`.
For a far-behind `H=0`, `T=318`, and `C=300`, catch-up steps back three `K=6` intervals and
returns `Catchup(299)`, terminating at height 300.

For `g=1000`, `d1=12`, `d2=2`, and an observed L1 head `(n, hash, t=1013)`, the proposed Sync time
is 1025 and `T=floor((1025-1000)/2)=12`. If parent-derived production reaches block 12 at timestamp
1024, 1024 is the Sync timestamp and exact bundle pin; the scheduler does not force 1025.

If the next observed L1 head after a missed slot has `t=1036`, its proposal is 1048 and its target
height is 24. With current L2 head 12, the 12-block gap is greater than nominal `K=6`, so the
trigger returns `Catchup(11)`: eleven Live blocks and one structural Sync at height 24. It does not
invent an L1 head or a rich Sync block at height 18.

The executable mirror of these calculations, including invalid configurations, supersession,
late/equality boundaries, proof/inclusion anchor separation, range lengths, all 23 header field
names, and checked header timestamps, is
[`fixtures/timing-header-fixture.py`](fixtures/timing-header-fixture.py).

---

*Next: [§3 The Composer](03-composer.md).*
