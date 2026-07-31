# 5. Execution Profile

EEZ defines execution entries, lookups, state deltas, rolling hashes, value accounting, proxy
calls, and settlement consumption. Rollup0 uses those rules without changing their wire formats.
See [EEZ Execution Model](../eez-protocol-spec/03-execution-model.md).

## 5.1 Selected EEZ Subset

Rollup0 selects this subset:

- exactly one top-level state-changing Ethereum-to-Rollup0 action in each trigger transaction;
- one return value;
- no cross-network lookup, including `STATICCALL`;
- no direct execution-network-to-execution-network action;
- no cross-network reentrancy;
- no nested cross-network action; and
- no synchronous action originating on Rollup0.

The one-action rule covers the complete Ethereum execution trace. The action may be reached through
a Safe, router, or any other ordinary Ethereum call chain; it does not need to occur at EVM call
depth zero. In this chapter, *top-level* means that the action has no parent EEZ action. A second
Ethereum-to-Rollup0 action anywhere in the same trigger transaction makes the candidate invalid,
including when the caller catches its revert.

Ordinary nested calls that remain on one network are allowed. An Ethereum transaction with no
Rollup0 action is not a trigger transaction and is not part of the candidate's trigger manifest.

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

## 5.2 Rollup0 State Transition

Let `A` be the Rollup0 state root currently stored by EEZ. Let `R0` be the state root after
executing the complete anchored block range through the terminal block's pure-L2 transaction
prefix, but before executing any synchronous action.

Every Rollup0 anchor starts its EEZ batch with one immediate execution entry. This entry has:

- `proxyEntryHash = 0`;
- `destinationRollupId` equal to the Rollup0 EEZ rollup ID;
- one Rollup0 state delta from `A` to `R0`;
- `etherDelta = 0`; and
- no calls, lookups, return data, or rolling-hash effects.

The entry is part of the transient prefix, so EEZ applies it during `postAndVerifyBatch`. It is
also present for a pure-L2 anchor that has no synchronous action. The blob contains the complete
Rollup0 block range; the state delta records only its combined effect on the state root. EEZ does
not decode the Rollup0 blocks.

For Rollup0, a catch-up anchor has only this leading state transition. It has `n = 0`, no
synchronous execution entry, no failed lookup, and an empty Ethereum trigger manifest. Its `R0`
is the state root of its historical terminal Sync block.

The proof or validator signatures bind the bytes of the leading entry and the selected blob
hashes. Validators reconstruct the published blocks from `A`, verify that they form the claimed
chain, and accept the entry only when replay produces `R0`. The fixed EEZ proof digest does not,
however, bind the dispatch count that makes this entry immediate.

Every anchor contains at least one post-genesis block. Because EIP-2935 is active from genesis and
stores a new parent block hash in every block, `R0` differs from `A` even when the range contains
no user transaction.

!!! warning "FIXED EEZ LIMITATION: dispatch counts are not signed"
    A Rollup0 batch requires `transientExecutionEntryCount = 1` and
    `transientLookupCallCount = 0`. The first value makes the leading `A -> R0` entry immediate.
    The second keeps synchronous failed lookups available to their later Ethereum triggers.

    The fixed EEZ public-input hash excludes both fields. A relayer or builder can therefore
    change them without invalidating the proof or validator signatures. This can defer the anchor
    entry, change which later entries are published, or change lookup availability.

    Followers can detect the changed calldata and resulting state transition, but detection does
    not prevent EEZ state from changing on Ethereum. This is a production blocker. Rollup0 must
    define a settlement restriction that enforces the two values and prevents the same proof from
    bypassing that restriction through a direct EEZ call, or it must state an explicit trusted
    submission assumption. The EL cannot fix this behavior.

!!! note "TO BE DISCUSSED: applying the anchor root"
    Rollup0 currently selects the leading `A -> R0` entry described above. The exact
    contract-level failure rule is still to be selected.

    The current EEZ contract catches a failed immediate entry and continues
    `postAndVerifyBatch`. The transaction can therefore succeed and emit `BatchPosted` even when
    the `A -> R0` transition was not applied. `BatchPosted` alone never proves that a Rollup0
    anchor was accepted.

    The available enforcement choices are:

    1. **Check the applied result during derivation.** Keep the current contracts and treat the
       candidate as settled only when the exact settlement transaction actually changes the
       stored Rollup0 root from `A` to `R0`. This needs no contract change, but a skipped entry
       does not revert the settlement transaction and can still affect temporary EEZ batch
       bookkeeping.
    2. **Use a Rollup0 settlement wrapper.** The wrapper calls `postAndVerifyBatch`, reads the
       resulting Rollup0 root, and reverts unless it equals `R0`. This gives the anchor
       transaction atomic success or failure without changing EEZ, but adds a Rollup0-specific
       contract and integration path. The Rollup0 proof policy must also make the wrapper
       mandatory; otherwise the same proof can be submitted directly to EEZ.

    Until this is selected, followers must check the actual stored-root transition and its
    correctly ordered `L2ExecutionPerformed` event. They must not infer settlement from
    `BatchPosted`.

