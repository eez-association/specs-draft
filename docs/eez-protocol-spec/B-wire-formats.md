# Appendix B. Wire Formats and Conformance Vectors

This appendix is the normative byte-exact annex for the EEZ execution state machines in
[§4](04-execution-model.md). Conformance evidence was reproduced from `eez-core-protocol` commit
`3a6ca65c4858792fc3a143d34c5484877ef8f68c`; the layouts below, not that repository, define
`eez-evm@0.2-draft`. Canonical tuples follow Solidity member order exactly. `uint` is written as
`uint256`; no field may be reordered, omitted, changed to another type, or decoded with the tuple
family from the other side.

Unless stated otherwise:

- integers are unsigned 256-bit ABI words;
- addresses are left-padded to 32 bytes;
- `bytes32` is encoded in place;
- `bytes`, arrays, and structs containing them use standard ABI head/tail encoding;
- hashes are Keccak-256, not standardized SHA3-256;
- `abi.encode` and `abi.encodePacked` are distinct operations and MUST be used where specified.

## B.1 L1 canonical tuples

### B.1.1 Leaf tuples

| Solidity type | Canonical tuple |
|---|---|
| `StateDelta` | `(uint256,bytes32,bytes32,int256)` |
| `L2ToL1Call` | `(bool,address,uint256,bytes,address,uint256,uint256)` |
| `ExpectedL1ToL2Call` | `(bytes32,uint256,uint256,bytes)` |
| `ExpectedStateRootPerRollup` | `(uint256,bytes32)` |
| `RollupIdWithProofSystems` | `(uint256,uint64[])` |
| `ProxyInfo` | `(address,uint64)` |
| `RollupConfig` | `(address,bytes32,uint256)` |

The L1 leaf member order is:

```text
StateDelta:
  rollupId, currentState, newState, etherDelta

L2ToL1Call:
  isStatic, targetAddress, value, data, sourceAddress, sourceRollupId, revertSpan

ExpectedL1ToL2Call:
  crossChainCallHash, destinationRollupId, callCount, returnData

ExpectedStateRootPerRollup:
  rollupId, stateRoot
```

### B.1.2 L1 nested lookup

```text
(bytes32,uint256,bytes,bool,uint64,uint64,uint64,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,uint256,bytes)[],
 uint256,bytes32)
```

Member order:

```text
crossChainCallHash
destinationRollupId
returnData
failed
l2ToL1CallNumber
lastL1ToL2CallConsumed
executingLookupIndex
l2ToL1Calls
expectedL1ToL2Calls
callCount
rollingHash
```

### B.1.3 L1 execution entry

```text
((uint256,bytes32,bytes32,int256)[],
 bytes32,
 uint256,
 bytes,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,uint256,bytes)[],
 (bytes32,uint256,bytes,bool,uint64,uint64,uint64,
  (bool,address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,uint256,bytes)[],
  uint256,bytes32)[],
 uint256,
 bytes32)
```

Member order:

```text
stateDeltas
proxyEntryHash
destinationRollupId
returnData
l2ToL1Calls
expectedL1ToL2Calls
expectedLookups
callCount
rollingHash
```

`returnData` is the fourth member. Older layouts that place it after `callCount`, omit
`expectedLookups`, or omit `isStatic` are incompatible.

### B.1.4 L1 top-level lookup

```text
(bytes32,
 uint256,
 bytes,
 bool,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,uint256,bytes)[],
 (bytes32,uint256,bytes,bool,uint64,uint64,uint64,
  (bool,address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,uint256,bytes)[],
  uint256,bytes32)[],
 uint256,
 bytes32,
 (uint256,bytes32)[])
```

Member order:

```text
crossChainCallHash
destinationRollupId
returnData
failed
l2ToL1Calls
expectedL1ToL2Calls
expectedLookups
callCount
rollingHash
expectedStateRoots
```

### B.1.5 L1 proof-system batch

The member order is:

```text
entries
l1ToL2lookupCalls
transientExecutionEntryCount
transientLookupCallCount
proofSystems
rollupIdsWithProofSystems
blobIndices
callData
proofs
blockNumber
```

