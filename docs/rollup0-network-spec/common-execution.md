# Common Execution Rules

| | |
|---|---|
| **Ruleset ID** | `rollup0-common-execution@0.2-draft` |
| **EEZ framework** | `eez-framework@0.1-draft` |
| **EVM binding** | `eez-evm@0.2-draft` |
| **Status** | Draft normative ruleset |

This document is the complete common ruleset. Rollup0 and Gnosis Chain can select it without
importing either network's identity, candidate-admission policy, or governance. References to the
Rollup0 chapters are informative explanations and do not add text to this import.

## 1. Import Contract

An importing network profile MUST name the exact ruleset ID and MUST select the exact
`eez-framework` and `eez-evm` editions above. It MUST also fix, or mark as a release blocker, every
parameter in this table:

| Parameter | Required selection |
|---|---|
| `NETWORK` | execution-network identity, EIP-155 chain ID, EEZ rollup ID, native asset, and genesis commitment |
| `SETTLEMENT` | settlement-chain identity, EEZ deployment, network manager, proof contracts, activation, and finality |
| `D1`, `D2` | nominal settlement-chain interval and execution-network block interval, in milliseconds |
| `P`, `S_lead`, `C` | proof budget, submission lead time, and maximum blocks a producer can add at one catch-up trigger |
| `N_max` | maximum blocks accepted in one candidate range |
| `HEADER` | complete genesis execution state, fork schedule, and per-field block-header construction rules |
| `ADMIT(c, p)` | network-specific candidate authentication or eligibility predicate at settlement position `p` |
| `PROOF_POLICY(c, p)` | accepted proof systems, verification keys, membership, threshold, and verification predicate |
| `MANAGER(n)` | network-manager custom data for explicit settlement-chain proof-context block `n` |
| `SYSTEM_TX` | deterministic system address, authorization, transaction envelope, gas, nonce, and value rules |
| `LOWERING` | deterministic field-by-field construction linking each semantic effect, L1 entry, L2 sidecar object, explicit inbound arguments, and system transaction |
| `BUNDLE` | atomic settlement-chain inclusion construction and bundle limits |
| `CURSOR_GUARD` | enforceable comparison and atomic advancement of the exact settled execution-network cursor identity |
| `PREFIX_GUARD` | enforceable prevention of an applied effect after a non-applied anchor or effect |
| `ROUTING` | authentication of every settlement-routing input not bound by the selected EEZ proof input |
| `FEES` | execution fees, fee recipient, settlement-cost funding, and reimbursement rules |
| `GOVERNANCE` | governance, upgrades, signer or prover rotation, emergency action, and recovery |

A production client MUST NOT infer an unresolved parameter from Rollup0 source code, Gnosis source
code, a development deployment, or an implementation default. A release-blocker selection is not a
wildcard. It prevents production activation.

Within this document, "candidate" means one proposed execution-network range plus its exact parent
height, parent block hash, parent state root, EEZ batch, DA payload, proofs, authorization data, and
settlement-chain operation that can select that range.

`ADMIT(c, p)` adds network policy to the common validity rules. It MUST NOT waive or replace any
rule in this document, the selected EEZ editions, or `PROOF_POLICY(c, p)`. A permissionless
profile can select the constant predicate `true`. A permissioned profile can require an
authenticated candidate signature.

Settlement position `p` is the authenticated canonical position immediately before candidate
application. The importing profile MUST define its exact block, transaction, call, and pre-state
coordinates so that `ADMIT(c, p)` and `PROOF_POLICY(c, p)` cannot observe different positions.

## 2. Timing and Blocks

### 2.1 Configuration

All timing values are unsigned integers. A profile is invalid unless:

```text
D1 > 0
D2 > 0
P > 0
S_lead >= 0
D2 mod 1000 = 0
D1 mod D2 = 0
K = D1 / D2
K >= 2
P + S_lead < D1
P + S_lead <= (K - 1) * D2
C > 0
N_max > 0
```

Every conversion, addition, subtraction, multiplication, and height calculation MUST use checked
arithmetic. Only an operation explicitly identified as saturating may saturate.

Let `g` be the execution-network genesis timestamp in seconds:

```text
d1 = D1 / 1000
d2 = D2 / 1000
B_budget = P + S_lead
Q = ceil(B_budget / D2)
F_future = Q - 1
L_live = K - Q
T_offset = D1 - Q * D2
```