For each candidate, the composer and every validator/prover independently:

1. execute every nonterminal block after the named Rollup0 parent;
2. execute the terminal block's pure-L2 transaction prefix and record `R0`;
3. execute each synchronous action in its intended Ethereum trigger order, stopping after the first
   failed action;
4. construct `B[i]` and record `R[i]` after each action `i`;
5. represent a successful Ethereum-side result with its EEZ execution entry and a reverting result
   with its failed lookup;
6. derive the state deltas, return data, and value changes for every prefix; and
7. require the EEZ state sequence to be `R0, R[1], ..., R[n]`.

The corresponding L1 EEZ batch contains:

- the leading immediate entry from `A` to `R0`;
- one execution entry from `R[i - 1]` to `R[i]` for each successful synchronous action `i`;
  and
- zero or one failed lookup pinned to `R[n - 1]`, with no state delta, when the final synchronous
  action `n` fails.

The proof or signatures authenticate every intermediate block and root inside a multi-block
pure-L2 range. Those intermediate roots do not need separate EEZ state deltas.

For a successful action, the L1 EEZ entry and the L2 `EEZL2` entry are different objects. The L1
entry returns the precomputed result to the Ethereum trigger and updates EEZ's stored Rollup0 root.
The L2 entry is part of the protocol transaction and executes the application call on Rollup0.

The two entries keep separate rolling hashes because they describe different execution frames.
Under the initial one-way profile, the L1 entry executes no Rollup0-to-Ethereum child call, so its
`callCount` and `rollingHash` are zero. The L2 entry executes the inbound application call, so its
`callCount` is one and its rolling hash commits to that call's start, success or failure result,
and return data. The two rolling hashes are not required to be equal.

Candidate validation must still prove that both entries describe the same action. The L1 action
hash and returned result, the L2 entry and rolling hash, and the independently replayed call must
agree on the source, destination, value, calldata, success result, and return data.

The protocol transaction keeps the `EEZL2` array-based ABI. All table data supplied by a valid
transaction must be consumed by that transaction. Under the initial Rollup0 rules, a successful
action therefore supplies exactly one L2 `ExecutionEntry` and no top-level L2 `LookupCall`. The
entry contains exactly one non-static inbound call, has no expected outgoing call or nested lookup,
and sets `callCount = 1`. Its action hash, source and destination, value, calldata, return data, and
rolling hash must match replay.

Rollup0.x can permit additional entries, lookups, and nested-call data without changing the ABI.
That version must define how every additional object is reached and consumed. Unused table data
remains invalid in every version.

For a failed Ethereum-to-Rollup0 action, there is no Rollup0 protocol transaction or L2 execution
table. The composer and every validator/prover execute the call temporarily from `R[i - 1]`, verify
the exact failure and revert data, and discard the complete result. The L1 EEZ batch contains one
failed lookup pinned to `R[i - 1]`. The trigger manifest and proof or signatures bind that lookup
to the exact Ethereum transaction and action position.

Under the initial one-way, non-nested profile, that L1 lookup has:

- `failed = true`;
- the exact action hash and Rollup0 destination ID;
- the original application revert data in `returnData`;
- exactly one state-root pin, for Rollup0 at `R[i - 1]`;
- no calls, expected reentrant calls, or nested lookups;
- `callCount = 0`; and
- `rollingHash = 0`.

It is a persistent lookup made available to its Ethereum trigger later in the settlement block,
not part of the immediate lookup prefix.

`R0` is the Sync-block root when no synchronous action is processed. For a successful action
`i`, its EEZ entry requires `R[i - 1]` and produces `R[i]`. A failed action adds no transaction and
no receipt to the Sync block. Therefore both `B[i]` and `R[i]` equal their preceding values. It
consumes no Rollup0 block gas and causes no L2 nonce, value, fee, log, or state change.

A successful action always has an execution entry, including when the complete Rollup0 world state
does not change. In that case, the entry's current and new state roots are equal and its
`etherDelta` is zero. The protocol transaction has no sender nonce or L2 fee state change. It still
consumes block gas and remains in the transaction and receipt roots. It can return data and emit
logs, and its Ethereum trigger can change Ethereum state. Validators must verify the exact entry,
transaction position, receipt, and block hash because an equal state root alone cannot distinguish
this success from a failed action.

The transaction root commits the exact protocol transaction and its position. The receipt root
commits its status, cumulative gas use, bloom, and logs. Exact return or revert data remains
committed by the EEZ execution data and is checked by deterministic replay; Ethereum-style
receipts do not contain return data.