Its fully expanded canonical tuple is the argument between the outer parentheses of:

```text
postAndVerifyBatch(
 (
  (
   (uint256,bytes32,bytes32,int256)[],
   bytes32,uint256,bytes,
   (bool,address,uint256,bytes,address,uint256,uint256)[],
   (bytes32,uint256,uint256,bytes)[],
   (
    bytes32,uint256,bytes,bool,uint64,uint64,uint64,
    (bool,address,uint256,bytes,address,uint256,uint256)[],
    (bytes32,uint256,uint256,bytes)[],
    uint256,bytes32
   )[],
   uint256,bytes32
  )[],
  (
   bytes32,uint256,bytes,bool,
   (bool,address,uint256,bytes,address,uint256,uint256)[],
   (bytes32,uint256,uint256,bytes)[],
   (
    bytes32,uint256,bytes,bool,uint64,uint64,uint64,
    (bool,address,uint256,bytes,address,uint256,uint256)[],
    (bytes32,uint256,uint256,bytes)[],
    uint256,bytes32
   )[],
   uint256,bytes32,
   (uint256,bytes32)[]
  )[],
  uint256,uint256,address[],(uint256,uint64[])[],
  uint256[],bytes,bytes[],uint64
 )
)
```

Whitespace is illustrative and is absent from the canonical selector string. This batch does
**not** contain `crossProofSystemInteractions`.

## B.2 L2 canonical tuples

### B.2.1 Leaf tuples

| Solidity type | Canonical tuple |
|---|---|
| `CrossChainCall` | `(bool,address,uint256,bytes,address,uint256,uint256)` |
| `ExpectedOutgoingCrossChainCall` | `(bytes32,uint256,bytes)` |

The call leaf has the same wire shape as L1 `L2ToL1Call`, but it is a different side-specific
type with self-relative semantics.

### B.2.2 L2 nested lookup

```text
(bytes32,bytes,bool,uint64,uint64,uint64,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 uint256,bytes32)
```

Member order:

```text
crossChainCallHash
returnData
failed
callNumber
lastOutgoingCallConsumed
executingLookupIndex
incomingCalls
expectedOutgoingCalls
callCount
rollingHash
```

### B.2.3 L2 execution entry

```text
(bytes32,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 (bytes32,bytes,bool,uint64,uint64,uint64,
  (bool,address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,bytes)[],
  uint256,bytes32)[],
 uint256,
 bytes,
 bytes32)
```

Member order:

```text
proxyEntryHash
incomingCalls
expectedOutgoingCalls
expectedLookups
callCount
returnData
rollingHash
```

### B.2.4 L2 top-level lookup

```text
(bytes32,
 bytes,
 bool,
 (bool,address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 (bytes32,bytes,bool,uint64,uint64,uint64,
  (bool,address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,bytes)[],
  uint256,bytes32)[],
 uint256,
 bytes32)
```

Member order:

```text
crossChainCallHash
returnData
failed
incomingCalls
expectedOutgoingCalls
expectedLookups
callCount
rollingHash
```

L2 has no `destinationRollupId` or state-root-pin tail.

## B.3 Function signatures and selectors

The runtime selector is the first four bytes of `keccak256(canonicalSignature)`. Return types and
mutability do not enter that hash, but they are normative parts of this binding's ABI. The
machine-readable corpus reproduces the complete `deployed_abi` manifest below. Its canonical JSON
form (sorted object keys, no insignificant whitespace) has SHA-256
`0x642b81e32d3f8cca5510097278bb9753e8ea090a93b591803b1971db3d2820da`.
The validator checks that digest and recomputes every function selector. The following creation
and fallback entries have no selector:

| Contract | ABI entry | Mutability |
|---|---|---|
| `EEZ` | default constructor with empty creation input | non-payable |
| `EEZL2` | `constructor(uint256 _rollupId,address _systemAddress)` | non-payable |
| `CrossChainProxy` | `constructor(address _eez,address _originalAddress,uint256 _originalRollupId)` | non-payable |
| `CrossChainProxy` | `fallback()` | `payable` |