The constraints guarantee `L_live >= 1`, `F_future >= 0`, and:

```text
L_live Live positions || F_future Future positions || 1 Sync position
```

An importing profile selects the numeric values. This ruleset does not select the production or
development cadence of either network.

### 2.2 Trigger and Range Construction

For each authenticated canonical settlement-chain head
`E = (e_number, e_hash, e_timestamp)`, compute:

```text
trigger_at(E)         = e_timestamp + T_offset / 1000
proposed_sync_time(E) = e_timestamp + d1
target_height(E)      = floor(saturating_sub(proposed_sync_time(E), g) / d2)
```

A scheduler retains the latest target and at most one pending trigger. A newer canonical head
supersedes an unfired trigger. A client MUST use an observed delayed or off-grid settlement-chain
timestamp as observed and MUST NOT invent a missing settlement-chain block.

Every produced execution-network block has:

```text
number    = parent.number + 1
timestamp = parent.timestamp + d2
```

At a trigger, let `h` be the producer's authenticated local execution-network head and let
`T = target_height(E)`.

- If `h >= T`, produce no block.
- If `0 < T - h <= K`, produce the missing suffix through `T`. Height `T` is the Sync block. The
  preceding `F_future` slot positions are Future positions, and any earlier missing positions are
  Live positions.
- If `T - h > K`, enter catch-up. Choose the greatest height `T_catch` such that:

```text
h < T_catch <= T
T_catch - h <= C
(T - T_catch) mod K = 0
```

If no such height exists, produce no block at this trigger. Otherwise produce every height in
`(h, T_catch]`; the last is a Sync block and all preceding blocks in that chunk are Live blocks.
All comparisons, differences, and height calculations use checked arithmetic.

This residue rule steps backward from the observed target by whole `K` intervals. It remains
deterministic when genesis or an observed settlement timestamp puts `T` at a nonzero residue
modulo `K`. A catch-up Sync block MUST NOT add a new cross-network effect.

This state machine controls producer scheduling. `h` is not a candidate field and an independent
validator does not need to reproduce the producer's prior local-head observation. `C` limits only
the blocks that a producer adds at one catch-up trigger. Candidate endpoint and range validity use
the authenticated settlement header, settled cursor, and `N_max` under §3.2.

The schedule does not elect a producer. A candidate can settle only when the profile's
`ADMIT(c, p)` predicate and all common validity rules pass. The network's admission and competition
rules decide which candidates can settle.

### 2.3 Anchors and Headers

An implementation MUST keep these values distinct:

| Value | Function |
|---|---|
| scheduling head | supplies the observed settlement-chain number, hash, and timestamp |
| proof-context block | supplies explicit recent settlement-chain context through `MANAGER(n)` |
| construction parent | supplies the next block number, timestamp, pre-state, and parent fields |
| settled cursor | supplies the first unsettled height and initial state root |
| candidate Sync endpoint | supplies the end of the proposed range |
| inclusion block | supplies canonical settlement-chain transaction order, receipts, logs, and finality |

For any candidate built from settlement-chain head number `e_number`, `batch.blockNumber` MUST equal
`e_number`. `e_number` MUST be an explicit recent past block supported by `MANAGER`. Values `0` and
`uint64.max` are forbidden. A validator MUST authenticate the canonical block hash and the exact
opaque bytes returned by `MANAGER(e_number)`. The future inclusion block MUST NOT be used as proof
context. An anchor-only candidate MUST NOT use a timeless sentinel.

Every construction and replay path MUST use the same selected `HEADER`, parent, ordered body, and
execution environment. A validator or follower MUST:

1. canonically decode the complete header, body, and transaction envelopes;
2. authenticate the exact parent;
3. recompute the checked number and timestamp;
4. enforce every header-field and fork-presence rule in `HEADER`;
5. enforce ordinary EVM transaction and block validity;
6. reconstruct the exact system and user transaction order;
7. execute from the parent state;
8. recompute every state, transaction, receipt, withdrawal, request, and header commitment; and
9. compare the complete sealed header and body.

Transaction-list equality or endpoint-root equality alone is insufficient.

## 3. Data Availability and Candidate Range

### 3.1 Calldata Codec

The complete DA payload is:

