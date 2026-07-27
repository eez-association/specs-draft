# Appendix A. Protocol Reference

This appendix is a lookup index. The normative chapters and Appendix B remain authoritative if
this summary disagrees with them.

## A.1 Binding identity and constants

| Item | Value |
|---|---|
| Framework edition | `eez-framework@0.1-draft` |
| EVM-binding edition | `eez-evm@0.2-draft` |
| Conformance-evidence source | `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` |
| L1 reserved rollup ID | `MAINNET_ROLLUP_ID = 0` |
| Registered/L2 rollup IDs | non-zero |
| Minimum execution fork | Cancun (`TLOAD`, `TSTORE`, `MCOPY`, and `BLOBHASH`) |
| Replay tags | `CALL_BEGIN = 1`, `CALL_END = 2`, `NESTED_BEGIN = 3`, `NESTED_END = 4` |
| Proxy compiler profile | solc `0.8.34+commit.80d5c536`, optimizer runs `200`, `via_ir = true`, EVM target `osaka` |
| Proxy creation-code length | `1111` bytes |
| Proxy creation-code hash | `0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8` |

The exact bytes, rather than a source-repository revision, are normative in the immutable
[proxy creation-code artifact](fixtures/cross-chain-proxy-creation-code.json).

EEZ does not define a chain ID, a network-specific fork beyond the Cancun minimum, block time, gas
limit, fee policy, `SYSTEM_ADDRESS`, predeploy address, DA tag, finality rule, or deployment
address.

## A.2 Deployed ABI index

Creation ABIs:

| Contract | Creation input |
|---|---|
| `EEZ` | empty, non-payable |
| `EEZL2` | `constructor(uint256,address)`, non-payable |
| `CrossChainProxy` | `constructor(address,address,uint256)`, non-payable |

Functions shared by both manager runtimes:

| Function | Selector |
|---|---|
| `authorizedProxies(address)` | `0x360d95b6` |
| `computeCrossChainCallHash(uint256,address,uint256,bytes,address,uint256)` | `0x1f314db1` |
| `createCrossChainProxy(address,uint256)` | `0x2dd72120` |
| `computeCrossChainProxyAddress(address,uint256)` | `0xb761ba7e` |
| `executeCrossChainCall(address,bytes)` | `0x9af53259` |
| `staticCallLookup(address,bytes)` | `0x7aa4da2e` |
| `executeInContextAndRevert(uint256)` | `0x37b99a56` |

Additional `EEZ` runtime functions:

| Function | Selector |
|---|---|
| `MAINNET_ROLLUP_ID()` | `0x199350cf` |
| `_transientExecutions(uint256)` | `0xd8422037` |
| `_transientLookupCalls(uint256)` | `0xd3f60360` |
| `attemptApplyImmediate(uint256)` | `0xd4ccaf87` |
| `executeL2TX(uint256)` | `0xccdcf581` |
| `executionQueueIndex(uint256)` | `0x72e991d3` |
| `lastVerifiedBlock(uint256)` | `0x206bbf07` |
| `postAndVerifyBatch(<B.1.5 tuple>)` | `0xd1fc6b5a` |
| `queueLength(uint256)` | `0x48cae3e2` |
| `registerRollup(address,bytes32)` | `0x559cd946` |
| `rollupCounter()` | `0xa3271832` |
| `rollups(uint256)` | `0xb794e5a3` |
| `setStateRoot(uint256,bytes32)` | `0x2bdd1f16` |

Additional `EEZL2` runtime functions:

| Function | Selector |
|---|---|
| `ROLLUP_ID()` | `0xb5ed5559` |
| `SYSTEM_ADDRESS()` | `0x3434735f` |
| `executeIncomingCrossChainCall(<expanded B.3.3 arguments>)` | `0xf882a0ad` |
| `executionIndex()` | `0xc6109dc9` |
| `executions(uint256)` | `0xf76c9229` |
| `lastLoadBlock()` | `0xa0d8dd9d` |
| `loadExecutionTable(<expanded B.3.3 arguments>)` | `0xc1b4427c` |
| `lookupCalls(uint256)` | `0xd3886c9f` |

`CrossChainProxy` has a payable fallback, `executeOnBehalf(address,bytes)` (`0x532f0839`), and
`staticCheck()` (`0x9f149e1b`). It has no public immutable getters. Appendix B.3 gives every exact
canonical signature, return tuple, and mutability. Its collaborator-interface table also gives
the callback selectors that the core contracts call. Selectors from another binding edition are
not aliases.

## A.3 Formulae

**Action hash** (§3.3):

```text
keccak256(abi.encode(
    targetRollupId,
    targetAddress,
    value,
    data,
    sourceAddress,
    sourceRollupId
))
```

