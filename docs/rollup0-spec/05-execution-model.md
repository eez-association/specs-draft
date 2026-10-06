# 5. Execution Profile

EEZ defines execution entries, lookups, state deltas, rolling hashes, value accounting, proxy
calls, and settlement consumption. Rollup0 uses those rules without changing their wire formats.
See [EEZ Execution Model](../eez-protocol-spec/03-execution-model.md).

## 5.1 Selected EEZ Subset

Rollup0 selects this subset:

- exactly one top-level state-changing Ethereum-to-Rollup0 action in each proposed trigger
  transaction;
- one return value;
- no cross-network lookup, including `STATICCALL`;
- no direct execution-network-to-execution-network action;
- no cross-network reentrancy;
- no nested cross-network action; and
- no synchronous action originating on Rollup0.

For a proposed trigger, the one-action rule covers the complete Ethereum execution trace. The
action may be reached through a Safe, router, or any other ordinary Ethereum call chain; it does not
need to occur at EVM call depth zero. In this chapter, *top-level* means that the action has no
parent EEZ action. A second Ethereum-to-Rollup0 action anywhere in a proposed trigger makes that
delivery proposal invalid, including when the caller catches its revert.

An equivalent carrier transaction is not pre-authenticated by the candidate. Candidate protocol
V1 therefore requires the production L1 EEZ path to enforce the state-relevant rule directly: one
outer transaction can successfully consume at most one ordered Rollup0 action. Additional
mismatched or failed calls that create no Rollup0 transition are L1-only behavior and do not affect
Rollup0 derivation. This remains a production blocker until the Chapter 7 EEZ guard is deployed and
tested.

A trigger MUST NOT be an EIP-4844 blob transaction or otherwise require a blob sidecar. This
restriction applies to the proposed delivery transaction and any equivalent transaction that
performs an ordered action. The separate `submitCandidate` settlement transaction is blob-carrying.
This separation reserves sidecar transport for candidate DA, avoids transporting and simulating
additional private trigger sidecars, and lets the L1 EEZ path distinguish current blob-bearing
transaction types with `BLOBHASH(0)`. If a future Ethereum transaction type requires a sidecar but
does not expose a nonzero `BLOBHASH(0)`, Rollup0 MUST extend the EEZ carrier-policy check before
permitting that type on Ethereum; the current opcode check alone would not enforce the general rule.

An EIP-7702 type-`0x04` transaction MAY be a trigger because it has no blob sidecar. Proposed-trigger
validators apply the complete-trace one-action rule to delegated code as well. The L1 EEZ guard
enforces at most one successful consumption per outer transaction, including equivalent carriers;
it does not count failed or mismatched calls.

Ordinary nested calls that remain on one network are allowed. An Ethereum transaction with no
Rollup0 action is not a trigger transaction and is not part of the candidate's action manifest.

These restrictions keep the initial Rollup0 execution profile small. They are not restrictions on
EEZ. A later Rollup0.x version is expected to enable nested composability in both directions,
including cross-network reads and actions originating on Rollup0.

Sequencers should reject a pure-L2 transaction when simulation reaches a cross-network proxy,
because initial Rollup0 cannot resolve an outbound action. This is transaction-admission policy,
not a special EVM validity rule. A rejected transaction is not included, does not consume its
nonce, and pays no on-chain fee. Sequencers handle repeated or expensive rejected submissions with
ordinary RPC limits, peer limits, and bans.

If a producer nevertheless includes the transaction, the unprepared proxy call reverts under the
existing EVM contract behavior. The transaction may catch that revert. It consumes gas and its
nonce in the same way as any other included Ethereum-style transaction, and the attempted call
does not by itself make the block invalid. A candidate is invalid only if it claims that such an
outbound action was successfully resolved as part of the initial Rollup0 protocol.

## 5.2 Rollup0 Block-Hash Commitment and Transition

For terminal variant `B[k]`, where `k` is the number of successful synchronous actions, define:

```text
H[k] = the Rollup0 block hash of B[k]
R[k] = the EVM state root in the header of B[k]
```

`R0` is another name for `R[0]`, the state root after the complete anchored block range and the
terminal block's pure-L2 transaction prefix, but before any synchronous action.