Neither manager has a fallback or `receive` entry. `CrossChainProxy` has no `receive` entry.

### B.3.1 Shared and collaborator selectors

Every `EEZ` and `EEZL2` runtime contains these functions:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x360d95b6` | `authorizedProxies(address)` | `view` | `(address originalAddress,uint64 originalRollupId)` |
| `0x1f314db1` | `computeCrossChainCallHash(uint256,address,uint256,bytes,address,uint256)` | `pure` | `bytes32` |
| `0x2dd72120` | `createCrossChainProxy(address,uint256)` | non-payable | `address proxy` |
| `0xb761ba7e` | `computeCrossChainProxyAddress(address,uint256)` | `view` | `address` |
| `0x9af53259` | `executeCrossChainCall(address,bytes)` | `payable` | `bytes result` |
| `0x7aa4da2e` | `staticCallLookup(address,bytes)` | `view` | `bytes` |
| `0x37b99a56` | `executeInContextAndRevert(uint256)` | non-payable | none |

`CrossChainProxy` contains:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x532f0839` | `executeOnBehalf(address,bytes)` | `payable` | none |
| `0x9f149e1b` | `staticCheck()` | non-payable | none |

`executeOnBehalf` has no declared ABI output, even though its assembly implementation returns the
target's raw success bytes or reverts with the target's raw failure bytes.

The L1 manager calls these collaborator interfaces. They are not runtime functions of `EEZ`,
`EEZL2`, or `CrossChainProxy`:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x74a8ffc4` | `rollupContractRegistered(uint256)` | non-payable | none |
| `0xbed3a169` | `checkProofSystemsAndGetVkeys(address[])` | `view` | `bytes32[] vkeys` |
| `0x9aeb8564` | `getCustomData(uint64)` | `view` | `bytes customData` |
| `0x6b406341` | `verify(bytes,bytes32)` | `view` | `bool valid` |
| `0x455d16c7` | `executeMetaCrossChainTransactions()` | non-payable | none |

### B.3.2 L1 selectors

In addition to the shared manager functions in §B.3.1, the `EEZ` runtime contains:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x199350cf` | `MAINNET_ROLLUP_ID()` | `view` | `uint256` |
| `0xd8422037` | `_transientExecutions(uint256)` | `view` | `(bytes32 proxyEntryHash,uint256 destinationRollupId,bytes returnData,uint256 callCount,bytes32 rollingHash)` |
| `0xd3f60360` | `_transientLookupCalls(uint256)` | `view` | `(bytes32 crossChainCallHash,uint256 destinationRollupId,bytes returnData,bool failed,uint256 callCount,bytes32 rollingHash)` |
| `0xd4ccaf87` | `attemptApplyImmediate(uint256)` | non-payable | none |
| `0xccdcf581` | `executeL2TX(uint256)` | non-payable | `bytes result` |
| `0x72e991d3` | `executionQueueIndex(uint256)` | `view` | `uint256` |
| `0x206bbf07` | `lastVerifiedBlock(uint256)` | `view` | `uint256` |
| `0xd1fc6b5a` | full `postAndVerifyBatch` signature below | non-payable | none |
| `0x48cae3e2` | `queueLength(uint256)` | `view` | `uint256` |
| `0x559cd946` | `registerRollup(address,bytes32)` | non-payable | `uint256 rollupId` |
| `0xa3271832` | `rollupCounter()` | `view` | `uint256` |
| `0xb794e5a3` | `rollups(uint256)` | `view` | `(address rollupContract,bytes32 stateRoot,uint256 etherBalance)` |
| `0x2bdd1f16` | `setStateRoot(uint256,bytes32)` | non-payable | none |

The full canonical `postAndVerifyBatch` selector preimage, on one line, is:

```text
postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,bytes,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,uint256,bytes)[],(bytes32,uint256,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[],(bytes32,uint256,bytes,bool,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,uint256,bytes)[],(bytes32,uint256,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32,(uint256,bytes32)[])[],uint256,uint256,address[],(uint256,uint64[])[],uint256[],bytes,bytes[],uint64))
```

