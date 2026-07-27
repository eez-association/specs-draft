# 4. EEZ Execution State Machines

This chapter normatively specifies the execution behavior of `EEZ` on L1 and `EEZL2` on an L2.
The conformance evidence reproduces `eez-core-protocol` commit
`3a6ca65c4858792fc3a143d34c5484877ef8f68c`. The specification, not that repository, is the
normative source. Network choices about sequencing, block construction, system transactions, data
availability, proof-system policy, and supported call shapes do not change these machines.

The two machines share proxy identity, action hashes, replay tags, and lookup concepts. They do
**not** share one ABI data model. A producer MUST construct the L1 and L2 objects independently
and MUST use the exact side-specific layouts in this chapter and [Appendix B](B-wire-formats.md).

## 4.1 State

### 4.1.1 Shared proxy state

Both managers maintain:

```solidity
struct ProxyInfo {
    address originalAddress;
    uint64 originalRollupId;
}

mapping(address proxy => ProxyInfo) authorizedProxies;
```

`authorizedProxies[p].originalAddress == address(0)` means that `p` is not authorized. A manager
rejects creation of a proxy for its own network. L1 uses `MAINNET_ROLLUP_ID = 0`; an `EEZL2`
instance has immutable, non-zero `ROLLUP_ID` and immutable `SYSTEM_ADDRESS`.

### 4.1.2 L1 persistent and execution state

L1 additionally maintains:

```solidity
uint256 rollupCounter;

struct RollupConfig {
    address rollupContract;
    bytes32 stateRoot;
    uint256 etherBalance;
}

struct RollupVerification {
    uint256 lastVerifiedBlock;
    ExecutionEntry[] executionQueue;
    LookupCall[] lookupQueue;
    uint256 executionQueueIndex;
}
```

There is one `RollupConfig` and one `RollupVerification` per registered rollup. The manager also
holds a batch-global transient entry array, a batch-global transient lookup array, and transient
cursors/context:

- the next transient entry;
- the current persistent rollup and entry;
- the one-based flat-call cursor;
- the number of successful expected reentrant calls consumed;
- the tagged rolling hash;
- the signed net ETH flow of the current entry;
- the current lookup host and nested lookup;
- a deferred L1 nested-call-miss flag.

The transient arrays are ordinary storage in this source revision, but are loaded and deleted in
one `postAndVerifyBatch` call. Their semantics, not the Solidity storage class, are transient.

### 4.1.3 L2 persistent and execution state

L2 maintains:

```solidity
ExecutionEntry[] executions;
LookupCall[] lookupCalls;
uint256 lastLoadBlock;
uint256 executionIndex;
```

It also has transient current-entry, flat-call, expected-outgoing-call, rolling-hash, and lookup
context. L2 has no rollup registry, state-root ledger, `StateDelta`, proof state, per-rollup queue,
or protocol ETH ledger.

## 4.2 Exact side-specific data model

Member order is ABI-significant. The Solidity declarations below are exact. Expanded canonical
tuple strings and selectors are in [Appendix B](B-wire-formats.md).

### 4.2.1 L1 types

```solidity
struct StateDelta {
    uint256 rollupId;
    bytes32 currentState;
    bytes32 newState;
    int256 etherDelta;
}

struct L2ToL1Call {
    bool isStatic;
    address targetAddress;
    uint256 value;
    bytes data;
    address sourceAddress;
    uint256 sourceRollupId;
    uint256 revertSpan;
}

struct ExpectedL1ToL2Call {
    bytes32 crossChainCallHash;
    uint256 destinationRollupId;
    uint256 callCount;
    bytes returnData;
}

struct ExpectedLookup {
    bytes32 crossChainCallHash;
    uint256 destinationRollupId;
    bytes returnData;
    bool failed;
    uint64 l2ToL1CallNumber;
    uint64 lastL1ToL2CallConsumed;
    uint64 executingLookupIndex;
    L2ToL1Call[] l2ToL1Calls;
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;
    uint256 callCount;
    bytes32 rollingHash;
}

struct ExecutionEntry {
    StateDelta[] stateDeltas;
    bytes32 proxyEntryHash;
    uint256 destinationRollupId;
    bytes returnData;
    L2ToL1Call[] l2ToL1Calls;
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;
    ExpectedLookup[] expectedLookups;
    uint256 callCount;
    bytes32 rollingHash;
}

struct ExpectedStateRootPerRollup {
    uint256 rollupId;
    bytes32 stateRoot;
}

struct LookupCall {
    bytes32 crossChainCallHash;
    uint256 destinationRollupId;
    bytes returnData;
    bool failed;
    L2ToL1Call[] l2ToL1Calls;
    ExpectedL1ToL2Call[] expectedL1ToL2Calls;
    ExpectedLookup[] expectedLookups;
    uint256 callCount;
    bytes32 rollingHash;
    ExpectedStateRootPerRollup[] expectedStateRoots;
}

struct RollupIdWithProofSystems {
    uint256 rollupId;
    uint64[] proofSystemIndex;
}

struct ProofSystemBatchPerVerificationEntries {
    ExecutionEntry[] entries;
    LookupCall[] l1ToL2lookupCalls;
    uint256 transientExecutionEntryCount;
    uint256 transientLookupCallCount;
    address[] proofSystems;
    RollupIdWithProofSystems[] rollupIdsWithProofSystems;
    uint256[] blobIndices;
    bytes callData;
    bytes[] proofs;
    uint64 blockNumber;
}
```

In particular, `ExecutionEntry.returnData` precedes all three call/lookup arrays, every call has
the leading `isStatic` field, and the batch has no `crossProofSystemInteractions` field.

### 4.2.2 L2 types