Rollup0 uses `H[k]`, not `R[k]`, as its 32-byte EEZ state commitment. The block hash commits the
parent, block number, state root, transaction root, receipt root, and the other header fields. A
follower can fetch the exact header by this hash and use its `stateRoot` to verify full or snap
state synchronization.

This choice also distinguishes two valid terminal variants when their execution produces the same
EVM state root. EIP-2935 does not remove that need. The state of `B[k]` contains its parent block
hash because the EIP-2935 system call runs before the block's transactions. It cannot contain
`H[k]` without creating a circular dependency, and every sibling variant writes the same parent
hash. EIP-2935 therefore helps verify the parent chain, while `H[k]` remains the exact terminal
checkpoint.

The EEZ contracts treat this value as opaque bytes, so this choice does not change their encoding
or execution. In every EEZ object for Rollup0, fields named `stateRoot`, `currentState`,
`newState`, or `ExpectedStateRootPerRollup.stateRoot` contain a Rollup0 block hash.

!!! note "LEGACY TERMINOLOGY: EEZ calls the commitment `stateRoot`"
    The EEZ Solidity identifiers describe this opaque commitment as a state root. That name is
    misleading for Rollup0 and does not clearly describe networks that use a block hash or another
    state commitment.

    A later EEZ revision SHOULD rename these identifiers to `stateCommitment`,
    `currentCommitment`, and `newCommitment`, including related lookup pins, events, errors, and the
    manager escape function. This rename is not a Rollup0 production prerequisite: the fields are
    opaque `bytes32` values and the current encoding is unambiguous. Rollup0 clients MUST treat
    their state-named values as block hashes. Comparing one with an EVM header's `stateRoot` is
    incorrect.

`Hparent` is the parent Rollup0 block hash: the hash of the latest Rollup0 block accepted through
canonical Ethereum and currently stored by EEZ. It is not an Ethereum block hash. Every candidate
must extend this exact Rollup0 block.

Every Rollup0 anchor starts its EEZ batch with one immediate execution entry. This entry has:

- `proxyEntryHash = 0`;
- `destinationRollupId` equal to the Rollup0 EEZ rollup ID;
- one Rollup0 state delta from `Hparent` to `H[0]`;
- `etherDelta = 0`; and
- no calls, lookups, return data, or rolling-hash effects.

The entry is part of the transient prefix, so EEZ applies it during `postAndVerifyBatch`. It is
also present for a pure-L2 anchor that has no synchronous action. The blob contains the complete
Rollup0 block range; the state delta records its exact terminal block commitment. EEZ does not
decode the Rollup0 blocks.

For Rollup0, a catch-up anchor has only this leading commitment transition. It has `n = 0`, no
synchronous execution entry, no failed lookup, and an empty action manifest. `H[0]` is
the hash of its historical terminal Sync block and `R0` is that block's EVM state root.

The proof or validator signatures bind the bytes of the leading entry and the selected blob
hashes. Validators reconstruct the published blocks after `Hparent`, verify that they form the
claimed chain, and accept the entry only when replay produces both `R0` and `H[0]`. The fixed EEZ
proof digest does not, however, bind the transient-prefix length that makes this entry immediate.

Every anchor contains at least one post-genesis block, so `H[0]` differs from `Hparent`. Because
EIP-2935 is active from genesis and stores a new parent block hash in every block, `R0` also differs
from the parent block's state root even when the range contains no user transaction.

!!! warning "FIXED EEZ LIMITATION: transient-prefix lengths are not signed"
    A Rollup0 batch requires `transientExecutionEntryCount = 1` and
    `transientLookupCallCount = 0`. These fields are array split points, not counts of synchronous
    actions or Rollup0 protocol transactions.

    The first value makes only the leading `Hparent -> H[0]` anchor entry immediate. Successful
    synchronous entries remain deferred for their corresponding Ethereum trigger transactions.
    The second value keeps every synchronous failed lookup deferred for its later Ethereum trigger.
    A separate candidate rule requires exactly one Rollup0 protocol transaction for each successful
    trigger.

    The fixed EEZ public-input hash excludes both fields. A relayer or builder can therefore
    change them without invalidating the proof or validator signatures. This can defer the anchor
    entry, change which later entries are published, or change lookup availability.

    Followers can detect changed calldata and resulting state transitions, but detection alone
    does not prevent EEZ state from changing on Ethereum. Initial Rollup0 therefore enforces the
    two values through the manager-gated settlement wrapper defined in Appendix D. The manager
    rejects a direct EEZ submission that bypasses that wrapper.