### B.3.3 L2 selectors

In addition to the shared manager functions in §B.3.1, the `EEZL2` runtime contains:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0xb5ed5559` | `ROLLUP_ID()` | `view` | `uint256` |
| `0x3434735f` | `SYSTEM_ADDRESS()` | `view` | `address` |
| `0xf882a0ad` | full `executeIncomingCrossChainCall` signature below | `payable` | `bytes result` |
| `0xc6109dc9` | `executionIndex()` | `view` | `uint256` |
| `0xf76c9229` | `executions(uint256)` | `view` | `(bytes32 proxyEntryHash,uint256 callCount,bytes returnData,bytes32 rollingHash)` |
| `0xa0d8dd9d` | `lastLoadBlock()` | `view` | `uint256` |
| `0xc1b4427c` | full `loadExecutionTable` signature below | non-payable | none |
| `0xd3886c9f` | `lookupCalls(uint256)` | `view` | `(bytes32 crossChainCallHash,bytes returnData,bool failed,uint256 callCount,bytes32 rollingHash)` |

The full canonical selector preimages are:

```text
loadExecutionTable((bytes32,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])

executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,(bytes32,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(bool,address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])
```

### B.3.3.1 Generated and manual view behavior

For `authorizedProxies` and `rollups`, an absent mapping key returns the all-zero tuple. The L1
manual `lastVerifiedBlock`, `queueLength`, and `executionQueueIndex` views also return zero for an
uninitialized rollup ID.

For `_transientExecutions`, `_transientLookupCalls`, `executions`, and `lookupCalls`, an index
outside the current array length reverts with Solidity panic payload
`0x4e487b71 || abi.encode(uint256(0x32))`. A generated public array-of-struct getter omits all
nested array members. The ABI returns only the direct members listed in the tables; a client MUST
NOT attempt to decode the full storage struct.

### B.3.4 Custom-error selectors

A custom-error payload starts with the listed selector and continues with
`abi.encode(arguments...)` in canonical-signature order. A no-argument payload is exactly four
bytes. [Appendix A.5](A-reference.md#a5-errors) specifies the argument meanings, reverting
contexts, and exact conditions.

Shared `EEZBase` errors:

| Selector | Canonical signature |
|---|---|
| `0xe53dc94a` | `UnauthorizedProxy()` |
| `0x29c3b7ee` | `NotSelf()` |
| `0xed6bc750` | `ExecutionNotFound()` |
| `0xf3a3b67c` | `RollingHashMismatch()` |
| `0x0816f53c` | `ContextResult(bytes32,uint256,uint256,bool)` |
| `0x8664b1a5` | `UnexpectedContextRevert(bytes)` |
| `0x0bdb621e` | `LookupCallProxyNotDeployed(address)` |
| `0xd1f02ab2` | `StaticCallWithValue()` |
| `0x77bcc5b4` | `SameNetworkProxy(uint256)` |

L1 `EEZ` errors:

| Selector | Canonical signature |
|---|---|
| `0x09bde339` | `InvalidProof()` |
| `0x8b4f56d9` | `PostBatchReentry()` |
| `0x690969c2` | `NotRollupContract()` |
| `0x033feec7` | `RollupBatchActiveThisBlock(uint256)` |
| `0xd0e1ecec` | `InvalidRollupContract()` |
| `0xe851b378` | `InsufficientRollupBalance()` |
| `0xde315ee4` | `EtherDeltaMismatch()` |
| `0xf1df384f` | `ResidualEntryEtherIn()` |
| `0x78cb4214` | `StateRootMismatch(uint256)` |
| `0x2ae204bd` | `ExecutionNotInCurrentBlock(uint256)` |
| `0xbd2663f5` | `L2TXNotAllowedDuringExecution()` |
| `0xd161d374` | `SetStateRootNotAllowedDuringExecution()` |
| `0xdd148d75` | `TransientCountExceedsEntries()` |
| `0x68888636` | `TransientLookupCallCountExceedsLookupCalls()` |
| `0x61fcacac` | `TransientLookupCallsWithoutTransientEntries()` |
| `0xa287649c` | `InvalidProofSystemConfig()` |
| `0x23ce5bbc` | `DuplicateProofSystem(address)` |
| `0xf0b9be82` | `RollupNotInBatch(uint256)` |
| `0xdd0c77c5` | `UnconsumedL2ToL1Calls()` |
| `0xed4a913d` | `UnconsumedL1ToL2Calls()` |
| `0xe7e18c36` | `EntryDestinationNotInStateDeltas(uint256)` |
| `0x76e2810c` | `LookupDestinationNotPinned(uint256)` |
| `0x4d347cf3` | `CallSourceNotVerified(uint256)` |
| `0xd7510cae` | `ReentrantDestinationNotVerified(uint256)` |
| `0x612a8387` | `ReentrantDestinationMismatch(uint256,uint256)` |
| `0xb185698a` | `StateDeltasNotStrictlyIncreasing(uint256)` |
| `0x119af6e2` | `ExpectedStateRootsNotStrictlyIncreasing(uint256)` |

L2 `EEZL2` errors:

| Selector | Canonical signature |
|---|---|
| `0x82b42900` | `Unauthorized()` |
| `0x5f115753` | `InvalidRollupId()` |
| `0xf9d330ad` | `ExecutionNotInCurrentBlock()` |
| `0x6747a288` | `EtherTransferFailed()` |
| `0x574daa08` | `EmptyEntries()` |
| `0xdd8e4af7` | `ValueMismatch()` |
| `0xc2098b88` | `EntryHashMismatch()` |
| `0x093a2b9f` | `UnconsumedIncomingCalls()` |
| `0x03ae6521` | `UnconsumedOutgoingCalls()` |

The L1 and L2 `ExecutionNotInCurrentBlock` errors have different canonical signatures and
selectors. An implementation MUST NOT use one side's selector on the other side.

## B.4 Event ABIs

Indexed parameters affect topic layout but not the event signature hash. Exact declarations:

```solidity
// Shared
event CrossChainProxyCreated(
    address indexed proxy,
    address indexed originalAddress,
    uint256 indexed originalRollupId
);
event CrossChainCallExecuted(
    bytes32 indexed crossChainCallHash,
    address indexed proxy,
    address sourceAddress,
    bytes callData,
    uint256 value
);