The DA payload does not need to repeat execution-derived header fields. It supplies the exact
transaction bytes and order, block boundaries, parent, and every header input that cannot be
derived from the protocol rules. Validators and followers then derive the transaction root,
receipts, receipt root, logs bloom, gas used, state root, and block hash. A block hash carried in
the payload is only a claimed value and must equal the hash produced by replay.

The proof or signatures cover the EEZ public-input hash, including commitments to the execution
entries, lookups, and Rollup0 DA payload. A supplied root or return value is not trusted without
re-execution. Every value that can change candidate validity or a resulting Rollup0 block must
either be derived uniquely from prior canonical state and this specification, or be authenticated
by the EEZ public-input hash. Validator-only side data must not affect the accepted result.

!!! note "TO BE DEFINED: candidate domain and blob encoding"
    The blob-format specification must define the exact encoding and placement of every
    non-derived input. It must also define how the authenticated candidate is bound to the
    Ethereum chain, EEZ deployment, Rollup0 ID, protocol version, blob-format version, parent, and
    settlement context. Some values can be carried by the EEZ batch or manager `customData`
    instead of being repeated in the blob, but none can remain unauthenticated.

## 5.3 Required Invariants

A valid candidate preserves all EEZ invariants, including:

- the current state in each state delta equals the state committed before the effect;
- state deltas form one continuous state transition;
- `R0` contains the complete pure-L2 prefix and no synchronous effect;
- every trigger transaction contains exactly one top-level Rollup0 action in its complete trace;
- no trigger follows a failed action in the candidate manifest;
- every `B[i]` contains protocol transactions for exactly the successful actions among the first
  `i` Ethereum triggers;
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
transaction also reverts. Under the intended atomic-bundle rule, a bundle containing that trigger is
ineligible and a selected shorter bundle contains no later trigger. Chapter 7 describes the current
builder trust assumption and the unresolved enforcement design.

!!! note "TO BE DISCUSSED: actions after a caught failure"
    Initial Rollup0 ends a candidate's trigger manifest at its first failed action. This prevents a
    failed lookup, which has no consumption cursor, from being skipped while a later prepared
    execution entry still advances Rollup0.

    Two alternatives remain open for a later Rollup0 version:

    1. **Trust the Ethereum builder to preserve the exact submitted trigger prefix.** This permits
       later actions without changing EEZ, but a proof or signature cannot stop the builder from
       omitting the failed trigger and including a later transaction.
    2. **Add one ordered cursor for successful entries and failed lookups, plus a compatible way to
       acknowledge caught failures.** The cursor would allow only prefixes. If action `i` were
       omitted or its outer transaction reverted, action `i + 1` would remain blocked; clients
       would not simulate every possible subset. However, the current proxy reports an application
       failure with `REVERT`, which also rolls back any cursor increment. An EEZ contract and data
       model change alone cannot retain that progress. This option also needs an acknowledgement
       after the caller catches the failure, a transaction wrapper, different proxy semantics, or
       an EVM change. No design that preserves transparent dApp behavior has been selected.

    The selected terminal-failure rule does not solve general bundle repackaging or duplicate call
    hashes. Chapter 7 tracks those separate issues.

The candidate remains valid only when every composer-supplied result, `B[i]`, and prefix root
exactly matches independent execution.

## 5.5 Native-Value Backing

Initial Rollup0 uses the existing L1 EEZ custody model. A cross-chain proxy does not retain
`msg.value`; it forwards the value to the EEZ contract. EEZ holds the pooled ETH and accounts for
Rollup0 separately in its per-rollup `etherBalance`.

For a successful Ethereum-to-Rollup0 action carrying value `v`:

- the L1 EEZ contract receives `v`;
- the Rollup0 `etherBalance` in EEZ increases by `v`;
- the Rollup0 protocol transaction creates exactly `v` of temporary protocol credit; and
- the application call distributes that value while `EEZL2` ends with its pre-transaction balance.

A successful Rollup0-to-Ethereum value release performs the reverse accounting: EEZ decreases the
Rollup0 `etherBalance` and transfers the same value through the proxy to the Ethereum target. The
ledger cannot become negative. A failed action changes neither side.

The ETH balance of the L1 EEZ contract must be at least the sum of its per-rollup
`etherBalance` values. ETH forced into the contract without a valid EEZ action is surplus and does
not credit Rollup0. Rollup0's ledger backs the native value issued through EEZ. L2 fee burning or
otherwise inaccessible value can make the backing greater than the remaining redeemable value.

Rollup0 genesis gives no ordinary account a native balance. Any faucet or operational balance must
enter through a collateralized EEZ deposit. Genesis can still install contract code and storage,
including the predeploys defined in Chapter 3, without assigning those accounts native value.

!!! note "TO BE DISCUSSED: dedicated Rollup0 vault"
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