**Proxy CREATE2 address** (§3.2):

```text
salt     = keccak256(abi.encodePacked(originalRollupId, originalAddress))
initCode = CrossChainProxy.creationCode
           || abi.encode(manager, originalAddress, originalRollupId)
proxy    = low20(keccak256(0xff || manager || salt || keccak256(initCode)))
```

**Tagged replay hash** (§4.6):

```text
CALL_BEGIN(n) = keccak256(abi.encodePacked(h, uint8(1), uint256(n)))
CALL_END(n)   = keccak256(abi.encodePacked(
                    h, uint8(2), uint256(n), bool(success), bytes(returnData)))
NESTED_BEGIN(n) = keccak256(abi.encodePacked(h, uint8(3), uint256(n)))
NESTED_END(n)   = keccak256(abi.encodePacked(h, uint8(4), uint256(n)))
```

`CALL_END` uses the live flat-call cursor after any reentrant work.

**Static lookup subhash** (§4.8.3):

```text
h_0 = bytes32(0)
h_i = keccak256(abi.encodePacked(h_(i-1), bool(success_i), bytes(returnData_i)))
```

**L1 entry accounting** (§4.11.1):

```text
sum(StateDelta.etherDelta)
    = sum(all inbound msg.value)
    - sum(all successful non-static replay outflow)
```

**Successful replay partition** (§4.6.2):

```text
entry.callCount
    + sum(consumed expected-call callCount)
    = flat-call array length
```

The authoritative endpoint checks are equality of the live flat and expected-call cursors with
their array lengths.

**Proof public inputs** (§5.3): hash each ABI-encoded L1 entry and top-level lookup; fold each
manager's opaque custom data in rollup-ID order; hash those arrays, blob hashes, `callData`, and
the custom-data accumulator into `sharedPublicInput`; then fold each proof system's selected local
verification keys and hash the result with `sharedPublicInput`. Appendix B.6 is byte-exact.

## A.4 Glossary

- **Action hash**: the six-field identity of one observed cross-chain action.
- **Applied endpoint**: a root written by a state delta whose execution frame and receipt survived.
- **Binding edition**: one immutable set of EVM layouts, selectors, hashes, and behavior.
- **Cross-chain proxy**: a deterministic local representative of a remote `(rollupId, address)`.
- **Entry**: one successful replay unit. L1 and L2 entries have distinct tuple types.
- **Expected call**: a precomputed successful reentrant result consumed sequentially from its host.
- **Expected lookup**: a nested static or failed result keyed inside an entry or top-level lookup.
- **Flat-call cursor**: the live cursor shared by a replay entry and its successful nested frames.
- **Lookup**: a reusable top-level static or failed result; it does not consume a successful entry.
- **Network profile**: the versioned network choices required by §7.
- **Proof system**: a contract that verifies one proof against one `publicInputsHash`.
- **Recorded root**: the state root currently stored by `EEZ`; it is not necessarily a valid
  rollup state.
- **State delta**: one L1-tracked rollup's pre-state, post-state, and signed book-balance change.
- **Transient prefix**: the leading entries/lookups loaded for same-transaction consumption and
  deleted at cleanup.

## A.5 Errors

For every custom error below, the revert payload is:

```text
bytes4(keccak256(bytes(canonicalSignature))) || abi.encode(arguments...)
```

