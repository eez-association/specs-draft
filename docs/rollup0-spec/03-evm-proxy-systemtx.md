# 3. EVM, Proxy, and Inbound Transactions

## 3.1 EVM Profile

Rollup0 executes an Ethereum-equivalent EVM. It adds no custom opcode or precompile. Cross-network
behavior is provided by contracts and protocol-derived transactions.

Rollup0 has no beacon chain. It keeps the Cancun header shape but does not execute the EIP-4788
beacon-roots contract update. Chapter 4 fixes `parentBeaconBlockRoot` to zero.

Rollup0 starts with the Ethereum Cancun execution rules. It adopts later Ethereum execution
hardforks through explicit Rollup0 hardforks.

!!! note "TO BE DEFINED"
    The activation rule and schedule for post-Cancun hardforks are not yet selected.

## 3.2 EEZ Proxies

Rollup0 uses the EEZ cross-chain proxy mechanism without changing its address derivation, call
hash, authorization, or execution behavior. Those rules are defined by
[EEZ EVM Contracts and Proxies](../eez-protocol-spec/02-evm-and-proxies.md), with vectors in
[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md).

Rollup0 installs the `EEZL2` contract from `eez-core-protocol` at this predeploy address:

| Address | Purpose |
|---|---|
| `0xee50000000000000000000000000000000000000` | Rollup0 `EEZL2` predeploy |

Rollup0 does not change the selected contract's ABI, bytecode, storage layout, proxy behavior, or
execution-table lifecycle. The production genesis binds its exact runtime bytecode and constructor
settings to the predeploy address.

!!! note "TO BE DEFINED: EEZL2 artifact"
    Rollup0 will use the latest `eez-core-protocol` `EEZL2` version selected when the production
    genesis is finalized. The final genesis specification must state its bytecode hash, Rollup0
    rollup ID, and system caller. The selected version must support the verified application-failure
    behavior defined in this chapter. A later `EEZL2` version requires a Rollup0 hardfork.

!!! note "Separate EEZ predeploy namespace"
    Rollup0 reserves the
    `0xee50000000000000000000000000000000000xxx` namespace. The `0xee5` prefix is
    a visual mnemonic for EEZ.

    Rollup0 does not use addresses after the first 2,048 OP Stack predeploys. Those addresses remain
    inside the OP Stack `0x4200000000000000000000000000000000000xxx` namespace. Using a separate
    namespace avoids clashes with current and future OP Stack predeploys.

## 3.3 Inbound Protocol Transaction

Each accepted Ethereum-to-Rollup0 action is delivered in the Sync block by a deterministic,
unsigned EIP-2718 transaction. This protocol transaction is included in the normal Rollup0
transaction list. It is authorized by Rollup0 derivation rules rather than by a signature.

The protocol transaction:

- appears after the Sync block's pure-L2 transactions and after any earlier inbound protocol
  transaction;
- calls `executeIncomingCrossChainCall` on the `EEZL2` predeploy using the ABI selected for
  genesis;
- carries the exact destination, value, calldata, source, execution entries, and lookups selected
  by the accepted EEZ action;
- provides exactly the value delivered by that action under the selected value-source rule;
- has a normal transaction hash, transaction index, typed receipt, and trace position; and
- is reconstructed identically by composers, validators/provers, and followers.

A protocol transaction is valid only in its derived Sync-block position and only when every field
matches the accepted Ethereum trigger and EEZ action. A node MUST reject this transaction type
from its public transaction pool and from `eth_sendRawTransaction`.

The caller is the address reserved by EIP-4788:

```text
SYSTEM_ADDRESS = 0xfffffffffffffffffffffffffffffffffffffffe
```

The same address is stored as the `EEZL2` system caller and is the protocol transaction's EVM
sender. It has no protocol private key and needs no prefunded balance. The transaction has no nonce
field and does not change the system caller's account nonce.

The protocol transaction uses this EVM environment:

| Field | Rollup0 rule |
|---|---|
| `tx.origin` | `SYSTEM_ADDRESS` |
| initial `msg.sender` | `SYSTEM_ADDRESS` |
| chain ID | the Rollup0 chain ID |
| access list | empty |
| blob versioned hashes | empty |
| authorization list | empty |
| gas price | TO BE DISCUSSED with the protocol-transaction fee model |

