# Appendix E. Wire Formats & Conformance Vectors

Normative byte-exact wire formats for the Rollup0 protocol. These layouts are the canonical
encodings every implementation MUST reproduce for `rollup0-v0`. Contract-defined surfaces come
from `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`; the DA codec and
signed legacy system-transaction framing come from
`eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c`, as selected by §0. All multi-byte ABI
words are big-endian 32-byte slots per the Solidity ABI; `keccak256` is Ethereum Keccak-256
(not NIST SHA3-256).

Two distinct hashing disciplines appear throughout:

- **`abi.encode(...)`** — positional, 32-byte-aligned ABI encoding (head/tail for dynamic
  types). Used wherever structured fields with their own type widths are committed.
- **`abi.encodePacked(...)`** — raw concatenation with each value at its natural width
  (`uint8` → 1 byte, `uint256` → 32 bytes, `address` → 20 bytes, `bytes`/`string` → raw, no
  length prefix). Used for the rolling hash, the CREATE2 salt/address, and the public-inputs
  packing step.

---

## E.1 Core struct layouts (ABI)

Field order and types are normative — `abi.encode` lays them out positionally, so any
reordering changes every derived hash or layout-sensitive selector. L1 and L2 deliberately use
different struct families; a client MUST NOT ABI-encode an L1 struct where an L2 struct is
required.

### `StateDelta`  `(uint256,bytes32,bytes32,int256)`