The selector does not include argument names. The encoded arguments use the listed order and
standard Solidity ABI rules. A no-argument error therefore has a four-byte payload. The declarations
and selectors are also collected without conditions in [Appendix B.3.4](B-wire-formats.md#b34-custom-error-selectors)
and in the machine-readable conformance corpus.

Shared `EEZBase` errors can originate from either `EEZ` or `EEZL2`:

| Canonical declaration | Selector | Reverting context | Payload values and condition |
|---|---|---|---|
| `error UnauthorizedProxy();` | `0xe53dc94a` | `executeCrossChainCall`, `staticCallLookup` | `authorizedProxies[msg.sender].originalAddress == address(0)`. |
| `error NotSelf();` | `0x29c3b7ee` | Both `executeInContextAndRevert` helpers; L1 `attemptApplyImmediate` | `msg.sender != address(this)`. |
| `error ExecutionNotFound();` | `0xed6bc750` | Entry, expected-call, and failed-lookup resolution | No required sequential entry, expected call, or eligible lookup matches. L1 also raises it at the enclosing boundary after a deferred nested miss. |
| `error RollingHashMismatch();` | `0xf3a3b67c` | Tagged entry/failed-lookup replay or static lookup replay | The computed tagged or static rolling hash differs from the record's declared endpoint. |
| `error ContextResult(bytes32 rollingHash, uint256 reentrantConsumed, uint256 callsProcessed, bool callNotFound);` | `0x0816f53c` | Successful terminal path of either `executeInContextAndRevert` helper | Carries the logical replay state out of the deliberately reverted frame. L1 supplies its expected L1-to-L2 cursor, flat L2-to-L1 cursor, and deferred-miss flag. L2 supplies its expected-outgoing cursor, flat incoming cursor, and `false`. |
| `error UnexpectedContextRevert(bytes revertData);` | `0x8664b1a5` | Caller of `executeInContextAndRevert` | The caught payload does not start with `ContextResult.selector`, or its length is less than 132 bytes. `revertData` is the complete caught payload. A matching payload of at least 132 bytes is decoded from its first four argument words; trailing bytes are ignored. |
| `error LookupCallProxyNotDeployed(address sourceProxy);` | `0x0bdb621e` | Static lookup subcall replay | The computed `sourceProxy` has no code. The argument is that computed address. |
| `error StaticCallWithValue();` | `0xd1f02ab2` | Mutating tagged replay | A flat call has `isStatic == true` and `value != 0`. Static lookup replay ignores these metadata fields as specified in §4.8.3. |
| `error SameNetworkProxy(uint256 rollupId);` | `0x77bcc5b4` | Explicit or automatic proxy creation | The full requested `rollupId` equals the manager's own network ID. |

L1 `EEZ` errors are:

| Canonical declaration | Selector | Reverting context | Payload values and condition |
|---|---|---|---|
| `error InvalidProof();` | `0x09bde339` | Batch proof verification | A selected proof-system call returns `false`. A verifier revert is forwarded instead. |
| `error PostBatchReentry();` | `0x8b4f56d9` | `postAndVerifyBatch` | The batch-global transient entry table is already non-empty on entry. |
| `error NotRollupContract();` | `0x690969c2` | `setStateRoot` | `msg.sender` is not the registered manager for the supplied rollup ID. |
| `error RollupBatchActiveThisBlock(uint256 rollupId);` | `0x033feec7` | `setStateRoot` | `verificationByRollup[rollupId].lastVerifiedBlock == block.number`. The argument is the supplied rollup ID. |
| `error InvalidRollupContract();` | `0xd0e1ecec` | `registerRollup` | The supplied manager is the zero address or the `EEZ` address. |
| `error InsufficientRollupBalance();` | `0xe851b378` | State-delta application | A negative `etherDelta` exceeds the named rollup's book balance. |
| `error EtherDeltaMismatch();` | `0xde315ee4` | Entry finalization | The signed sum of state-delta ETH changes differs from the entry's observed net ETH flow. |
| `error ResidualEntryEtherIn();` | `0xf1df384f` | Immediate zero-hash execution or `executeL2TX` | A no-value top-level path begins with a non-zero entry ETH accumulator. |
| `error StateRootMismatch(uint256 rollupId);` | `0x78cb4214` | State-delta application | A delta's `currentState` differs from the live root. The argument is that delta's rollup ID. |
| `error ExecutionNotInCurrentBlock(uint256 rollupId);` | `0x2ae204bd` | L1 proxy dispatch or `executeL2TX` | The routed rollup's `lastVerifiedBlock` differs from `block.number`. The argument is the routed or supplied rollup ID. |
| `error L2TXNotAllowedDuringExecution();` | `0xbd2663f5` | `executeL2TX` | Tagged replay is already active. |
| `error SetStateRootNotAllowedDuringExecution();` | `0xd161d374` | `setStateRoot` | Tagged replay is already active. |
| `error TransientCountExceedsEntries();` | `0xdd148d75` | Batch structural validation | `transientExecutionEntryCount > entries.length`. |
| `error TransientLookupCallCountExceedsLookupCalls();` | `0x68888636` | Batch structural validation | `transientLookupCallCount > l1ToL2lookupCalls.length`. |
| `error TransientLookupCallsWithoutTransientEntries();` | `0x61fcacac` | Batch structural validation | The transient lookup count is non-zero while the transient entry count is zero. |
| `error InvalidProofSystemConfig();` | `0xa287649c` | Batch structural validation or key fetch | The proof-system/proof lengths, rollup set, registration, local index set, or returned verification-key vector violates §4.5.1. |
| `error DuplicateProofSystem(address proofSystem);` | `0x23ce5bbc` | Batch structural validation | The current proof-system address is zero or is not strictly greater than the previous address. The argument is the offending address. |
| `error RollupNotInBatch(uint256 rollupId);` | `0xf0b9be82` | Batch structural validation | A state-delta or root-pin rollup is absent from `rollupIdsWithProofSystems`. The argument is the offending ID. |
| `error UnconsumedL2ToL1Calls();` | `0xdd0c77c5` | L1 entry or failed-lookup finalization | The flat L2-to-L1 call cursor does not equal the active flat-array length. |
| `error UnconsumedL1ToL2Calls();` | `0xed4a913d` | L1 entry or failed-lookup finalization | The expected L1-to-L2 cursor does not equal the active expected-call-array length. |
| `error EntryDestinationNotInStateDeltas(uint256 rollupId);` | `0xe7e18c36` | Batch structural validation | An entry destination is absent from its own delta set. The argument is the destination ID. |
| `error LookupDestinationNotPinned(uint256 rollupId);` | `0x76e2810c` | Batch structural validation | A top-level lookup destination is absent from its own root-pin set. The argument is the destination ID. |
| `error CallSourceNotVerified(uint256 rollupId);` | `0x4d347cf3` | Batch structural validation | A flat call source is absent from its host entry's delta set or top-level lookup's pin set. The argument is the source ID. |
| `error ReentrantDestinationNotVerified(uint256 rollupId);` | `0xd7510cae` | Batch structural validation | An expected-call or nested-lookup destination is absent from its host routing set. The argument is the destination ID. |
| `error ReentrantDestinationMismatch(uint256 declared, uint256 actual);` | `0x612a8387` | Expected-call or nested-lookup consumption | The record's declared destination differs from the calling proxy's rollup. The arguments are the declared ID, then the actual ID. |
| `error StateDeltasNotStrictlyIncreasing(uint256 rollupId);` | `0xb185698a` | Batch structural validation | Delta IDs are zero, duplicate, or out of order. The argument is the first offending ID. |
| `error ExpectedStateRootsNotStrictlyIncreasing(uint256 rollupId);` | `0x119af6e2` | Batch structural validation | Root-pin IDs are zero, duplicate, or out of order. The argument is the first offending ID. |

`InvalidRollupContract()` is the only explicit validation error raised directly by
`registerRollup`. A manager callback can revert with arbitrary bytes, which `registerRollup`
forwards unchanged. A counter overflow uses Solidity's checked-arithmetic panic, and a no-code
callback target returns successfully because the callback has no return value.

L2 `EEZL2` errors are:

| Canonical declaration | Selector | Reverting context | Payload values and condition |
|---|---|---|---|
| `error Unauthorized();` | `0x82b42900` | `loadExecutionTable`, `executeIncomingCrossChainCall` | `msg.sender != SYSTEM_ADDRESS`. |
| `error InvalidRollupId();` | `0x5f115753` | `EEZL2` construction | The constructor receives reserved rollup ID zero. |
| `error ExecutionNotInCurrentBlock();` | `0xf9d330ad` | L2 proxy dispatch | `lastLoadBlock != block.number`. This no-argument error is distinct from L1 `ExecutionNotInCurrentBlock(uint256)`. |
| `error EtherTransferFailed();` | `0x6747a288` | Value-bearing L2-originated proxy dispatch | The empty-calldata value call to `SYSTEM_ADDRESS` returns `success == false`. |
| `error EmptyEntries();` | `0x574daa08` | `executeIncomingCrossChainCall` | The supplied entry array is empty. |
| `error ValueMismatch();` | `0xdd8e4af7` | `executeIncomingCrossChainCall` | `msg.value != value`. |
| `error EntryHashMismatch();` | `0xc2098b88` | `executeIncomingCrossChainCall` | The action hash computed from the explicit parameters differs from `entries[0].proxyEntryHash`. |
| `error UnconsumedIncomingCalls();` | `0x093a2b9f` | L2 entry or failed-lookup finalization | The flat incoming-call cursor does not equal the active flat-array length. |
| `error UnconsumedOutgoingCalls();` | `0x03ae6521` | L2 entry or failed-lookup finalization | The expected-outgoing cursor does not equal the active expected-call-array length. |

Reference manager failures visible during batch verification include `ThresholdNotMet`,
`ProofSystemNotAllowed`, and `BlockHashUnavailable`. A different manager can use different errors
while satisfying the manager interface, so their signatures are not part of `eez-evm@0.2-draft`.

Cached target revert bytes are forwarded raw rather than wrapped. Malformed counts or spans can
also produce an EVM bounds or arithmetic panic.

## A.6 Events

Appendix B.4 gives exact event ABIs. `BatchPosted` records completion of the batch transaction;
`L2ExecutionPerformed` records one applied L1 state delta; and `EntryExecuted` records completion of
one entry's replay checks. Events emitted inside a frame that later reverts do not survive.

---

*See [Appendix B](B-wire-formats.md) for canonical tuples, selectors, events, hashes, and vectors.*