```text
payload = 0x00 || rlp([blockTxCounts, transactions, l2Entries])
```

`batch.blobIndices` MUST be empty.

- `blockTxCounts` is a nonempty list of canonical unsigned integers, one transported-user count
  per proposed block.
- `transactions` is the block-major list of complete signed EIP-2718 user envelopes.
- `l2Entries` is the ordered list of complete ABI encodings of the selected
  `eez-evm@0.2-draft` L2 execution objects needed to rebuild system transactions.

A decoder MUST require the `0x00` tag, exactly one canonical three-element RLP list, no trailing
bytes, canonical-minimal counts at most `65535`, and a checked count sum equal to the transaction
list length. It MUST completely decode each transaction and ABI value. Missing, extra, reordered,
duplicated, trailing, or field-mismatched data invalidates the candidate.

The exact outer-codec vector and rejection cases are in
[Appendix B](B-da-codec.md). The L1 and L2 tuple layouts are distinct and come from
[EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md).

### 3.2 Cursor-Derived Range

Let `cursor_block` be the last execution-network block selected by preceding canonical
settlement-chain history, or the activated genesis block. Its exact identity is
`(cursor_block.number, cursor_block.hash, cursor_block.stateRoot)`. A candidate MUST commit to this
complete identity as its parent. In the arithmetic below, `cursor = cursor_block.number`.

Let `E` be the authenticated canonical settlement-chain header selected as the candidate's proof
context under §2.3, let `T = target_height(E)`, and let `b = len(blockTxCounts)`:

```text
first = cursor + 1
sync  = cursor + b
range = (cursor, sync]
```

All arithmetic MUST be checked. A candidate range is admissible only when:

```text
b = sync - cursor = len(blockTxCounts)
cursor < sync <= T
(T - sync) mod K = 0
1 <= b <= N_max
```

`sync = T` is the current target. `sync < T` is a catch-up endpoint stepped back from `T` by whole
`K` intervals. If `T <= cursor`, no positive candidate is admissible for `E`. `C` does not bound
`b`; it bounds only new producer work at one trigger. `N_max` is the consensus candidate-range
bound.

System transactions are not counted in `blockTxCounts`. The first state precondition MUST equal
`cursor_block.stateRoot`, replay MUST cover exactly `b` blocks, and the selected endpoint MUST
equal the replayed Sync root.

### 3.3 Sidecar Correspondence

This ruleset supports exactly one flat, non-static, successful top-level cross-network call per
interaction. A candidate MUST NOT contain a static, failed, nested, reentrant, or multi-call EEZ
effect. Top-level and nested lookup arrays MUST be empty.

This edition supports effects only between the importing execution network and its selected
settlement chain, whose EEZ rollup ID is `0`. An outbound effect has source rollup ID `rid` and
target rollup ID `0`. An inbound effect has source rollup ID `0` and target rollup ID `rid`.
Execution-network-to-execution-network effects are unsupported. This edition does not define the
combined candidate, proof, DA, admission, or partial-settlement rules that such an effect requires.

Each inbound effect MUST originate from one distinct settlement-chain trigger transaction. One
trigger transaction MUST NOT produce more than one inbound effect for this candidate.

Let `rid` be the importing network's EEZ rollup ID. Let `O[0..o-1]` be the ordered outbound
effects and `I[0..i-1]` the ordered inbound effects. The EEZ batch and DA sidecar MUST have:

```text
batch.entries = [anchor, O_l1[0], ..., O_l1[o-1], I_l1[0], ..., I_l1[i-1]]
l2Entries     = [        O_l2[0], ..., O_l2[o-1], I_l2[0], ..., I_l2[i-1]]

batch.transientExecutionEntryCount = 1 + o
batch.transientLookupCallCount      = 0
batch.l1ToL2lookupCalls             = []
len(l2Entries)                      = o + i
```

The anchor has no sidecar counterpart. An anchor-only candidate has `o = i = 0`,
`batch.entries = [anchor]`, and `l2Entries = []`.

The anchor and every effect entry MUST have `destinationRollupId = rid`. Every
`O_l1[k].proxyEntryHash` is zero and belongs to the leading transient prefix. Every
`I_l1[k].proxyEntryHash` is the nonzero action hash selected by `eez-evm@0.2-draft` and belongs to
the deferred suffix.