!!! success "DECISION: derive anchor acceptance from the applied commitment"
    Rollup0 accepts an anchor only when canonical Ethereum execution applies the leading
    `Hparent -> H[0]` commitment transition. Followers must verify the actual transition and its
    correctly ordered `L2ExecutionPerformed` event. They must then derive any later synchronous
    transitions in the bundle in order.

    `BatchPosted` identifies a publication attempt. It does not prove that Rollup0 accepted the
    anchor. If EEZ catches or skips the leading entry, no Rollup0 anchor is accepted even when
    `postAndVerifyBatch` succeeds.

!!! success "DECISION: make anchor application atomic through the settlement wrapper"
    The current immutable EEZ contract catches a failed immediate entry and continues
    `postAndVerifyBatch`. The settlement transaction can therefore succeed and emit `BatchPosted`
    without applying `Hparent -> H[0]`.

    The Rollup0 settlement wrapper checks the stored commitment after `postAndVerifyBatch` and
    reverts unless EEZ applied the exact leading transition. The Rollup0 manager accepts
    `getCustomData` during settlement only after the active wrapper authorizes the transaction, so
    the same proof cannot bypass the check through a direct EEZ call. Followers still apply the
    observed-commitment rule above rather than trusting `BatchPosted`.

For each candidate, the composer and every validator/prover independently:

1. execute every nonterminal block after the named Rollup0 parent;
2. execute the terminal block's pure-L2 transaction prefix and record `R0`;
3. execute each synchronous action in manifest order, stopping after the first
   failed action;
4. construct `B[k]` and record both `H[k]` and `R[k]` after each successful action `k`; a failed
   terminal action creates no variant;
5. represent a successful Ethereum-side result with its EEZ execution entry and a reverting result
   with its failed lookup;
6. derive the state deltas, return data, and value changes for every prefix; and
7. require the EEZ commitment sequence to be `H[0], H[1], ..., H[s]`, where `s` is the candidate's
   successful-action count.

The corresponding L1 EEZ batch contains:

- the leading immediate entry from `Hparent` to `H[0]`;
- one execution entry from `H[k - 1]` to `H[k]` for each successful synchronous action `k`;
  and
- zero or one failed lookup pinned to `H[s]`, with no state delta, when the final manifest action
  fails.

The terminal variants are siblings: every `B[k]` has the same Rollup0 parent block. The EEZ
transition `H[k - 1] -> H[k]` records progressive selection by successful Ethereum triggers; it
does not mean that `B[k]` is a child of `B[k - 1]`.

There is no circular block hash. The L2 `EEZL2` entry inside a protocol transaction contains no L1
state delta and no `H[k]`. The composer first constructs and hashes `B[k]`, then writes `H[k]` into
the separate L1 EEZ batch. A future protocol-transaction field must not depend on the hash of the
block that contains that transaction.

The proof or signatures authenticate `H[0]` in the leading EEZ state delta. Because every Rollup0
header contains its parent's hash, `H[0]` transitively commits every intermediate header in the
multi-block pure-L2 range, and each intermediate header commits its own state root. Those
intermediate values do not need separate blob fields or EEZ state deltas.

For a successful action, the L1 EEZ entry and the L2 `EEZL2` entry are different objects. The L1
entry returns the precomputed result to the Ethereum trigger and updates EEZ's stored Rollup0
commitment. The L2 entry is part of the protocol transaction and executes the application call on
Rollup0.

The two entries keep separate rolling hashes because they describe different execution frames.
Under the initial one-way profile, the L1 entry executes no Rollup0-to-Ethereum child call, so its
`callCount` and `rollingHash` are zero. The L2 entry executes the inbound application call, so its
`callCount` is one and its rolling hash commits to that call's start, success or failure result,
and return data. The two rolling hashes are not required to be equal.

Candidate validation must still prove that both entries describe the same action. The L1 action
hash and returned result, the L2 entry and rolling hash, and the independently replayed call must
agree on the source, destination, value, calldata, success result, and return data.

