# 3. EVM, Cross-Chain Proxy & System Transaction

## 3.1 EVM target

The L2 executes an **Ethereum-equivalent EVM at the Cancun fork**: no custom opcodes, no custom
precompiles, the standard gas schedule and transaction types. Cross-chain behavior is layered on
top via genesis-predeployed contracts, ordinary transactions, and an off-chain simulation step —
never via EVM changes. To any tool, the L2 is "Ethereum, plus contracts."

Genesis predeploys:

| Address | Contract |
|---|---|
| `0x4200…0007` | `EEZL2` — the L2 cross-chain manager + proxy factory; carries `SYSTEM_ADDRESS` as an immutable. |
| `0x4200…0008` | L2 `BridgeReceiver`. |

## 3.2 Cross-chain proxy

A **cross-chain proxy** is the local stand-in for a remote contract. For a contract `A` on rollup
`R`, the manager deploys (via CREATE2) a deterministic local proxy `P = proxy(A, R)`:

```
salt          = keccak256(abi.encodePacked(R, A))
bytecodeHash  = keccak256(CrossChainProxy.creationCode ‖ abi.encode(manager, A, R))
P             = address(keccak256(0xff ‖ manager ‖ salt ‖ bytecodeHash)[12:])
```

The `proxy(A, R)` notation lists the address first for readability; the **salt encodes `R`
(rollupId) first**, as shown above (byte-exact in [Appendix D](D-wire-formats.md) D.3). The salt
carries no chain/domain term, so the same `(A, R)` maps to the same `P` on any manager
sharing the deployer address and proxy bytecode — letting operator and follower agree without
coordination. Calling `P` *is* calling `A`-on-`R`: the proxy forwards the call into the manager's
`executeCrossChainCall`, which resolves it against the proven execution tables (§5). The manager
records each proxy in `authorizedProxies : address → (A, R)` at storage slot `0`; a zero entry
means "not a proxy." The proxy detects a **static** (read-only) call context and routes it to the
read-only resolution path (§5).

## 3.3 Cross-chain call hash

Every cross-chain call is identified by one 32-byte hash over its six identity fields:

```
crossChainCallHash = keccak256(abi.encode(
    targetRollupId, targetAddress, value, data, sourceAddress, sourceRollupId))
```

The same value appears as `ExecutionEntry.proxyEntryHash` and `LookupCall.crossChainCallHash`. It
is the join key between what the proxy observes at replay and what the batch precomputed (§5).

## 3.4 The system transaction (inbound delivery)

When a cross-chain call targets an L2 contract, the L2 side is delivered by a **system
transaction**: a **type-`0x7E`, unsigned, deterministically-reconstructible** transaction from
`SYSTEM_ADDRESS` that invokes
`EEZL2.executeIncomingCrossChainCall(destination, value, data, sourceAddress, sourceRollup, …)`.
On-chain it:

- is callable only by `SYSTEM_ADDRESS`;
- **mints exactly `value`** (it is the source of the L2 ETH delivered) and enforces
  `msg.value == value`;
- checks the delivered call's hash equals the proven entry's `proxyEntryHash`;
- drives the entry through the flat call processor (§5).

System transactions are placed at the **head of the Sync block**, before any user transactions.
Being unsigned and deterministic, both the operator and any follower reconstruct them identically
from the batch's entries, so they need not be carried in the data-availability payload (§7). The
full `executeIncomingCrossChainCall` signature is in [Appendix D](D-wire-formats.md); the
type-`0x7E` **transaction envelope** (its byte/RLP serialization, hashing, and gas/nonce treatment)
is an execution-layer artifact pinned by the execution-layer specification — not by the settlement
contracts — and operator and followers MUST serialize it identically.

> **Explorer visibility.** The type-`0x7E` system transaction appears in the L2 block like any
> other transaction and is fully on-chain (the inbound `from = SYSTEM_ADDRESS`, the minted `value`,
> and the delivered call). Surfacing it to users needs block-explorer/tooling support for the
> `0x7E` type — a presentation concern, not a side channel.

## 3.5 Call-scheme rules

Cross-chain interactions must be provable, so each EVM call scheme maps to a defined outcome when
its target is a registered proxy:

| Scheme | Cross-chain semantics |
|---|---|
| **`CALL`** | A state-mutating cross-chain call; recorded as a call within an execution entry; may carry `value`. |
| **`STATICCALL`** | A **read-only** cross-chain call: a proven read recorded as a lookup (call + precomputed result), resolved without mutating state; `value` forced to `0`. |
| **`DELEGATECALL` / `CALLCODE`** | **Forbidden** — the proxy's cross-chain identity is undefined under the caller's storage context; MUST revert. |

Only `CALL` may trigger a state-mutating cross-chain dispatch; a `STATICCALL` to a proxy is a
proven read — recorded as a **lookup entry in the execution table** so its result can be proven —
and MUST NOT mutate state. Both are part of v0: the single state-mutating L1→L2 call is a `CALL`
with one return value (§9), and cross-chain reads are `STATICCALL`s resolved as lookups (§5.3).

---

*Next: [§4 Block Production & Header Fields](04-block-production.md).*
