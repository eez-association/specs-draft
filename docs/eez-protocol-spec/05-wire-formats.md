# 5. Wire Formats and Conformance Vectors

These layouts are the canonical encodings every implementation MUST reproduce. All multi-byte ABI
words are big-endian 32-byte slots per the Solidity ABI. `keccak256` is Ethereum Keccak, not NIST
SHA3-256.

Two distinct hashing disciplines appear throughout:

- **`abi.encode(...)`** — positional, 32-byte-aligned ABI encoding with head and tail sections for
  dynamic types.
- **`abi.encodePacked(...)`** — raw concatenation with each value at its natural width. It has no
  length prefix for `bytes` or `string`.

## 5.1 Core struct layouts

Field order and types are normative. Any reordering changes every derived hash.

### `StateDelta`

Canonical tuple: `(uint256,bytes32,bytes32,int256)`

| # | Field | Type | Notes |
|---|---|---|---|
| 0 | `rollupId` | `uint256` | |
| 1 | `currentState` | `bytes32` | Expected pre-state |
| 2 | `newState` | `bytes32` | Post-state |
| 3 | `etherDelta` | `int256` | Signed, two's-complement ABI word |

### `L2ToL1Call`

Canonical tuple: `(address,uint256,bytes,address,uint256,uint256)`

| # | Field | Type | Notes |
|---|---|---|---|
| 0 | `targetAddress` | `address` | |
| 1 | `value` | `uint256` | |
| 2 | `data` | `bytes` | Dynamic |
| 3 | `sourceAddress` | `address` | |
| 4 | `sourceRollupId` | `uint256` | |
| 5 | `revertSpan` | `uint256` | `0` = normal; positive = forced-revert span |

### `ExpectedL1ToL2Call`

Canonical tuple: `(bytes32,uint256,bytes)`