In particular, the explicit `destination`, `value`, `data`, `sourceAddress`, and `sourceRollup`
arguments to `EEZL2.executeIncomingCrossChainCall` must equal the corresponding fields in the first
`incomingCalls` item. That item must also satisfy the initial Rollup0 rules for a non-static
top-level call. The `EEZL2` action-hash check does not replace this field-for-field candidate rule.

The protocol transaction keeps the `EEZL2` array-based ABI. All table data supplied by a valid
transaction must be consumed by that transaction. Under the initial Rollup0 rules, a successful
action therefore supplies exactly one L2 `ExecutionEntry` and no top-level L2 `LookupCall`. The
entry contains exactly one non-static inbound call, has no expected outgoing call or nested lookup,
and sets `callCount = 1`. Its action hash, source and destination, value, calldata, return data, and
rolling hash must match replay.

For each successful action `k` carrying value `v`, its deferred L1 EEZ execution entry contains
the Rollup0 state delta from `H[k - 1]` to `H[k]` with `etherDelta = +v`. Under the V1 one-way,
non-nested profile, the trigger delivers `etherIn = v` to EEZ and the entry sends no Ethereum-side
`etherOut`, so EEZ's per-entry conservation rule requires that exact delta. For `v = 0`, the delta
is zero. A different delta is invalid even if the validator threshold signed it.

Rollup0.x can permit additional entries, lookups, and nested-call data without changing the ABI.
That version must define how every additional object is reached and consumed. Unused table data
remains invalid in every version.

For a failed Ethereum-to-Rollup0 action, there is no Rollup0 protocol transaction or L2 execution
table. The composer and every validator/prover execute the call temporarily from `R[s]`, where `s`
is the number of preceding successful actions, verify the exact failure and revert data, and discard
the complete result. The L1 EEZ batch contains one failed lookup pinned to `H[s]`. The action
manifest and proof or signatures bind that lookup to its ordered call position, not to an exact
outer Ethereum transaction.

Under the initial one-way, non-nested profile, that L1 lookup has:

- `failed = true`;
- the exact action hash and Rollup0 destination ID;
- the original application revert data in `returnData`;
- exactly one commitment pin, encoded in the EEZ `stateRoot` field, for Rollup0 at `H[s]`;
- no calls, expected reentrant calls, or nested lookups;
- `callCount = 0`; and
- `rollingHash = 0`.

It is a persistent lookup made available to its Ethereum trigger later in the settlement block,
not part of the immediate lookup prefix.

`R0` is the Sync-block state root when no synchronous action is processed. For successful action
`k`, its EEZ entry requires `H[k - 1]` and produces `H[k]`; replay separately moves the EVM state
from `R[k - 1]` to `R[k]`. A failed action adds no transaction or receipt and creates no additional
`B`, `H`, or `R` variant. It consumes no Rollup0 block gas and causes no L2 nonce, value, fee, log,
or state change.

A successful zero-value action always has an execution entry, including when the complete Rollup0
world state does not change. In that case, `R[k]` can equal `R[k - 1]`, but `H[k]` differs because
the protocol transaction and its receipt are present in `B[k]`. Its `etherDelta` is zero because
`v = 0`. The protocol transaction has no sender nonce or L2 fee state change. It still consumes
block gas, remains in the
transaction and receipt roots, and can return data or emit logs. The block-hash commitment therefore
distinguishes this success from a failed action without pretending that the EVM state root changed.

The transaction root commits the exact protocol transaction and its position. The receipt root
commits its status, cumulative gas use, bloom, and logs. Exact return or revert data remains
committed by the EEZ execution data and is checked by deterministic replay; Ethereum-style
receipts do not contain return data.

The DA payload does not need to repeat execution-derived header fields. It supplies the exact
pure-L2 transaction bytes, the authenticated inputs that uniquely derive protocol-transaction
bytes, transaction order, block boundaries, parent, and every header input that cannot be derived
from the protocol rules. Validators and followers then derive the transaction root, receipts,
receipt root, logs bloom, gas used, state root, and block hash. A block hash carried in the payload
is only a claimed value and must equal the hash produced by replay.

The proof or signatures cover the EEZ public-input hash, including commitments to the execution
entries, lookups, and Rollup0 DA payload. A supplied root or return value is not trusted without
re-execution. Every value that can change candidate validity or a resulting Rollup0 block must
either be derived uniquely from prior canonical state and this specification, or be authenticated
by the EEZ public-input hash. Validator-only side data must not affect the accepted result.

