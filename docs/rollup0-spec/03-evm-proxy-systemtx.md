# 3. EVM, Proxy, and System Transactions

## 3.1 EVM Profile

Rollup0 executes an Ethereum-equivalent EVM at the Cancun fork. It adds no custom opcode or
precompile. Cross-network behavior is provided by contracts and system transactions.

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

## 3.3 Inbound System Transaction

An accepted Ethereum-to-Rollup0 action is delivered in the Sync block by an unsigned,
deterministic system transaction. The transaction:

- is placed before every other Sync-block transaction;
- originates from the reserved `SYSTEM_ADDRESS`;
- calls `executeIncomingCrossChainCall` on the L2 EEZ manager;
- carries the exact destination, value, calldata, source, execution entries, and lookups selected
  by the accepted EEZ action;
- mints exactly the value delivered by that action and requires the call value to equal it;
- uses the next system nonce; and
- is reconstructed identically by composers, validators/provers, and followers.

The draft reserves transaction type `0x7e` for this operation. The complete envelope, gas fields,
nonce rule, and value source are not yet defined. They must be specified before independent
clients can produce byte-identical Sync blocks.

The Sync block contains no ordinary user transaction in this draft. A Sync block with no inbound
action contains no system transaction.

## 3.4 Call Rules

The selected cross-network action uses `CALL`. It MAY carry value. A read-only cross-network call
uses the EEZ lookup mechanism and MUST NOT change state or carry value.

`DELEGATECALL` and `CALLCODE` to a cross-chain proxy are invalid. Their remote identity is
undefined under the caller's storage context.

---

*Next: [Chapter 4, Block Production and Headers](04-block-production.md).*