For each effect, a validator MUST independently derive the L1 batch entry and the distinct L2
sidecar object from the same sequential execution. It MUST compare every call field, network and
address, value, calldata, table, call count, return value, success value, cursor, rolling hash,
order, and multiplicity selected by `eez-evm@0.2-draft`. It MUST NOT decode one tuple family as the
other, infer a missing sidecar object from the L1 entry, partition or reorder the mixed list, or
discard duplicates.

`LOWERING` MUST define a total, deterministic construction for the supported interaction shape. For
each authenticated semantic effect, it MUST fix every field of the L1 entry and L2 sidecar object,
the six-field action-hash direction, all zero or empty fields, call and lookup arrays, counts,
return and success data, rolling hashes, and, for an inbound effect, the explicit
`executeIncomingCrossChainCall` arguments and transaction value. Naming an implementation function
or requiring two producer-supplied hashes to match is not a construction rule.

Every L1 effect entry MUST contain exactly one state delta for `rid` at its effect position. Every
sidecar object MUST correspond to exactly that effect and carries no L1 `StateDelta`. Equality of
hashes supplied by a producer is insufficient.

Two consecutive deltas MAY have equal root values when an effect causes no importing-network state
change. Equal root values do not merge effects: their effect indices, ordered occurrences, and
multiplicity remain distinct. `PREFIX_GUARD` MUST remain sound when any two chain roots are equal;
root inequality or set membership is not an enforcement mechanism.

For a rich candidate, the final `blockTxCounts` item MUST equal `o`. Its final-block items in
`transactions` MUST be exactly the consuming user transaction for each outbound effect, in
outbound-effect order. An inbound-only rich candidate has a zero final count. An anchor-only
candidate's final count MAY be nonzero and covers its complete ordinary Sync user body.

## 4. Sync Block and Exact Effect Roots

Let:

- `A = header(cursor).stateRoot`, the state root selected before the candidate;
- `S_pre` be the state after executing every nonterminal block in the candidate range; and
- `root(T)` be the state root obtained by building the terminal Sync block on `S_pre` with the
  exact `HEADER` environment, applying every mandatory pre-execution state change, and executing
  ordered transaction body `T`.

The zero-effect Sync prefix is:

```text
Z = root([])
```

`Z` includes the terminal Sync block's mandatory pre-execution changes. It is not the pre-Sync
parent root.

### 4.1 Rich Candidate

A rich candidate has `m = o + i > 0` effects. Its complete ordered effect groups are:

```text
load(k) =
    system transaction calling loadExecutionTable([O_l2[k]], [])

deliver(j) =
    system transaction calling executeIncomingCrossChainCall(
        exact action fields for I[j],
        [I_l2[j]],
        []
    )

G[k]   = [load(k), outbound-user[k]]  for 0 <= k < o
G[o+j] = [deliver(j)]                 for 0 <= j < i
```

`deliver(j)` MUST use the exact inbound transaction value selected by effect `I[j]`.

The full rich Sync body and prefix roots are:

```text
body = G[0] || G[1] || ... || G[m-1]
R[k] = root(G[0] || G[1] || ... || G[k])
```

The body MUST contain exactly those groups. It MUST NOT contain an unrelated user transaction
before, between, or after them. Every claimed cross-network effect in the candidate range MUST
occur in one of these terminal groups. A load and its consuming outbound user transaction are one
indivisible group for construction and prefix repair.

Each `root(...)` calculation MUST start from the same pre-Sync parent `S_pre` and use the same
terminal environment. A client MUST NOT build one prefix as a child block of another prefix.

The importing-network state-delta chain MUST be:

```text
anchor          = (rid, A,      Z,    0)
effect[0]       = (rid, Z,      R[0], etherDelta[0])
effect[k], k>0  = (rid, R[k-1], R[k], etherDelta[k])
```

Each `etherDelta[k]` MUST describe only effect `k`'s exact cross-network value movement. The final
`R[m-1]` MUST equal the full candidate Sync root. A client MUST reject a collapsed final-root
construction, an anchor that ends at the pre-Sync parent, or an effect root that includes a later
effect.

### 4.2 Anchor-Only Candidate

An anchor-only candidate has no cross-network effect, effect entry, sidecar object, or
cross-network system transaction. Let `U` be its complete ordered Sync body of ordinary user
transactions that produce no claimed EEZ effect, and let:

```text
F = root(U)
anchor-only = (rid, A, F, 0)
```

Its sole importing-network delta MUST be `anchor-only`. When `U` is empty, `F = Z`. The transition
applies in full or does not apply; an anchor-only body has no separately settleable effect prefix.

### 4.3 Anchor Entry and System Transactions

The first EEZ batch entry is the anchor. It MUST have exactly one state delta, the rich `A -> Z`
anchor or the anchor-only `A -> F` delta. Its other fields are:

```text
proxyEntryHash       = bytes32(0)
destinationRollupId  = rid
returnData           = 0x
l2ToL1Calls          = []
expectedL1ToL2Calls  = []
expectedLookups      = []
callCount            = 0
rollingHash          = bytes32(0)
```

Every system transaction uses the `loadExecutionTable` or
`executeIncomingCrossChainCall` operation defined by `eez-evm@0.2-draft`. The selected
`SYSTEM_TX` parameter fixes its sender, exact envelope, nonce, gas, fees, value source, and
authorization. System transactions use consecutive authority nonces in rich-body order.

An implementation MUST reject a system envelope it cannot reconstruct byte for byte. It MUST
enforce the reserved sender, forbid a reserved-sender transaction in a nonterminal block, and
forbid any other reserved-sender transaction in the Sync block. A missing authorization input is
a construction failure, not permission to omit a required system transaction.

## 5. Settlement-Chain Operation

### 5.1 Candidate Validation

Define:

```text
CommonValid(c, p) =
    all rules in this document
    AND all selected EEZ rules

Admissible(c, p) = ADMIT(c, p) AND CommonValid(c, p)

SettlementReady(c, p) =
    Admissible(c, p)
    AND PROOF_POLICY(c, p)
```

A validator or prover MUST establish `CommonValid(c, p)` before it attests to or proves the
candidate. Before submission or derivation, a client MUST establish `SettlementReady(c, p)`.
Authorization and proof acceptance do not replace full validity.

The selected proof and authentication mechanisms MUST bind to the same candidate bytes, profile,
activation, parent, DA payload, complete effective EEZ batch, proof context, settlement
deployments, and routing fields.

The candidate's EEZ batch MUST use the selected binding, empty `blobIndices`, the explicit proof
context in §2.3, the exact state-delta chain in §4, and `PROOF_POLICY(c, p)`. The selected
`ROUTING` mechanism MUST authenticate every effective batch or submission field that can change
settlement behavior but is absent from the selected EEZ proof public input.

The selected `CURSOR_GUARD` mechanism MUST compare the candidate's exact named parent with the
current settled cursor at position `p` and atomically advance that cursor to the selected endpoint
identity. It MUST reject a stale sibling even when its parent state root equals the current state
root. The identity MUST include the execution-network height, block hash, and state root, or an
unambiguous collision-resistant commitment to them. The `eez-evm@0.2-draft` root check alone does
not satisfy this rule. The mechanism MUST remain sound for stale siblings and repeated root values.
For a rich candidate, it MUST authenticate the deterministic endpoint identity for `Z` and every
`R[k]`; for an anchor-only candidate, it MUST authenticate `F`. A profile without such a mechanism
is blocked from production activation.

The selected `PREFIX_GUARD` mechanism MUST prevent the settlement operation from completing when
the anchor does not apply but an effect applies, or when any effect applies after an earlier
effect did not apply. Follower rejection after canonical inclusion is not enforcement. The
mechanism MUST remain sound for repeated root values, caught immediate-entry failure,
deferred-entry failure, and same-block queue replacement. A profile that cannot supply such a
mechanism for the selected EVM binding is blocked from production activation.

### 5.2 Atomic Operation

For the `i` deferred inbound effects defined in §3.3, the candidate identifies one exact ordered
settlement-chain operation:

```text
[postAndVerifyBatch, trigger[0], ..., trigger[i-1]]
```

`trigger[j]` MUST be the one exact transaction selected by `BUNDLE` to attempt consumption of
`I_l1[j]`. The trigger transactions MUST be distinct. There is one trigger per inbound effect, in
inbound-effect order, and no other trigger. The post and triggers MUST occupy consecutive
settlement-chain transaction indices with no interleaved transaction or call that can replace or
consume the selected queue. The selected `BUNDLE` mechanism MUST guarantee exact ordering and
all-or-none transaction inclusion in one settlement-chain block. It MUST NOT omit a trigger or
treat a transaction that failed envelope, signature, chain-domain, nonce, fee, balance,
intrinsic-gas, block-gas, or sequential-execution validity as included.

