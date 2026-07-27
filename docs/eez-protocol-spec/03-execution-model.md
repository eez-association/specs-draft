# 3. Execution Model

This chapter specifies how the settlement manager (`EEZ`) and execution manager (`EEZL2`) execute
a verified batch. The execution machinery supports arbitrary bidirectional, multi-call, reentrant
cross-chain interactions.

## 3.1 Data model

A batch carries **execution entries**:

```solidity
struct StateDelta {
    uint256 rollupId;
    bytes32 currentState;
    bytes32 newState;
    int256 etherDelta;
}

struct L2ToL1Call {
    address targetAddress;
    uint256 value;
    bytes data;
    address sourceAddress;
    uint256 sourceRollupId;
    uint256 revertSpan;
}

struct ExpectedL1ToL2Call {
    bytes32 crossChainCallHash;
    uint256 callCount;
    bytes returnData;
}

struct ExecutionEntry {
    StateDelta[] stateDeltas;
    bytes32 proxyEntryHash;
    uint256 destinationRollupId;
    L2ToL1Call[] L2ToL1Calls;
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;
    uint256 callCount;
    bytes returnData;
    bytes32 rollingHash;
}

struct LookupCall {
    bytes32 crossChainCallHash;
    uint256 destinationRollupId;
    bytes returnData;
    bool failed;
    uint64 callNumber;
    uint64 lastNestedActionConsumed;
    L2ToL1Call[] calls;
    bytes32 rollingHash;
}
```

A top-level entry always succeeds. A reverting top-level result is expressed as a lookup; there is
no `failed` flag on `ExecutionEntry`.

Every entry MUST carry at least one `StateDelta`. An entry with none is unpinned from any state
trajectory and is rejected by the pre-state check. `callCount` is the entry's top-level iteration
count. The full call array also contains calls consumed by nested frames.

## 3.2 The rolling hash

A single `bytes32` accumulator attests the entry's execution. Each call is bracketed by two tagged
folds:

```text
CALL_BEGIN (1): h = keccak256(h, uint8(1), callNumber)
CALL_END   (2): h = keccak256(h, uint8(2), callNumber, success, returnData)
```

Reentrant frames add:

```text
NESTED_BEGIN (3): h = keccak256(h, uint8(3), nestedNumber)
NESTED_END   (4): h = keccak256(h, uint8(4), nestedNumber)
```

Starting from `0`, any divergence in a call's result, success flag, order, or count yields a
different final hash. The entry is accepted only if the accumulator equals `entry.rollingHash`.
This binds on-chain replay to the precomputed execution.

## 3.3 Consumption

`EEZ` exposes three consumption entry points:

- **`executeCrossChainCall(sourceAddress, callData)`** — callable by a registered proxy. It
  recovers `(targetRollupId, targetAddress)` from `authorizedProxies[msg.sender]`, computes the call
  hash, and consumes the next entry on that rollup's queue whose `proxyEntryHash` matches. The
  target rollup MUST have been verified in the current settlement block.
- **`executeL2TX(rollupId)`** — permissionless; consumes the next entry whose
  `proxyEntryHash == 0`. It is not callable while already inside an execution.
- **`staticCallLookup(...)`** — read-only resolution for `STATICCALL`-context cross-chain reads.
  The read is matched to a proven lookup entry and MUST NOT mutate state.

The consumption cursor advances **only on a match**. There is no out-of-order consumption and no
search. Each entry is consumed exactly once, in posted order. Consuming an entry runs its
`L2ToL1Calls` through the flat processor, accumulates the rolling hash and ether, then applies its
state deltas.

## 3.4 Verification at consumption

After processing an entry's calls, the manager asserts:

```text
rollingHash      == entry.rollingHash
callsProcessed   == entry.L2ToL1Calls.length
totalEtherDelta  == etherIn - etherOut
```

It then applies each `StateDelta`:

- check `rollups[delta.rollupId].stateRoot == delta.currentState`, else
  `StateRootMismatch`;
- set `rollups[delta.rollupId].stateRoot = delta.newState`; and
- move the rollup's ether balance by `delta.etherDelta`, reverting on underflow.

`etherIn` is the value delivered to the entry. `etherOut` is the sum of `value` over successful
calls. `totalEtherDelta` is the sum of its `StateDelta.etherDelta`. Ether is conserved per entry.

The pre-state binding and ether conservation are enforced independently of proof verification. A
proof cannot land a state transition that breaks the state chain or creates ether.

## 3.5 Reentrancy

A successful reentrant cross-chain call is pre-resolved as a nested action:

```text
{ crossChainCallHash, callCount, returnData }
```

A single global cursor walks the entry's flat `L2ToL1Calls`. The partition invariant holds:

```text
entry.callCount
    + sum(expectedL1ToL2Calls[i].callCount)
    == entry.L2ToL1Calls.length
```

Reentrant frames are bracketed in the rolling hash by `NESTED_BEGIN` and `NESTED_END`.

## 3.6 Lookups

Proven cross-chain reads use `STATICCALL`, set `failed = false`, and resolve through
`staticCallLookup` without mutating state.

An intentionally reverting cross-chain call is looked up rather than executed on the mutating
path. It sets `failed = true` and replays by reverting with the cached data. The lookup carries the
call and its precomputed result, matched by `crossChainCallHash` plus the cursor coordinate.
Read sub-calls are checked against the lookup's own rolling hash.

The lookup-call sub-call accumulator starts at zero and uses:

```text
h = keccak256(abi.encodePacked(h, success, returnData))
```

This scheme has no tag byte or call number.

## 3.7 Forced rollback

`revertSpan` forces the state effects of a span of otherwise successful calls to roll back at the
protocol layer. The processor self-calls a context that always reverts, carrying the cursors and
rolling hash out in the revert payload.

`revertSpan` is for forced reverts only. A naturally reverting call uses `revertSpan = 0`.

## 3.8 Settlement lifecycle

`postAndVerifyBatch(batch)` is the settlement entry point. The call:

1. guards against reentry;
2. validates the batch structure without external calls;
3. verifies each selected proof system over its public-inputs hash;
4. marks each touched rollup verified in the current settlement block;
5. loads the leading `transientExecutionEntryCount` entries into the transient execution table,
   then executes inline the leading run whose `proxyEntryHash == 0`;
6. invokes the caller's meta hook, if `msg.sender` has code, so it can consume remaining transient
   entries through proxy calls;
7. publishes remaining entries to per-rollup queues for consumption in the current block; and
8. emits `BatchPosted`.

Entries are consumable only in the settlement block in which they were posted. Unconsumed entries
are not carried over.

`transientExecutionEntryCount` and `transientLookupCallCount` are raw counts of the leading entries
and lookups loaded as transient. Each count MUST NOT exceed its array length. The inline-executed
set is the leading `proxyEntryHash == 0` run within the transient prefix, which may be shorter than
that prefix. The remainder is consumed through the meta hook or the per-rollup queue.

## 3.9 Cross-rollup routing

`destinationRollupId` routes entries to per-rollup queues. This enables synchronous composition
across more than one L2 and supports both L1-to-L2 and L2-to-L1 flows.

## 3.10 Invariants

| # | Invariant |
|---|---|
| H.1 | **Pre-state binding.** State advances only through `StateDelta` application or the manager escape `setStateRoot`; each `currentState` is checked against the live root. |
| H.2 | **Ether conservation.** Per entry, `totalEtherDelta == etherIn - etherOut`. |
| H.3 | **Sequential consumption.** Each entry is consumed once, in posted order; the cursor advances only on a `proxyEntryHash` match. |
| H.4 | **Rolling-hash integrity.** End-of-entry checks attest every call ran in order with the correct results and count. |
| H.5 | **Proxy determinism.** `proxy(targetAddress, targetRollupId)` is fully determined by the manager, salt, and proxy bytecode. |
| H.6 | **Same-block execution.** Entries posted in a settlement block are consumable only in that block. |
| H.7 | **Reentry guard.** Re-entering `postAndVerifyBatch` reverts. |

## 3.11 L2 specifics

`EEZL2` uses the same structs and rolling hash, with these differences: it has no proofs, registry,
or `StateDelta` application; a trusted `SYSTEM_ADDRESS` loads and drives entries; inbound delivery
mints exactly `value` and enforces `msg.value == value`; and a proxy-routed call originating on L2
forces its own `ROLLUP_ID` as the source and burns any `msg.value` to `SYSTEM_ADDRESS`.

## 3.12 Access control

| Function | Caller |
|---|---|
| `registerRollup` | anyone; assigns a fresh rollup ID |
| `postAndVerifyBatch` | anyone; the proof verifies authorization |
| `executeCrossChainCall` | registered proxies |
| `executeL2TX(rollupId)` | anyone, not inside an execution |
| `staticCallLookup` | registered proxies through `STATICCALL` |
| `setStateRoot(rollupId, root)` | the rollup manager, except in a block that already touched that rollup |
| `loadExecutionTable` / `executeIncomingCrossChainCall` | `SYSTEM_ADDRESS` |

The protocol is intentionally reentrant. The call cursor serializes all work within one entry.
Verification-time manager and proof-system calls are `view`, so they cannot mutate state during
settlement.

---

*Next: [Proving and Settlement](04-proving-and-settlement.md).*
