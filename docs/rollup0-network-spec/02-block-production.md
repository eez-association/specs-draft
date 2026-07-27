# 2. Timing, Production, and Header Rules

Sections 2.1-2.6 are normative. Production and development values are distinct.

## 2.1 Timing and Block Grid

Each activation selects unsigned millisecond values:

| Symbol | Meaning |
|---|---|
| `D1` | nominal settlement-network block interval |
| `D2` | Rollup0 block interval |
| `P` | candidate construction and proof budget |
| `S` | required submission lead time |
| `C` | maximum blocks a producer can add at one catch-up trigger |
| `N_max` | maximum blocks accepted in one candidate range |

The node MUST reject a configuration unless:

```text
D1 > 0
D2 > 0
P  > 0
S  >= 0
D2 mod 1000 = 0
D1 mod D2 = 0
K = D1 / D2
K >= 2
P + S < D1
P + S <= (K - 1) * D2
C > 0
N_max > 0
```

Every conversion, addition, subtraction, multiplication, and height calculation MUST be checked in
its declared integer width. Overflow is a configuration or observation error. Only an operation
explicitly identified as saturating may saturate.

Production fixes:

```text
D1 = 12,000 ms
D2 =  2,000 ms
K  = 6
```

The production values of `P`, `S`, `C`, and `N_max` are unresolved release blockers. A node MUST
NOT infer them from the current implementation.

The Chiado development environment uses:

```text
D1 = 5,000 ms
D2 = 1,000 ms
P  =   500 ms
S  = 1,300 ms
K  = 5
C  = 300 blocks
```

The Chiado value of `N_max` is unresolved. The development profile is not complete until an
activation record selects it.

The common execution rules state the same timing algorithm with profile parameters. They do not
import either numeric cadence from this chapter.

## 2.2 Production State Machine

Let the Rollup0 genesis timestamp be `g`, in seconds. Let:

```text
d1 = D1 / 1000
d2 = D2 / 1000
B  = P + S
Q  = ceil(B / D2)
F  = Q - 1
L  = K - Q
O  = D1 - Q * D2
```

`L` is the number of live positions, `F` is the number of prebuilt future positions, and the last
position is the Sync block:

```text
L Live blocks || F Future blocks || 1 Sync block
```

The configuration constraints guarantee `L >= 1`, `F >= 0`, and `L + F + 1 = K`.

For each observed canonical settlement head `A = (n, hash, t)`, compute with checked arithmetic:

```text
trigger_at(A)         = t + O / 1000
proposed_sync_time(A) = t + d1
target_height(A)      = floor(saturating_sub(proposed_sync_time(A), g) / d2)
```

The scheduler retains the latest target height and at most one pending trigger. A newer canonical
head supersedes an un-fired trigger. The scheduler MUST NOT invent a head for a missed settlement
slot. An off-grid or delayed settlement timestamp is used as observed.

Every produced Rollup0 block has:

```text
number    = parent.number + 1
timestamp = parent.timestamp + d2
```

Both additions are checked. Wall clock, a scheduling label, or a proposed settlement timestamp
cannot change the parent-derived timestamp.

At a trigger:

1. If the local head is already at or above the target, produce no block.
2. Produce the missing Live suffix up to the prebuild region.
3. Produce `F` Future blocks when those heights are still missing.
4. Produce one terminal Sync block.
5. If the gap is too large, produce a positive catch-up chunk ending at a Sync residue and
   containing at most `C` blocks.

A catch-up Sync block MUST NOT carry new cross-network effects. It can settle a positive historical
range. `C` limits the producer's new work at this trigger. It does not make a longer independently
replayed candidate invalid. The nominal width `K` is not a batch-length validity rule.

### Candidate Independence

Each composer runs this state machine against its own authenticated view. Two composers can produce
different valid siblings. The schedule does not elect a leader and does not make either sibling
invalid. Candidate competition is resolved only by §3.5 and canonical Ethereum order.

The producer's local head is not a candidate field. An independent validator checks the candidate
endpoint against the authenticated proof-context Ethereum header, settled cursor, cadence, and
`N_max` under §4.2. It does not reproduce the producer's earlier local-head observation.

### Lateness

A composer MAY build a rich candidate only when it can still meet the activated proof and
submission budgets. Its lateness test MUST use the exact observed anchor and activated `P` and `S`.
A late trigger produces or retains ordinary L2 cadence but MUST NOT claim an exact-target
cross-network bundle that can no longer meet the target.

### Operational Bounds

A deployment MAY configure a maximum speculative unsafe depth. Zero MAY disable that bound.
Speculative depth controls local production; it is not block validity and MUST NOT change safe
derivation. The current Chiado compose file sets it to zero. The old implementation default of 64
is not a production profile value.

## 2.3 Anchors

The following anchors have different roles and MUST NOT be substituted:

| Anchor | Function |
|---|---|
| settlement scheduling head | supplies observed number, hash, and timestamp for the trigger |
| proof-context block | supplies the recent Ethereum context committed through Rollup0 manager `getCustomData` |
| construction parent | fixes the next L2 number, timestamp, pre-state, and parent-derived header fields |
| settled cursor | fixes the first unposted L2 block and initial state root |
| candidate Sync endpoint | fixes the end of the DA range and final Rollup0 state |
| Ethereum inclusion block | supplies canonical transaction order, receipts, events, and finality |