// L1
event RollupCreated(
    uint256 indexed rollupId,
    address indexed rollupContract,
    bytes32 initialState
);
event StateUpdated(uint256 indexed rollupId, bytes32 newStateRoot);
event L2ExecutionPerformed(uint256 indexed rollupId, bytes32 newState);
event ExecutionConsumed(
    bytes32 indexed crossChainCallHash,
    uint256 indexed rollupId,
    uint256 indexed executionQueueIndex
);
event L2TXExecuted(uint256 indexed rollupId, uint256 indexed executionQueueIndex);
event BatchPosted(uint256 indexed rollupCount);
event ImmediateEntrySkipped(uint256 indexed transientIdx, bytes revertData);
event L1ToL2CallNotFound(
    uint256 indexed entryIndex,
    bytes32 indexed crossChainCallHash,
    uint256 currentL2ToL1Call,
    uint256 lastL1ToL2CallConsumed
);
event CallResult(
    uint256 indexed entryIndex,
    uint256 indexed l2ToL1CallNumber,
    bool success,
    bytes returnData
);
event L1ToL2CallConsumed(
    uint256 indexed entryIndex,
    uint256 indexed l1ToL2CallNumber,
    bytes32 crossChainCallHash,
    uint256 callCount
);
event EntryExecuted(
    uint256 indexed entryIndex,
    bytes32 rollingHash,
    uint256 l2ToL1CallsProcessed,
    uint256 l1ToL2CallsConsumed
);
event RevertSpanExecuted(
    uint256 indexed entryIndex,
    uint256 startL2ToL1Call,
    uint256 span
);