| # | field | type | notes |
|---|---|---|---|
| 0 | `rollupId` | `uint256` | |
| 1 | `currentState` | `bytes32` | expected pre-state; checked `== rollups[rollupId].stateRoot` |
| 2 | `newState` | `bytes32` | post-state |
| 3 | `etherDelta` | `int256` | **signed** (two's-complement in the ABI word) |

Static struct (no dynamic members): encodes inline as 4 consecutive 32-byte words.

### `L2ToL1Call`  `(address,uint256,bytes,address,uint256,uint256)`

| # | field | type | notes |
|---|---|---|---|
| 0 | `targetAddress` | `address` | |
| 1 | `value` | `uint256` | |
| 2 | `data` | `bytes` | **dynamic** |
| 3 | `sourceAddress` | `address` | |
| 4 | `sourceRollupId` | `uint256` | |
| 5 | `revertSpan` | `uint256` | 0 = normal; N>0 = forced-revert span |

Dynamic (contains `bytes`): the tuple head holds offsets for `data`.

### `ExpectedL1ToL2Call`  `(bytes32,uint256,bytes)`

| # | field | type | notes |
|---|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` | |
| 1 | `callCount` | `uint256` | iterations of the nested frame over the parent `L2ToL1Calls[]` |
| 2 | `returnData` | `bytes` | **dynamic**; pre-computed success return |

Dynamic.

### L1 `ExpectedLookup`

Canonical tuple:

```
(bytes32,bytes,bool,uint64,uint64,uint64,
 (address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],uint256,bytes32)
```

| # | field | type | notes |
|---|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` | |
| 1 | `returnData` | `bytes` | **dynamic** |
| 2 | `failed` | `bool` | `true` for a caught reverting nested call |
| 3 | `l2ToL1CallNumber` | `uint64` | live flat-call cursor |
| 4 | `lastL1ToL2CallConsumed` | `uint64` | live reentrant cursor |
| 5 | `executingLookupIndex` | `uint64` | 0 = host; `k` = inside host lookup `k-1` |
| 6 | `l2ToL1Calls` | `L2ToL1Call[]` | sub-execution call table |
| 7 | `expectedL1ToL2Calls` | `ExpectedL1ToL2Call[]` | sub-execution reentrant table |
| 8 | `callCount` | `uint256` | top-level iterations of the sub-execution |
| 9 | `rollingHash` | `bytes32` | untagged for static mode; tagged for reverted mode |

Nested lookup matching uses fields 0, 3, 4, and 5. It is entry-scoped and has no
`destinationRollupId`.

### L1 `ExecutionEntry`

Canonical tuple:

```
((uint256,bytes32,bytes32,int256)[],bytes32,uint256,
 (address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 (bytes32,bytes,bool,uint64,uint64,uint64,
  (address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,bytes)[],uint256,bytes32)[],
 uint256,bytes,bytes32)
```

| # | field | type | notes |
|---|---|---|---|
| 0 | `stateDeltas` | `StateDelta[]` | **dynamic** |
| 1 | `proxyEntryHash` | `bytes32` | the entry trigger's `crossChainCallHash`; `bytes32(0)` = immediate / L2-tx |
| 2 | `destinationRollupId` | `uint256` | |
| 3 | `l2ToL1Calls` | `L2ToL1Call[]` | **dynamic**; full flat call list |
| 4 | `expectedL1ToL2Calls` | `ExpectedL1ToL2Call[]` | **dynamic** |
| 5 | `expectedLookups` | `ExpectedLookup[]` | **dynamic**; entry-scoped nested lookup table |
| 6 | `callCount` | `uint256` | top-level iterations |
| 7 | `returnData` | `bytes` | **dynamic** |
| 8 | `rollingHash` | `bytes32` | expected accumulator after the entry completes |

Dynamic. `entryHash = keccak256(abi.encode(entry))` (see E.5 and E.10).

### `ExpectedStateRootPerRollup`  `(uint256,bytes32)`

| # | field | type |
|---|---|---|
| 0 | `rollupId` | `uint256` |
| 1 | `stateRoot` | `bytes32` |

### L1 `LookupCall`

Canonical tuple:

```
(bytes32,uint256,bytes,bool,
 (address,uint256,bytes,address,uint256,uint256)[],
 (bytes32,uint256,bytes)[],
 (bytes32,bytes,bool,uint64,uint64,uint64,
  (address,uint256,bytes,address,uint256,uint256)[],
  (bytes32,uint256,bytes)[],uint256,bytes32)[],
 uint256,bytes32,(uint256,bytes32)[])
```

| # | field | type | notes |
|---|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` | |
| 1 | `destinationRollupId` | `uint256` | |
| 2 | `returnData` | `bytes` | **dynamic** |
| 3 | `failed` | `bool` | true ⇒ replayed as a revert |
| 4 | `l2ToL1Calls` | `L2ToL1Call[]` | static or reverted sub-execution calls |
| 5 | `expectedL1ToL2Calls` | `ExpectedL1ToL2Call[]` | reverted-mode reentrant table |
| 6 | `expectedLookups` | `ExpectedLookup[]` | reverted-mode nested lookup table |
| 7 | `callCount` | `uint256` | reverted-mode top-level iterations; 0 in static mode |
| 8 | `rollingHash` | `bytes32` | untagged in static mode; tagged in reverted mode |
| 9 | `expectedStateRoots` | `ExpectedStateRootPerRollup[]` | live-root match pins |

Dynamic. A top-level candidate matches when `crossChainCallHash` matches and every
`expectedStateRoots[i]` equals the live root for its `rollupId`. The contract scans candidates;
a stale pin skips the candidate instead of reverting. `destinationRollupId` selects the persistent
queue but, at `5c51e02`, is not an additional comparison in the top-level match predicate.

### `RollupIdWithProofSystems`  `(uint256,uint64[])`

| # | field | type | notes |
|---|---|---|---|
| 0 | `rollupId` | `uint256` | |
| 1 | `proofSystemIndex` | `uint64[]` | **dynamic**; strictly-increasing indices into `proofSystems[]` |

### `ProofSystemBatchPerVerificationEntries` (the `postAndVerifyBatch` argument)

Field order (EEZ.sol:49–61), normative:

| # | field | type |
|---|---|---|
| 0 | `entries` | `ExecutionEntry[]` |
| 1 | `l1ToL2lookupCalls` | `LookupCall[]` |
| 2 | `transientExecutionEntryCount` | `uint256` |
| 3 | `transientLookupCallCount` | `uint256` |
| 4 | `proofSystems` | `address[]` (strictly increasing) |
| 5 | `rollupIdsWithProofSystems` | `RollupIdWithProofSystems[]` (strictly increasing by `rollupId`) |
| 6 | `crossProofSystemInteractions` | `bytes32` |
| 7 | `blobIndices` | `uint256[]` |
| 8 | `callData` | `bytes` |
| 9 | `proofs` | `bytes[]` (one per `proofSystems` entry) |
| 10 | `blockNumber` | `uint64` |

### Lean L2 struct family

The L2 source declares separate structs in `IEEZL2.sol`. Their canonical layouts are:

| Struct | Canonical tuple |
|---|---|
| `CrossChainCall` | `(address,uint256,bytes,address,uint256,uint256)` |
| `ExpectedOutgoingCrossChainCall` | `(bytes32,uint256,bytes)` |
| L2 `ExpectedLookup` | `(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)` |
| L2 `ExecutionEntry` | `(bytes32,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)` |
| L2 `LookupCall` | `(bytes32,bytes,bool,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)` |

The L2 `ExecutionEntry` fields are, in order:
`proxyEntryHash`, `incomingCalls`, `expectedOutgoingCalls`, `expectedLookups`, `callCount`,
`returnData`, `rollingHash`. The L2 `LookupCall` fields are, in order:
`crossChainCallHash`, `returnData`, `failed`, `incomingCalls`, `expectedOutgoingCalls`,
`expectedLookups`, `callCount`, `rollingHash`. L2 omits `StateDelta`,
`destinationRollupId`, and `ExpectedStateRootPerRollup`.

For any of these dynamic structs, Solidity `abi.encode(structValue)` encodes a single dynamic
tuple argument and therefore begins with the outer offset word `0x20`. Function calldata instead
starts with the 4-byte selector followed by the argument head; clients MUST use the contextually
correct form.

---

## E.2 `crossChainCallHash`

Single formula used everywhere (L1 `EEZ` and L2 `EEZL2`, `EEZBase.computeCrossChainCallHash`):

```
crossChainCallHash = keccak256(abi.encode(
    uint256  targetRollupId,
    address  targetAddress,
    uint256  value,
    bytes    data,
    address  sourceAddress,
    uint256  sourceRollupId))
```

`abi.encode` (not packed). Field order is: target rollup, target address, value, data,
then the source pair. The L2ToL1Call struct uses a different order and has no `targetRollupId`
member — do NOT derive the hash from the struct layout. The same value populates
`ExecutionEntry.proxyEntryHash` and `LookupCall.crossChainCallHash`.

Caller-specific bindings (not part of the formula, but fixed by the entry point):
- L1 `executeCrossChainCall`: `sourceRollupId = MAINNET_ROLLUP_ID = 0`; `targetRollupId =
  proxyInfo.originalRollupId`.
- L2 `executeCrossChainCall`/`staticCallLookup`: `sourceRollupId = ROLLUP_ID` (the L2's own
  id); `value = 0` in the static-lookup path.

---

## E.3 Cross-chain proxy CREATE2 derivation

`CrossChainProxy` is deployed once per `(originalRollupId, originalAddress)` pair via CREATE2
from the manager (`EEZ` on L1, `EEZL2` on L2). Constructor args are
`(address eez, address originalAddress, uint256 originalRollupId)`.

```
salt          = keccak256(abi.encodePacked(uint256 originalRollupId, address originalAddress))
initCode      = type(CrossChainProxy).creationCode ‖ abi.encode(eez, originalAddress, originalRollupId)
bytecodeHash  = keccak256(initCode)
proxyAddress  = address(uint160(uint256(keccak256(abi.encodePacked(
                    bytes1(0xff), eez, salt, bytecodeHash)))))
```

Notes:
- The salt packs `originalRollupId` as a full `uint256` (32 bytes) followed by the 20-byte
  `address` — `abi.encodePacked`, so 52 bytes total, no padding between.
- The constructor-arg tail is `abi.encode` (three 32-byte words), appended to the raw
  creation code.
- There is **no** `domain` / `block.chainid` in the salt (two-parameter derivation only).
- `eez` is the deploying manager's own address (`address(this)`), so proxy addresses are
  manager-specific.

The proxy creation-code bytecode is compiler-output of `CrossChainProxy.sol` at the pinned
commit with the project's solc 0.8.34 / `via_ir` / `optimizer_runs = 200` settings. The full
hex is embedded below so proxy CREATE2 addresses are derivable from this spec alone; the
`keccak256` and length are the integrity check (differing optimizer settings yield a different
creation code and therefore a different `bytecodeHash`).

```
# type(CrossChainProxy).creationCode  (1111 bytes)
# length            = 1111 bytes
# keccak256(creationCode) = 0x0a2e4d916da3a258d274e03e75d9236477f377b91173aa46c9bde942adfb660c
0x60e03461009557601f61045738819003918201601f19168301916001600160401b038311848410176100995780849260609460405283398101031261009557610047816100ad565b906040610056602083016100ad565b9101519160805260a05260c05260405161039590816100c28239608051818181610140015281816102ac015261032f015260a05181505060c051815050f35b5f80fd5b634e487b7160e01b5f52604160045260245ffd5b51906001600160a01b03821682036100955756fe60806040526004361061023e575f3560e01c8063532f08391461002b57639f149e1b0361023e57610096565b6040366003190112610092576004356001600160a01b0381168103610092576024359067ffffffffffffffff821161009257366023830112156100925781600401359167ffffffffffffffff8311610092573660248483010111610092576024019061013d565b5f80fd5b34610092575f366003190112610092573330036100b2575f805d005b61023e565b634e487b7160e01b5f52604160045260245ffd5b90601f8019910116810190811067ffffffffffffffff8211176100ed57604052565b6100b7565b67ffffffffffffffff81116100ed57601f01601f191660200190565b3d15610138573d9061011f826100f2565b9161012d60405193846100cb565b82523d5f602084013e565b606090565b337f00000000000000000000000000000000000000000000000000000000000000006001600160a01b0316036100b257825f9392849360405192839283378101848152039134905af161018e61010e565b901561019c57602081519101f35b602081519101fd5b6001600160a01b0390911681526040602082018190528101829052606091805f848401375f828201840152601f01601f1916010190565b6020818303126100925780519067ffffffffffffffff8211610092570181601f820112156100925780519061020f826100f2565b9261021d60405194856100cb565b8284526020838301011161009257815f9260208093018386015e8301015290565b5f806040516020810190639f149e1b60e01b8252600481526102616024826100cb565b519082305af161026f61010e565b50610304575f806040516020810190633d526d1760e11b82526102a88161029a3633602484016101a4565b03601f1981018352826100cb565b51907f00000000000000000000000000000000000000000000000000000000000000005afa6102d561010e565b90805b6102ea575b1561019c57602081519101f35b90806020806102fe935183010191016101db565b906102dd565b5f806040516020810190639af5325960e01b825261032a8161029a3633602484016101a4565b5190347f00000000000000000000000000000000000000000000000000000000000000005af161035861010e565b90806102d856fea2646970667358221220ccb81427bb41bbb8a276a72f0ded5edb9066871bffff6541a80c99966e5f18ae64736f6c63430008220033
```

(The `0x000…000` slots in the listing above are the contract's immutable placeholders — solc
emits the manager, original address, and original rollup-id immutables as runtime-resolved values, but the
*creation code* keccak and length are fixed by the embedded bytes regardless.)

---

## E.4 Rolling hash

Entry-level accumulator `_rollingHash` starts at `bytes32(0)` at the start of every entry and
is folded at four tagged event points. Domain tags are 1-byte (`uint8`) constants. All folds
use `abi.encodePacked` (raw widths):

```
CALL_BEGIN   (0x01)  _rollingHash = keccak256(abi.encodePacked(
                         bytes32 prev, uint8 0x01, uint256 callNumber))
CALL_END     (0x02)  _rollingHash = keccak256(abi.encodePacked(
                         bytes32 prev, uint8 0x02, uint256 callNumber, bool success, bytes retData))
NESTED_BEGIN (0x03)  _rollingHash = keccak256(abi.encodePacked(
                         bytes32 prev, uint8 0x03, uint256 nestedNumber))
NESTED_END   (0x04)  _rollingHash = keccak256(abi.encodePacked(
                         bytes32 prev, uint8 0x04, uint256 nestedNumber))
```

Argument widths (packed): `prev` 32B, tag 1B, `callNumber`/`nestedNumber` 32B, `success` 1B
(`0x00`/`0x01`), `retData` raw bytes (no length prefix). `callNumber` and `nestedNumber` are
1-indexed. The final value is checked `== entry.rollingHash` at end-of-entry.

**Static-lookup sub-call hash is a different, untagged scheme**
(`_rollingHashStaticResult`), verified against the active `LookupCall.rollingHash` or
`ExpectedLookup.rollingHash`:

```
computedHash = keccak256(abi.encodePacked(bytes32 prev, bool success, bytes retData))
```

per sub-call, with `prev` starting at `bytes32(0)`. No tag byte, no call number — the
surrounding lookup key already pins context. A `failed = true` reverted lookup that executes a
mini-entry instead uses the tagged entry scheme and its `callCount`/reentrant partition. Do not
conflate static and reverted lookup modes.

---

## E.5 Public-inputs-hash fold

Computed in `EEZ._verifyProofSystemBatch`. Per-entry / per-lookup-call / per-blob commitments:

```
entryHashes[i]      = keccak256(abi.encode(entries[i]))
lookupCallHashes[i] = keccak256(abi.encode(l1ToL2lookupCalls[i]))
blobHashes[i]       = blobhash(blobIndices[i])
```

Shared input (one `abi.encodePacked` over five items, then keccak):

```
sharedPublicInput = keccak256(abi.encodePacked(
    abi.encode(entryHashes),          // bytes32[] dynamic ABI encoding
    abi.encode(lookupCallHashes),     // bytes32[] dynamic ABI encoding
    abi.encode(blobHashes),           // bytes32[] dynamic ABI encoding
    keccak256(callData),              // bytes32
    crossProofSystemInteractions))    // bytes32
```

`abi.encode(bytes32[])` here is the full encoding of one dynamic argument: outer offset
`0x20`, length word, then elements. Those three encodings are raw-concatenated with the two
trailing `bytes32` words.

Per proof system `k` (index into `proofSystems[]`), fold attesting rollups in
**rollupId-ascending order** — the same order the batch enforces (`rollupIdsWithProofSystems`
strictly increasing by `rollupId`, validated in `_validateStructure`; out-of-order or
duplicate rollups revert `InvalidProofSystemConfig`):

```
acc_k = bytes32(0)
for each rollup r (ascending) whose proofSystemIndex[] contains k:
    acc_k = keccak256(abi.encode(
        bytes32 acc_k, uint256 rollupId_r, bytes32 vkey_rk, bytes32 blockHash_r, uint256 timestamp_r))
publicInputsHash[k] = keccak256(abi.encodePacked(sharedPublicInput, acc_k))
```

- `vkey_rk` is rollup `r`'s verification key for PS `k`, returned by the rollup manager's
  `checkProofSystemsAndGetVkeys(subset)` (guaranteed non-zero on success). For the v0 ECDSA
  PS, the "vkey" is an opaque `bytes32` the manager stores per PS (it is NOT the signer
  address used by the verifier — see E.6).
- `(blockHash_r, timestamp_r)` come from the rollup manager's
  `getTimestampAndBlockHash(batch.blockNumber)`, fetched once per rollup. With
  `blockNumber == 0` the reference manager returns `(0, bytes32(0))`; `type(uint64).max`
  binds `(block.timestamp, blockhash(block.number-1))`; any other value binds
  `blockhash(blockNumber)` (and reverts `BlockHashUnavailable` if 0).
- The inner fold uses `abi.encode` (positional); the final wrap uses `abi.encodePacked`.
- `crossProofSystemInteractions` is consumed as a raw `bytes32` domain separator. The
  contract assigns it no internal structure. The Rollup0 v0 profile nevertheless fixes it to
  `bytes32(0)` under §4.3; a nonzero contract vector below demonstrates the binding's hash
  behavior and is not a valid Rollup0 batch.

Verification is atomic: `IProofSystem(proofSystems[k]).verify(proofs[k], publicInputsHash[k])`
must return true for **every** `k`, else the whole `postAndVerifyBatch` reverts `InvalidProof`.
All verifier calls are `view` (STATICCALL).

`transientExecutionEntryCount` and `transientLookupCallCount` are not inputs to this hash. They
change transient/immediate routing and publication behavior without changing the proof digest.
The operational restriction and unresolved proof-reuse risk are normative in §§4.3 and 9.4.1.

---

## E.6 Attestation / threshold (as implemented)

The selected v0 source realizes "N-of-M" as **one proof system per attester**, NOT as N
signatures packed into a single `proofs[k]`:

- `proofSystems[]` is a batch-global, strictly-increasing-by-address list. `proofs[k]` is the
  attestation of PS `k` over `publicInputsHash[k]`. There is exactly one `proofs[k]` per PS.
- Each rollup picks the SUBSET it accepts via `RollupIdWithProofSystems[r].proofSystemIndex[]`
  (strictly increasing indices into `proofSystems[]`).
- **Threshold** is enforced per-rollup by the rollup manager:
  `checkProofSystemsAndGetVkeys(subset)` reverts `ThresholdNotMet` if
  `subset.length < threshold`, and reverts `ProofSystemNotAllowed` for any PS without a
  non-zero stored vkey. So the threshold check is "≥ `threshold` distinct accepted proof
  systems attested," one verifier call each.
- Signer ordering / dedup: enforced as **address ordering on `proofSystems[]`** (strictly
  increasing ⇒ no duplicate PS) and on each rollup's `proofSystemIndex[]` (strictly
  increasing). There is no separate signer list inside a proof blob to dedup.

The reference ECDSA verifier (`ECDSAProofSystem.verify`):

```
recovered = ECDSA.recover(publicInputsHash, proof)   // proof = abi.encodePacked(r, s, v), 65 bytes
return recovered == signer                            // single configured signer per PS
```

- `proof` is a 65-byte signature `r ‖ s ‖ v` (`abi.encodePacked`): `bytes32 r`, `bytes32 s`,
  `uint8 v`. `v` MUST be 27 or 28 (OZ `ECDSA.recover` does not normalize 0/1).
- The verifier signs the **raw `publicInputsHash` digest** — NO EIP-191 (`\x19Ethereum
  Signed Message`) prefix, NO EIP-712 domain.
- This PS is single-signer. An N-of-M policy means deploying M accepted
  `ECDSAProofSystem` instances (one signer each), listing at least N distinct accepted instances
  in the batch subset, and setting the rollup's `threshold = N`.

---

## E.7 DA payload grammar (tag 0x00)

The v0 DA payload is posted in the batch's Gnosis Chain calldata:

```
payload  := 0x00 ‖ rlp([ blockTxCounts, transactions, l2_entries ])
```

| element | type | meaning |
|---|---|---|
| `blockTxCounts` | `uint16[]` | one entry per L2 block in `(fromBlock, toBlock]`; `blockTxCounts[i]` = user-tx count of block `fromBlock + 1 + i`; length `== toBlock − fromBlock` |
| `transactions` | `bytes[]` | flat, **block-major** list of EIP-2718 signed user transactions |
| `l2_entries` | `bytes[]` | ABI-encoded L1-shape derivation `ExecutionEntrySol` values; followers validate their exact §4.1.2 transformation from the on-chain entries and lower them to the lean L2 ABI; empty only when there are no producing entries |

The selected codec source authors the positive encoding shape and canonical-minimal count
encoding. Rollup0 adds profile-level acceptance validation because EEZ treats `callData` as
opaque. A conforming decoder MUST enforce all §4.1 rules, including:

- a nonempty `0x00`-tagged payload;
- exactly one canonical three-list RLP body with no trailing bytes;
- a nonempty count list;
- canonical-minimal `uint16` counts with no leading zero;
- `sum(blockTxCounts) == transactions.length`;
- complete byte-string consumption by transaction and entry decoders; and
- exact sidecar cardinality and field correspondence to `batch.entries` under §4.1.2.

The pinned `eez-payload-codec` decoder does not currently enforce every additional acceptance
rule: in particular, it can accept an empty count list and does not reject every trailing-body
case. That is a nonconforming implementation gap and release blocker under §§6.8 and 8.3. It is
not an alternate grammar and does not authorize clients to weaken profile validation.

Ordering: `transactions` is block-major (all of block `fromBlock+1`, then block `fromBlock+2`,
…). `blockTxCounts[i]` partitions that flat list per block.

**Sync block:** `toBlock` is the Sync block. Its signed system transactions are reconstructed from
the derivation entries, parent-state nonce, activation parameters, and signing key; they are not
transported or counted. Its user-transaction count can be nonzero. Because
`blockTxCounts.length == toBlock - fromBlock`, the Sync block always has a final count entry.

RLP integer note: `blockTxCounts` entries are `uint16`-valued and are encoded by the pinned
`alloy_rlp` codec as canonical minimal big-endian RLP integers, not fixed-width 2-byte strings.
Zero is the empty byte string and therefore encodes as `0x80`.

---

## E.8 System entry points and signed legacy transactions

L2 inbound delivery entry point (`EEZL2.executeIncomingCrossChainCall`), full resolved
Solidity declaration:

```solidity
function executeIncomingCrossChainCall(
    address destination,
    uint256 value,
    bytes   calldata data,
    address sourceAddress,
    uint256 sourceRollup,
    IEEZL2.ExecutionEntry[] calldata entries,
    IEEZL2.LookupCall[]     calldata lookupCalls
) external payable onlySystemAddress returns (bytes memory result);
```

The two tuple arrays use the **lean L2 layouts** in E.1. On-chain behavior: callable only by
`SYSTEM_ADDRESS`; reverts `EmptyEntries` if `entries.length == 0`; reverts `ValueMismatch` unless
`msg.value == value` (strict equality; the prefunded sender transfers exactly `value`); atomically
replaces the execution and lookup tables; computes
`crossChainCallHash = computeCrossChainCallHash(ROLLUP_ID, destination, value, data,
sourceAddress, sourceRollup)`, reverts `EntryHashMismatch` unless `entries[0].proxyEntryHash`
equals it; drives `entries[0]` through `_processNCalls(entry.callCount)`; checks
`_rollingHash == entry.rollingHash`, `_currentIncomingCall == entry.incomingCalls.length`, and
`_lastOutgoingCallConsumed == entry.expectedOutgoingCalls.length`; sets `executionIndex = 1`,
resets `_currentIncomingCall = 0`, returns `entries[0].returnData`, and emits
`IncomingCrossChainCallExecuted`.

The selected Rollup0 implementation builds one inbound transaction for each L1-shape derivation
entry whose `destinationRollupId` equals this rollup and whose `l2ToL1Calls` is non-empty. For v0,
the builder:

1. reads `outer = entry.l2ToL1Calls[0]` (the shared builder rejects
   `l2ToL1Calls.length > 1` or `callCount > 1`);
2. constructs one lean L2 `ExecutionEntry` with the recomputed call hash,
   `incomingCalls = [outer]`, empty reentrant/lookup arrays, `callCount = 1`,
   `returnData = entry.returnData`, and the tagged rolling hash for
   `CALL_BEGIN(1)` then `CALL_END(1, true, returnData)`;
3. ABI-encodes
   `executeIncomingCrossChainCall(outer.targetAddress, outer.value, outer.data,
   outer.sourceAddress, outer.sourceRollupId, [l2Entry], [])`; and
4. signs the transaction below.

The transaction is a canonical **legacy EIP-155** transaction:

```
signingPayload = rlp([
    nonce, gasPrice, gasLimit, EEZL2, value, calldata, chainId, 0, 0
])

rawTransaction = rlp([
    nonce, gasPrice, gasLimit, EEZL2, value, calldata, v, r, s
])

v = 35 + 2 * chainId + yParity
transactionHash = keccak256(rawTransaction)
```

RLP integers use canonical minimal big-endian form; `to` is the 20-byte `EEZL2` address; `value`
equals `outer.value`; calldata is raw bytes. There is **no EIP-2718 type byte** before the legacy
RLP. `nonce` is read from the `SYSTEM_ADDRESS` account in the Sync block's parent state and is
incremented once per emitted system transaction. `chainId`, `gasPrice`, and `gasLimit` are
activation parameters. The signature MUST recover the configured `SYSTEM_ADDRESS`.

Rollup0 v0 also uses `loadExecutionTable` for outbound entries. The canonical Sync order is all
outbound `[loadExecutionTable, paired user]` pairs, then all inbound deliveries, then remaining
user transactions. System nonces are consecutive in that full order. Appendix C specifies the
lowering, calldata, envelope, fees, value accounting, receipts, and failure behavior.

Possession of the signing key is therefore an input to byte-identical derivation. It is not
recoverable from L1 data; §0.5 records the resulting activation blocker.

---

## E.9 ABI selector fingerprint

These canonical signature strings and selectors are normative. Names inside structs do not enter
the selector, but every tuple field type, position, and array suffix does.

### L1 settlement

```
0x8b1a095a
postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,uint256,bytes,bool,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32,(uint256,bytes32)[])[],uint256,uint256,address[],(uint256,uint64[])[],bytes32,uint256[],bytes,bytes[],uint64))
```

### L2 table load

```
0x59683c8b
loadExecutionTable((bytes32,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])
```

### L2 inbound delivery

```
0xeb494246
executeIncomingCrossChainCall(address,uint256,bytes,address,uint256,(bytes32,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes,bytes32)[],(bytes32,bytes,bool,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],(bytes32,bytes,bool,uint64,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes32)[],uint256,bytes32)[])
```

### Manager context

```
0x6db96461
getTimestampAndBlockHash(uint64)
```

Additional fixed selectors:

| Signature | Selector |
|---|---|
| `computeCrossChainCallHash(uint256,address,uint256,bytes,address,uint256)` | `0x1f314db1` |
| `createCrossChainProxy(address,uint256)` | `0x2dd72120` |
| `computeCrossChainProxyAddress(address,uint256)` | `0xb761ba7e` |
| `executeCrossChainCall(address,bytes)` | `0x9af53259` |
| `staticCallLookup(address,bytes)` | `0x7aa4da2e` |
| `executeL2TX(uint256)` | `0xccdcf581` |
| `checkProofSystemsAndGetVkeys(address[])` | `0xbed3a169` |

### Settlement events

The following declarations and topic hashes are normative for settlement attribution. The events
are non-anonymous. Every indexed `uint256` is encoded as one 32-byte big-endian topic, and an
indexed `bytes32` occupies one topic unchanged.

| Event declaration | `topic0` | Indexed topics after `topic0` | Data |
|---|---|---|---|
| `BatchPosted(uint256 indexed rollupCount)` | `0xd6f8d71ce42a799b91f399271f4b0e91f85eb87fac7bb2cedd4b3a52fad36182` | `rollupCount` | empty |
| `L2ExecutionPerformed(uint256 indexed rollupId, bytes32 newState)` | `0x0133f662c29e67eedfc9b53c0c1f657b30ebaf9748094d09fa4659d769dd4f78` | `rollupId` | one ABI word: `newState` |
| `ImmediateEntrySkipped(uint256 indexed transientIdx, bytes revertData)` | `0x62cc6fa8d0d1b1170559640dfa2d36932712a5d761c0924ea23aabf3b602cb3c` | `transientIdx` | `abi.encode(revertData)` |
| `ExecutionConsumed(bytes32 indexed crossChainCallHash, uint256 indexed rollupId, uint256 indexed cursor)` | `0x207e371295f3ff0efe443424ce128c96f8ecea6a25636fc38ad7c222c446699c` | `crossChainCallHash`, `rollupId`, `cursor` | empty |

`ImmediateEntrySkipped.transientIdx` is the zero-based index in the batch's transient prefix.
`ExecutionConsumed.cursor` is the zero-based persistent queue index for that rollup, not an index
within the posted batch. The exact receipt-association and prefix algorithm is in §4.5. A decoder
MUST retain the emitting address, transaction boundary, receipt status, and `logIndex`; the topic
values alone are not settlement evidence.

---

## E.10 Conformance vectors

Contract vectors below were computed by running `script/WireVectors.s.sol` (saved as
[`fixtures/wire-vectors.s.sol`](fixtures/wire-vectors.s.sol)) against an isolated export of the selected contract
commit.

Reproduce:

```
git -C sync-rollups-protocol rev-parse HEAD   # must be 5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba
cp docs/rollup0-network-spec/fixtures/wire-vectors.s.sol \
  sync-rollups-protocol/script/WireVectors.s.sol