An empty access list does not restrict state access. It means that no additional account or storage
slot is prewarmed; the selected Ethereum fork's ordinary warm-access rules still apply. Normal
Rollup0 transactions can use access lists under the transaction rules of that fork.

`BLOBHASH` returns zero for every index during the protocol transaction because its blob-hash list
is empty.
Other block-context opcodes, including `CHAINID`, `BASEFEE`, and `BLOBBASEFEE`, use the ordinary
Rollup0 block environment.

For now, each included Ethereum trigger transaction produces exactly one Rollup0 protocol
transaction. These transactions execute in canonical Ethereum trigger order. Each one has its own
transaction execution context. Persistent state from an earlier transaction remains visible, while
transient storage, warmed addresses, gas refunds, and other transaction-scoped state reset.

!!! note "TO BE DISCUSSED: protocol-transaction grouping"
    Rollup0 currently selects option 1. Clients must use this option unless a later specification
    changes it.

    1. **One protocol transaction per Ethereum trigger transaction.** This gives each action its
       own execution context, gas budget, and failure boundary. It also maps each action directly
       to the Ethereum transaction that receives its result. It has some repeated call overhead.
    2. **One protocol transaction for the complete accepted trigger prefix.** The L2 EEZ contract
       would loop over every action. This reduces call overhead, but the actions share one gas budget and
       transaction-scoped EVM state. One outer failure could prevent later actions.
    3. **One protocol transaction per EEZ execution entry.** This follows EEZ's internal data
       structure, but does not map cleanly to Ethereum transactions when EEZ contains nested or
       reentrant calls.

!!! note "TO BE DEFINED: protocol transaction envelope"
    The transaction representation is selected, but its type byte, byte-exact payload, unique
    source identifier, transaction hash vectors, and RPC extensions are not yet defined. The
    receipt uses the same EIP-2718 type as the transaction and contains the standard status,
    cumulative gas used, log bloom, and logs fields.

    The source identifier must distinguish two otherwise identical actions and prevent replay
    between domains. It can use only values known before the candidate is encoded and signed. The
    exact Ethereum chain, EEZ deployment, Rollup0 instance, protocol version, signed trigger
    transaction hash, and manifest-position fields included in that identifier are still to be
    selected. It cannot use the trigger's actual Ethereum inclusion block hash or transaction
    index, because the builder selects those after candidate construction.

    [Appendix F](F-system-transaction-design.md) explains why Rollup0 selected a protocol-derived
    transaction and discusses the `0x7e` compatibility question.

Protocol transactions and ordinary transactions use the same block gas pool. Rollup0 does not
reserve a separate system gas pool and does not impose a smaller per-transaction cap. Each inbound
protocol transaction encodes a gas limit equal to the gas remaining under the block's
`30,000,000` gas limit immediately before it starts.

Before EVM execution, Rollup0 charges the standard intrinsic gas for a non-creation transaction
under the active Ethereum fork. The calculation uses the complete calldata passed to `EEZL2`.
At Cancun, with the selected empty access list, it is:

```text
intrinsicGas = 21,000
             + 4  * zeroCalldataBytes
             + 16 * nonZeroCalldataBytes
```

The EVM frame receives the remaining gas after this charge. The intrinsic gas remains used when
the application or outer call reverts. A candidate is invalid if the block does not have enough
gas for the intrinsic charge. Intrinsic and EVM execution gas both contribute to the transaction
receipt and block `gasUsed`, and leave less gas for later transactions.

The proof or validator policy must execute the exact candidate and check this gas accounting before
the candidate can settle on Ethereum. A candidate is invalid if its cumulative gas use exceeds the
block gas limit or an outer `EEZL2` call has a protocol failure. Ethereum does not perform this
Rollup0 gas check itself.

An out-of-gas inside the target application can still be a valid application result when `EEZL2`
has enough gas to verify the expected failure and return the dedicated verified-failure error. The
corresponding Ethereum transaction then observes that precomputed failure. If `EEZL2` itself runs
out of gas, the candidate is invalid and cannot be used in a settlement bundle.