// L2-only names; CallResult, EntryExecuted, and RevertSpanExecuted have
// the same ABI types as their L1 counterparts.
event ExecutionTableLoaded(ExecutionEntry[] entries);
event ExecutionConsumed(
    bytes32 indexed crossChainCallHash,
    uint256 indexed executionIndex
);
event IncomingCrossChainCallExecuted(
    bytes32 indexed crossChainCallHash,
    address destination,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollup
);
event OutgoingCallConsumed(
    uint256 indexed entryIndex,
    uint256 indexed nestedNumber,
    bytes32 crossChainCallHash,
    uint256 callCount
);
```

No lookup-consumption event exists.

## B.5 Hash preimages

### B.5.1 Action hash

```text
keccak256(abi.encode(
    uint256 targetRollupId,
    address targetAddress,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollupId
))
```

This is dynamic ABI encoding because `data` is dynamic.

### B.5.2 Proxy CREATE2

```text
salt = keccak256(abi.encodePacked(
    uint256 originalRollupId,
    address originalAddress
))

initCode = CrossChainProxy.creationCode
    || abi.encode(address manager, address originalAddress, uint256 originalRollupId)

proxy = low20(keccak256(
    bytes1(0xff) || address manager || bytes32 salt || keccak256(initCode)
))
```

`abi.encodePacked(originalRollupId, originalAddress)` is 52 bytes: a 32-byte integer followed by a
20-byte address.

For `eez-evm@0.2-draft`, `CrossChainProxy.creationCode` is the exact 1111-byte sequence in the
normative [creation-code artifact](fixtures/cross-chain-proxy-creation-code.json). Its Keccak-256
hash is `0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8`.
Recompiling a source file is not a normative way to obtain this sequence. A different sequence,
length, or hash requires a different binding edition and changes derived proxy addresses.

### B.5.3 Tagged replay

```text
callBegin =
    keccak256(abi.encodePacked(h, uint8(1), uint256(liveCallNumber)))

callEnd =
    keccak256(abi.encodePacked(
        h, uint8(2), uint256(liveCallNumber), bool(success), bytes(returnData)))

nestedBegin =
    keccak256(abi.encodePacked(h, uint8(3), uint256(nestedNumber)))

nestedEnd =
    keccak256(abi.encodePacked(h, uint8(4), uint256(nestedNumber)))
```

In packed encoding, the tag and boolean occupy one byte each, the counters occupy 32 bytes, and
the final `bytes` payload is included raw without a length or padding. `callEnd` uses the live
flat-call cursor after any reentrant work.

### B.5.4 Static lookup subhash

```text
staticHash_0 = bytes32(0)
staticHash_i = keccak256(abi.encodePacked(
    staticHash_(i-1), bool(success_i), bytes(returnData_i)))
```

There are no tags or call numbers in this schema.

## B.6 Proof public inputs

```text
entryHashes[i]      = keccak256(abi.encode(entries[i]))
lookupCallHashes[i] = keccak256(abi.encode(l1ToL2lookupCalls[i]))
blobHashes[i]       = blobhash(blobIndices[i])

customDataAcc_0 = bytes32(0)
customDataAcc_r = keccak256(abi.encode(
    customDataAcc_(r-1),
    rollupId_r,
    getCustomData_r(blockNumber)
))

sharedPublicInput = keccak256(abi.encodePacked(
    abi.encode(entryHashes),
    abi.encode(lookupCallHashes),
    abi.encode(blobHashes),
    keccak256(callData),
    customDataAcc_final
))

acc_k_0 = bytes32(0)
acc_k_r = keccak256(abi.encode(
    acc_k_(r-1),
    rollupId_r,
    vkey_r_for_k
))

publicInputsHash_k =
    keccak256(abi.encodePacked(sharedPublicInput, acc_k_final))
