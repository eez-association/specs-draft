# 7. Data Availability, Batches, and Ethereum Bundles

## 7.1 Rollup0 DA Payload

Rollup0 publishes its anchored chain data in Ethereum blobs. The EEZ batch identifies the blobs
that belong to the candidate.

The published data must let an independent follower recover:

- the exact settled parent named by the candidate;
- every Rollup0 block and block boundary in the anchored range;
- every signed pure-L2 transaction in block order, including those at the start of the Sync block;
- every authenticated input needed to derive the exact serialized bytes of each protocol-derived
  transaction in block order;
- every non-derived header input;
- the EEZ objects and origin fields for every synchronous action;
- the ordered EEZ action brackets from which each manifest index, EEZ cross-chain call hash, and
  expected outcome are derived; and
- the format version.

Execution-derived fields do not need separate encodings. A follower derives each transaction root,
receipt, receipt root, logs bloom, gas-used value, state root, header, and block hash from the
published inputs. Any redundant claimed value must equal the replayed value.

The action manifest identifies actions by ordered call, not by exact Ethereum transaction. It is
not a separately encoded array: it is derived from the top-level EEZ action brackets in decoded
message order. Bracket `i` has zero-based `manifestIndex = i`; its `Call` fields determine the EEZ
cross-chain call hash, and its `ReturnSuccess` or `ReturnFail` determines the expected outcome. The
corresponding authenticated EEZ execution entry or failed lookup must match that bracket. The
candidate domain, manifest index, and call hash determine a successful action's Rollup0
`sourceHash` as defined in Appendix F.

Every bracket's `InitiateCrossChainTransaction.tx_data` is empty. It does not carry a proposed
Ethereum transaction or transaction hash. Appendix G explains why candidate protocol V1 identifies
the ordered call independently of its replaceable delivery transaction.

A composer separately supplies proposed signed Ethereum trigger transactions to validators,
relayers, and builders. Each proposed trigger must execute exactly one manifest action, but its
transaction hash is delivery data rather than Rollup0 action identity. A different Ethereum
transaction that produces the candidate's next expected call is intentionally the same Rollup0
action. The published candidate need not contain an omitted proposed trigger's signed bytes. A
follower obtains the exact bytes of every trigger that actually executes from canonical Ethereum
and reconstructs only the selected Rollup0 endpoint.

An EIP-4844 blob transaction, transaction type `0x03`, MUST NOT be a trigger. More generally, a
trigger must not require a blob sidecar. `submitCandidate` is the candidate's only required blob
transaction.

!!! danger "PRODUCTION BLOCKER: byte-exact blob format"
    Appendix D defines the linear V0 codec and initial codec vectors. The complete action-manifest,
    transaction-bearing, terminal-variant, and derivation vector suite remains unfinished.
    Appendix G records the design rationale. Appendix D also defines the candidate domain
    independently: the Rollup0 manager supplies the execution environment and settlement context,
    while the authenticated blob envelope supplies its own format version.

## 7.2 Range Correspondence

Let `fromBlock` be the settled parent derived from the candidate's first block header and the
current settled cursor. It is not a separate blob field. Let `toNumber` be the terminal block
number.
The payload covers exactly:

```text
(fromBlock.number, toNumber]
```

The first block header binds `fromBlock`. Let `n` be the number of actions in the manifest and `s`
the number of successful actions in the complete candidate. Because an optional failure must be
terminal, `s` is either `n` or `n - 1`. The published data defines terminal variants `B[0]` through
`B[s]`. Every variant has block number `toNumber`, the same timestamp, the same pure-L2 prefix, and
exactly its first `k` successful protocol transactions. Candidate validation checks every variant
by replaying it from the candidate's same settled parent, which must be the current
Ethereum-confirmed Rollup0 safe head when the candidate settles. A failed action must be the final
action in the manifest and does not create another block variant.

`H[k]` is the block hash of `B[k]`. It is the Rollup0 commitment used in EEZ state deltas.
`R[k]` is the EVM state root in that block's header, and `R[0]` is also called `R0`.