cd sync-rollups-protocol
forge script script/WireVectors.s.sol -vvv
```

solc 0.8.34, `via_ir = true`, `optimizer = true`, `optimizer_runs = 200` (the project
`foundry.toml`). The proxy CREATE2 vector uses a fixed manager address
`0x00000000000000000000000000000000000ee200` (selected `EEZ` code etched there) so the address is
reproducible; substitute your own manager address to derive production proxies.

### Vector 1 — `crossChainCallHash`
| input | value |
|---|---|
| `targetRollupId` | `1` |
| `targetAddress` | `0x00000000000000000000000000000000deadbeef` |
| `value` | `1000000000000000000` (1 ether) |
| `data` | `0xdeadbeef` |
| `sourceAddress` | `0x0000000000000000000000000000000000c0ffee` |
| `sourceRollupId` | `0` |

```
crossChainCallHash = 0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2
```

### Vector 2 — cross-chain proxy address (CREATE2)
| input | value |
|---|---|
| manager (`eez`) | `0x00000000000000000000000000000000000ee200` |
| `originalAddress` | `0x0000000000000000000000000000000000c0ffee` |
| `originalRollupId` | `1` |

```
salt                  = 0x9b795495c996503b00c5938a264389c4df5c002802eae27e9463f48ea7aafdd5
creationCode length   = 1111 bytes
keccak256(creationCode) = 0x0a2e4d916da3a258d274e03e75d9236477f377b91173aa46c9bde942adfb660c
bytecodeHash          = 0x1f9d5a077e0d412d378cb6dab69a46400ad1d04d34817760a89ecbdff0b39561
proxyAddress          = 0xaa1096867F5756Db3f25F514708Af546EE99E757
```

(`keccak256(creationCode)` and the 1111-byte length are reproducibility anchors: identical
init code is required for the address to match. `bytecodeHash` already folds in the
constructor-arg tail `abi.encode(eez, originalAddress, originalRollupId)`.)

### Vector 3 — rolling hash, CALL_BEGIN(1) + CALL_END(1, true, 0x01)
Start `_rollingHash = 0x00…00`; `callNumber = 1`, `success = true`, `retData = 0x01`.

```
after CALL_BEGIN(1)            = 0xa578faae9568ec79d80e92f83b4d08a4537677b5145aef1ab04b0c67dd76c63f
after CALL_END(1,true,0x01)    = 0x696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d
```

### Vector 4 — `abi.encode(ExecutionEntry)` + `entryHash`
Entry: `stateDeltas = [ (rollupId 1, currentState 0xaa, newState 0xbb, etherDelta 0) ]`,
`proxyEntryHash = <Vector 1 hash>`, `destinationRollupId = 1`,
`l2ToL1Calls = [ (target 0x…deadbeef, value 0, data 0xdeadbeef, source 0x…c0ffee,
sourceRollupId 0, revertSpan 0) ]`, `expectedL1ToL2Calls = []`, `expectedLookups = []`,
`callCount = 1`, `returnData = 0x`, `rollingHash = <Vector 3 final>`.

```
abi.encode(entry) =
0x0000000000000000000000000000000000000000000000000000000000000020
  0000000000000000000000000000000000000000000000000000000000000120
  6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2
  0000000000000000000000000000000000000000000000000000000000000001
  00000000000000000000000000000000000000000000000000000000000001c0
  0000000000000000000000000000000000000000000000000000000000000300
  0000000000000000000000000000000000000000000000000000000000000320
  0000000000000000000000000000000000000000000000000000000000000001
  0000000000000000000000000000000000000000000000000000000000000340
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
  0000000000000000000000000000000000000000000000000000000000000000
  0000000000000000000000000000000000000000000000000000000000000000
  0000000000000000000000000000000000000000000000000000000000000000

