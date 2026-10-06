# 3. EVM, Proxy, and Inbound Transactions

## 3.1 EVM Profile

Rollup0 executes an Ethereum-equivalent EVM. It adds no custom opcode or precompile. Cross-network
behavior is provided by contracts and protocol-derived transactions.

Rollup0 starts with the Osaka execution-layer rules of Ethereum's Fusaka network upgrade. Every
Ethereum execution fork through Osaka is active at genesis. Rollup0 adopts each later Ethereum
execution fork at that fork's Ethereum mainnet activation timestamp.

Rollup0 has no beacon chain. It keeps the post-Cancun header shape but does not execute the
EIP-4788 beacon-roots contract update. Chapter 4 fixes `parentBeaconBlockRoot` to zero.

!!! success "DECISION: Ethereum-aligned hardfork timestamps"
    If Ethereum mainnet activates an execution fork at Unix timestamp `T`, Rollup0 applies that
    fork's execution rules to every block with `timestamp >= T`. Rollup0 clients must publish and
    adopt an explicit chain-spec and client release that contains `T` before activation. The need
    for a release does not create a separate Rollup0 activation vote or permit a different
    timestamp.

    Rollup0 adopts execution-layer behavior only. Its explicit rules for the absence of a beacon
    chain, empty withdrawals and requests, `prevRandao`, and protocol transactions continue to
    apply. If a future Ethereum fork introduces another consensus-layer dependency, the Rollup0
    specification and clients must define its Rollup0 behavior before `T`.