During canonical Ethereum execution, `k` is the number of successful Rollup0 actions consumed in
order. If a later trigger receives and catches the candidate's terminal Rollup0 failure, that fact
changes canonical Ethereum history but creates no Rollup0 transaction, commitment transition, or
additional `B`, `H`, or `R` value. A Rollup0 follower does not need to establish whether that
failure was reached. The Rollup0 endpoint is always `B[k]`.

A live candidate has a terminal timestamp equal to its intended Ethereum settlement timestamp. A
catch-up candidate has an older terminal timestamp, only the `B[0]` variant, and an empty action
manifest. It contains no inbound protocol transaction or failed lookup. A terminal timestamp later
than the intended Ethereum settlement timestamp is invalid. The relationship between the two
timestamps determines the anchor form; the blob does not need a separate mode flag.

The following must agree:

- the number of encoded block boundaries equals `toNumber - fromBlock.number`;
- the first encoded block is `fromBlock.number + 1`;
- the last encoded block has number `toNumber`;
- the terminal timestamp follows the live or catch-up rule above;
- every user transaction appears once in its selected block;
- every required L2 entry corresponds to one exact successful EEZ action;
- every failed action corresponds to one exact failed EEZ lookup and no L2 transaction; and
- replay from `fromBlock` produces every `B[k]`, `H[k]`, and `R[k]` for `0 <= k <= s`.

!!! success "DECISION: fill catch-up publication capacity"
    A catch-up range MAY contain any positive number of complete six-position intervals, up to the
    largest historical prefix that fits the blobs and all other limits selected for that candidate.
    It is not capped at one nominal Ethereum interval.

    A catch-up composer SHOULD use the largest blob allotment it can reasonably get included and
    SHOULD fill that allotment with the longest valid historical prefix available from the settled
    parent. This maximizes recovery speed, but maximality is not a validity rule: a smaller valid
    range remains valid and competing composers can make different fee and inclusion choices.

    Blob hashes and contents are fixed before candidate signing, so "available" means the blob
    allotment selected for that candidate under Ethereum's transaction and block limits. It does
    not mean unused capacity discovered after the candidate has been signed.

    A candidate must fit its complete authenticated range into its selected blobs. Rollup0 adds no
    lower candidate-wide block-count, transaction-count, or execution-gas cap. If a composer builds
    an unsafe interval whose encoded range cannot fit a valid settlement candidate, that unsafe
    branch cannot become safe. Another composer can rebuild a smaller sibling from the settled
    cursor, omitting or reordering pure-L2 transactions as ordinary candidate competition permits.
    This can replace unsafe history but cannot deadlock canonical Rollup0 history.

    Composers SHOULD therefore keep their unsafe branches anchorable and publish before accumulated
    data exceeds the capacity they can reasonably obtain. Reducing an existing lag requires the
    effective publication rate to exceed the six new Rollup0 positions scheduled per Ethereum
    slot. If capacity or inclusion is lower, the lag can remain constant or grow even while every
    catch-up anchor advances the cursor.

    Unsafe transaction backlog is local to each open composer, not a canonical chain obligation. A
    composer MAY omit unanchored transactions and SHOULD reduce or stop new pure-L2 intake when that
    helps its branch catch up. Synchronous actions cannot settle through a catch-up anchor.

!!! success "DECISION: timestamps identify scheduled chain positions"
    A catch-up range proves a valid chain whose timestamps occupy the scheduled Rollup0 positions.
    It does not prove that those blocks were produced or gossiped at those historical times. An
    open composer can construct a competing historical range later and include transactions that
    it received after the scheduled timestamps. If Ethereum selects that candidate, applications
    observe the scheduled timestamps through the EVM.

    Initial Rollup0 accepts this limitation. It does not add local first-seen rules, timely
    attestations, or external precommitments. Such mechanisms would add availability, trust, or
    publication requirements and could be unavailable during the same outage that requires
    catch-up. A Rollup0 timestamp therefore identifies a consensus position; Ethereum settlement
    determines when that position becomes safe and finalized.

## 7.3 EEZ Batch

