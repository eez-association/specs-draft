# 3. EVM Binding, Cross-Chain Proxy, and Delivery

## 3.1 EVM requirements

The EEZ binding uses ordinary EVM contracts, calls, CREATE2, Solidity ABI encoding, EVM logs, and
Ethereum `keccak256`. It adds no custom opcode or precompile. It does require the following
standard Cancun opcodes:

- EIP-1153 `TLOAD` and `TSTORE` for transaction-scoped replay state and proxy static-context
  detection;
- EIP-5656 `MCOPY` in the compiler-generated ABI and memory-copy paths; and
- EIP-4844 `BLOBHASH` when constructing the L1 proof public input.

Both the Ethereum settlement EVM and every execution-network EVM that deploys this binding MUST
execute a Cancun-or-later fork that implements those opcodes with Cancun-compatible semantics. A
network profile MUST pin that fork or activation rule, the chain ID, genesis or settlement
identity, deployed contract
addresses and code commitments, and any L2 predeploys.

This binding does not select a particular gas schedule beyond that minimum fork, a transaction
envelope, or fixed predeploy addresses. Those are network choices.

## 3.2 Proxy identity and state

A cross-chain proxy is the local representative of a remote `(rollupId, address)` pair. Both
managers store:

```solidity
struct ProxyInfo {
    address originalAddress;
    uint64 originalRollupId;
}

mapping(address proxy => ProxyInfo) authorizedProxies;
```

`authorizedProxies[p].originalAddress == address(0)` means that `p` is not authorized. L1 uses
rollup ID `0`; every `EEZL2` instance has an immutable non-zero `ROLLUP_ID`. A manager rejects a
proxy whose remote rollup ID equals its own network ID.

For remote address `A` on rollup `R`, manager `M` derives:

```text
salt     = keccak256(abi.encodePacked(uint256(R), address(A)))
initCode = CrossChainProxy.creationCode || abi.encode(M, A, R)
proxy    = low20(keccak256(0xff || M || salt || keccak256(initCode)))
```

The salt encodes the rollup ID first as 32 bytes and the address second as 20 bytes. It contains no
chain or deployment domain. The deploying manager address and exact creation code still affect the
final address. Appendix B gives the exact formula and links the normative
[creation-code artifact](fixtures/cross-chain-proxy-creation-code.json).

The usable proxy-identity domain is:

```text
A != address(0)
R <= type(uint64).max
R != manager network ID
```

The deployed contract does not reject the first two violations. If `A == address(0)`, it deploys
code and writes a `ProxyInfo` whose zero `originalAddress` remains the unauthorized sentinel. If
`R > type(uint64).max`, CREATE2 and the proxy immutable use the full `uint256`, while
`authorizedProxies` stores `uint64(R)` and subsequent manager dispatch uses that truncated value.
These inputs are non-canonical. Producers and profiles MUST NOT generate them; an implementation
that indexes existing transactions MUST reproduce the behavior above.

`createCrossChainProxy(A, R)` is permissionless, but it is not idempotent. After the same-network
check, every call attempts CREATE2. If the derived address already has the proxy code, the CREATE2
collision reverts through the Solidity contract-creation path; the call does not return the
existing address and emits no second creation event. During mutating replay, a manager attempts
creation only when the derived address is not authorized. Read-only replay cannot deploy and
reverts `LookupCallProxyNotDeployed` when a required source proxy has no code.

The proxy stores immutable manager, original address, and original rollup ID. Its selector dispatch
is transparent:

1. The payable fallback detects static context by self-calling `staticCheck()`. The self-call tries
   `TSTORE`; failure means the inherited context is static.
2. In a non-static context, fallback calls
   `executeCrossChainCall(msg.sender, msg.data)` on the manager with the full `msg.value`.
3. In a static context, fallback static-calls
   `staticCallLookup(msg.sender, msg.data)` on the manager with value fixed to zero.
4. `executeOnBehalf(address destination, bytes data)` directly calls `destination` with
   `msg.value` only when `msg.sender` is the manager. It returns the target's raw result or forwards
   its raw revert bytes.
5. A non-manager call with ABI-valid calldata whose selector is
   `executeOnBehalf(address,bytes)` does not fail an access check. It enters the same fallback path
   with the original caller, calldata, and value. Malformed matching-selector calldata can fail
   Solidity ABI decoding before the function body runs.
6. `staticCheck()` executes its `TSTORE` only when called by the proxy itself. A call from any other
   address enters the same fallback path.

Rules 5 and 6 are consensus-relevant selector-collision behavior. An implementation MUST NOT
replace them with unconditional only-manager or only-self reverts. On either fallback route, a
manager revert is forwarded byte-for-byte. A successful manager response MUST be a canonical ABI
encoding of one `bytes` return value; the proxy decodes it and returns the inner bytes. Malformed
successful return data fails ABI decoding.

## 3.3 Action hash

Every observed cross-chain action is identified by:

```text
crossChainCallHash = keccak256(abi.encode(
    uint256 targetRollupId,
    address targetAddress,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollupId
))
```