A validly included trigger transaction whose corresponding EEZ consumption call reverts records
that effect as non-applied. It is permitted only as part of the exact applied-prefix outcome in
§5.3. After the exact trigger transaction is authenticated, its status-`0` receipt is sufficient
evidence that its effect did not apply; internal revert data or non-surviving logs are not
consensus evidence. A revert cannot excuse a missing, reordered, or unrelated trigger.

Candidate-signing authority and settlement-chain relay authority are different profile fields. An
import of this ruleset grants neither.

### 5.3 Canonical Evidence and Competition

A follower MUST authenticate the canonical settlement-chain header, exact transaction hash and
index, receipt status, activated contract address, and ordered log occurrences. It MUST preserve
receipt boundaries, transaction indices, log indices, event kind, effect index, queue cursor, and
duplicate multiplicity. `BatchPosted` or a matching root alone is not settlement evidence.

For each candidate post in canonical settlement-chain execution order:

1. Reject it if `SettlementReady(c, p)` fails.
2. Treat it as stale unless its named parent height, block hash, and state root equal the exact
   current settled cursor identity at `p`.
3. Authenticate the exact post transaction, consecutive trigger transactions, receipts, and
   ordered event occurrences.
4. Classify the anchor and every effect from its own receipt-bound evidence.
5. For a rich candidate, require either no applied anchor and no applied effect, or the applied
   anchor followed by exactly the first `q` effects for one `0 <= q <= m`.
6. If the rich anchor did not apply, leave the execution-network range and cursor unchanged.
7. If the rich anchor applied, select endpoint `Z` for `q = 0` or `R[q-1]` for `q > 0`.
8. For an anchor-only candidate, require its sole `A -> F` delta either to apply in full or not to
   apply. Select `F` only when it applied.
9. Require the final applied state occurrence to equal the independently replayed selected
   endpoint.
10. Use the applied endpoint's height, block hash, and state root as the cursor identity for the
    next candidate.

For an immediate entry, the exact ordered `L2ExecutionPerformed` occurrence classifies an applied
delta and the exact ordered `ImmediateEntrySkipped` occurrence classifies its non-application. For
a deferred entry, the exact successful trigger receipt and its ordered `ExecutionConsumed` and
`L2ExecutionPerformed` occurrences classify application. After the exact trigger is authenticated,
a status-`0` receipt classifies non-application. A client MUST NOT require unavailable internal
revert data or logs removed by transaction rollback.

An applied effect after a non-applied effect, an effect applied without the anchor, a missing
occurrence, ambiguous effect attribution, or evidence from another transaction invalidates the
candidate. Repeated root values are valid when exact effect indices and receipt occurrences
preserve their order and multiplicity. A client MUST NOT deduplicate effects by root value. A
non-applying candidate does not consume a range.

The first `SettlementReady` candidate whose exact named parent is still the current cursor and
whose anchor applies wins. A producer identity, local arrival time, signature time, proof time,
fee, range length, or candidate hash MUST NOT replace canonical settlement-chain execution order.

## 6. Derivation

### 6.1 Exact Prefix Repair

For a rich candidate whose anchor applied with `q` applied effects:

- `q = 0` selects `Z`;
- `0 < q < m` selects `R[q-1]`; and
- `q = m` selects the proposed Sync root.

The selected rich body is:

```text
B(q) = G[0] || G[1] || ... || G[q-1]
B(0) = []
```

The follower MUST omit every later group. It MUST NOT append the user transaction from an omitted
outbound group or any unrelated user transaction. The repaired body's user count is the number of
outbound groups among the first `q` effects, not necessarily the full candidate's final
`blockTxCounts` value.

For `q < m`, the follower MUST derive a new terminal header from `B(q)`. It MUST recompute the
transaction root, receipt root, logs bloom, gas fields, state root, block hash, and every other
`HEADER` commitment. It MUST NOT reuse the proposed full-body Sync header.