The settlement transaction carries the batch object defined by
[EEZ Proving and Settlement](../eez-protocol-spec/04-proving-and-settlement.md).
Candidate protocol V1 requires a Rollup0-only batch. No other EEZ network may appear in its entries,
lookups, state deltas, routing, or proof-policy mapping. This keeps candidate validation, transient
prefixes, proof interaction, and failure handling independent from other networks. A later
candidate protocol may define shared-batch cost sharing under a new domain tag.

The batch's `crossProofSystemInteractions` field MUST equal `bytes32(0)`. Candidate protocol V1 has
no cross-network or cross-proof-system interaction for this opaque field to identify.

Every Rollup0 batch also requires:

- `blockNumber = 2^64 - 1` to select the authenticated current Ethereum settlement context;
- submission through the active Rollup0 settlement wrapper;
- no other EEZ batch that contains Rollup0 in the same Ethereum block;
- `callData` equal to the empty byte string;
- a nonempty `blobIndices` array of length `m` equal to `[0, 1, ..., m - 1]`;
- `blobhash(i) != bytes32(0)` for every `0 <= i < m`, and `blobhash(m) = bytes32(0)` to prove that
  the outer transaction carries exactly `m` blobs;
- the exact Rollup0 manager domain defined in Appendix D;
- Rollup0 state deltas derived from `H[0]` and every successful synchronous action;
- enough L2 entries and ordered-action data to reconstruct every protocol transaction; and
- the proof or signatures required by Chapter 8.

The batch therefore selects every blob carried by `submitCandidate`, once and in transaction
order; the transaction cannot carry an unrelated or unreferenced sidecar. EEZ hashes that exact
ordered versioned-hash list into every `publicInputsHash`. A validator MUST derive the list from
the exact transaction and sidecars it validates. With canonical indices, a relayer that changes a
blob, its position, or the blob count changes the signed list; a relayer that changes
`blobIndices` violates the wrapper profile. The nonzero and contiguous checks additionally reject
an out-of-range `BLOBHASH` result rather than authenticating a zero placeholder.

Rollup0 does not redefine the EEZ batch tuple or public-input hash.

!!! success "DECISION: version the transient-prefix policy"
    Candidate protocol V1 fixes `transientExecutionEntryCount = 1` and
    `transientLookupCallCount = 0`. The active settlement wrapper enforces those values.

    A later Rollup0.x version that enables top-level Rollup0-to-Ethereum actions may activate a
    new wrapper and candidate-domain tag. Its execution prefix is expected to contain the anchor
    followed by the leading top-level outbound entries. Nested calls inside an entry do not add
    another prefix element. Appendix D defines the update path.

## 7.4 Ethereum Bundle

For delivery, let `p` be the number of proposed triggers in a submitted bundle. Every settlement
choice uses this order:

```text
bundle[p] = [submitCandidate, trigger1, ..., triggerP]
```

`submitCandidate` calls the active Rollup0 settlement wrapper. The wrapper enforces the candidate
protocol policy, calls `EEZ.postAndVerifyBatch`, and establishes `H[0]` as Rollup0's EEZ commitment.
A proposed `trigger` is one exact signed, non-blob Ethereum transaction supplied for bundle
delivery. Its cross-chain proxy call must match the next prepared EEZ action. Canonical execution
may instead use a different non-blob transaction that produces the same next ordered call.

A catch-up candidate has `n = 0`, so its only bundle is `[submitCandidate]`. A live candidate
without a synchronous action uses the same one-transaction bundle.

A successful `submitCandidate` establishes `B[0]`. During the remainder of that Ethereum block,
successful trigger transactions may move the retained Rollup0 commitment through `H[1]` to `H[k]`.
At every point, the retained commitment must correspond to the first `k` successful actions in the
authenticated action manifest. Every accepted trigger must succeed as an outer Ethereum
transaction, make the next expected proxy call, and receive its committed success or terminal
revert result. Other Ethereum transactions may be included in the block, but they must not consume
an out-of-order prepared result or change the Rollup0 endpoint. A submitted bundle is a delivery
request, not settlement evidence.

The canonical endpoint is `B[k]`; EEZ stores its block hash `H[k]`, and its EVM state root is
`R[k]`. A proposed prefix may also include the caught terminal failure as its last trigger. It does
not advance the Rollup0 commitment or successful-action cursor.