For a rich candidate built from observed Ethereum head `A = (n, hash, t)`:

- `batch.blockNumber` MUST equal `n`;
- `n` MUST be a recent explicit past block supported by the activated Rollup0 manager;
- the validator MUST authenticate `hash` and the exact opaque custom data returned for `n`;
- `blockNumber = 0` and `blockNumber = uint64.max` are forbidden; and
- the future inclusion block MUST NOT be used as proof context.

The activated profile MUST define the exact Rollup0 `getCustomData(n)` encoding. That encoding is
currently unresolved for production and is a release blocker. The EEZ binding defines how the
opaque bytes enter the proof public input.

An anchor-only catch-up candidate still uses an explicit authenticated proof context. It does not
use a timeless sentinel.

## 2.4 Header Construction and Validation

All construction paths use the same chain specification, parent, ordered transaction list, and
execution environment.

The fixed Rollup0 header choices are:

| Field | Rule |
|---|---|
| `parentHash` | exact selected parent hash |
| `ommersHash` | Keccak-256 of RLP `[]` |
| `beneficiary` | zero address |
| `stateRoot` | exact post-execution state root |
| `transactionsRoot` | exact indexed transaction-trie root |
| `receiptsRoot` | exact indexed receipt-trie root |
| `logsBloom` | bloom of the exact receipts |
| `difficulty` | zero |
| `number` | checked `parent.number + 1` |
| `gasLimit` | `30,000,000` |
| `gasUsed` | exact cumulative execution gas, at most `gasLimit` |
| `timestamp` | checked `parent.timestamp + D2 / 1000` |
| `extraData` | empty |
| `mixHash` / `prevRandao` | zero |
| `nonce` | eight zero bytes |
| `baseFeePerGas` | canonical EIP-1559 value derived from the parent |
| `withdrawalsRoot` | active-fork empty-withdrawals root |
| `blobGasUsed` | execution-derived value |
| `excessBlobGas` | canonical parent-derived value |
| `parentBeaconBlockRoot` | zero when the selected fork requires the field |
| `requestsHash` | exact execution-request hash when the selected fork requires it |
| later optional fields | present only when the activated fork schedule requires them |

The production fork schedule and genesis base fee are unresolved. An activation MUST pin them.
The Chiado development genesis activates the reviewed implementation fork schedule in Appendix D.

The body has no ommers. When withdrawals are active, the withdrawals list is present and empty.
Transactions are the exact ordered sequence selected by §4 and Appendix C.

A validator or deriver MUST:

1. canonically decode the complete header, body, and transaction envelopes;
2. require the exact canonical parent;
3. recompute checked number and timestamp;
4. require every fixed field above;
5. validate active-fork field presence and all Ethereum execution rules;
6. validate signatures, chain IDs, nonces, intrinsic gas, balances, fee constraints, and block-gas
   fit;
7. reconstruct the exact system and user transaction order;
8. execute from the parent state;
9. recompute state, transaction, receipt, withdrawal, request, and header hashes; and
10. require the complete sealed header and body to equal any locally reusable block.

Transaction-list equality or endpoint-state equality alone is insufficient. A mismatch invalidates
the candidate range and leaves the settled cursor unchanged.

`PREVRANDAO` returns zero on Rollup0 0.2. Applications MUST NOT treat it as randomness.

## 2.5 Candidate Outcome State Machine

A local composer MAY track one or more submissions. For each candidate:

```text
Built -> Proving -> Submitted -> Included
                            \-> Expired
Included -> Applicable -> Derived
         \-> Stale
         \-> InvalidEvidence
```

- **Applicable:** the candidate's exact parent height, block hash, and state root matched the
  current settled cursor, and canonical evidence shows that its exact effect chain advanced.
- **Stale:** canonical Ethereum ordered another transition first, so this candidate did not
  advance.
- **Expired:** the exact target can no longer include the intended bundle.
- **InvalidEvidence:** inclusion exists but its receipts, order, events, or endpoint do not satisfy
  §4.5.

A stale or expired local candidate can cause local unsafe rollback and transaction requeue. It
cannot roll back a different canonical candidate. Recovery MUST re-read the settled cursor while
holding the implementation's reconciliation lock.

## 2.6 Reorganizations

On an Ethereum reorganization, a node:

1. finds the authenticated common ancestor within its automatic history;
2. removes orphaned candidate records and settlement evidence;
3. retreats safe and finalized Rollup0 heads to surviving canonical endpoints;
4. retreats the local canonical L2 head to that cursor;
5. requeues eligible transactions only when they have no canonical replacement receipt; and
6. derives the replacement Ethereum branch in order.

A reorganization deeper than the configured automatic history or displacement of finalized
Ethereum history requires an authenticated recovery procedure. A node MUST halt instead of
guessing.

## 2.7 Worked Cadences

| Environment | Values | Nominal result |
|---|---|---|
| production | `D1=12000`, `D2=2000` | six Rollup0 positions per Ethereum interval |
| Chiado development | `D1=5000`, `D2=1000`, `P=500`, `S=1300` | 3 Live, 1 Future, 1 Sync |

The production Live/Future split cannot be computed until production `P` and `S` are activated.

---

*Next: [§3 Composer and Candidate Competition](03-composer.md).*