For an applied anchor-only candidate, the follower uses the complete transported body `U` and
endpoint `F`. It MUST NOT truncate `U`; anchor-only settlement has no effect-prefix repair.

Dropped outbound users MAY return to a local transaction pool only after canonical
replacement-receipt checks.

### 6.2 Replay and Commit

A follower:

1. strictly decodes the payload and partitions transported users by `blockTxCounts`;
2. reconstructs and executes every nonterminal block from the authenticated cursor;
3. obtains `S_pre`, constructs the exact terminal environment, and independently computes `Z`;
4. rebuilds every full-candidate effect prefix from the same `S_pre` and validates each `R[k]`;
5. authenticates settlement evidence and selects no range, rich effect count `q`, or the
   anchor-only body;
6. rebuilds the selected terminal body under §6.1;
7. executes it from the same `S_pre` with the same terminal environment;
8. recomputes every receipt and complete sealed header;
9. requires the result to equal `Z`, `R[q-1]`, or `F`, as applicable; and
10. commits the complete range and advances the cursor height, block hash, and state root to the
    selected `sync` block atomically.

If the anchor did not apply, the follower MUST discard tentative execution and leave the cursor
unchanged. Nonterminal blocks remain the same for every applied rich prefix. Only the terminal body
and terminal header change.

A local-block fast path is valid only when its ancestry, complete ordered body, execution result,
receipts, and every header field equal the selected reconstruction.

A malformed codec item, unsupported transaction, invalid EVM transition, unauthorized or misplaced
system transaction, sidecar mismatch, `A`, `Z`, `R[k]`, or `F` mismatch, effect-chain mismatch, or
ambiguous settlement occurrence invalidates the range. The follower MUST roll back all tentative
work and leave its cursor unchanged. Persistent invalid canonical history halts derivation.

### 6.3 Reorganizations and Labels

On a settlement-chain reorganization, a follower removes orphaned evidence, returns to the last
endpoint supported by the surviving branch, lowers safe and finalized labels, and derives the
replacement branch in canonical order. A recovery beyond the activated automatic history or
displacement of finalized settlement-chain history requires the selected `GOVERNANCE` procedure;
a client MUST halt instead of guessing.

- **Unsafe** is valid local execution not selected by canonical settlement.
- **Safe** is a block reached by complete deterministic replay of canonical settlement evidence.
- **Finalized** is a safe block whose selecting settlement-chain history is finalized under the
  profile.

`finalized` MUST NOT exceed `safe`. Publication, a candidate signature, a proof, `BatchPosted`, or a
matching root without exact effect attribution cannot advance either label.

## 7. Fees and Limits

User and system transactions obey ordinary EVM admission, execution, refund, receipt, block-gas,
and fee rules selected by `HEADER` and `FEES`. System transactions consume the block gas budget and
obey the selected base-fee rule. The profile MUST fix all fee recipients, system funding, value
backing, gas limits, capacity limits, and settlement-cost treatment.

This common ruleset defines no L1-data surcharge, fee oracle, fee vault, submitter reimbursement,
or guaranteed profitability. A network that adds one MUST specify it in its profile or select a
new common-rules edition when it changes a rule above.

## 8. Excluded Network Choices

This ruleset does not select:

- open or permissioned candidate admission;
- candidate signature or authentication rules;
- composer, validator, prover, signer, relay, or builder membership;
- execution or settlement chain identity, native asset, genesis, or deployments;
- timing values, proof budget, submission slack, or catch-up bound;
- maximum accepted candidate range;
- header constants, fork schedule, proof context, or manager encoding;
- proof-system membership, verification keys, threshold, or routing mitigation;
- system address, authorization, transaction envelope, or value source;
- bundle capacity or atomic-inclusion mechanism;
- exact settled-cursor identity and stale-sibling enforcement;
- applied-prefix enforcement for skipped, reverting, or equal-root effects;
- fee recipient, funding, reimbursement, or settlement-cost policy;
- finality threshold, governance, upgrade authority, or emergency recovery; or
- any development fixture or implementation default as a production value.

An importing specification MUST cite:

```text
rollup0-common-execution@0.2-draft
```

It MUST publish a SHA-256 digest of the exact UTF-8 document bytes before production activation.
A change to any normative rule in this document requires a new ruleset edition. A local override
is not part of this edition unless this document identifies the affected item as a profile
parameter.