```solidity
struct CrossChainCall {
    bool isStatic;
    address targetAddress;
    uint256 value;
    bytes data;
    address sourceAddress;
    uint256 sourceRollupId;
    uint256 revertSpan;
}

struct ExpectedOutgoingCrossChainCall {
    bytes32 crossChainCallHash;
    uint256 callCount;
    bytes returnData;
}

struct ExpectedLookup {
    bytes32 crossChainCallHash;
    bytes returnData;
    bool failed;
    uint64 callNumber;
    uint64 lastOutgoingCallConsumed;
    uint64 executingLookupIndex;
    CrossChainCall[] incomingCalls;
    ExpectedOutgoingCrossChainCall[] expectedOutgoingCalls;
    uint256 callCount;
    bytes32 rollingHash;
}

struct ExecutionEntry {
    bytes32 proxyEntryHash;
    CrossChainCall[] incomingCalls;
    ExpectedOutgoingCrossChainCall[] expectedOutgoingCalls;
    ExpectedLookup[] expectedLookups;
    uint256 callCount;
    bytes returnData;
    bytes32 rollingHash;
}

struct LookupCall {
    bytes32 crossChainCallHash;
    bytes returnData;
    bool failed;
    CrossChainCall[] incomingCalls;
    ExpectedOutgoingCrossChainCall[] expectedOutgoingCalls;
    ExpectedLookup[] expectedLookups;
    uint256 callCount;
    bytes32 rollingHash;
}
```

The L2 types are not aliases for the L1 types. L2 deliberately omits state deltas, clear-text
destination rollup ids, state-root pins, proof fields, and queue routing.

## 4.3 State-transition entry points