entryHash = keccak256(abi.encode(entry))
          = 0x0daea58ce2cc9573afca8e0d65214a534a31d70deba38062ae3026bd0ebc171e
```

### Vector 5 — `publicInputsHash` (1 rollup, 1 proof system)
Batch: `entries = [<Vector 4 entry>]`, no lookup calls, no blobs, `callData = 0x`,
`crossProofSystemInteractions = bytes32(0)`; single rollup `rollupId = 1` with `vkey = 0x100`,
single PS `k = 0`, `blockNumber = 0` ⇒ `(timestamp, blockHash) = (0, bytes32(0))`.

This vector exercises the compatibility contract's legacy sentinel branch. It is not a valid
Rollup0 production batch: §§4.3 and 9.9 require a nonzero explicit past Chiado context.

```
keccak256(callData = 0x)   = 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
sharedPublicInput          = 0xbb081e7ec0c841ca0ba342cf456d052f6a2a0821ef5b54ce2886a16968c91faa
acc (single rollup folded)  = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]        = 0x0b2211d86f9cfb891f0218e282a449be439653ffee72c1aba57373f08501b206
```

`acc = keccak256(abi.encode(bytes32(0), uint256(1), bytes32(0x100), bytes32(0), uint256(0)))`;
`publicInputsHash[0] = keccak256(abi.encodePacked(sharedPublicInput, acc))`.

### Vector 6 — `publicInputsHash`, 2 rollups × 2 proof systems
Exercises the ascending-`rollupId` fold and per-`k` rollup selection.
`proofSystems = [PS0, PS1]` (k = 0, 1); rollup 1 lists `proofSystemIndex = [0, 1]` (attests
via both), rollup 2 lists `proofSystemIndex = [1]` (attests via PS1 only). Per-rollup vkeys:
rollup 1 → `[0x100, 0x101]`, rollup 2 → `[0x201]`. `blockNumber = 0` ⇒ `(timestamp,
blockHash) = (0, bytes32(0))` for both. `sharedPublicInput` is the same shape as Vector 5
(single entry, empty callData/blobs, zero `crossProofSystemInteractions`).

```
sharedPublicInput      = 0xbb081e7ec0c841ca0ba342cf456d052f6a2a0821ef5b54ce2886a16968c91faa