!!! note "TO BE DISCUSSED: shared block gas"
    Rollup0 currently uses one gas pool for ordinary and protocol-derived transactions. This keeps
    the block's execution bound and `gasUsed` accounting close to Ethereum. Pure-L2 transactions
    can leave less gas for synchronous execution, so composers must check the complete candidate
    before submission.

    A separate system gas pool would prevent pure-L2 traffic from consuming synchronous capacity,
    but would increase the maximum work in one block and require separate accounting. Unlimited
    execution is not an option because Ethereum does not meter the Rollup0 target's EVM execution.

Gas metering does not decide who pays for an inbound protocol transaction. It has no user signature
that authorizes ordinary fee deduction from an L2 payer. The system caller is also not prefunded
for an ordinary EIP-1559 upfront gas purchase.

!!! note "TO BE DISCUSSED: protocol-transaction fees"
    Rollup0 has not selected a production fee mechanism for synchronous execution.

    1. **Charge no L2 execution fee.** The call still consumes block gas. This is simple, but
       composers and infrastructure subsidize synchronous execution and have no protocol-level
       reimbursement.
    2. **Charge through the Ethereum trigger or settlement flow.** This can make the party
       requesting synchronous execution pay, but requires a quote, custody and refund rules, and a
       defined recipient.
    3. **Charge a Rollup0 account.** This resembles an ordinary user transaction, but the protocol
       transaction has no user signature identifying an authorized payer. Rollup0 would need a
       separate authorization and funding mechanism.
    4. **Charge the composer or relayer.** This can reimburse the network directly, but requires a
       funded protocol account or settlement bond and may discourage open candidate production.

    The final rule must define the payer, asset, price calculation, recipient, refund behavior, and
    the values returned by the EVM `GASPRICE` opcode and receipt `effectiveGasPrice`. It must not
    silently deduct the application call's `msg.value`.

    This is also a transaction-validity rule. Rollup0 must either bypass the ordinary fee-cap,
    upfront-balance, fee-deduction, and refund checks for this derived transaction type, or define
    the exact fee fields and funded account that satisfy them. Clients cannot infer this from the
    block's base fee.

The Sync block begins with an ordered pure-L2 transaction prefix. These transactions are fixed for
the candidate and execute regardless of which later Ethereum trigger transactions succeed. A Sync
block with no applied inbound action contains only this pure-L2 prefix.

When the target application succeeds, the `EEZL2` call returns normally after it verifies the
execution entry. The protocol transaction has receipt status `1`.

When the target application returns `success = false`, `EEZL2` first verifies that result, the exact
return or revert data, and the rolling hash. This includes `REVERT` and exceptional EVM failures
such as an out-of-gas inside the target call. `EEZL2` then reverts its own call with a dedicated
error. The provisional error is:

```solidity
error InboundApplicationReverted(bytes revertData);
```

The Rollup0 executor treats this error as a completed failed protocol transaction only when the
candidate expected that application failure. Its receipt has status `0`. The outer revert rolls
back all state changes, proxy creation, value movement, and logs from the transaction. Therefore
the state root after the failed action equals the state root before it. The transaction and receipt
roots still distinguish this action from a block that did not include it. The corresponding result
on Ethereum is an EEZ failed lookup with the same revert data.

Any other `EEZL2` revert, including an authorization error, malformed entry, hash mismatch,
unexpected application result, or out-of-gas in the outer `EEZL2` call, makes the candidate
block invalid.

!!! note "TO BE DISCUSSED: failed inbound calls"
    Rollup0 currently selects option 3. Clients must use this option unless a later specification
    changes it.

    1. **Let `executeIncomingCrossChainCall` return normally after a verified target revert.** This
       works with the current reference behavior, but temporary tables, proxy creation, and failed
       call value can remain in `EEZL2`. The full Rollup0 state root can change.
    2. **Have the Rollup0 executor discard a failed protocol transaction's state checkpoint.** This
       keeps the state root unchanged without changing `EEZL2`, but moves rollback rules into every
       execution client even though the EVM call returned successfully.
    3. **Make `EEZL2` return a dedicated verified-failure error.** The EVM performs the rollback,
       failed value returns to the protocol-transaction source, and clients can distinguish an
       expected application revert from a protocol failure. This requires the
       `eez-core-protocol` version selected for genesis to include the behavior.

    The exact error name and ABI remain open until the production `EEZL2` artifact is selected.