Rollup0 activates the
[EIP-2935 block-hash history contract](https://eips.ethereum.org/EIPS/eip-2935) at genesis. Before
the transactions in every block after genesis, the executor performs the standard EIP-2935 system
operation and stores the parent block hash. The call uses
`0xfffffffffffffffffffffffffffffffffffffffe` as its caller, transfers no value, and does not
consume gas from the Rollup0 block gas pool. The genesis state contains the standard history
contract at `0x0000F90827F1C53a10cb7A02335B175320002935`.

The EIP-2935 write is part of the state transition. Consequently, every non-genesis Rollup0 block
changes the state root even when it contains no transaction.

Rollup0 does not support ordinary EIP-4844 blob transactions. A node must reject transaction type
`0x03` from its transaction pool and `eth_sendRawTransaction`. A Rollup0 block that contains a blob
transaction or a transaction with a non-empty blob-versioned-hash list is invalid.

Rollup0 retains the post-Cancun execution header fields. The genesis values of `blobGasUsed` and
`excessBlobGas` are zero. Every later block has `blobGasUsed = 0` and derives `excessBlobGas` from
its parent under the active Ethereum execution fork. It therefore remains zero. `BLOBBASEFEE`
returns the standard value for that header, and `BLOBHASH` returns zero for every index in every
valid Rollup0 transaction.

This rule does not affect Rollup0 data availability. The Ethereum settlement transaction publishes
Rollup0 data in blobs on L1; that transaction is not part of a Rollup0 block.

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

!!! note "GENESIS PARAMETER: EEZL2 artifact"
    Rollup0 will use the latest `eez-core-protocol` `EEZL2` version selected when the production
    genesis is finalized. The final genesis specification must state its bytecode hash, Rollup0
    rollup ID, and system caller. A later `EEZL2` version requires a Rollup0 hardfork.

!!! note "Separate EEZ predeploy namespace"
    Rollup0 reserves the
    `0xee50000000000000000000000000000000000xxx` namespace. The `0xee5` prefix is
    a visual mnemonic for EEZ.

    Rollup0 does not use addresses after the first 2,048 OP Stack predeploys. Those addresses remain
    inside the OP Stack `0x4200000000000000000000000000000000000xxx` namespace. Using a separate
    namespace avoids clashes with current and future OP Stack predeploys.

## 3.3 Inbound Protocol Transaction

Each successful Ethereum-to-Rollup0 action is delivered in the Sync block by a deterministic,
unsigned EIP-2718 transaction. This protocol transaction is included in the normal Rollup0
transaction list. It is authorized by Rollup0 derivation rules rather than by a signature. A
failed action uses an EEZ failed lookup on Ethereum and does not create a Rollup0 transaction.

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
field and does not change the system caller's account nonce. The composer derives the transaction
bytes. Validators sign the candidate, not this transaction; no composer, relayer, or separate
service signs on behalf of `SYSTEM_ADDRESS`.

The protocol transaction uses this EVM environment:

| Field | Rollup0 rule |
|---|---|
| `tx.origin` | `SYSTEM_ADDRESS` |
| `EEZL2` frame `msg.sender` | `SYSTEM_ADDRESS` |
| chain ID | the Rollup0 chain ID |
| access list | empty |
| blob versioned hashes | empty |
| authorization list | empty |
| gas price | `0` |

The protocol transaction's sender is not the original caller on Ethereum. The following identities
have different purposes:

- the envelope's `chainId` is the Rollup0 EVM chain ID;
- `sourceRollup` in the `EEZL2` calldata is the source network's EEZ rollup ID; the settlement L1
  uses the reserved value `0`; and
- the transaction's source identifier binds the settlement chain ID and EEZ deployment. Candidate
  validation uses these values to separate the L2 transaction identity between settlement domains,
  even though they do not need separate EVM execution fields.

`sourceRollup` is an EEZ network identifier, not an EVM chain ID. For the initial Ethereum-to-
Rollup0 path, the settlement chain ID is the Ethereum chain ID. A development deployment uses its
configured settlement chain ID instead, such as Chiado's. This value is included in the
source-identifier calculation. It SHOULD NOT also be encoded as a second top-level transaction
field. Duplicating a fixed value would add a new mismatch case without changing execution. An RPC
implementation MAY expose it as derived metadata. For a future L2 source, `sourceRollup` is the
identity used by EEZ; its EVM chain ID does not replace that registry ID.

The inbound call has the following caller path:

```text
SYSTEM_ADDRESS
    -> EEZL2.executeIncomingCrossChainCall(..., sourceAddress, sourceRollup, ...)
    -> proxy(sourceAddress, sourceRollup).executeOnBehalf(destination, data)
    -> destination
```

| EVM frame | `msg.sender` | `tx.origin` |
|---|---|---|
| `EEZL2.executeIncomingCrossChainCall` | `SYSTEM_ADDRESS` | `SYSTEM_ADDRESS` |
| `proxy(sourceAddress, sourceRollup).executeOnBehalf` | `EEZL2` | `SYSTEM_ADDRESS` |
| application destination | `proxy(sourceAddress, sourceRollup)` | `SYSTEM_ADDRESS` |

The protocol transaction is not only a marker for an already-applied state change. It is the EVM
transaction that makes `EEZL2` load the verified execution data and run the application call. Its
execution consumes block gas and produces the application state changes, logs, trace, and receipt.
The EEZ calldata and source proxy provide the cross-chain caller identity during that execution.

The `sourceAddress` is the address whose call reached the cross-chain proxy on the source network.
It is the source-side `msg.sender`, which can be a user account or a contract. It is not the
source-side `tx.origin`. The destination observes the deterministic
`proxy(sourceAddress, sourceRollup)` as `msg.sender`; `tx.origin` remains `SYSTEM_ADDRESS` for the
complete Rollup0 transaction. Applications that need an end-user identity behind a source contract
must carry and authenticate that identity in application calldata. Applications MUST authenticate
the remote caller through the expected proxy and MUST NOT treat `tx.origin` as the remote caller.

The full `sourceAddress` and `sourceRollup` values are already present in the `EEZL2` calldata and
execution entry, both of which the transaction root commits. The envelope must not duplicate them.
Candidate validation checks that the calldata, execution entry, Ethereum trigger, and independently
replayed call all agree.

An empty access list does not restrict state access. It means that no additional account or storage
slot is prewarmed; the selected Ethereum fork's ordinary warm-access rules still apply. Normal
Rollup0 transactions can use access lists under the transaction rules of that fork.

`BLOBHASH` returns zero for every index during the protocol transaction because its blob-hash list
is empty, as it is for every valid Rollup0 transaction.
Other block-context opcodes, including `CHAINID`, `BASEFEE`, and `BLOBBASEFEE`, use the ordinary
Rollup0 block environment.

For now, each included Ethereum trigger whose Rollup0 action succeeds produces exactly one Rollup0
protocol transaction. Failed actions produce none. The protocol transactions execute in canonical
Ethereum trigger order. Each one has its own transaction execution context. Persistent state from
an earlier transaction remains visible, while transient storage, warmed addresses, gas refunds, and
other transaction-scoped state reset.

!!! success "DECISION: one protocol transaction per successful trigger"
    Rollup0 selects option 1. Clients must use this option unless a later specification changes it.

    1. **One protocol transaction per successful Ethereum trigger.** This gives each successful
       action its own execution context and gas budget. It also maps each delivered state transition
       directly to the Ethereum transaction that receives its result. It has some repeated call
       overhead.
    2. **One protocol transaction for the complete accepted trigger prefix.** The L2 EEZ contract
       would loop over every action. This reduces call overhead, but the actions share one gas budget and
       transaction-scoped EVM state. One outer failure could prevent later actions.
    3. **One protocol transaction per EEZ execution entry.** This follows EEZ's internal data
       structure, but does not map cleanly to Ethereum transactions when EEZ contains nested or
       reentrant calls.

!!! success "DECISION: type `0x45` RLP envelope"
    Envelope version `0` uses transaction type `0x45`, the ASCII byte for `E`, and the exact RLP
    payload defined in Appendix F. Its transaction hash is the Keccak-256 hash of the complete typed
    transaction bytes. The matching type-`0x45` receipt contains only the standard status,
    cumulative gas used, log bloom, and logs fields.

!!! danger "PRODUCTION BLOCKER: transaction conformance"
    Rollup0 must still publish transaction, receipt, execution, RPC, and invalid-input conformance
    vectors for the fixed Appendix F schema. The blob format must carry the authenticated
    non-derived inputs from which every type-`0x45` field and the exact serialized envelope are
    reconstructed. It must not duplicate the derived envelope bytes.

!!! success "DECISION: protocol transaction source identity"
    The `sourceHash` calculation in Appendix F is fixed for envelope version `0`. It binds the
    settlement chain ID, L1 EEZ address, EEZ Rollup0 ID, Rollup0 chain ID, envelope version,
    intended settlement timestamp, known Ethereum parent hash, action-manifest index, and EEZ
    cross-chain call hash. It cannot use the actual L1 child block hash, transaction index, or log
    index because the builder selects those after candidate construction.

    The calculation intentionally omits the outer Ethereum transaction hash and nonce. Rollup0
    identifies the action by its ordered call, not by the exact transaction carrying it. Every
    validator and follower must recompute `sourceHash` and reject a mismatch.

    This source identifier does not replace the candidate domain folded into the EEZ
    `publicInputsHash`. Chapter 8 and Appendix D define that separate settlement-signature domain.

    The current proxy observes the call hash, and the successful EEZ queue assigns a match to its
    next ordered position. A different outer transaction that produces the next expected call is
    intentionally the same Rollup0 action. Chapter 7 defines the resulting prefix rule.

    [Appendix F](F-system-transaction-design.md) explains why Rollup0 selected a protocol-derived
    transaction, defines its envelope, and compares it with OP's `0x7e` deposit.

Protocol transactions and ordinary transactions use the same block gas pool. Rollup0 does not
reserve a separate system gas pool. Under the Fusaka rules, every transaction has the EIP-7825
maximum gas limit of `16,777,216` (`2^24`). Each inbound protocol transaction therefore encodes:

```text
gasLimit = min(gas remaining in the block, 16,777,216)
```

The numeric `16,777,216` cap is frozen for inbound envelope version `0`, even if a later Ethereum
fork changes its ordinary-transaction cap. Changing this derivation changes the typed transaction
bytes, transaction root, receipt context, and `H[k]`; it therefore requires a new inbound envelope
version and Rollup0 hardfork. Ordinary signed transactions follow the cap of the active Ethereum
execution fork.

Before EVM execution, Rollup0 charges the standard intrinsic gas for a non-creation transaction
under the active Ethereum fork. The calculation uses the complete calldata passed to `EEZL2`.
With the selected empty access list, the Osaka values are:

```text
calldataTokens = zeroCalldataBytes + 4 * nonZeroCalldataBytes
intrinsicGas   = 21,000 + 4  * calldataTokens
calldataFloor  = 21,000 + 10 * calldataTokens
```

The gas limit must cover both `intrinsicGas` and `calldataFloor`. The EVM frame receives the gas
remaining after the intrinsic charge. Under EIP-7623, the final transaction gas used is:

```text
gasUsed = 21,000 + max(
    4 * calldataTokens + executionGasUsed,
    10 * calldataTokens
)
```

Unlike the envelope's numeric gas-limit cap, intrinsic-gas and calldata-floor semantics follow the
active Ethereum execution fork. Chapter 3.1 requires Rollup0 to specify any new consensus-layer
dependency before adopting a later fork; a client MUST NOT keep the displayed Osaka formula if
that active fork changes it.

This gas remains used when the successful action catches an internal application revert. A
candidate is invalid if an envelope-version-`0` transaction exceeds its fixed `16,777,216` cap,
its outer `EEZL2` call reverts, or the block does not have enough gas for the required intrinsic
and calldata-floor charges.
Intrinsic and EVM execution gas contribute to the transaction receipt and block `gasUsed`, and
leave less gas for later transactions.

The proof or validator policy must execute the exact candidate and check this gas accounting before
the candidate can settle on Ethereum. A candidate is invalid if its cumulative gas use exceeds the
block gas limit or an outer `EEZL2` call has a protocol failure. Ethereum does not perform this
Rollup0 gas check itself.

An out-of-gas in the simulated target application is a failed action. It is handled by an EEZ
failed lookup on Ethereum and does not produce a Rollup0 protocol transaction. An out-of-gas in a
protocol transaction that was expected to succeed makes the candidate invalid.

!!! success "DECISION: shared block gas"
    Rollup0 uses one gas pool for ordinary and protocol-derived transactions. This keeps
    the block's execution bound and `gasUsed` accounting close to Ethereum. Pure-L2 transactions
    can leave less gas for synchronous execution, so composers must check the complete candidate
    before submission.

    A separate system gas pool would prevent pure-L2 traffic from consuming synchronous capacity,
    but would increase the maximum work in one block and require separate accounting. Unlimited
    execution is not an option because Ethereum does not meter the Rollup0 target's EVM execution.

Gas metering is separate from payment. The inbound protocol transaction has no user signature that
authorizes a fee deduction, and the system caller is not prefunded for an ordinary EIP-1559 upfront
gas purchase.

!!! success "DECISION: no V1 protocol-transaction fee"
    Type-`0x45` consumes the common block gas pool and contributes its exact intrinsic, calldata-
    floor, and execution gas to the receipt and block `gasUsed`. It pays no L2 fee. Clients MUST
    skip the ordinary fee-cap, signed-payer upfront-balance, fee-deduction, and refund checks for
    this type. They MUST NOT burn a fee, credit the block beneficiary, or deduct from the action's
    `msg.value`.

    The EVM transaction gas price is zero, so `GASPRICE` returns `0`. JSON-RPC reports
    `gasPrice = 0` for the transaction and `effectiveGasPrice = 0` for its receipt. Gas consumption
    still affects the block's `gasUsed` and therefore the next block's EIP-1559 base fee.

    A failed inbound action creates no protocol transaction and has no Rollup0 fee. Rollup0 also
    defines no reimbursement for its simulation or validation. Adding a payer, fee fields, or a
    protocol-level debit requires a later envelope version and a Rollup0 hardfork.

The Sync block begins with an ordered pure-L2 transaction prefix. These transactions are fixed for
the candidate and execute regardless of which later Ethereum trigger transactions succeed. The
block then contains one protocol transaction for each successful Rollup0 action, in Ethereum
trigger order. A Sync block with no successful inbound action contains only the pure-L2 prefix.

When the target application succeeds, the `EEZL2` call returns normally after it verifies the
execution entry. The protocol transaction has receipt status `1`.

When the simulated Rollup0 application returns `success = false`, the L1 EEZ batch contains one
failed lookup with the exact action hash, pre-action block-hash commitment, and revert data. The
proof or validator signatures bind that lookup and the action manifest. No Rollup0 protocol
transaction is created, no `EEZL2` table is loaded, and no L2 gas, nonce, receipt, log, value credit,
or state change is recorded. This includes `REVERT` and exceptional EVM failures such as an
out-of-gas in the target call.

The failed lookup makes the Ethereum proxy call revert with the verified application data. If the
outer Ethereum transaction catches that revert and succeeds, the action is processed. That
transaction must be the final trigger in the candidate. If the outer transaction reverts, that
transaction leaves no retained EEZ effect and does not advance the selected successful prefix.

An authorization error, malformed entry, hash mismatch, unexpected application result, or
out-of-gas in a protocol transaction that was expected to succeed makes the candidate invalid.

!!! success "DECISION: protocol failures invalidate the candidate"
    Rollup0 selects option 1. Clients must use this option unless a later specification changes it.

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
balance after the successful call must equal `managerBalanceBefore`. A balance mismatch is a
protocol failure and invalidates the candidate. Failed actions do not call `EEZL2`.

The Rollup0 genesis sets the `EEZL2` balance to zero. Unsolicited ETH received later is not part of
the protocol's value supply and cannot fund an EEZ action.

!!! success "DECISION: per-transaction EEZL2 balance neutrality"
    Rollup0 selects option 1. Clients must use this option unless a later specification changes it.

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

Any balance already held by `SYSTEM_ADDRESS` is ignored when funding the action. The protocol
credits exactly `v` regardless of that balance, and the ordinary value transfer debits exactly
`v`. Rollup0 imposes no pre-call or post-call zero-balance invariant on `SYSTEM_ADDRESS`: value can
be sent there through ordinary EVM behavior, but that residual value cannot fund a later action.

If the application call succeeds, the value moves through `EEZL2` according to the verified EEZ
action. The resulting increase in Rollup0 native value must be backed by the corresponding value
held on Ethereum. Any verified value movement out of Rollup0 is accounted for separately and can
offset that increase.

If the simulated application call fails, Rollup0 does not open the checkpoint, credit the system
caller, or create a protocol transaction. The failed proxy call on Ethereum rolls back its value
transfer. Rollup0 balances and native supply remain unchanged. A composer cannot choose `v`: it is
bound to the failed lookup and checked by the proof or validator policy.

!!! success "DECISION: temporary protocol credit"
    Rollup0 selects option 1. Clients must use this option unless a later specification changes it.

    1. **Credit the system caller immediately before a successful call.** This preserves ordinary
       EVM `CALL` and `msg.value` behavior without a funded private key. Failed actions never reach
       this step.
    2. **Prefund the system caller.** This avoids a protocol-level credit, but the reserve can run
       out and does not directly bind issued Rollup0 value to value held on Ethereum.
    3. **Create value inside a special EVM call.** This avoids a caller balance, but changes normal
       EVM value-transfer behavior and makes execution harder to reproduce with standard tooling.

    Initial Rollup0 uses the existing EEZ pooled-custody contract and its per-rollup
    `etherBalance`. Chapter 5 defines the selected backing rule. A dedicated Rollup0 vault remains
    under discussion for a later version.

## 3.4 Call Rules

The selected cross-network action uses `CALL`. It MAY carry value. If Rollup0 later selects the
cross-network `STATICCALL` extension, that call will use the EEZ lookup mechanism and MUST NOT
change state or carry value.

`DELEGATECALL` and `CALLCODE` to a cross-chain proxy are invalid. Their remote identity is
undefined under the caller's storage context.

---

*Next: [Chapter 4, Block Production and Headers](04-block-production.md).*