For a successful Rollup0 result, the follower checks the retained EEZ consumption and state-update
logs and reconstructs the resulting Rollup0 transaction and block. For a Rollup0 revert caught by
the Ethereum caller, the failed EEZ frame leaves no retained log or Rollup0 effect. A Rollup0
follower therefore need not replay or classify that transaction. An L1 application or indexer that
wants to report the caught failure must replay the exact canonical Ethereum transaction; a
successful Ethereum receipt alone does not reveal the inner revert.

`eth_sendBundle` is a builder API, not an Ethereum consensus rule. Composers SHOULD NOT broadcast
`submitCandidate` and its proposed triggers independently through the public mempool: doing so
provides no atomicity, same-block inclusion, or ordering guarantee. This is delivery guidance, not
a validity prohibition. If canonical Ethereum execution nevertheless satisfies the Rollup0 rules,
the candidate remains valid regardless of how its transactions reached the builder.

The exact signed trigger transactions remain private before inclusion. Validators, relayers, and
builders that receive them are trusted not to leak them. This confidentiality assumption is
separate from validity: leaking or repackaging a transaction must not let an invalid sequence
consume a Rollup0 result or advance the Rollup0 commitment. Chapter 6 describes the remaining harm
that a leaked valid Ethereum transaction can cause on L1.

!!! success "DECISION: enforce ordered calls, not exact trigger transactions"
    Rollup0 enforces the successful action prefix on chain. Builder cooperation is not part of the
    validity or security model. Candidate protocol V1 requires all of the following:

    1. one successful settlement activates one authenticated candidate for the current block;
    2. a successful consumption can apply only the candidate's next ordered call and transition;
    3. a mismatched or out-of-order call cannot consume an unauthorized result or apply a Rollup0
       transition;
    4. a reverted outer transaction rolls back its consumption and cursor update, so the next
       expected action does not change;
    5. the retained commitment can be only `H[k]` after `k` successful actions, and stopping after
       any prefix is allowed; and
    6. the manager and wrapper permit at most one successful Rollup0 candidate activation in an
       Ethereum block, so another batch cannot replace its manifest, queues, or progress cursor;
    7. one outer Ethereum transaction can successfully consume at most one Rollup0 action; and
    8. an EIP-4844 blob transaction cannot consume a Rollup0 action.

    The successful EEZ queue already advances only in order and only when the current call hash
    matches its next entry. An outer transaction revert rolls back that consumption. The production
    manager and wrapper add the authenticated leading anchor transition and one-candidate-per-block
    gate. Together these rules enforce the successful Rollup0 transition prefix.

    A failed lookup has no retained progress cursor because the proxy returns it with `REVERT`.
    Initial Rollup0 therefore permits a failure only as the final manifest action and does not count
    it as a Rollup0 commitment transition. The same failed lookup may be called again in the
    settlement block, but it can neither change `H[k]` nor unlock a successful suffix. Its L1
    occurrence is outside the Rollup0 endpoint derivation rule.

    `eth_sendBundle` may deliver one or more candidate prefixes, but correctness does not depend on
    the builder preserving a proposed transaction list. A different transaction that produces the
    next expected call is intentionally the same action. A mismatched call cannot consume the next
    successful queue entry, and no action follows a terminal failed lookup. Candidate relay remains
    permissionless.