```

The custom-data fold includes every participating rollup in strictly increasing rollup-id order.
The per-proof-system fold includes only rollups whose `proofSystemIndex` contains that global
proof-system index, in the same order. `vkey_r_for_k` uses the matching **local** position in the
jagged manager return vector.

`abi.encode(entryHashes)` means ABI encoding of one `bytes32[]` value, including its dynamic-array
head. It is not concatenation of the hash elements. The same applies to lookup and blob hash
arrays.

## B.7 Conformance vectors

The Solidity fixture in `companion-docs/wire-vectors-eez-current.s.sol` recomputes these vectors from the
pinned structs and `CrossChainProxy.creationCode` (the companion file is outside the MkDocs
documentation tree). The same results are available as a machine-readable
[current-binding corpus](fixtures/eez-evm-0.2-conformance.json).

The creation-code corpus above references the separate immutable artifact. Conformance tooling
MUST verify that artifact's declared length and Keccak-256 hash before using the proxy vector.

### B.7.1 Vector 1 — action hash

Inputs:

```text
targetRollupId = 1
targetAddress  = 0x00000000000000000000000000000000deadbeef
value          = 1000000000000000000
data           = 0xdeadbeef
sourceAddress  = 0x0000000000000000000000000000000000c0ffee
sourceRollupId = 0
```

Result:

```text
0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2
```

### B.7.2 Vector 2 — direct tagged replay

Start at zero. Fold `CALL_BEGIN(1)`, then
`CALL_END(liveCallNumber = 1, success = true, returnData = 0x01)`:

```text
after CALL_BEGIN =
0xa578faae9568ec79d80e92f83b4d08a4537677b5145aef1ab04b0c67dd76c63f

after CALL_END =
0x696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d
```

### B.7.3 Vector 3 — nested live-cursor replay

Sequence:

```text
CALL_BEGIN(1)
NESTED_BEGIN(1)
CALL_BEGIN(2)
CALL_END(2, true, 0x02)
NESTED_END(1)
CALL_END(2, true, 0x01)
```

Intermediate values:

```text
parent begin  = 0xa578faae9568ec79d80e92f83b4d08a4537677b5145aef1ab04b0c67dd76c63f
nested begin  = 0x3d834e314673d097a9dce11f90f7ebf82cde953e278c09167ce2a42b395b4cec
child begin   = 0x510b8848f50072c10d20af2e942be40a28b5ab71dc59658a053fa3645e6b2b2b
child end     = 0x911db8ecc073330d76f92ed44c532d42128c630d888bf985e8b23e54a84aa824
nested end    = 0xa4579cf4c504625737acdc1efb0a7a424e18c733de251ff23951746cf9e6d36b
parent end    = 0x34d9159317893ed5b9711a8212ff385c11c99bf74124608d0d219c85c429e151
```

The parent end uses call number 2, demonstrating the live-cursor rule.

### B.7.4 Vector 4 — static lookup subhash

For zero previous hash, `success = true`, and `returnData = 0xabcd`:

```text
0xcadce27f539c1a651c804a271c7011fd8529acc643c3f6369a60adaa4aae1177
```

### B.7.5 Vector 5 — L1 `ExecutionEntry`

The entry uses Vector 1 as `proxyEntryHash`, Vector 2's final hash, and:

```text
stateDeltas = [{
  rollupId: 1,
  currentState: bytes32(0xaa),
  newState: bytes32(0xbb),
  etherDelta: 1000000000000000000
}]
destinationRollupId = 1
returnData = 0x
l2ToL1Calls = [{
  isStatic: false,
  targetAddress: 0x00000000000000000000000000000000deadbeef,
  value: 0,
  data: 0xdeadbeef,
  sourceAddress: 0x0000000000000000000000000000000000c0ffee,
  sourceRollupId: 1,
  revertSpan: 0
}]
expectedL1ToL2Calls = []
expectedLookups = []
callCount = 1
```

Results:

```text
abi.encode length = 928
entryHash =
0x51e1632383c7841fd9e2a174163aed36834896ede9a3d2f4936e1e67801bec71
```

The full encoding is:

```text
0x000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000001206254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000001e0000000000000000000000000000000000000000000000000000000000000034000000000000000000000000000000000000000000000000000000000000003600000000000000000000000000000000000000000000000000000000000000001696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000aa00000000000000000000000000000000000000000000000000000000000000bb0000000000000000000000000000000000000000000000000de0b6b3a7640000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000deadbeef000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000c0ffee000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004deadbeef0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
```

### B.7.6 Vector 6 — L1 top-level lookup

Input:

```text
crossChainCallHash = bytes32(0x1234)
destinationRollupId = 1
returnData = 0xabcd
failed = true
l2ToL1Calls = []
expectedL1ToL2Calls = []
expectedLookups = []
callCount = 0
rollingHash = bytes32(0)
expectedStateRoots = [{ rollupId: 1, stateRoot: bytes32(0xaa) }]
```

Results:

```text
abi.encode length = 608
lookupCallHash =
0x85be8606cad0ae3cb989136c5b255fe107c1b93f36b086538a041f5f70185b57
```

### B.7.7 Vector 7 — proof public input

Use Vector 5 as the only entry, no lookups, no blobs, empty `callData`, one rollup with
`rollupId = 1`, `getCustomData(0) = 0x`, and one proof-system verification key
`bytes32(uint256(0x100))`:

```text
customDataAcc =
0xc0dc72cf9435ef1cd9a5e872346bf9ca5cf6306d8f62305d089f6a9d582792b8