!!! note "TO BE DISCUSSED: protocol failures"
    Rollup0 currently selects option 1. Clients must use this option unless a later specification
    changes it.

    1. **Invalidate the candidate block.** Authorization failures, malformed inputs, verification
       mismatches, unexpected application outcomes, unconsumed execution data, and outer
       protocol-transaction failures make the complete candidate invalid.
    2. **Stop after the previous valid action.** This would shorten the processed prefix during
       Rollup0 execution, after the Ethereum bundle was selected. The resulting Rollup0 block could
       then disagree with Ethereum transactions already included in that bundle.
    3. **Convert the protocol error into an application failure.** This would let malformed
       protocol data use ordinary application-revert handling and could hide an invalid candidate.

    A composer may propose a shorter prefix before submission. Rollup0 execution does not shorten
    or repair a candidate after its settlement bundle has been selected.

Let `managerBalanceBefore` be the `EEZL2` balance immediately before a protocol transaction. The
balance after a successful call must equal `managerBalanceBefore`. A verified failed call reverts
its complete frame and therefore also restores `managerBalanceBefore`. A balance mismatch is a
protocol failure and invalidates the candidate.

The Rollup0 genesis sets the `EEZL2` balance to zero. Unsolicited ETH received later is not part of
the protocol's value supply and cannot fund an EEZ action.

!!! note "TO BE DISCUSSED: EEZL2 balance"
    Rollup0 currently selects option 1. Clients must use this option unless a later specification
    changes it.

    1. **Require balance neutrality for every protocol transaction.** The pre-call and post-call
       `EEZL2` balances must match. This prevents one action from leaving value for another while
       tolerating ETH that was transferred to the predeploy without using the EEZ protocol.
    2. **Require the absolute balance to remain zero.** This is simpler, but a forced ETH transfer
       could make future candidates invalid unless Rollup0 adds a sweep or balance-clearing rule.
    3. **Allow `EEZL2` to accumulate value.** This complicates native-asset backing and could let
       one action subsidize another.

For an inbound call with value `v`, Rollup0 opens a state checkpoint before crediting the system
caller. It then credits exactly `v` and calls `EEZL2` with `value = v`. The credit is not a fee or
block reward.

If the application call succeeds, the value moves through `EEZL2` according to the verified EEZ
action. The resulting increase in Rollup0 native value must be backed by the corresponding value
held on Ethereum. Any verified value movement out of Rollup0 is accounted for separately and can
offset that increase.

If the application call fails with the expected verified-failure error, the EVM revert returns
`v` to the system caller. Rollup0 then discards the checkpoint, including the exact credit. The
caller balance, native supply, and all application balances remain as they were before the call.
The failed receipt and the transaction's used gas remain part of the block, as for an ordinary
failed Ethereum transaction. A composer cannot choose `v`: it is bound to the accepted EEZ action
and checked by the proof or validator policy.

!!! note "TO BE DISCUSSED: protocol-transaction value source"
    Rollup0 currently selects option 1. Clients must use this option unless a later specification
    changes it.

    1. **Credit the system caller immediately before the call.** This preserves ordinary EVM
       `CALL` and `msg.value` behavior without a funded private key. A failed call removes the
       unused credit.
    2. **Prefund the system caller.** This avoids a protocol-level credit, but the reserve can run
       out and does not directly bind issued Rollup0 value to value held on Ethereum.
    3. **Create value inside a special EVM call.** This avoids a caller balance, but changes normal
       EVM value-transfer behavior and makes execution harder to reproduce with standard tooling.

    The exact Ethereum custody contract and complete backing invariant remain to be defined before
    production genesis.

## 3.4 Call Rules

The selected cross-network action uses `CALL`. It MAY carry value. If Rollup0 later selects the
cross-network `STATICCALL` extension, that call will use the EEZ lookup mechanism and MUST NOT
change state or carry value.

`DELEGATECALL` and `CALLCODE` to a cross-chain proxy are invalid. Their remote identity is
undefined under the caller's storage context.

---

*Next: [Chapter 4, Block Production and Headers](04-block-production.md).*
