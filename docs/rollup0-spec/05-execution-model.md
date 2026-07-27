# 5. Execution Model

This chapter specifies how the L1 manager (`EEZ`) and L2 manager (`EEZL2`) execute a verified
batch. It covers the **v0 model** — a single L1→L2 call with one return value. The general
bidirectional, multi-call, reentrant model (reentrant frames, reverting-call lookups, `revertSpan`,
cross-rollup routing) is specified in [§13](13-rollup1-general-model.md); v0 does not exercise it.
(Proven `STATICCALL` reads, by contrast, **are** in v0 — §3.5, §5.3.)

## 5.1 Data model

A batch carries **execution entries**. The v0 fields:

```solidity
struct StateDelta {                 // one rollup's state transition caused by one entry
    uint256 rollupId;
    bytes32 currentState;           // expected pre-state; checked == rollups[rollupId].stateRoot at consumption
    bytes32 newState;               // post-execution state root
    int256  etherDelta;             // signed change in the rollup's ETH balance
}

struct L2ToL1Call {                 // one call in the entry's flat call array
    address targetAddress;
    uint256 value;
    bytes   data;
    address sourceAddress;
    uint256 sourceRollupId;
    uint256 revertSpan;             // v0: 0 (forced-revert spans are general-model, §13)
}

struct ExecutionEntry {
    StateDelta[]         stateDeltas;          // the entry's state transition(s)
    bytes32              proxyEntryHash;       // crossChainCallHash of the entry's trigger; 0 = system-driven
    uint256              destinationRollupId;
    L2ToL1Call[]         L2ToL1Calls;          // flat array of all calls in execution order (v0: the inbound call)
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;  // v0: empty (reentrancy is general-model, §13)
    uint256              callCount;            // top-level iterations
    bytes                returnData;           // the entry's return value
    bytes32              rollingHash;          // expected accumulator after the entry completes
}
```

A top-level entry always succeeds (a reverting top-level result is expressed as a *lookup*,
§13); there is no `failed` flag. Every entry MUST carry at least one `StateDelta` (its true state
transition); an entry with none is unpinned from any trajectory and is rejected by the pre-state
check (§5.4). `callCount` is the entry's top-level iteration count; in v0 (no reentrant frames) it
equals `L2ToL1Calls.length`. The byte-exact ABI member order of every struct here — and the
batch-level structs not shown (`LookupCall`, used for v0 proven `STATICCALL` reads (§3.5);
`RollupIdWithProofSystems`; and the general-model `ExpectedL1ToL2Call`) — are in
[Appendix D](D-wire-formats.md). `L2ToL1Call` is the general-model struct name reused here; in v0
it carries the inbound **L1→L2** call, despite the name.

## 5.2 The rolling hash

A single `bytes32` accumulator attests the entry's execution. Each call is bracketed by two tagged
folds:

```
CALL_BEGIN (1): h = keccak256(h, uint8(1), callNumber)
CALL_END   (2): h = keccak256(h, uint8(2), callNumber, success, returnData)
```

(Reentrant frames add `NESTED_BEGIN`/`NESTED_END` tags — general-model, §13.) Starting from `0`,
any divergence in a call's result, success flag, order, or count yields a different final hash. The
entry is accepted only if the accumulator equals `entry.rollingHash` (§5.4). This binds the
on-chain replay to exactly what the operator simulated and the validators attested.

## 5.3 Consumption

`EEZ` exposes three consumption entry points:

- **`executeCrossChainCall(sourceAddress, callData)`** — callable by a registered proxy. It
  recovers `(targetRollupId, targetAddress)` from `authorizedProxies[msg.sender]`, computes the
  call hash (§3.3), and consumes the next entry on that rollup's queue whose
  `proxyEntryHash` matches. The target rollup MUST have been verified this L1 block, else it
  reverts.
- **`executeL2TX(rollupId)`** — permissionless; consumes the next entry whose `proxyEntryHash == 0`
  (a system-driven entry). Not callable while already inside an execution.
- **`staticCallLookup(...)`** — read-only resolution for `STATICCALL`-context cross-chain reads
  (**v0**): the read is matched to a proven **lookup entry** in the execution table and MUST NOT
  mutate state. (Lookups for *reverting* calls, `failed = true`, are general-model, §13.)

The consumption cursor advances **only on a match** (`entry.proxyEntryHash == hash`); there is no
out-of-order consumption and no search. Each entry is consumed exactly once, in posted order.
Consuming an entry runs its `L2ToL1Calls` through the flat processor, accumulating the rolling
hash and ether, then applies its state deltas (§5.4).

## 5.4 Verification at consumption

After processing an entry's calls, the manager asserts, in order:

```
rollingHash      == entry.rollingHash            // else RollingHashMismatch
callsProcessed   == entry.L2ToL1Calls.length     // else UnconsumedCalls
totalEtherDelta  == etherIn − etherOut           // else EtherDeltaMismatch
```

and applies each `StateDelta`:

- check `rollups[delta.rollupId].stateRoot == delta.currentState`, else `StateRootMismatch` — the
  **pre-state binding**;
- set `rollups[delta.rollupId].stateRoot = delta.newState`;
- move the rollup's ether balance by `delta.etherDelta` (revert on underflow).

**`etherIn`** is the value delivered to the entry (the inbound `msg.value`); **`etherOut`** is the
sum of `value` over the entry's successful calls; **`totalEtherDelta`** is the sum of its
`StateDelta.etherDelta`. Ether is conserved per entry.

The pre-state binding is the soundness backstop: the validators' signatures attest the entry, **and**
the contract independently checks the claimed pre-state against the live root and conserves ether —
so even a fully-malicious validator set cannot land a state transition that breaks the state chain
or conjures ether (it reverts regardless of the signature; see also [§8](08-proving-settlement.md)).

## 5.5 Settlement lifecycle (`postAndVerifyBatch`)

`postAndVerifyBatch(batch)` is the L1 settlement entry point. In v0 the operator posts **one batch
per L1 block** covering the slot's blocks. The call:

1. **Guards** against reentry.
2. **Validates** the batch structure (no external calls).
3. **Verifies** the proof: fetches each rollup's validator set + threshold from its manager and
   checks the N-of-M signatures over the public-inputs hash (§8). Any failure reverts the whole
   call.
4. **Marks** each touched rollup verified this L1 block (the read-gate for consumption).
5. **Loads** the leading `transientExecutionEntryCount` entries into the transient execution table,
   then **executes inline** the leading run of those whose `proxyEntryHash == 0` (system-driven).
6. **Invokes the caller's meta hook** (if `msg.sender` has code) so it can consume the remaining
   transient entries via proxy calls within the same transaction.
7. **Publishes** any remaining entries to per-rollup queues for consumption this block.
8. **Emits** `BatchPosted`.

Entries are consumable only in the L1 block they were posted (the verified-this-block read-gate);
unconsumed entries are not carried over. `transientExecutionEntryCount` and
`transientLookupCallCount` are **raw counts** of the leading entries / lookup calls loaded as
transient; the only structural bound is `transientExecutionEntryCount ≤ entries.length` (and
`transientLookupCallCount ≤ l1ToL2lookupCalls.length`). The inline-executed set (step 5) is the
leading `proxyEntryHash == 0` run *within* that transient prefix, which may be shorter than the
prefix; the remainder is consumed via the meta hook (step 6) or the per-rollup queue (step 7).

## 5.6 Invariants

| # | Invariant |
|---|---|
| H.1 | **Pre-state binding.** State advances only via `StateDelta` application or the manager escape `setStateRoot`; each `currentState` is checked against the live root (`StateRootMismatch`). |
| H.2 | **Ether conservation.** Per entry, `totalEtherDelta == etherIn − etherOut`. |
| H.3 | **Sequential consumption.** Each entry is consumed once, in posted order, on its rollup's cursor; the cursor advances only on a `proxyEntryHash` match. |
| H.4 | **Rolling-hash integrity.** The end-of-entry checks (§5.4) attest every call ran in order with the right results and count. |
| H.5 | **Proxy determinism.** `proxy(targetAddress, targetRollupId)` is fully determined by the manager, salt, and proxy bytecode (§3.2). |
| H.6 | **Same-block execution.** Entries posted in an L1 block are consumable only in that block. |
| H.7 | **Reentry guard.** `postAndVerifyBatch` re-entered from any path reverts. |

## 5.7 L2 specifics (`EEZL2`)

`EEZL2` uses the same structs and rolling hash, with these differences: no proofs, no registry, no
`StateDelta` application; a trusted `SYSTEM_ADDRESS` loads/drives entries (§3.4); inbound delivery
mints exactly `value` (`msg.value == value`); and a proxy-routed call originating on L2 forces its
own `ROLLUP_ID` as the source and burns any `msg.value` to `SYSTEM_ADDRESS` (L2 keeps no ether
accounting). v0 drives only the single inbound delivery.

## 5.8 Access control

| Function | Caller |
|---|---|
| `registerRollup` | anyone (assigns a fresh rollup id) |
| `postAndVerifyBatch` | anyone (the proof verifies authorization) |
| `executeCrossChainCall` | registered proxies |
| `executeL2TX(rollupId)` | anyone, not inside an execution |
| `staticCallLookup` | registered proxies (via `STATICCALL`) |
| `setStateRoot(rid, root)` | the rollup's manager (locked the L1 block a batch touched the rollup) |
| `loadExecutionTable` / `executeIncomingCrossChainCall` (L2) | `SYSTEM_ADDRESS` |

The protocol is intentionally reentrant — calls reach proxies that call back — and the call cursor
serializes everything within one entry. The verification-time external calls (the manager's
threshold check and each signature verify) are `view`, so they cannot mutate state mid-settlement.

---

*Next: [§6 The Composer](06-composer.md).*