This uses `abi.encode`, not packed encoding. Field order is normative. The same hash appears in
entry, expected-call, and lookup records and joins an action observed during replay to a
precomputed result.

The manager fixes part of the identity at each entry point:

- L1 proxy dispatch sets `sourceRollupId = 0` and derives the target pair from the calling proxy;
- L2 proxy dispatch sets `sourceRollupId = ROLLUP_ID` and derives the target from the proxy;
- L2 inbound delivery sets `targetRollupId = ROLLUP_ID` and receives the other five fields; and
- static lookup sets `value = 0`.

## 3.4 Complete deployed ABI

This section specifies every creation input and runtime function of the three core contracts.
[Appendix B.3](B-wire-formats.md#b3-function-signatures-and-selectors) gives the canonical
signature strings, including the fully expanded struct tuples. Constructor and fallback entries
do not have function selectors.

### 3.4.1 Creation ABI

| Contract | Creation input | Mutability |
|---|---|---|
| `EEZ` | empty; the default constructor takes no arguments | non-payable |
| `EEZL2` | `constructor(uint256 _rollupId,address _systemAddress)` | non-payable |
| `CrossChainProxy` | `constructor(address _eez,address _originalAddress,uint256 _originalRollupId)` | non-payable |

`EEZL2` stores both arguments as immutables and reverts `InvalidRollupId()` when `_rollupId == 0`.
It does not separately reject a zero `_systemAddress`. `CrossChainProxy` stores all three
arguments as internal immutables and exposes no getters for them. Its deployed code has a payable
fallback and no `receive` entry. Neither manager has a fallback or `receive` entry.

### 3.4.2 Shared manager runtime ABI

Both `EEZ` and `EEZL2` expose:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x360d95b6` | `authorizedProxies(address)` | `view` | `(address originalAddress,uint64 originalRollupId)` |
| `0x1f314db1` | `computeCrossChainCallHash(uint256,address,uint256,bytes,address,uint256)` | `pure` | `bytes32` |
| `0xb761ba7e` | `computeCrossChainProxyAddress(address,uint256)` | `view` | `address` |
| `0x2dd72120` | `createCrossChainProxy(address,uint256)` | non-payable | `address proxy` |
| `0x9af53259` | `executeCrossChainCall(address,bytes)` | `payable` | `bytes result` |
| `0x37b99a56` | `executeInContextAndRevert(uint256)` | non-payable | none |
| `0x7aa4da2e` | `staticCallLookup(address,bytes)` | `view` | `bytes` |

`executeInContextAndRevert` is externally visible only to create an isolated EVM frame. It
accepts calls only from its own manager.

### 3.4.3 L1 runtime ABI

In addition to §3.4.2, `EEZ` exposes:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x199350cf` | `MAINNET_ROLLUP_ID()` | `view` | `uint256` |
| `0xd8422037` | `_transientExecutions(uint256)` | `view` | `(bytes32 proxyEntryHash,uint256 destinationRollupId,bytes returnData,uint256 callCount,bytes32 rollingHash)` |
| `0xd3f60360` | `_transientLookupCalls(uint256)` | `view` | `(bytes32 crossChainCallHash,uint256 destinationRollupId,bytes returnData,bool failed,uint256 callCount,bytes32 rollingHash)` |
| `0xd4ccaf87` | `attemptApplyImmediate(uint256)` | non-payable | none |
| `0xccdcf581` | `executeL2TX(uint256)` | non-payable | `bytes result` |
| `0x72e991d3` | `executionQueueIndex(uint256)` | `view` | `uint256` |
| `0x206bbf07` | `lastVerifiedBlock(uint256)` | `view` | `uint256` |
| `0xd1fc6b5a` | `postAndVerifyBatch(<B.1.5 tuple>)` | non-payable | none |
| `0x48cae3e2` | `queueLength(uint256)` | `view` | `uint256` |
| `0x559cd946` | `registerRollup(address,bytes32)` | non-payable | `uint256 rollupId` |
| `0xa3271832` | `rollupCounter()` | `view` | `uint256` |
| `0xb794e5a3` | `rollups(uint256)` | `view` | `(address rollupContract,bytes32 stateRoot,uint256 etherBalance)` |
| `0x2bdd1f16` | `setStateRoot(uint256,bytes32)` | non-payable | none |

`attemptApplyImmediate` is a self-call helper and accepts calls only from `EEZ`. The three manual
views `lastVerifiedBlock`, `queueLength`, and `executionQueueIndex` expose the corresponding
fields of `verificationByRollup[_rollupId]`. There is no public getter for a persistent queue
element or for the persistent lookup queue.

### 3.4.4 L2 runtime ABI

In addition to §3.4.2, `EEZL2` exposes:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0xb5ed5559` | `ROLLUP_ID()` | `view` | `uint256` |
| `0x3434735f` | `SYSTEM_ADDRESS()` | `view` | `address` |
| `0xf882a0ad` | `executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,<B.2.3[]>,<B.2.4[]>)` | `payable` | `bytes result` |
| `0xc6109dc9` | `executionIndex()` | `view` | `uint256` |
| `0xf76c9229` | `executions(uint256)` | `view` | `(bytes32 proxyEntryHash,uint256 callCount,bytes returnData,bytes32 rollingHash)` |
| `0xa0d8dd9d` | `lastLoadBlock()` | `view` | `uint256` |
| `0xc1b4427c` | `loadExecutionTable(<B.2.3[]>,<B.2.4[]>)` | non-payable | none |
| `0xd3886c9f` | `lookupCalls(uint256)` | `view` | `(bytes32 crossChainCallHash,bytes returnData,bool failed,uint256 callCount,bytes32 rollingHash)` |

The angle-bracket tuple references in the two tables are display abbreviations only. They MUST
be expanded exactly as specified in Appendix B before computing a selector or encoding calldata.
The L1 and L2 `ExecutionEntry` and `LookupCall` names denote different tuple families.

### 3.4.5 Proxy runtime ABI and getter behavior

`CrossChainProxy` exposes a payable fallback and these functions:

| Selector | Canonical signature | Mutability | ABI return |
|---|---|---|---|
| `0x532f0839` | `executeOnBehalf(address,bytes)` | `payable` | none |
| `0x9f149e1b` | `staticCheck()` | non-payable | none |

Although `executeOnBehalf` declares no ABI return, it returns the target's raw success bytes with
assembly and forwards the target's raw revert bytes on failure. A caller MUST NOT expect a
standard ABI value solely from this declaration.

The generated getters have these Solidity ABI rules:

- a missing mapping key returns the all-zero value or tuple;
- an array getter with an index outside the array reverts with Solidity panic selector
  `0x4e487b71` and panic code `0x32`;
- a public array-of-struct getter returns only the direct members listed above; it omits every
  nested array member; and
- return member order and widths are exact, including `uint64 originalRollupId`.

The manual L1 verification views return zero for an uninitialized rollup ID because the
underlying mapping entry and queue length are zero.

## 3.5 Inbound L2 delivery

Only the profile-selected immutable `SYSTEM_ADDRESS` can call
`executeIncomingCrossChainCall`. The function:

1. requires a non-empty L2 entry array and `msg.value == value`;
2. replaces the L2 execution and lookup tables;
3. computes the action hash from the five explicit action parameters and `ROLLUP_ID`;
4. requires that hash to equal `entries[0].proxyEntryHash`;
5. replays entry zero and checks its rolling hash and both consumption cursors;
6. sets the next execution index to one; and
7. returns the entry's cached `returnData`.

The contract does not mint value. It requires value to arrive with the call. It also does not
compare the explicit action parameters with `entries[0].incomingCalls[0]` field by field. A
network profile MUST define the value source and the deterministic construction linking the
explicit action, L1 objects, L2 objects, and transaction.

The implementation relies on an execution-layer precondition that is not enforced by `EEZL2`.
`SYSTEM_ADDRESS` MUST be node-controlled and unable to execute reentrant code, or the profile MUST
pin an equivalent guard that prevents table replacement during execution. The delivery envelope
MUST permit at most one top-level `executeIncomingCrossChainCall` per transaction. The function
does not reset all transaction-scoped replay state before it starts; it relies on zero-valued
transient storage at transaction entry. A second or reentrant inbound call in the same transaction
is outside the conforming envelope and has no profile-portable fresh-cursor semantics.

EEZ does not select the L2 transaction that carries this call. A profile MUST pin its byte
serialization, authorization or signature rule, sender, nonce, fee fields, gas limit, placement,
value-supply rule, and reconstruction inputs. A network cannot claim deterministic derivation
while any of those values remains implicit.

## 3.6 EVM call schemes

An authorized proxy reached through ordinary `CALL` can perform mutating dispatch. A proxy reached
in a static context resolves through `staticCallLookup`; value is fixed to zero and resolution does
not mutate protocol state.

The current contracts contain no dedicated opcode check that names `DELEGATECALL` or `CALLCODE`.
Executing proxy code in the caller's storage context does not make that caller an authorized proxy,
so manager authorization normally fails. A profile MAY reject those call schemes as producer
inputs, but an implementation MUST NOT invent a core custom error or claim an opcode rule that this
binding does not implement.

A cross-chain proxy is an identity and dispatch adapter, not a code-equivalent copy of the remote
contract. Code and balance inspection of the proxy observes the proxy, and block-environment
opcodes observe the EVM on which the destination executes. The destination sees the deterministic
proxy as `msg.sender`. A proxy also forwards manager and destination reverts without adding an
origin envelope, so an application cannot rely on revert bytes alone to distinguish missing EEZ
execution data from an application failure.

Reentrant proxy calls, static and failed lookups, and forced rollback are current execution
behavior, not fields reserved only for a future protocol. Their exact semantics are in §4.

---

*Next: [§4 EEZ Execution State Machines](04-execution-model.md).*