!!! danger "PRODUCTION BLOCKER: required L1 EEZ trigger-consumption guard"
    **This requires a change to the L1 EEZ contract.** A manager or settlement-wrapper change alone
    is insufficient because later trigger transactions call the EEZ consumption path directly.

    The production EEZ contract MUST store a per-rollup carrier-policy flag. Only the registered
    manager for that rollup may change its flag. The Rollup0 manager MUST enable the flag before V1
    activation and MUST keep it enabled while candidate protocol V1 is active. This scopes the
    restriction to Rollup0 without limiting unrelated EEZ rollups.

    In `EEZ.executeCrossChainCall`, after resolving `targetRollupId` and matching its next prepared
    queue entry, but before advancing the cursor, emitting `ExecutionConsumed`, or applying the
    entry, EEZ MUST perform the following checks when that rollup's carrier-policy flag is enabled:

    1. `BLOBHASH(0)` MUST equal zero. Otherwise the consumption MUST revert, so an EIP-4844 blob
       transaction cannot act as a trigger.
    2. A transaction-scoped transient successful-consumption latch, keyed by `targetRollupId`, MUST
       be unset. EEZ MUST set it before advancing the cursor. A later successful consumption for
       the same Rollup0 ID in the same outer transaction MUST revert.

    The latch MUST use EIP-1153 transient storage, or equivalent transaction-scoped state with the
    same semantics. For one `targetRollupId`, it is shared by all call frames in the outer
    transaction, remains set after the first successful consumption returns, rolls back with the
    EEZ call or surrounding transaction if execution reverts, and is empty in the next outer
    transaction. A missing or mismatched entry and the separate prepared-failure lookup path MUST
    NOT set the latch because none creates a successful Rollup0 transition. Existing call-hash,
    cursor, and state-transition checks continue to run; this guard does not replace them.

    Conformance tests MUST cover a non-blob first success, a rejected second success in the same
    outer transaction, a successful consumption in the following transaction, blob-carrier
    rejection, per-rollup scoping, latch rollback on revert, and failed-lookup reuse without a
    retained latch.
    Synchronous production cannot rely on ordered-call substitution until this EEZ change and its
    tests are deployed.

!!! note "DEPLOYMENT POLICY: bundle delivery"
    The initial operator SHOULD submit `n + 1` overlapping strict-prefix bundles when its builder
    API supports them, or use an equivalent smaller request set that preserves the desired prefix
    opportunities. This is inclusion policy, not a validity rule. `submitCandidate` must be an
    EIP-4844 blob transaction, and the selected relay and builder APIs must simulate its sidecar
    together with each request. The exact API, builder set, fee policy, sidecar support, and request
    size limits are deployment configuration.

## 7.5 Ordered Call Identity

The EEZ call hash identifies the target network, target address, value, calldata, source address,
and source network. It does not identify the Ethereum transaction that made the call. Rollup0
intentionally defines action identity as:

```text
(authenticated settlement context, manifestIndex, crossChainCallHash)
```

The settlement context identifies the candidate's intended Ethereum slot and parent. The manifest
index identifies the next action position, and the call hash identifies the call semantics. The
outer Ethereum transaction hash, sender nonce, and unrelated L1 effects are not Rollup0 action
identity.

Two manifest positions MAY have the same call hash. They remain distinct ordered actions because
the successful-entry cursor assigns the first matching call to the first position and advances
before the second can execute. Their prepared results may differ because they execute against
different Rollup0 states. If a transaction originally proposed for a later identical position
arrives first, it intentionally performs the current position and receives that position's result.
Its ordinary Ethereum behavior is determined by canonical L1 execution.

An Ethereum transaction from a different effective source address normally produces a different
call hash and cannot consume the entry. A different transaction from the same EOA, or a transaction
routed through the same source contract, can produce the same hash; at the expected position it is
intentionally equivalent for Rollup0. This rule preserves the current proxy and wallet call path
while making clear that Rollup0 does not authenticate the outer transaction's nonce, fee payer, or
unrelated L1 effects.

Consequently, consuming one position can change what a previously proposed trigger does when it is
included later. It can revert if no matching position remains, or it can consume the next position
when that position has the same call hash. The latter position may have a different prepared result
because it was evaluated against a later Rollup0 state. Canonical Ethereum ordering determines
these L1 consequences; the successful-entry cursor still determines the unambiguous Rollup0
prefix.

## 7.6 Canonical Evidence

A follower uses canonical Ethereum transaction and receipt order. It verifies:

- the exact settlement transaction and authenticated ordered action manifest;
- successful settlement execution;
- logs from the selected EEZ deployment only;
- the Rollup0 ID;
- the successful-action count `k`, `B[k]`, `H[k]`, `R[k]`, and the resulting safe cursor; and
- the candidate's position relative to competing candidates.

An event name or matching block-hash value by itself is not settlement evidence.

---

*Next: [Chapter 8, Proving and Settlement](08-proving-settlement.md).*