# PS0 (k=0): folded only by rollup 1 (vk 0x100)
acc(PS0)               = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]    = 0x0b2211d86f9cfb891f0218e282a449be439653ffee72c1aba57373f08501b206

# PS1 (k=1): folded by rollup 1 (vk 0x101) THEN rollup 2 (vk 0x201), in ascending rollupId order
acc(PS1)               = 0x1d1754cd9a1ce70d42038aeb1110bad91b9500d6a586e07f93ffb690a18222e6
publicInputsHash[1]    = 0xec9b476c834a8b33aa6a72ed990c9924c6d4a1322838102499a8175f82e71ac3
```

`acc(PS1) = keccak256(abi.encode( keccak256(abi.encode(bytes32(0), uint256(1),
bytes32(0x101), bytes32(0), uint256(0))), uint256(2), bytes32(0x201), bytes32(0),
uint256(0)))`. (PS0's `acc`/`publicInputsHash` are identical to Vector 5 — same single-rollup
fold — a built-in cross-check.)

### Vector 7 — `sharedPublicInput`, non-empty `callData` + 1 lookup call
Exercises the non-empty `abi.encode(bytes32[])` packing for `lookupCallHashes` and a non-empty
`callData`. `entries = [<Vector 4 entry>]`; one `LookupCall` `{ crossChainCallHash = 0x1234,
destinationRollupId = 1, returnData = 0xabcd, failed = true, l2ToL1Calls = [],
expectedL1ToL2Calls = [], expectedLookups = [], callCount = 0, rollingHash = 0,
expectedStateRoots = [(rollupId 1, stateRoot 0xaa)] }`; `callData = 0xcafebabe`;
`crossProofSystemInteractions = keccak256("xpsi")`; single rollup 1 / single PS, `vk = 0x100`,
`blockNumber = 0`.

This is a compatibility-contract hash vector, not a valid Rollup0 batch. Rollup0 v0 rejects both
the nonzero `crossProofSystemInteractions` value and the zero context sentinel.

```
lookupCallHash               = 0x85be8606cad0ae3cb989136c5b255fe107c1b93f36b086538a041f5f70185b57
keccak256(callData=0xcafebabe) = 0x6fe2683bd1d27cbb7a05c570693bea39e0c082ed16722e5ecadcfb7cfdbd20db
crossProofSystemInteractions = 0x6043818a14fa81cd43674dca578863f795ae1551407871464d237744a4ac209e
sharedPublicInput            = 0xaee602d41405a32e905e848daca99f27113c0880e3c4b5092bd41cf81a7e051c
acc (rollup1, vk 0x100)      = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]          = 0xd64353ce5ac0c337a4dbac18e889a7591877c52b6e3d9f0226f0def5bab4bbfc
```

`lookupCallHash = keccak256(abi.encode(lookupCall))` — same per-element commitment the
contract uses for `lookupCallHashes[i]`.

### Vector 8 — DA tag-`0x00` outer and strict round trips

**Codec-authored, not contract-authored.** The outer encoding shape is pinned to
`eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c`,
`crates/eez-payload-codec/src/lib.rs` blob
`533d978b2e3dd2e91c1d29f3416ffe3da04314a5`. Rollup0 adds the strict acceptance checks in
§4.1. The outer-codec fixture covers `[2, 1]`, so the Sync-block count is nonzero:

```text
blockTxCounts = [2, 1]
payload length = 136 bytes
keccak256(payload) = 0x2e6652704d2b1093b46c9e5029e0ecbc540c491e87ca4eeb9de5321267dc1504
```

Those inner transaction and entry samples are deliberately opaque and are not accepted derivation
inputs. The separate strict vector uses `[0, 1]`, one complete signed type-2 user envelope, and
complete L1-shape outbound and inbound sidecar entries with their corresponding anchor, outbound,
and lean inbound on-chain entries:

```text
payload length = 1601 bytes
keccak256(payload) = 0x179bdc0defb0e2a4979efa52123be6cee63c6b86eefb121ea5bddca974e48e5f
```

The complete bytes, ten outer rejection cases, and four inner/correspondence rejection cases are
in [Appendix B](B-da-codec.md),
[`fixtures/da-rlp-fixture.py`](fixtures/da-rlp-fixture.py), and
[`fixtures/da-strict-fixture.py`](fixtures/da-strict-fixture.py).

### Vector 9 — signed legacy system-transaction pair

**Rollup-implementation-authored.** Starting from system nonce `7`, the pair contains an outbound
table load at nonce `7` followed by an inbound delivery at nonce `8`. Both use EIP-155 chain ID
`1`, gas price `1 gwei`, gas limit `2,000,000`, and private key `0x00...01`.

```text
SYSTEM_ADDRESS = 0x7e5f4552091a69125d5dfcb7b8c2659029395bdf