[§3.4](03-evm-binding.md#34-complete-deployed-abi) is the complete normative deployed ABI,
including constructors and all generated and manual views. The calls below are the entry points
that drive the state machines in this chapter:

```solidity
// Shared surface
executeCrossChainCall(address sourceAddress, bytes callData)
    external payable returns (bytes result);
staticCallLookup(address sourceAddress, bytes callData)
    external view returns (bytes result);
createCrossChainProxy(address originalAddress, uint256 originalRollupId)
    external returns (address proxy);
computeCrossChainProxyAddress(address originalAddress, uint256 originalRollupId)
    external view returns (address proxy);
computeCrossChainCallHash(
    uint256 targetRollupId,
    address targetAddress,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollupId
) external pure returns (bytes32);

// L1
registerRollup(address rollupContract, bytes32 initialState)
    external returns (uint256 rollupId);
postAndVerifyBatch(ProofSystemBatchPerVerificationEntries batch) external;
executeL2TX(uint256 rollupId) external returns (bytes result);
setStateRoot(uint256 rollupId, bytes32 newStateRoot) external;

// L2
loadExecutionTable(ExecutionEntry[] entries, LookupCall[] lookupCalls) external;
executeIncomingCrossChainCall(
    address destination,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollup,
    ExecutionEntry[] entries,
    LookupCall[] lookupCalls
) external payable returns (bytes result);
```

The self-call helpers `executeInContextAndRevert(uint256)` on both sides and
`attemptApplyImmediate(uint256)` on L1 are also runtime functions. They are externally visible
only to support isolated EVM call frames and reject any caller other than the manager itself.

### 4.3.1 Rollup registration transition

`rollupCounter` starts at zero. `registerRollup(rollupContract, initialState)` performs these steps
in order:

1. If `rollupContract` is the zero address or the `EEZ` contract itself, revert
   `InvalidRollupContract()`.
2. Increment `rollupCounter` using checked `uint256` arithmetic. The incremented value is the new
   `rollupId`; the first registration therefore receives ID `1`.
3. Store
   `RollupConfig(rollupContract, initialState, 0)` at `rollups[rollupId]`.
4. Call `rollupContractRegistered(rollupId)` on `rollupContract`.
5. Emit `RollupCreated(rollupId, rollupContract, initialState)`.
6. Return `rollupId`.

The callback signature is:

```solidity
rollupContractRegistered(uint256 rollupId) external;
```

Its selector is `0x74a8ffc4`. The stored configuration is visible during the callback. There is no
registration reentrancy guard, code-size requirement, callback return value, or manager-uniqueness
check. A callback revert is forwarded and rolls back the counter increment, stored configuration,
nested effects, and event. A call to an address with no code succeeds because the callback has no
return value; later manager calls will normally fail ABI decoding. Reentrant callbacks follow
ordinary EVM call order and can allocate additional IDs before the outer `RollupCreated` event.

## 4.4 Action and proxy construction

For every observed cross-chain action:

```text
crossChainCallHash = keccak256(abi.encode(
    targetRollupId,
    targetAddress,
    value,
    data,
    sourceAddress,
    sourceRollupId
))
```

The source and target ids depend on the side:

- L1 proxy dispatch fixes `sourceRollupId = 0` and derives the target from
  `authorizedProxies[msg.sender]`.
- L2 proxy dispatch fixes `sourceRollupId = ROLLUP_ID` and derives the target from the proxy.
- L2 inbound delivery fixes `targetRollupId = ROLLUP_ID` and receives the other five identity
  fields from the system call.
- Static lookup fixes `value = 0`.

For remote address `A` on rollup `R`, manager `M` computes:

```text
salt     = keccak256(abi.encodePacked(R, A))
initHash = keccak256(CrossChainProxy.creationCode || abi.encode(M, A, R))
proxy    = address(uint160(uint256(keccak256(0xff || M || salt || initHash))))
```

`createCrossChainProxy` rejects `R` equal to the manager's own rollup id and otherwise always
attempts CREATE2. Repeating the same creation reverts on the address collision; it does not return
the existing proxy. During mutating replay, the manager attempts creation only when the source
proxy is not authorized. Static replay cannot deploy and instead reverts
`LookupCallProxyNotDeployed` if the source proxy has no code. The non-canonical zero-address and
greater-than-`uint64` behavior is specified in §3.2.

The proxy records immutable manager, original address, and original rollup id. Its ordinary
fallback routes to `executeCrossChainCall`; when its self-call to `staticCheck()` cannot execute
`TSTORE`, it routes to `staticCallLookup`. A manager call to
`CrossChainProxy.executeOnBehalf(address,bytes)` performs the local target call and returns or
forwards the target's raw revert data. Calls to `executeOnBehalf` from any other address and calls
to `staticCheck()` from any address other than the proxy itself enter the ordinary fallback path.
This transparent selector-collision behavior is specified exactly in §3.2.

## 4.5 L1 batch construction and proof public inputs

### 4.5.1 Structural validity

Before any external call, L1 rejects a batch unless all of the following hold:

1. `proofSystems` is non-empty, has the same length as `proofs`, consists of non-zero addresses,
   and is strictly increasing by address.
2. `rollupIdsWithProofSystems` is non-empty and strictly increasing by non-zero `rollupId`; every
   rollup is registered.
3. Every `proofSystemIndex` is non-empty, strictly increasing, and in range.
4. Each entry's `stateDeltas` is strictly increasing by non-zero `rollupId`; every delta rollup
   occurs in the batch; and `destinationRollupId` occurs in that entry's deltas.
5. Every `L2ToL1Call.sourceRollupId`, every
   `ExpectedL1ToL2Call.destinationRollupId`, and every nested-lookup destination and subcall
   source occurs in its host entry's delta set.
6. Each top-level lookup's `expectedStateRoots` is strictly increasing by non-zero `rollupId`;
   every pin occurs in the batch; and the lookup destination occurs in its pins.
7. Every call source and reentrant destination under a top-level lookup occurs in that lookup's
   pin set.
8. Both transient counts are within their respective array lengths. A non-zero transient lookup
   count requires a non-zero transient entry count.

Rules 4 and 6 make an empty delta or pin array invalid because its destination cannot be a member.
The contract does not pre-validate call-count partitions, `revertSpan` bounds, lookup-key
uniqueness, static-call metadata, L2 zero entry hashes, or `blobIndices`. Blob indices can be
empty, repeated, unsorted, or outside the transaction's blob range. The other values are producer
invariants in §4.13; malformed values otherwise fail during replay, sometimes with an EVM bounds
or arithmetic panic.

### 4.5.2 Public-input construction

Let `H(x) = keccak256(x)`. The verifier computes:

```text
entryHashes[i]      = H(abi.encode(batch.entries[i]))
lookupCallHashes[i] = H(abi.encode(batch.l1ToL2lookupCalls[i]))
blobHashes[i]       = blobhash(batch.blobIndices[i])

customDataAcc = bytes32(0)
for r in rollupId-ascending batch order:
    customData_r = IRollupContract(rollups[r].rollupContract)
        .getCustomData(batch.blockNumber)
    customDataAcc = H(abi.encode(customDataAcc, r, customData_r))

sharedPublicInput = H(abi.encodePacked(
    abi.encode(entryHashes),
    abi.encode(lookupCallHashes),
    abi.encode(blobHashes),
    H(batch.callData),
    customDataAcc
))

for each global proof-system index k from 0 through batch.proofSystems.length - 1:
    acc_k = bytes32(0)
    for r in rollupId-ascending batch order where proofSystemIndex_r contains k:
        j = the local position of k in proofSystemIndex_r
        acc_k = H(abi.encode(acc_k, r, vkMatrix[r][j]))
    publicInputsHash_k = H(abi.encodePacked(sharedPublicInput, acc_k))
    require(IProofSystem(batch.proofSystems[k])
        .verify(batch.proofs[k], publicInputsHash_k))
```

Each `blobIndices[i]` is passed directly to the EIP-4844 `BLOBHASH` opcode. An index at or above
the number of versioned blob hashes in the transaction produces `bytes32(0)`; it does not revert.
Repeated indices repeat the same hash in `blobHashes`, and order is preserved.

For each rollup, L1 first resolves the indexed proof-system addresses and calls
`checkProofSystemsAndGetVkeys(address[])` on its registered manager. The returned vector MUST have
the same length; the manager is responsible for membership and threshold policy. Manager and
proof-system calls are `view` calls. Any revert, invalid vector, false verification result, or
unavailable custom data reverts the batch.

The key, custom-data, and verifier calls execute as EVM static calls. A manager or verifier revert
is forwarded unchanged. Malformed successful ABI return data fails Solidity ABI decoding. `EEZ`
checks only the returned verification-key vector length; it does not reject a zero key, which is
folded verbatim when a manager returns one. A verifier return value of `false` becomes
`InvalidProof()`, while a verifier revert remains that verifier's revert data. A
`getCustomData(uint64)` revert or malformed successful return also reverts the complete batch.

`getCustomData(uint64)` returns opaque bytes. The reference rollup manager returns empty bytes for
block number `0`; for `type(uint64).max` it returns an ABI encoding of the current timestamp and
previous block hash; and for an available historical block it returns an ABI encoding of zero and
that block hash. A different conforming rollup manager may define different bytes.

The transient prefix counts are dispatch choices and are not inputs to `sharedPublicInput`.
Changing the split does not change the proven entry and lookup contents, but it does change how
those contents are executed, dropped, or published. The proof therefore does not authorize the
split.

## 4.6 Tagged replay and cursors

Each entry or reverted-lookup mini-entry starts with:

```text
h = 0
flatCallCursor = 0
expectedCallCursor = 0
```

The flat cursor is both an array cursor and a one-based call number after increment. The following
folds use `abi.encodePacked` exactly:

```text
CALL_BEGIN(n):
    h = keccak256(abi.encodePacked(h, uint8(1), uint256(n)))

CALL_END(n, success, returnData):
    h = keccak256(abi.encodePacked(
        h, uint8(2), uint256(n), bool(success), bytes(returnData)))

NESTED_BEGIN(n):
    h = keccak256(abi.encodePacked(h, uint8(3), uint256(n)))

NESTED_END(n):
    h = keccak256(abi.encodePacked(h, uint8(4), uint256(n)))
```

For a direct iteration, replay:

1. reads the call at `flatCallCursor`;
2. increments the cursor;
3. folds `CALL_BEGIN` with the incremented number;
4. derives and, on the mutating path, creates the source proxy;
5. invokes `sourceProxy.executeOnBehalf(targetAddress, data)` by `STATICCALL` when `isStatic`,
   otherwise by `CALL` with `value`;
6. folds `CALL_END` with the **live** global flat-call cursor and the observed low-level result.

The last point is intentional and observable. Reentrancy may consume more flat calls between the
parent begin and end, so a parent can begin with number 1 and end with number 2 or greater. A
producer MUST simulate this live-cursor rule; it MUST NOT reuse the parent's saved begin number.

A low-level target revert is data, not an entry failure: replay records `success = false` and the
raw return data, folds them, and continues. A successful L1 non-static call subtracts its value
from the entry's net-flow accumulator. A failed call does not.

### 4.6.1 Reentrant expected calls

When a target calls another cross-chain proxy while replay is active, the manager first compares
the next sequential expected-call record:

- L1 uses `ExpectedL1ToL2Call` and additionally requires its declared destination to equal the
  calling proxy's rollup.
- L2 uses `ExpectedOutgoingCrossChainCall`.

On a match, the manager advances the expected-call cursor, folds `NESTED_BEGIN(index + 1)`, runs
that record's `callCount` iterations against the **same flat array and cursor**, folds
`NESTED_END(index + 1)`, and returns the cached `returnData`.

Expected-call order has priority over a failed nested lookup. Successful reentrant calls MUST be
expected-call records. Failed reentrant calls that the application observes through try/catch are
lookups (§4.8).

### 4.6.2 Call-count partition

For a canonical producer, the call-count partition is:

```text
entry.callCount
    + sum(entry.expectedCalls[i].callCount for every consumed expected call)
    == entry.flatCalls.length
```

This is a producer invariant, not a separate on-chain equality check. It is a dynamic partition,
not necessarily a static sum over all records before execution:
expected calls may themselves be consumed from reverted lookup hosts, and `revertSpan` changes how
outer loop iterations advance. The authoritative checks are that the flat cursor equals the flat
array length and the expected-call cursor equals the expected-call array length. A malformed
positive span that exceeds the remaining current-frame iteration count can still reach those
cursor endpoints and pass the contract checks. Such an entry is outside the conforming producer
domain even if the deployed contract accepts it.

## 4.7 Forced rollback with `revertSpan`

`revertSpan == 0` selects ordinary replay. A positive value on the current flat call starts an
isolated forced-rollback span:

1. save the current flat-call index and the positive span;
2. temporarily write `revertSpan = 0` at that element;
3. self-call `executeInContextAndRevert(span)`;
4. process `span` **current-frame loop iterations**; after successful logical processing, the
   helper reverts with
   `ContextResult(rollingHash, expectedConsumed, callsProcessed, callNotFound)`;
5. decode and restore only those logical replay values in the caller;
6. restore the stored span, emit `RevertSpanExecuted`, and advance the outer processed count by
   `span`.

All ordinary state changes, ETH transfers, proxy creations, and logs in the isolated frame roll
back. The carried rolling hash and cursors make the enclosing logical trace advance as if the
calls ran. Nested calls can advance the flat cursor inside the span.

A producer MUST place a positive span only at its first element, MUST ensure it does not overrun
the remaining current-frame iterations or the active flat array, and MUST use it only for a forced
rollback. A naturally reverting low-level call uses `revertSpan = 0` and is represented by its
`CALL_END(false, returnData)`.

## 4.8 Lookups

Lookups represent calls whose top-level result is resolved without consuming a successful
execution entry:

- static mode validates optional read-only subcalls and returns cached data;
- failed mode executes a mini-entry for validation and then reverts with the cached raw data.

There is no lookup-consumption cursor and no lookup-consumed event. Lookup pools are scanned from
index zero on every use, so a matching lookup is reusable until its table is replaced or, on L1,
its state-root pins stop matching.

### 4.8.1 Top-level lookup matching

Outside replay, L1 scans exactly one pool:

- while a batch's transient entry table exists, only the transient lookup pool;
- otherwise, the calling proxy's destination-rollup persistent lookup queue.

The first record matches only if its action hash and `destinationRollupId` match and every
`expectedStateRoots` pin equals the corresponding live L1 root. A candidate with a stale pin is
skipped rather than reverting.

L2 scans its single `lookupCalls` table and matches the first record by action hash alone.

`staticCallLookup` itself has **no current-block gate on either side**. Consequently, a persistent
L1 lookup can remain readable after its posting block until a later verified batch replaces that
rollup's queue, provided its pins still match. An L2 lookup can remain readable until the next
table replacement. By contrast, the failed-lookup fallback reached from ordinary
`executeCrossChainCall` occurs only after that function's current-block gate.

### 4.8.2 Nested lookup matching

During replay, nested lookups are scoped to the active host's `expectedLookups` array. L1 matches:

```text
(crossChainCallHash,
 l2ToL1CallNumber,
 lastL1ToL2CallConsumed,
 executingLookupIndex)
```

and then requires the declared destination to equal the calling proxy's rollup. L2 matches the
corresponding:

```text
(crossChainCallHash,
 callNumber,
 lastOutgoingCallConsumed,
 executingLookupIndex)
```

`executingLookupIndex == 0` denotes the host entry or top-level lookup. Value `k > 0` denotes the
sub-execution of host `expectedLookups[k - 1]`. A deeper reverted lookup resolves from the same
flat host lookup table because Solidity structs cannot be recursive. Producers MUST therefore
make these keys unique within each host and execution context.

On L1, a nested ordinary-call miss scans failed nested lookups, then sets a deferred flag and
returns empty bytes if none matches. The enclosing entry boundary later reverts
`ExecutionNotFound`; this ordering preserves the trace until the boundary. On L2, the tentative
expected-call cursor increment and the whole frame revert immediately with `ExecutionNotFound` on
a miss, so the increment rolls back.

### 4.8.3 Static lookup replay

Static lookup subcalls are executed in array order using:

```text
sourceProxy.staticcall(
    abi.encodeCall(CrossChainProxy.executeOnBehalf, (targetAddress, data)))
```

The local accumulator starts at zero and folds, without tags or call numbers:

```text
staticHash = keccak256(abi.encodePacked(
    staticHash, bool(success), bytes(returnData)))
```

It MUST equal the lookup's `rollingHash`, including the zero value for an empty subcall array.
This code path does not consult the subcall's `isStatic`, `value`, or `revertSpan` fields. A
canonical producer MUST set them to `true`, `0`, and `0`; relying on ignored non-canonical values
is non-conforming. Every source proxy must already be deployed.

After validation, `failed == false` returns `returnData`; `failed == true` reverts with exactly
those bytes.

### 4.8.4 Failed lookup replay

An ordinary top-level entry always succeeds and has no `failed` flag. If its action hash does not
match the next entry, ordinary proxy dispatch scans for a top-level `LookupCall` with
`failed == true`. A matching failed lookup resets the replay cursors, runs its `callCount` as a
tagged mini-entry, checks its rolling hash and both consumption cursors, and then always reverts
with its cached raw `returnData`.

A matching failed nested lookup behaves the same way using the host's nested record. All subcall
state, value transfers, proxy creations, and logs roll back with the terminal revert. A miss
becomes `ExecutionNotFound` as described above.

## 4.9 L1 settlement and queue lifecycle

`postAndVerifyBatch` has the following order:

1. Reject reentry while the transient entry array is non-empty.
2. Validate structure without external calls.
3. Fetch per-rollup verification keys and verify every proof.
4. For every participating rollup, set `lastVerifiedBlock = block.number`, delete both persistent
   queues, and reset its execution cursor.
5. Copy the leading transient entry and lookup prefixes into the global transient tables.
6. Drain the leading run of transient entries whose `proxyEntryHash == 0`.
7. If transient entries remain and `msg.sender` has code, call
   `executeMetaCrossChainTransactions()` on the sender.
8. Delete both transient tables and reset the global transient cursor.
9. Route every non-transient entry and lookup by `destinationRollupId` into its persistent queue.
10. Emit `BatchPosted`.

Step 4 runs on every verification, including another verification for the same rollup in the same
L1 block. The new batch **replaces**, rather than appends to, unconsumed persistent entries and
lookups.

Each immediate zero-hash entry runs through a self-call. On failure, that entry's changes roll
back, `ImmediateEntrySkipped(index, revertData)` is emitted by the outer batch frame, and the
transient cursor advances. The batch continues. This is the only caught per-entry settlement
failure.

The meta hook may consume all, some, or none of the remaining transient prefix. Successful
consumption commits immediately in the enclosing batch transaction. On a normal hook return, all
unconsumed transient entries and lookups are deleted; they are not moved to persistent queues.
The non-transient remainder is nevertheless published. Its `StateDelta.currentState`
preconditions cause dependent entries to fail later if a required transient predecessor was
dropped. If the hook itself reverts, the entire `postAndVerifyBatch` call reverts.

The transient phase is isolated from every persistent queue. While the transient entry table is
non-empty, all entry and top-level lookup resolution uses only the current batch's transient
tables. A rollup verified by an earlier batch in the same Ethereum block can satisfy the
current-block gate but still cannot consume its persistent entries or lookups from inside the
later batch's meta hook. Cross-network interaction during the hook therefore requires every
participating entry and lookup in the same transient batch.

Both transient counts and `msg.sender` are unbound routing inputs controlled by the transaction
submitter. A submitter can reuse an otherwise valid proof, change either count, submit from a
different address, and obtain a different immediate/meta/persistent split. In particular, a
front-runner can turn entries into a transient prefix that is deleted without a matching meta hook,
or turn intended immediate entries into persistent entries. This can change surviving state
updates, events, and queue availability under the same proof.

This behavior is exact for `eez-evm@0.2-draft`; the contract has no submitter allowlist, proof nonce,
or count commitment that mitigates it. This binding MUST NOT be used for a production network
unless a versioned profile rule prevents unauthorized proof reuse and mutated routing inputs, for
example through an authenticated private inclusion path that commits the exact calldata and sender.
The rule is external mitigation, not a contract guarantee. A future binding that commits the
counts, sender, or a batch nonce requires a new binding edition.

### 4.9.1 L1 entry consumption

`executeCrossChainCall` and `executeL2TX` require the routed rollup's
`lastVerifiedBlock == block.number`. During the transient phase, all rollups share one exact global
entry order; the next entry's hash and destination must match. Persistent consumption instead uses
one FIFO and cursor per destination rollup. There is no search or skip.

The selected cursor advances before replay, but an entry failure reverts that advancement and all
entry effects. A failing persistent head therefore blocks later entries in that queue. A later
verified batch can replace the queue. A successfully consumed entry cannot be consumed again.

For each selected L1 entry, replay and finalization occur in this exact order:

1. initialize rolling and consumption cursors, preserving the entry's already-recorded inbound
   net ETH;
2. process `entry.callCount`;
3. for every state delta in order, check the live root, write the new root, update the per-rollup
   ETH ledger, and emit `L2ExecutionPerformed`;
4. check, in order: no deferred nested miss; rolling hash equality; complete flat-call
   consumption; complete expected-call consumption; and
   `sum(stateDeltas.etherDelta) == entryNetEth`;
5. emit `EntryExecuted`, clear the active-execution cursor, and reset entry net ETH.

Checks after step 3 can still fail. In that case the EVM reverts all root, ledger, ETH, proxy, and
event changes from the entry frame.

## 4.10 L2 table lifecycle and consumption

Only `SYSTEM_ADDRESS` can call either table-loading entry point.

`loadExecutionTable(entries, lookups)` deletes the old arrays, resets `executionIndex` to zero,
copies both arrays, sets `lastLoadBlock = block.number`, and emits `ExecutionTableLoaded`.
Unconsumed entries and all old lookups are discarded.

`executeIncomingCrossChainCall(...)` performs the same replacement, but also:

1. requires a non-empty entry array and `msg.value == value`;
2. computes the action hash from the five explicit action parameters and `ROLLUP_ID`;
3. requires `entries[0].proxyEntryHash` to equal that hash;
4. processes `entries[0].callCount`;
5. checks rolling hash, complete incoming-call consumption, and complete expected-outgoing-call
   consumption;
6. sets `executionIndex = 1`, emits `EntryExecuted`, and returns the cached entry result.

The conforming execution-layer envelope MUST make the system call top-level and allow it at most
once per transaction so its transient cursors start at zero. `SYSTEM_ADDRESS` MUST be unable to
reenter either table-loading entry point while execution is active, or an equivalent profile-pinned
guard MUST reject that reentry. The contract does **not** enforce those conditions and does not
reset every transient cursor at the beginning of the call. A second or reentrant
`executeIncomingCrossChainCall` in the same transaction is outside the conforming envelope.

The contract does **not** compare the explicit action parameters with
`entries[0].incomingCalls[0]` field by field. The producer MUST construct a consistent L2 entry.
The network profile must specify the cross-side construction rule under
[§7](07-network-profile.md).

Ordinary `executeCrossChainCall` requires `lastLoadBlock == block.number`. At top level it consumes
exactly `executions[executionIndex]` when the entry hash matches, advances the cursor, replays, and
checks both cursors and the rolling hash. At nested depth it resolves an expected outgoing call or
a failed lookup. A failure reverts the cursor and all effects.

L2 does not structurally validate loaded tables. `SYSTEM_ADDRESS` and the producer are trusted to
supply well-formed arrays satisfying §4.13.

## 4.11 Value and custody accounting

### 4.11.1 L1

The L1 `EEZ` contract is the physical ETH custodian. A proxy forwards its call value into
`EEZ.executeCrossChainCall`; the proxy does not retain it. For one entry:

```text
entryNetEth
    = sum(all top-level and reentrant inbound msg.value)
    - sum(value of every successful non-static replay call)
```

The accumulator spans all nested frames. Failed calls do not subtract value. Forced-revert and
failed-lookup frames contribute zero after rollback. At completion:

```text
sum(delta.etherDelta for delta in entry.stateDeltas) == entryNetEth
```

Positive deltas increase the named rollup's book balance; negative deltas decrease it and revert
if the book balance is insufficient. The ledger does not itself transfer ETH. If the contract's
initial physical balance equals the sum of rollup ledgers and it receives no forced ETH, successful
entries preserve that aggregate relationship. Forced transfers can break the physical-versus-book
equality without changing the entry accounting rule.

All Solidity `int256` additions, subtractions, and negations in this accounting use checked
arithmetic and can revert with panic code `0x11`. Explicit conversion of a `uint256` call value to
`int256` interprets the same 256 bits as a signed two's-complement value; the conversion itself
does not range-check the value. In particular, negating `type(int256).min` in a negative state
delta panics. Producers MUST keep every value and intermediate sum in the signed range and MUST
reproduce the checked-operation order.

`setStateRoot` changes no ETH ledger. There is no core deposit or withdrawal entry point other
than value moving through replay.

### 4.11.2 L2

`EEZL2` has no book ledger and does not itself mint. It merely requires the inbound system call to
arrive with `msg.value == value`. Whether that value is minted by the execution layer, pre-funded
at `SYSTEM_ADDRESS`, or sourced another way is a network-profile rule.

Inbound value is held by `EEZL2` and can be forwarded by replay calls. A failed value-bearing call
does not transfer value and can leave funds in `EEZL2`. Conversely, value attached to an
L2-originated proxy call is sent to `SYSTEM_ADDRESS` before the action is resolved. This is the
core contract's burn sink; if the later frame reverts, the transfer reverts too.

No core rule equates an L1 ledger change with an L2 mint or burn or assigns custody across sides.
A value-bearing network MUST supply and test that accounting rule before release
([§6.5](06-security-model.md), [§7](07-network-profile.md)).

## 4.12 Events and failure semantics

The exact event ABIs are in [Appendix B.4](B-wire-formats.md#b4-event-abis). Event order in the
transaction receipt is normative. A follower that uses logs as settlement evidence MUST preserve
their receipt order and MUST apply the EVM rollback rules below.

### 4.12.1 Roles

| Scope | Event | Meaning |
|---|---|---|
| shared | `CrossChainProxyCreated` | a deterministic proxy was deployed and authorized |
| shared | `CrossChainCallExecuted` | an authorized proxy entered ordinary dispatch |
| L1 | `RollupCreated`, `StateUpdated` | registry creation or manager escape update |
| L1 | `BatchPosted` | the whole batch call completed |
| L1 | `ImmediateEntrySkipped` | an immediate entry failed in its caught self-call |
| L1 | `ExecutionConsumed`, `L2TXExecuted` | a transient or persistent entry was selected |
| L1 | `L2ExecutionPerformed` | one state delta was applied; it survives only if its frame succeeds |
| L1 | `L1ToL2CallConsumed`, `L1ToL2CallNotFound` | expected reentrant resolution or deferred miss |
| L2 | `ExecutionTableLoaded` | a system load replaced the table |
| L2 | `ExecutionConsumed`, `IncomingCrossChainCallExecuted` | an entry was selected or inbound delivery began |
| L2 | `OutgoingCallConsumed` | an expected outgoing result was selected |
| both | `CallResult`, `RevertSpanExecuted`, `EntryExecuted` | direct-call result, completed forced span, or fully validated entry |

There is no lookup-consumed event. `CrossChainCallExecuted`, `ExecutionConsumed`, and
`L2ExecutionPerformed` are emitted before all entry checks finish. Their emit sites alone do not
prove settlement. Only logs that remain in a successful ancestor receipt are observable.

### 4.12.2 Receipt and rollback rules

The EVM appends a child frame's surviving logs at the point of the call. Therefore, receipt order
is depth-first execution order:

1. logs emitted before a child call;
2. surviving logs emitted by that child and its descendants; and
3. logs emitted after the child returns.

If a frame reverts, every log emitted by that frame and all of its descendants is removed. This
remains true when its caller catches the revert. If an ancestor later reverts, logs from
previously successful descendants are also removed. Application, rollup-manager, proof-system,
meta-hook, and `SYSTEM_ADDRESS` logs follow the same rules and occur at their actual call sites
among the core logs described below.

View execution emits no core logs. In particular, `staticCallLookup` has no event path. A target
that attempts a state change or `LOG` opcode under its static call fails that subcall; the lookup
folds the failure bytes as specified in §4.8.3.

### 4.12.3 Recursive replay order

For one ordinary flat-call iteration with `revertSpan == 0`, core operations occur in this order:

1. advance the flat cursor and fold `CALL_BEGIN`; neither operation emits a log;
2. if the source proxy is absent, deploy and authorize it, then emit
   `CrossChainProxyCreated`;
3. call the source proxy and target; their surviving application and nested EEZ logs occur here;
4. fold `CALL_END`; and
5. emit `CallResult` with the live post-reentrancy call number, success flag, and raw return or
   revert bytes.

If the low-level target call reverts, its logs are removed. Replay continues and emits
`CallResult(...,false,rawRevertData)`. The proxy-creation event from step 2 survives if the
enclosing entry succeeds.

A successful reentrant cross-chain dispatch occurs during step 3, before the parent
`CallResult`. Its relative core order is:

```text
CrossChainCallExecuted
L1ToL2CallConsumed             // L1 manager
  or OutgoingCallConsumed      // L2 manager
events from recursively replaying the selected nested callCount
return to the target
... parent target logs, if any ...
parent CallResult
```

The consumed event precedes the `NESTED_BEGIN` fold. The recursive events precede the
`NESTED_END` fold and the return of the cached nested result. An automatically created proxy in
that recursive replay emits `CrossChainProxyCreated` before the corresponding proxy/target
invocation.

For a positive `revertSpan`, the helper frame recursively processes the span and then deliberately
reverts `ContextResult`. All core and application logs from that helper frame are removed. After
decoding the context result, the outer frame emits exactly one `RevertSpanExecuted`; no
`CallResult` from any iteration in the span survives. `RevertSpanExecuted` is itself removed if
the enclosing entry later reverts.

### 4.12.4 Successful top-level order

Let `REPLAY` mean the recursive sequence in §4.12.3 for all calls selected by an entry. Let
`DELTAS` mean one `L2ExecutionPerformed` per L1 state delta, in array order. The surviving core
event order for each successful entry point is:

| Entry point | Surviving core event order |
|---|---|
| `createCrossChainProxy` | `CrossChainProxyCreated` |
| `registerRollup` | surviving callback/nested logs, then outer `RollupCreated` |
| `setStateRoot` | `StateUpdated` |
| L1 top-level `executeCrossChainCall` | `CrossChainCallExecuted`, `ExecutionConsumed`, `REPLAY`, `DELTAS`, `EntryExecuted` |
| L1 `executeL2TX` | `L2TXExecuted`, `ExecutionConsumed`, `REPLAY`, `DELTAS`, `EntryExecuted` |
| L2 `loadExecutionTable` | `ExecutionTableLoaded` |
| L2 `executeIncomingCrossChainCall` | `ExecutionTableLoaded`, `IncomingCrossChainCallExecuted`, `REPLAY`, `EntryExecuted(0,...)` |
| L2 top-level `executeCrossChainCall` | `CrossChainCallExecuted`, `ExecutionConsumed`, `REPLAY`, `EntryExecuted` |

For a value-bearing L2-originated proxy call, the call that sends value to `SYSTEM_ADDRESS`
occurs before `CrossChainCallExecuted`. Any surviving `SYSTEM_ADDRESS` logs therefore precede the
L2 core sequence in the table.

The L1 state-delta events occur only after replay finishes and before the final entry checks.
`EntryExecuted` is emitted only after the rolling hash, both consumption endpoints, and, on L1,
the state-delta and ETH checks pass.

Registration stores the outer rollup configuration before calling
`rollupContractRegistered`. Logs from that callback, including any reentrant registration, occur
before the outer `RollupCreated`. A callback revert removes the counter update, stored
configuration, nested logs, and outer event.

For a successful `postAndVerifyBatch`, core logs occur in this order:

1. for each leading immediate entry, in transient-index order:
   - on success, `REPLAY`, `DELTAS`, then `EntryExecuted`; or
   - on failure, only `ImmediateEntrySkipped(transientIdx,revertData)`;
2. all surviving meta-hook logs and the complete top-level sequences of entries that the hook
   drives, in call order; and
3. `BatchPosted`, as the final log emitted by `EEZ` after transient cleanup and deferred
   publication.

Immediate entries do not emit `L2TXExecuted` or `ExecutionConsumed`. Proof and key callbacks are
static and cannot emit surviving logs. Cleanup and deferred publication emit no events.

### 4.12.5 Reverting and caught paths

Failure boundaries and their observable logs are normative:

- invalid batch structure, proof/key/custom-data failure, meta-hook revert, or any later uncaught
  batch failure removes every log emitted during `postAndVerifyBatch`, including earlier
  immediate successes, `ImmediateEntrySkipped` events, and callback logs; `BatchPosted` is absent;
- an immediate-entry self-call failure removes all logs from that entry and the outer batch frame
  emits only `ImmediateEntrySkipped` for it; that event survives only if the whole batch succeeds;
- a transient or persistent proxy/L2-transaction entry failure removes
  `CrossChainCallExecuted`, `L2TXExecuted`, `ExecutionConsumed`, replay, delta, proxy-creation, and
  nested logs from the failing caller frame;
- an L2 inbound-delivery failure removes both the table replacement and any
  `ExecutionTableLoaded` or `IncomingCrossChainCallExecuted` logs emitted before the failing
  check;
- an ordinary low-level target revert removes target-frame logs but can leave one
  `CallResult(...,false,rawRevertData)` when the enclosing entry succeeds;
- a failed lookup validates and executes its mini-entry, then deliberately reverts with cached raw
  bytes, so none of that lookup frame's logs survive;
- when a failed nested lookup is the low-level failure of an otherwise successful parent replay,
  the parent emits its ordinary `CallResult(...,false,cachedBytes)` after the lookup frame has
  unwound;
- a top-level failed lookup reverts the complete manager dispatch, so even an earlier
  `CrossChainCallExecuted` is absent from the receipt;
- `L1ToL2CallNotFound` is emitted before setting the deferred-miss flag, but the enclosing L1
  entry must later revert; consequently this event never survives as settlement evidence; and
- missing entries/lookups, wrong hashes or destinations, stale block gates, root/count/rolling
  mismatches, value mismatches, unauthorized callers, and Solidity panics remove all logs in
  their reverting frame.

Custom errors identify protocol failures; cached target failure data is forwarded raw and is not
wrapped. An unexpected malformed count or span can produce a Solidity panic rather than a named
protocol error. Appendix A indexes the named errors.

## 4.13 Required invariants

A conforming producer, prover, L1 manager, L2 system caller, and follower MUST maintain:

| ID | Invariant |
|---|---|
| E.1 | **Side separation.** L1 and L2 objects use their own exact ABI layouts; no object is decoded as the other side's type. |
| E.2 | **Action identity.** Every proxy-dispatched entry with a non-zero `proxyEntryHash`, expected call, and lookup carries the action hash derived from the exact six identity fields observed at its dispatch point. An entry dispatched through `attemptApplyImmediate` or `executeL2TX` carries the zero-hash sentinel instead. |
| E.3 | **Routing proof.** Every L1 entry destination occurs in its sorted delta set; every top-level lookup destination occurs in its sorted pin set; all call sources and reentrant destinations occur in that host set. |
| E.4 | **State trajectory.** Every applied `currentState` equals the live L1 root and every lookup pin describes the state at observation. |
| E.5 | **Exact order.** Transient entries use one batch-global FIFO; persistent entries use one FIFO per destination; expected reentrant calls use one sequential host cursor. |
| E.6 | **Complete partition.** Successful replay consumes every flat call and every expected call exactly once. Counts and positive spans never index outside their active arrays. |
| E.7 | **Live-cursor hash.** Every tag, number, success flag, and raw result is folded in replay order; `CALL_END` uses the live post-reentrancy cursor. |
| E.8 | **Lookup coordinates.** Nested lookup keys are unique in their host and use the live call cursor, expected-call cursor, and active lookup index at observation. |
| E.9 | **Static canonicality.** Static lookup subcalls have `isStatic = true`, `value = 0`, and `revertSpan = 0`; their source proxies already exist. |
| E.10 | **Rollback spans.** A positive `revertSpan` starts a bounded forced-rollback region and is never used to encode a naturally reverting call. |
| E.11 | **L1 value conservation.** The signed sum of an entry's deltas equals all inbound value less successful non-static outflow across the complete nested execution. No rollup book balance becomes negative. |
| E.12 | **Block/table freshness.** Mutating entry consumption satisfies its side's current-block gate. Static lookup follows the deliberately ungated table-lifetime rules in §4.8.1. |
| E.13 | **Top-level result form.** A successful top-level result is an execution entry; a top-level revert is a failed lookup. Cached result bytes equal the application's observed bytes. |
| E.14 | **L2 inbound consistency.** The explicit inbound parameters, entry-zero action hash, first incoming call, value supply, replay trace, and returned result describe one action. |
| E.15 | **Proof binding.** Entry, lookup, blob, calldata, custom-data, and per-proof-system vkey folds equal §4.5.2 byte-for-byte. |
| E.16 | **Replacement awareness.** Same-block L1 re-verification and every L2 table load replace prior unconsumed queues/tables; no consumer assumes append semantics. |
| E.17 | **Partial-consumption endpoint.** Any transient prefix left after a successful meta-hook return is dropped; followers and profiles use only effects that actually committed. |

These invariants include producer obligations not rejected by the L1 structural pre-pass or the L2
loader. Passing ABI decoding is not evidence that an entry is conforming.

## 4.14 Access control

| Function | Authorized caller |
|---|---|
| `registerRollup` | anyone; the supplied manager receives `rollupContractRegistered(uint256)` after its configuration is stored |
| `postAndVerifyBatch` | anyone; structure and proofs authorize effects |
| `createCrossChainProxy` | anyone, except for a same-network identity |
| `executeCrossChainCall` | an address in `authorizedProxies` |
| `staticCallLookup` | an address in `authorizedProxies`, normally through a proxy static context |
| `executeL2TX` | anyone, outside active replay and in the verified block |
| `setStateRoot` | the named rollup's registered manager, outside replay and outside a block that already verified that rollup |
| `loadExecutionTable` | L2 `SYSTEM_ADDRESS` |
| `executeIncomingCrossChainCall` | L2 `SYSTEM_ADDRESS` |
| `executeInContextAndRevert`, `attemptApplyImmediate` | the manager contract itself |

The replay path is intentionally reentrant. Correctness comes from the single flat cursor,
side-specific expected-call cursor, lookup coordinates, state-root checks, and EVM rollback
boundaries rather than from a blanket non-reentrancy guard.

---

*Next: [§5 Proving & Settlement](05-proving-settlement.md).*