!!! success "DECISION: manager-bound candidate domain"
    The production Rollup0 manager binds each candidate to the Rollup0 protocol version, Ethereum
    chain, EEZ deployment, manager, EEZ rollup ID, Rollup0 chain ID, target Ethereum timestamp,
    and parent Ethereum block hash through its authenticated `customData`. Appendix D defines the
    exact value.

    The leading EEZ entry separately binds `Hparent`, and the authenticated blob envelope carries
    its format version. These values do not need unauthenticated side data or duplicate fields.

!!! danger "PRODUCTION BLOCKER: exact blob encoding"
    Appendix D defines the V0 linear codec and initial codec vectors. Complete action-manifest,
    transaction-bearing, terminal-variant, and derivation vectors are still required. EEZ Core owns
    the unchanged physical packing and multi-blob rules. An independent client cannot claim
    production Rollup0 conformance until the remaining vectors are complete.

## 5.3 Required Invariants

A valid candidate preserves all EEZ invariants, including:

- the `currentState` block hash in each state delta equals the Rollup0 commitment before the
  effect;
- state deltas form one continuous block-hash commitment sequence;
- `R0` contains the complete pure-L2 prefix and no synchronous effect;
- every proposed trigger transaction contains exactly one top-level Rollup0 action in its complete
  trace;
- no trigger is an EIP-4844 blob transaction or otherwise requires a blob sidecar;
- no action follows a failed action in the candidate manifest;
- every `B[k]` contains exactly the first `k` successful protocol transactions;
- each L1 and L2 rolling hash matches the calls executed in its own frame;
- the L1 action record, L2 entry, and replayed result describe the same action and result;
- every expected successful call is consumed in replay;
- every expected failed lookup returns its exact committed revert data in replay;
- every consensus-affecting input is either uniquely derived or authenticated by the EEZ
  public-input hash;
- value is conserved under the EEZ accounting rules; and
- replay reproduces each complete block, including its transaction root, receipt root, logs bloom,
  gas used, state root, header, and block hash.

A candidate that fails an EEZ invariant is invalid regardless of how many parties signed it.

## 5.4 Failed Calls

An ordinary Rollup0 call failure is a possible precomputed result. This includes `REVERT` and an
exceptional halt such as an out-of-gas inside the target call. EEZ returns the committed failure
data on Ethereum through a failed lookup. If the outer Ethereum transaction catches that failure
and succeeds, the synchronous action is processed, but it must be the candidate's final trigger.
Rollup0 does not include or charge an L2 transaction for the failed action. Any charge for
simulation, validation, or proving must occur through the Ethereum settlement flow.

When the outer Ethereum trigger transaction reverts, any EEZ consumption and state update in that
transaction also reverts. The successful queue therefore remains at the same expected ordered call.
Chapter 7 defines this rule.

!!! success "DECISION: a caught failure ends the candidate manifest"
    Initial Rollup0 ends a candidate's action manifest at its first failed action. This prevents a
    failed lookup, which has no consumption cursor, from being skipped while a later prepared
    execution entry still advances Rollup0.

    A later Rollup0.x version may permit actions after a caught failure only after it adds one
    ordered cursor for successful entries and failed lookups, plus a compatible way to acknowledge
    caught failures. If action `i` were omitted or its outer transaction reverted, action `i + 1`
    would remain blocked; clients would not simulate every possible subset. However, the current
    proxy reports an application failure with `REVERT`, which also rolls back any cursor increment.
    An EEZ contract and data-model change alone cannot retain that progress. This design also needs
    an acknowledgement after the caller catches the failure, a transaction wrapper, different
    proxy semantics, or an EVM change. No design that preserves transparent dApp behavior has been
    selected. Trusting a builder to preserve the sequence is not an acceptable substitute.

    Candidate protocol V1 does not advance the successful-action count or create a block variant for
    that failure. Reusing the failed lookup cannot change the Rollup0 endpoint or unlock a suffix.
    A Rollup0 follower need not record its canonical L1 occurrence.

The candidate remains valid only when every composer-supplied result, `B[k]`, `H[k]`, and `R[k]`
exactly matches independent execution.

## 5.5 Native-Value Backing