sharedPublicInput =
0x53641eba159eb8caf003dccc161151497535a7b559ac5333ae663a596dfe4c79

proofSystemAcc =
0xf648b9fec533a721da003a85b25ec87bb231f0b8d429fb3b2099729a589a48a5

publicInputsHash =
0xe265e1c1fbc52c560558b76be4ede800269f90a65b7065c3e0ffc9baadb83076
```

### B.7.8 Vector 8 — side separation

The L2 entry corresponding to the same synthetic inbound action has:

```text
proxyEntryHash = Vector 1
incomingCalls = [{
  isStatic: false,
  targetAddress: 0x00000000000000000000000000000000deadbeef,
  value: 1000000000000000000,
  data: 0xdeadbeef,
  sourceAddress: 0x0000000000000000000000000000000000c0ffee,
  sourceRollupId: 0,
  revertSpan: 0
}]
expectedOutgoingCalls = []
expectedLookups = []
callCount = 1
returnData = 0x
rollingHash = Vector 2 final
```

Results:

```text
abi.encode length = 704
keccak256(abi.encode(l2Entry)) =
0x3308472f724b8141fe223e74d2ab939d2e0bd8668aaa25c21c8b611af0dec0fa
```

This checksum is a conformance aid. The L1 proof fold does not hash L2 entries.

### B.7.9 Vector 9 — proxy CREATE2

This vector is tied to the pinned source compiled with Solidity `0.8.34`, optimizer runs `200`,
and `via_ir = true`:

```text
manager         = 0x00000000000000000000000000000000000ee200
originalAddress = 0x0000000000000000000000000000000000c0ffee
originalRollupId = 1

creationCode length = 1111
keccak256(creationCode) =
0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8

salt =
0x9b795495c996503b00c5938a264389c4df5c002802eae27e9463f48ea7aafdd5

keccak256(initCode) =
0x7045969eb5c85c24a087914cfde032ebaa277996f1a2ea343a2b7d92af3e7c4b

proxy =
0xc5dc78b57986585780dc0c44b99a94888522e50c
```

Changing compiler version, metadata, optimizer configuration, source, constructor types, or
manager address changes the CREATE2 address.

## B.8 Source and compatibility boundary

Conformance was cross-checked read-only against:

- `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c`, including Solidity
  sources and generated ABIs;
- an adjacent implementation that pins an older, wire-incompatible EEZ core revision.

The inspected adjacent implementation uses an older tuple family: it lacks `isStatic` in call
leaves, lacks clear-text destinations in expected-call and nested-lookup records, orders L1 entry
fields differently, and includes the removed `crossProofSystemInteractions` batch field. Those
observations do not modify this binding. A network profile MUST pin one binding version and MUST
NOT decode one revision with another revision's tuple family.

---

*Back to [Appendix A](A-reference.md), or the [framework index](index.md).*
