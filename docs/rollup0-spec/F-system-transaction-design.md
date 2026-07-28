# Appendix F. Inbound Transaction Design

This appendix explains why Rollup0 records inbound EEZ execution as protocol-derived
transactions. It is informative; Chapters 3 through 5 define the selected behavior.

The representation needed an explicit protocol decision because it affects:

- which data the block header commits;
- how independent clients reconstruct and execute a block;
- how gas and transaction order are recorded;
- whether application logs have normal transaction hashes and indexes;
- whether receipts, traces, explorers, and indexers use standard Ethereum data; and
- how the block is transported, stored, removed after a reorganization, and replayed.

These rules cannot be left to each client. Two clients that represent the same inbound action in
different ways calculate different block hashes.

## F.1 Selected Design

Each accepted Ethereum trigger produces one unsigned, protocol-derived
[EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) transaction in the Rollup0 Sync block. The
transaction appears after the pure-L2 prefix and after any earlier protocol transaction.

Derivation authorizes the transaction. A user does not sign it, it has no nonce, and a node does
not accept it through the public transaction pool. Once derived, it occupies an ordinary position
in the block's transaction list and has a matching typed receipt.

This gives every inbound action:

- a transaction hash and transaction index;
- a receipt status and cumulative gas value;
- normal receipt logs and log indexes;
- a normal trace position;
- inclusion in the transaction and receipt roots; and
- the ordinary Rollup0 reorganization and history behavior.

Ordinary signed user transactions do not change. Wallets do not construct or submit the new
transaction type.

## F.2 Alternatives Considered

Rollup0 considered two block representations:

| Question | Out-of-band protocol call | Protocol-derived transaction |
|---|---|---|
| Block input commitment | separate record and header commitment | normal transaction root |
| Result commitment | separate result format | normal receipt and state roots |
| Application logs | custom log identity and APIs | normal receipt logs |
| Gas accounting | separate record and receipt relationship | normal cumulative receipt gas |
| Tracing | custom call identifier | transaction hash and index |
| Block transport | custom sidecar or body extension | normal transaction list |
| Client support | second execution and RPC path | custom transaction type across the client |

An out-of-band call resembles the fixed protocol operation used by
[EIP-4788](https://eips.ethereum.org/EIPS/eip-4788). That approach is suitable for a small,
fixed state update that does not need application receipts or event indexing.

Inbound Rollup0 execution is different. It can run arbitrary application code, transfer value,
consume substantial gas, emit logs, and return success or failure. An out-of-band design would
therefore need its own record, receipt, log-index, trace, storage, and RPC rules. If its logs were
omitted from `eth_getLogs`, applications would miss them. If Rollup0 added synthetic transaction
hashes to those logs, a later transaction lookup would refer to an item that was not in the
transaction root.

The protocol-derived transaction requires more than a decoder. Execution clients must support the
type in their block and receipt structures, encoding, storage, validation, block-building
interface, RPC conversion, tracing, and block propagation. It still avoids a separate execution
and receipt model. Rollup0 selected this option because inbound EEZ execution behaves like
application execution rather than fixed block maintenance.

## F.3 Exact Envelope

!!! note "TO BE DISCUSSED: transaction type and encoding"
    The transaction model is selected. The byte-exact envelope is not.

    1. **Use the OP deposit `0x7e` wire format.** OP-aware libraries can already decode its
       `sourceHash`, `from`, `to`, `mint`, `value`, `gas`, `isSystemTx`, and `data` fields. Rollup0
       would set `isSystemTx` to false because the transaction uses the common block gas pool.
       Several fields closely match Rollup0's needs. Rollup0 would still use its own derivation,
       failure, fee, and value rules, so wire compatibility would not mean complete OP client,
       RPC, or receipt compatibility.
    2. **Define a Rollup0-specific EIP-2718 type.** This can include only the required fields and
       state Rollup0's behavior without suggesting OP compatibility. Execution clients and raw
       block tools must support the new type throughout their transaction and receipt handling.

    Rollup0 must not use `0x7e` with an incompatible byte layout. OP-aware software could otherwise
    accept the type byte and decode the remaining fields incorrectly.

    The final choice must define:

    - the type byte and payload encoding;
    - the unique source identifier and its domain separation;
    - the exact sender, recipient, value, gas-limit, and calldata fields;
    - transaction-hash and receipt-encoding vectors;
    - any additional JSON-RPC fields;
    - transaction-pool and `eth_sendRawTransaction` rejection; and
    - how blobs carry the exact transaction bytes and authenticated origin data.

The source identifier must distinguish otherwise identical actions without relying on a system
account nonce. It also needs enough domain information to prevent an action from being reused
between settlement chains, EEZ deployments, Rollup0 instances, or protocol versions.

!!! note "TO BE DISCUSSED: source identity"
    The source identifier is part of the transaction bytes, transaction root, blob data, and signed
    candidate. It can contain only values known before Ethereum inclusion. The trigger's actual
    inclusion block hash and transaction index are not available yet.

    A stable identifier can bind the Ethereum chain ID, EEZ address, Rollup0 ID, protocol version,
    signed trigger transaction hash, and trigger ordinal in the candidate manifest. This permits
    the same candidate to be retried after non-inclusion.

    Adding an intended Ethereum settlement slot or parent can restrict replay further, but a retry
    for a later slot would require new transaction bytes and new validator signatures. The team must
    select the exact retry and domain-binding rule together.

## F.4 Value and Failure

An inbound action can carry value even though the system caller has no prefunded balance. Rollup0
therefore opens a state checkpoint before crediting the exact value and executing the `EEZL2`
call. On success, the value moves according to the verified EEZ action and the checkpoint is
committed. On a verified application failure, the checkpoint, transaction effects, and temporary
credit all roll back. The failed receipt and used-gas accounting remain.

This differs from the OP deposit execution rule, where the `mint` operation occurs before the
reverting EVM transition and can remain after a failed deposit. Reusing the OP wire format would
not make that behavior suitable for Rollup0.

A verified application failure produces a typed receipt with status `0`. An unexpected outer
`EEZL2` error is a protocol failure and invalidates the complete candidate; it is not accepted as
another failed transaction. Validators and followers must therefore re-execute the transaction and
classify its exact result. The receipt commits the failure status and gas use, but, like an Ethereum
receipt, does not contain return or revert data. EEZ execution data commits those bytes.

!!! note "TO BE DISCUSSED: fee fields"
    The selected representation does not decide who pays for synchronous execution. The final
    envelope and RPC rules must define any fee fields, the payer and recipient, refund behavior,
    `GASPRICE`, and receipt `effectiveGasPrice`.

    This choice also changes transaction validity. With a nonzero base fee and an unprefunded
    system caller, Rollup0 must either bypass the ordinary EIP-1559 fee-cap, upfront-balance,
    deduction, and refund checks for protocol transactions, or define fields and funding that
    satisfy those checks.

## F.5 Header and Identity Consequences

A separate `systemCallsHash` is not needed. The transaction root commits each protocol
transaction's exact bytes and position. The receipt root commits status, cumulative gas, bloom, and
logs. The state root commits persistent execution effects. Rollup0 therefore fixes
`parentBeaconBlockRoot` to zero and does not create a duplicate commitment.

A unique protocol-transaction hash also does not fix the EEZ duplicate-call problem by itself. The
current EEZ call identity does not include the originating Ethereum transaction hash. Rollup0 must
still either make that origin available to EEZ execution or reject duplicate top-level call hashes
within one candidate, as discussed in Chapter 7.

---

*This is the final appendix.*