outbound selector       = 0x59683c8b
outbound raw length     = 620 bytes
outbound transactionHash= 0x2e6768b4b7c3c8864d0142699bdfccc23c28de47d431a51962bfc29110b97b68

inbound selector        = 0xeb494246
inbound envelope value  = 1
inbound raw length      = 1133 bytes
inbound transactionHash = 0xf22f620d60f898285607a2a52f80beb4f07f6dc4a408afb231c97bf979e02632
```

[`fixtures/system-tx-fixture.py`](fixtures/system-tx-fixture.py) prints and checks all calldata,
signing preimages, signatures, raw transactions, hashes, and sender recovery.
[`fixtures/system-tx-vector.rs`](fixtures/system-tx-vector.rs) cross-checks the selected Rust
implementation.

### Generated corpus and verifier

The machine-readable Rollup0-only corpus is
[`fixtures/conformance-vectors.json`](fixtures/conformance-vectors.json). It is generated by
[`fixtures/conformance_vectors.py`](fixtures/conformance_vectors.py) and verified together with
the DA, system, timing/header, and genesis fixtures by:

```console
python3 -m pip install -r docs/rollup0-network-spec/fixtures/conformance-requirements.txt
python3 docs/rollup0-network-spec/fixtures/verify-conformance.py
```

Regenerate after an intentional vector change with `--write`, then run the normal verification.
The corpus also fixes the four settlement-event log encodings, valid and invalid applied-prefix
cases, the zero `crossProofSystemInteractions` profile value, and the development system-key
derivation. It contains only the Rollup0 `5c51e02` binding. The current EEZ `3a6ca65` framework
has different layouts, selectors, proxy code, and vectors and remains in the EEZ specification.

---

## E.11 Compatibility boundary

All contract-authored values in this appendix are for
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`. DA and
system-transaction values are for
`eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c`. The stale
`fe7bf66` submodule declaration and the later `eez-core-protocol@3a6ca65` ABI have different
wire fingerprints and MUST NOT be mixed into `rollup0-v0`; see §0.2 and §0.3.
