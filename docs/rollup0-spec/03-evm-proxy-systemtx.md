# 3. EVM, Proxy, and System Calls

## 3.1 EVM Profile

Rollup0 executes an Ethereum-equivalent EVM. It adds no custom opcode or precompile. Cross-network
behavior is provided by contracts and protocol-injected system calls.

!!! note "TO BE DEFINED"
    Rollup0 will target the latest Ethereum execution fork selected for its production genesis. The
    exact fork and any later activation schedule are not yet selected. The initial fork must include
    the Cancun features used by EEZ and Rollup0.

## 3.2 EEZ Proxies

Rollup0 uses the EEZ cross-chain proxy mechanism without changing its address derivation, call
hash, authorization, or execution behavior. Those rules are defined by
[EEZ EVM Contracts and Proxies](../eez-protocol-spec/02-evm-and-proxies.md), with vectors in
[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md).

The Rollup0 draft reserves these predeploy addresses:

| Address | Purpose |
|---|---|
| `0x4200000000000000000000000000000000000007` | L2 EEZ manager |
| `0x4200000000000000000000000000000000000008` | Bridge receiver |

The production genesis must bind exact bytecode to both addresses.

## 3.3 Inbound System Call

An accepted Ethereum-to-Rollup0 action is delivered in the Sync block by a deterministic,
EIP-4788-style system call. This is a protocol-injected EVM call, not a signed or unsigned
transaction. The system call:

- is placed after the Sync block's pure-L2 transactions and after any earlier synchronous system
  call;
- calls `executeIncomingCrossChainCall` on the L2 EEZ manager;
- carries the exact destination, value, calldata, source, execution entries, and lookups selected
  by the accepted EEZ action;
- provides exactly the value delivered by that action under the selected value-source rule; and
- is reconstructed identically by composers, validators/provers, and followers.

!!! note "TO BE DEFINED"
    The system-call mechanism is selected. Its exact caller address, gas limit, value source, and
    commitment of results and logs are not yet defined. Each call must start with a clean
    transaction-like transient execution context, even though it is not a transaction.

!!! info "System call compared with the recovered `0x7e` transaction"
    Rollup0 uses the system-call design.

    - The selected system call needs no private key, signature, nonce, fee, or transaction-envelope
      rule. Like EIP-4788, it is injected by block execution rather than included in the
      transaction list.
    - Because it is not a transaction, it has no standard transaction hash or receipt. Rollup0 must
      define how its application logs, gas use, and result are committed and exposed to RPC,
      explorers, and indexers.
    - The block header must commit to the ordered system calls and their results. Otherwise two
      prefixes with the same state root could have the same block hash. The exact commitment is
      still to be defined.
    - The recovered draft's `0x7e` proposal would place an unsigned typed transaction in the block
      body. It would naturally have a transaction-root entry, receipt, logs, and transaction
      ordering. It would also require custom transaction decoding, validity, authorization, and RPC
      rules in every Rollup0 execution client.

    The `0x7e` proposal is not part of Rollup0.

The Sync block begins with an ordered pure-L2 transaction prefix. These transactions are fixed for
the candidate and execute regardless of which later Ethereum trigger transactions succeed. A Sync
block with no applied inbound action contains only this pure-L2 prefix and any mandatory
block-level processing selected by the final system-call rules.

The protocol-injected call must complete even when the target application call reverts. It captures
the failure and revert data for the block commitment, while the target's state changes, value
transfer, and logs are rolled back. The system call must not leave other persistent L2 state changes
for that failed action. Its corresponding L1 result is represented by an EEZ failed lookup.

## 3.4 Call Rules

The selected cross-network action uses `CALL`. It MAY carry value. If Rollup0 later selects the
cross-network `STATICCALL` extension, that call will use the EEZ lookup mechanism and MUST NOT
change state or carry value.

`DELEGATECALL` and `CALLCODE` to a cross-chain proxy are invalid. Their remote identity is
undefined under the caller's storage context.

---

*Next: [Chapter 4, Block Production and Headers](04-block-production.md).*