| # | Field | Type | Notes |
|---|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` | |
| 1 | `callCount` | `uint256` | Nested-frame iterations over the parent call array |
| 2 | `returnData` | `bytes` | Dynamic; precomputed success return |

### `ExecutionEntry`

Canonical tuple:

```text
((uint256,bytes32,bytes32,int256)[],
 bytes32,
 uint256,
 (address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 uint256,
 bytes,
 bytes32)
```

| # | Field | Type |
|---|---|---|
| 0 | `stateDeltas` | `StateDelta[]` |
| 1 | `proxyEntryHash` | `bytes32` |
| 2 | `destinationRollupId` | `uint256` |
| 3 | `L2ToL1Calls` | `L2ToL1Call[]` |
| 4 | `expectedL1ToL2Calls` | `ExpectedL1ToL2Call[]` |
| 5 | `callCount` | `uint256` |
| 6 | `returnData` | `bytes` |
| 7 | `rollingHash` | `bytes32` |

`proxyEntryHash == bytes32(0)` identifies an immediate or L2-transaction entry.

### `LookupCall`

Canonical tuple:

```text
(bytes32,uint256,bytes,bool,uint64,uint64,
 (address,uint256,bytes,address,uint256,uint256)[],
 bytes32)
```

| # | Field | Type |
|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` |
| 1 | `destinationRollupId` | `uint256` |
| 2 | `returnData` | `bytes` |
| 3 | `failed` | `bool` |
| 4 | `callNumber` | `uint64` |
| 5 | `lastNestedActionConsumed` | `uint64` |
| 6 | `calls` | `L2ToL1Call[]` |
| 7 | `rollingHash` | `bytes32` |

The lookup key is:

```text
(crossChainCallHash, destinationRollupId, callNumber, lastNestedActionConsumed)
```

### `RollupIdWithProofSystems`

Canonical tuple: `(uint256,uint64[])`

| # | Field | Type |
|---|---|---|
| 0 | `rollupId` | `uint256` |
| 1 | `proofSystemIndex` | `uint64[]` |

### `ProofSystemBatchPerVerificationEntries`

| # | Field | Type |
|---|---|---|
| 0 | `entries` | `ExecutionEntry[]` |
| 1 | `l1ToL2lookupCalls` | `LookupCall[]` |
| 2 | `transientExecutionEntryCount` | `uint256` |
| 3 | `transientLookupCallCount` | `uint256` |
| 4 | `proofSystems` | `address[]` |
| 5 | `rollupIdsWithProofSystems` | `RollupIdWithProofSystems[]` |
| 6 | `crossProofSystemInteractions` | `bytes32` |
| 7 | `blobIndices` | `uint256[]` |
| 8 | `callData` | `bytes` |
| 9 | `proofs` | `bytes[]` |
| 10 | `blockNumber` | `uint64` |

## 5.2 Cross-chain call hash

```text
crossChainCallHash = keccak256(abi.encode(
    uint256 targetRollupId,
    address targetAddress,
    uint256 value,
    bytes data,
    address sourceAddress,
    uint256 sourceRollupId))
```

This uses `abi.encode`, not packed encoding. Field order is target rollup, target address, value,
data, then the source pair. `L2ToL1Call` uses a different order and has no `targetRollupId`; do
not derive this hash from that struct layout.

Caller-specific bindings:

- L1 `executeCrossChainCall` sets `sourceRollupId = MAINNET_ROLLUP_ID = 0` and takes
  `targetRollupId` from the proxy.
- L2 `executeCrossChainCall` and `staticCallLookup` set `sourceRollupId = ROLLUP_ID`.
- `staticCallLookup` sets `value = 0`.

## 5.3 Cross-chain proxy CREATE2 derivation

`CrossChainProxy` is deployed once per `(originalRollupId, originalAddress)` pair from the manager.
Constructor arguments are `(address eez, address originalAddress, uint256 originalRollupId)`.

```text
salt = keccak256(
    abi.encodePacked(uint256 originalRollupId, address originalAddress))

initCode =
    CrossChainProxy.creationCode
    || abi.encode(eez, originalAddress, originalRollupId)

bytecodeHash = keccak256(initCode)

proxyAddress = address(uint160(uint256(keccak256(abi.encodePacked(
    bytes1(0xff), eez, salt, bytecodeHash)))))
```

The salt is 52 bytes: a 32-byte `uint256` followed by a 20-byte address. It has no domain or
`block.chainid` term. `eez` is the deploying manager's address.

The exact creation code is 1111 bytes:

```text
keccak256(creationCode) =
0xb674ac54ef248bfe921085a167b225ed55b29a26f4d16538d568a88244d7c4af

0x60e03461009557601f61045738819003918201601f19168301916001600160401b038311848410176100995780849260609460405283398101031261009557610047816100ad565b906040610056602083016100ad565b9101519160805260a05260c05260405161039590816100c28239608051818181610140015281816102ac015261032f015260a05181505060c051815050f35b5f80fd5b634e487b7160e01b5f52604160045260245ffd5b51906001600160a01b03821682036100955756fe60806040526004361061023e575f3560e01c8063532f08391461002b57639f149e1b0361023e57610096565b6040366003190112610092576004356001600160a01b0381168103610092576024359067ffffffffffffffff821161009257366023830112156100925781600401359167ffffffffffffffff8311610092573660248483010111610092576024019061013d565b5f80fd5b34610092575f366003190112610092573330036100b2575f805d005b61023e565b634e487b7160e01b5f52604160045260245ffd5b90601f8019910116810190811067ffffffffffffffff8211176100ed57604052565b6100b7565b67ffffffffffffffff81116100ed57601f01601f191660200190565b3d15610138573d9061011f826100f2565b9161012d60405193846100cb565b82523d5f602084013e565b606090565b337f00000000000000000000000000000000000000000000000000000000000000006001600160a01b0316036100b257825f9392849360405192839283378101848152039134905af161018e61010e565b901561019c57602081519101f35b602081519101fd5b6001600160a01b0390911681526040602082018190528101829052606091805f848401375f828201840152601f01601f1916010190565b6020818303126100925780519067ffffffffffffffff8211610092570181601f820112156100925780519061020f826100f2565b9261021d60405194856100cb565b8284526020838301011161009257815f9260208093018386015e8301015290565b5f806040516020810190639f149e1b60e01b8252600481526102616024826100cb565b519082305af161026f61010e565b50610304575f806040516020810190633d526d1760e11b82526102a88161029a3633602484016101a4565b03601f1981018352826100cb565b51907f00000000000000000000000000000000000000000000000000000000000000005afa6102d561010e565b90805b6102ea575b1561019c57602081519101f35b90806020806102fe935183010191016101db565b906102dd565b5f806040516020810190639af5325960e01b825261032a8161029a3633602484016101a4565b5190347f00000000000000000000000000000000000000000000000000000000000000005af161035861010e565b90806102d856fea26469706673582212201ea9988aab655e2b566c7598029bd3fc167deceabd65dfbe04e27a732346a17c64736f6c63430008220033
```

The full byte sequence, length, and hash are normative.

## 5.4 Rolling hash

The entry accumulator starts at `bytes32(0)`. All folds use `abi.encodePacked`:

```text
CALL_BEGIN (0x01):
    h = keccak256(abi.encodePacked(
        bytes32 previous, uint8(0x01), uint256 callNumber))

CALL_END (0x02):
    h = keccak256(abi.encodePacked(
        bytes32 previous, uint8(0x02), uint256 callNumber,
        bool success, bytes returnData))

NESTED_BEGIN (0x03):
    h = keccak256(abi.encodePacked(
        bytes32 previous, uint8(0x03), uint256 nestedNumber))

NESTED_END (0x04):
    h = keccak256(abi.encodePacked(
        bytes32 previous, uint8(0x04), uint256 nestedNumber))
```

The tag is one byte. Call and nested numbers are 32 bytes and one-indexed. `success` is one byte.
`returnData` is raw bytes without a length prefix.

Lookup sub-calls use a different, untagged scheme:

```text
computedHash = keccak256(abi.encodePacked(
    bytes32 previous, bool success, bytes returnData))
```

The lookup accumulator also starts at `bytes32(0)`.

## 5.5 Public-inputs hash

```text
entryHashes[i]      = keccak256(abi.encode(entries[i]))
lookupCallHashes[i] = keccak256(abi.encode(l1ToL2lookupCalls[i]))
blobHashes[i]       = blobhash(blobIndices[i])

sharedPublicInput = keccak256(abi.encodePacked(
    abi.encode(entryHashes),
    abi.encode(lookupCallHashes),
    abi.encode(blobHashes),
    keccak256(callData),
    crossProofSystemInteractions))
```

`abi.encode(bytes32[])` is the full dynamic encoding: one length word followed by the elements.
The three encodings are concatenated with the two trailing `bytes32` values.

For proof system `k`, fold rollups in strictly increasing rollup-ID order:

```text
acc_k = bytes32(0)

for each rollup r whose proofSystemIndex contains k:
    acc_k = keccak256(abi.encode(
        bytes32 acc_k,
        uint256 rollupId_r,
        bytes32 vkey_rk,
        bytes32 blockHash_r,
        uint256 timestamp_r))

publicInputsHash[k] =
    keccak256(abi.encodePacked(sharedPublicInput, acc_k))
```

`vkey_rk` is returned by the rollup manager's
`checkProofSystemsAndGetVkeys(subset)`.
`(blockHash_r, timestamp_r)` comes from
`getTimestampAndBlockHash(batch.blockNumber)`.
`crossProofSystemInteractions` is an opaque `bytes32` domain separator.

Every proof system MUST return true for its proof and public-input hash.

## 5.6 Inbound delivery ABI

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

This ABI defines the contract call only. The transaction envelope is a network concern.

## 5.7 `postAndVerifyBatch` selector

```text
selector = 0x51dd0af6
```

Canonical function signature:

```text
postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes,bytes32)[],(bytes32,uint256,bytes,bool,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],bytes32)[],uint256,uint256,address[],(uint256,uint64[])[],bytes32,uint256[],bytes,bytes[],uint64))
```

The single argument is one `ProofSystemBatchPerVerificationEntries` tuple. Its first two nested
tuples are `ExecutionEntry[]` and `LookupCall[]`.

## 5.8 Conformance vectors

### Vector 1: cross-chain call hash

| Input | Value |
|---|---|
| `targetRollupId` | `1` |
| `targetAddress` | `0x00000000000000000000000000000000deadbeef` |
| `value` | `1000000000000000000` |
| `data` | `0xdeadbeef` |
| `sourceAddress` | `0x0000000000000000000000000000000000c0ffee` |
| `sourceRollupId` | `0` |

```text
crossChainCallHash =
0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2
```

### Vector 2: cross-chain proxy address

| Input | Value |
|---|---|
| `eez` | `0x00000000000000000000000000000000000ee200` |
| `originalAddress` | `0x0000000000000000000000000000000000c0ffee` |
| `originalRollupId` | `1` |

```text
salt =
0x9b795495c996503b00c5938a264389c4df5c002802eae27e9463f48ea7aafdd5

creationCode length = 1111 bytes

keccak256(creationCode) =
0xb674ac54ef248bfe921085a167b225ed55b29a26f4d16538d568a88244d7c4af

bytecodeHash =
0xc9400233a674b91a20b7dbeef0f767ff00795d47254a65ec4eedb379028792fe

proxyAddress =
0xF29a3823d1BA0BF93A46fAA6e919Ff01D9E15006
```

### Vector 3: rolling hash

Start with `h = bytes32(0)`, `callNumber = 1`, `success = true`, and
`returnData = 0x01`.

```text
after CALL_BEGIN(1) =
0xa578faae9568ec79d80e92f83b4d08a4537677b5145aef1ab04b0c67dd76c63f

after CALL_END(1,true,0x01) =
0x696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d
```

### Vector 4: execution entry

```text
stateDeltas = [
  (rollupId = 1, currentState = 0xaa, newState = 0xbb, etherDelta = 0)
]
proxyEntryHash = Vector 1
destinationRollupId = 1
L2ToL1Calls = [
  (
    targetAddress = 0x00000000000000000000000000000000deadbeef,
    value = 0,
    data = 0xdeadbeef,
    sourceAddress = 0x0000000000000000000000000000000000c0ffee,
    sourceRollupId = 0,
    revertSpan = 0
  )
]
expectedL1ToL2Calls = []
callCount = 1
returnData = 0x
rollingHash = Vector 3 final

abi.encode(entry) =
0x0000000000000000000000000000000000000000000000000000000000000020
  0000000000000000000000000000000000000000000000000000000000000100
  6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2
  0000000000000000000000000000000000000000000000000000000000000001
  00000000000000000000000000000000000000000000000000000000000001a0
  00000000000000000000000000000000000000000000000000000000000002e0
  0000000000000000000000000000000000000000000000000000000000000001
  0000000000000000000000000000000000000000000000000000000000000300
  696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d
  0000000000000000000000000000000000000000000000000000000000000001
  0000000000000000000000000000000000000000000000000000000000000001
  00000000000000000000000000000000000000000000000000000000000000aa
  00000000000000000000000000000000000000000000000000000000000000bb
  0000000000000000000000000000000000000000000000000000000000000000
  0000000000000000000000000000000000000000000000000000000000000001
  0000000000000000000000000000000000000000000000000000000000000020
  00000000000000000000000000000000000000000000000000000000deadbeef
  0000000000000000000000000000000000000000000000000000000000000000
  00000000000000000000000000000000000000000000000000000000000000c0
  0000000000000000000000000000000000000000000000000000000000c0ffee
  0000000000000000000000000000000000000000000000000000000000000000
  0000000000000000000000000000000000000000000000000000000000000000
  0000000000000000000000000000000000000000000000000000000000000004
  deadbeef00000000000000000000000000000000000000000000000000000000

entryHash =
0xf55a0b2f661170eb3d02881188f6fc27ce192d6653a2c45c3d6b9bc8e368ce39
```

### Vector 5: one rollup and one proof system

Use Vector 4 as the only entry, with no lookups, no blobs, empty `callData`, zero
`crossProofSystemInteractions`, rollup ID `1`, verification key `0x100`, and `blockNumber = 0`.

```text
keccak256(callData) =
0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470

sharedPublicInput =
0x9c4e7a3a4b9037140a02de516a8b3200968754093f4e585e1fd742b26adcb790

acc =
0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700

publicInputsHash[0] =
0xdcd57c2f57d42af6165678f3adbb7e07e0b4ba60765bd2e4c4a76921e8daa891
```

### Vector 6: two rollups and two proof systems

Rollup `1` lists proof-system indices `[0, 1]` with keys `[0x100, 0x101]`. Rollup `2` lists
index `[1]` with key `[0x201]`. Both use zero timestamp and block hash.

```text
sharedPublicInput =
0x9c4e7a3a4b9037140a02de516a8b3200968754093f4e585e1fd742b26adcb790

acc(PS0) =
0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700

publicInputsHash[0] =
0xdcd57c2f57d42af6165678f3adbb7e07e0b4ba60765bd2e4c4a76921e8daa891

acc(PS1) =
0x1d1754cd9a1ce70d42038aeb1110bad91b9500d6a586e07f93ffb690a18222e6

publicInputsHash[1] =
0x8821cb36904d46326985e8800791e6da3536634a68905c8823199772a2ba6643
```

### Vector 7: lookup and non-empty calldata

Use Vector 4 plus this lookup:

```text
crossChainCallHash = 0x1234
destinationRollupId = 1
returnData = 0xabcd
failed = true
callNumber = 0
lastNestedActionConsumed = 0
calls = []
rollingHash = 0
callData = 0xcafebabe
crossProofSystemInteractions = keccak256("xpsi")
```

Results:

```text
lookupCallHash =
0x30690221b19c8bbd95cd1379a35163a58e1c340e5689618d62583084ae4e0d43

keccak256(callData) =
0x6fe2683bd1d27cbb7a05c570693bea39e0c082ed16722e5ecadcfb7cfdbd20db

crossProofSystemInteractions =
0x6043818a14fa81cd43674dca578863f795ae1551407871464d237744a4ac209e

sharedPublicInput =
0x0c75410a2dca7acce877a745705bde1721f360436e4732068d0e013c4bbd96d8

acc =
0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700

publicInputsHash[0] =
0x5b37b84b0735b32baf70818d318fdba9ab43eaa16eb4cb8f9eb3fee990f7736d
```

---

*Back to the [EEZ specification index](index.md).*
