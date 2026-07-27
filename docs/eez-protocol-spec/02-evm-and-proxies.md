# 2. EVM and Cross-Chain Proxies

## 2.1 EVM target

EEZ executes on an **Ethereum-equivalent EVM at the Cancun fork**: no custom opcodes, no custom
precompiles, the standard gas schedule and transaction types. Cross-chain behavior is layered on
top via contracts and an off-chain simulation step, never via EVM changes.

## 2.2 Cross-chain proxy

A **cross-chain proxy** is the local stand-in for a remote contract. For a contract `A` on rollup
`R`, the manager deploys, via CREATE2, a deterministic local proxy `P = proxy(A, R)`:

```text
salt          = keccak256(abi.encodePacked(R, A))
bytecodeHash  = keccak256(CrossChainProxy.creationCode ‖ abi.encode(manager, A, R))
P             = address(keccak256(0xff ‖ manager ‖ salt ‖ bytecodeHash)[12:])
```

The `proxy(A, R)` notation lists the address first for readability; the **salt encodes `R`
(rollupId) first**, as shown above. The salt carries no chain or domain term, so the same `(A, R)`
maps to the same `P` on any manager sharing the deployer address and proxy bytecode.

Calling `P` *is* calling `A`-on-`R`: the proxy forwards the call into the manager's
`executeCrossChainCall`, which resolves it against the proven execution tables. The manager records
each proxy in `authorizedProxies : address → (A, R)` at storage slot `0`; a zero entry means "not
a proxy." The proxy detects a **static** call context and routes it to the read-only resolution
path.

## 2.3 Cross-chain call hash

Every cross-chain call is identified by one 32-byte hash over its six identity fields:

```text
crossChainCallHash = keccak256(abi.encode(
    targetRollupId, targetAddress, value, data, sourceAddress, sourceRollupId))
```

The same value appears as `ExecutionEntry.proxyEntryHash` and
`LookupCall.crossChainCallHash`. It is the join key between what the proxy observes at replay and
what the batch precomputed.

## 2.4 Inbound delivery

The L2 inbound delivery entry point is:

```solidity
function executeIncomingCrossChainCall(
    address destination,
    uint256 value,
    bytes calldata data,
    address sourceAddress,
    uint256 sourceRollup,
    ExecutionEntry[] calldata entries,
    LookupCall[] calldata lookupCalls
) external payable onlySystemAddress returns (bytes memory result);
```

It:

- is callable only by `SYSTEM_ADDRESS`;
- reverts `EmptyEntries` if `entries.length == 0`;
- reverts `ValueMismatch` unless `msg.value == value`;
- atomically replaces the execution table;
- computes the call hash from `ROLLUP_ID`, `destination`, `value`, `data`, `sourceAddress`, and
  `sourceRollup`;
- reverts `EntryHashMismatch` unless `entries[0].proxyEntryHash` equals that hash;
- drives `entries[0]` through the flat call processor;
- checks the rolling hash and both call-consumption cursors;
- sets `executionIndex = 1`; and
- returns `entries[0].returnData`.

It emits `IncomingCrossChainCallExecuted`.

The transaction envelope that invokes this function is not part of EEZ.

## 2.5 Call-scheme rules

Cross-chain interactions must be provable, so each EVM call scheme maps to a defined outcome when
its target is a registered proxy:

| Scheme | Cross-chain semantics |
|---|---|
| **`CALL`** | A state-mutating cross-chain call; recorded as a call within an execution entry; may carry `value`. |
| **`STATICCALL`** | A **read-only** cross-chain call: a proven read recorded as a lookup, resolved without mutating state; `value` forced to `0`. |
| **`DELEGATECALL` / `CALLCODE`** | **Forbidden** — the proxy's cross-chain identity is undefined under the caller's storage context; MUST revert. |

Only `CALL` may trigger a state-mutating cross-chain dispatch. A `STATICCALL` to a proxy is a
proven read, recorded as a lookup entry in the execution table, and MUST NOT mutate state.

---

*Next: [Execution Model](03-execution-model.md).*