Rollup0's native currency is ETH. Initial Rollup0 uses the existing L1 EEZ custody model. A
cross-chain proxy does not retain `msg.value`; it forwards the value to the EEZ contract. EEZ holds
the pooled ETH and accounts for Rollup0 separately in its per-rollup `etherBalance`.

For a successful Ethereum-to-Rollup0 action carrying value `v`:

- the L1 EEZ contract receives `v`;
- the Rollup0 `etherBalance` in EEZ increases by `v`;
- the Rollup0 protocol transaction creates exactly `v` of temporary protocol credit; and
- the application call distributes that value while `EEZL2` ends with its pre-transaction balance.

Any Rollup0 withdrawal must perform the reverse accounting: the backing attributed to Rollup0
decreases by the exact ETH amount released on Ethereum. The ledger cannot become negative. A failed
withdrawal changes neither side.

The ETH balance of the L1 EEZ contract must be at least the sum of its per-rollup
`etherBalance` values. ETH forced into the contract without a valid EEZ action is surplus and does
not credit Rollup0. Rollup0's ledger backs the native value issued through EEZ. Rollup0 does not
burn L2 fees: base fees and blob fees are credited to `FEE_COLLECTOR` (Chapter 11), so paying fees
does not reduce the native supply that the ledger backs. Value sent to an account nobody controls
can still make the backing greater than the value that can be redeemed in practice.

Permissionless registration of another EEZ rollup does not authorize it to spend Rollup0's ledger.
Every batch touching Rollup0 must satisfy Rollup0's proof policy and manager-gated settlement path;
V1 also rejects mixed-rollup batches. EEZ separately enforces per-entry ether conservation and
per-rollup balance-underflow checks. Those arithmetic checks alone do not isolate ledgers: debiting
Rollup0 by `v` and crediting a sibling by `v` could satisfy both. Rollup0's authorization and batch
scope prevent that reassignment. Pooled custody therefore relies on these checks together with
the validator and manager trust assumptions in Chapter 8. A dedicated vault is not part of V1.

Rollup0 genesis gives no ordinary account a native balance. Any faucet or operational balance must
enter through a collateralized EEZ deposit. Genesis can still install contract code and storage,
including the predeploys defined in Chapter 3, without assigning those accounts native value.

Initial Rollup0 requires an asynchronous ETH withdrawal path. A normal signed Rollup0 transaction
transfers or locks ETH in a withdrawal escrow or outbox and records a unique request. After the
containing anchor reaches the required Ethereum confirmation level, the user or another party can
prove and claim the backed ETH on Ethereum. The L1 claim atomically marks the request spent,
decreases Rollup0's EEZ `etherBalance`, and releases exactly the requested amount.

!!! success "DECISION: V1 withdrawals are asynchronous only"
    Initial Rollup0 does not add a bridge-only exception to the one-way call profile and does not
    support a synchronous ETH withdrawal. A later Rollup0.x version may add an Ethereum-initiated
    claim against ETH previously locked in an L2 withdrawal escrow. That direction-preserving
    design still needs an authenticated request, payout, and replay protocol and is not valid by
    convention under V1.

!!! danger "PRODUCTION BLOCKER: ETH withdrawal protocol"
    The asynchronous outbox, request identifier, qualifying confirmation level, claim proof, L1
    payout path, and replay rules are not yet defined.

    The design must work with EEZ's pooled custody. A launch implementation must release ETH only
    when the authenticated Rollup0 execution removes or locks the same amount and must prevent the
    same withdrawal from being paid twice.

!!! question "ROLLUP0.X DESIGN: dedicated Rollup0 vault"
    A later Rollup0 or EEZ version can keep Rollup0 backing in a dedicated vault instead of the
    shared EEZ balance. A chain-specific vault provides clearer isolation and can deploy some funds
    into liquidity positions or other approved strategies.

    This design changes the withdrawal guarantee. It must define the liquid reserve, synchronous
    redemption behavior, strategy permissions, valuation, yield ownership, loss allocation,
    insolvency handling, and emergency exit. If the vault cannot supply the requested ETH
    immediately, a synchronous Rollup0-to-Ethereum value action cannot settle.

    The current EEZ contract pays value from its own balance. Using a vault therefore requires an
    EEZ contract change or a compatible custody adapter; it is not an implementation choice for
    initial Rollup0.

---

*Next: [Chapter 6, Composer and Candidate Competition](06-composer.md).*
