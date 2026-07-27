# Appendix D. Wire Formats & Conformance Vectors

Normative byte-exact wire formats for the Rollup0 protocol. These layouts are the canonical
encodings every implementation MUST reproduce. Their provenance is the deployed
`sync-rollups-protocol` contracts at commit `fe7bf6644dacd64bb41707feae2d84699a97afb4`
(cited as the source of these byte layouts; this annex is otherwise client-agnostic). All
multi-byte ABI words are big-endian 32-byte slots per the Solidity ABI; `keccak256` is the
Ethereum keccak (not NIST SHA3-256).

Two distinct hashing disciplines appear throughout:

- **`abi.encode(...)`** — positional, 32-byte-aligned ABI encoding (head/tail for dynamic
  types). Used wherever structured fields with their own type widths are committed.
- **`abi.encodePacked(...)`** — raw concatenation with each value at its natural width
  (`uint8` → 1 byte, `uint256` → 32 bytes, `address` → 20 bytes, `bytes`/`string` → raw, no
  length prefix). Used for the rolling hash, the CREATE2 salt/address, and the public-inputs
  packing step.

---

## D.1 Core struct layouts (ABI)

Field order and types are normative — `abi.encode` lays them out positionally, so any
reordering changes every derived hash. Types below are the exact Solidity declarations.

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

### `ExecutionEntry`  `((uint256,bytes32,bytes32,int256)[],bytes32,uint256,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes,bytes32)`
| # | field | type | notes |
|---|---|---|---|
| 0 | `stateDeltas` | `StateDelta[]` | **dynamic** |
| 1 | `proxyEntryHash` | `bytes32` | the entry trigger's `crossChainCallHash`; `bytes32(0)` = immediate / L2-tx |
| 2 | `destinationRollupId` | `uint256` | |
| 3 | `L2ToL1Calls` | `L2ToL1Call[]` | **dynamic**; full flat call list |
| 4 | `expectedL1ToL2Calls` | `ExpectedL1ToL2Call[]` | **dynamic** |
| 5 | `callCount` | `uint256` | top-level iterations |
| 6 | `returnData` | `bytes` | **dynamic** |
| 7 | `rollingHash` | `bytes32` | expected accumulator after the entry completes |

Dynamic. `entryHash = keccak256(abi.encode(entry))` (see D.5, D.10).

### `LookupCall`  `(bytes32,uint256,bytes,bool,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],bytes32)`
| # | field | type | notes |
|---|---|---|---|
| 0 | `crossChainCallHash` | `bytes32` | |
| 1 | `destinationRollupId` | `uint256` | |
| 2 | `returnData` | `bytes` | **dynamic** |
| 3 | `failed` | `bool` | true ⇒ replayed as a revert |
| 4 | `callNumber` | `uint64` | `_currentCallNumber` at observation (top-level key = 0) |
| 5 | `lastNestedActionConsumed` | `uint64` | disambiguator (top-level key = 0) |
| 6 | `calls` | `L2ToL1Call[]` | **dynamic**; optional STATICCALL sub-calls |
| 7 | `rollingHash` | `bytes32` | expected hash of the sub-calls (untagged scheme, D.4) |

Dynamic. Lookup key is `(crossChainCallHash, destinationRollupId, callNumber, lastNestedActionConsumed)`.

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

---

## D.2 `crossChainCallHash`

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

## D.3 Cross-chain proxy CREATE2 derivation

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
# keccak256(creationCode) = 0xb674ac54ef248bfe921085a167b225ed55b29a26f4d16538d568a88244d7c4af
0x60e03461009557601f61045738819003918201601f19168301916001600160401b038311848410176100995780849260609460405283398101031261009557610047816100ad565b906040610056602083016100ad565b9101519160805260a05260c05260405161039590816100c28239608051818181610140015281816102ac015261032f015260a05181505060c051815050f35b5f80fd5b634e487b7160e01b5f52604160045260245ffd5b51906001600160a01b03821682036100955756fe60806040526004361061023e575f3560e01c8063532f08391461002b57639f149e1b0361023e57610096565b6040366003190112610092576004356001600160a01b0381168103610092576024359067ffffffffffffffff821161009257366023830112156100925781600401359167ffffffffffffffff8311610092573660248483010111610092576024019061013d565b5f80fd5b34610092575f366003190112610092573330036100b2575f805d005b61023e565b634e487b7160e01b5f52604160045260245ffd5b90601f8019910116810190811067ffffffffffffffff8211176100ed57604052565b6100b7565b67ffffffffffffffff81116100ed57601f01601f191660200190565b3d15610138573d9061011f826100f2565b9161012d60405193846100cb565b82523d5f602084013e565b606090565b337f00000000000000000000000000000000000000000000000000000000000000006001600160a01b0316036100b257825f9392849360405192839283378101848152039134905af161018e61010e565b901561019c57602081519101f35b602081519101fd5b6001600160a01b0390911681526040602082018190528101829052606091805f848401375f828201840152601f01601f1916010190565b6020818303126100925780519067ffffffffffffffff8211610092570181601f820112156100925780519061020f826100f2565b9261021d60405194856100cb565b8284526020838301011161009257815f9260208093018386015e8301015290565b5f806040516020810190639f149e1b60e01b8252600481526102616024826100cb565b519082305af161026f61010e565b50610304575f806040516020810190633d526d1760e11b82526102a88161029a3633602484016101a4565b03601f1981018352826100cb565b51907f00000000000000000000000000000000000000000000000000000000000000005afa6102d561010e565b90805b6102ea575b1561019c57602081519101f35b90806020806102fe935183010191016101db565b906102dd565b5f806040516020810190639af5325960e01b825261032a8161029a3633602484016101a4565b5190347f00000000000000000000000000000000000000000000000000000000000000005af161035861010e565b90806102d856fea26469706673582212201ea9988aab655e2b566c7598029bd3fc167deceabd65dfbe04e27a732346a17c64736f6c63430008220033
```

(The `0x000…000` slots in the listing above are the contract's immutable placeholders — solc
emits the manager / signer / threshold immutables as runtime-resolved values, but the
*creation code* keccak and length are fixed by the embedded bytes regardless.)

---

## D.4 Rolling hash

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

**Lookup-call sub-call hash is a DIFFERENT, untagged scheme** (`_rollingHashStaticResult`),
verified against `LookupCall.rollingHash`:

```
computedHash = keccak256(abi.encodePacked(bytes32 prev, bool success, bytes retData))
```

per sub-call, with `prev` starting at `bytes32(0)`. No tag byte, no call number — the
surrounding `LookupCall` lookup key already pins context. Do not conflate the two schemes.

---

## D.5 Public-inputs-hash fold

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

`abi.encode(bytes32[])` here is the full dynamic encoding (length word + elements), and those
three encodings are then raw-concatenated with the two trailing `bytes32` words.

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
  address used by the verifier — see D.6).
- `(blockHash_r, timestamp_r)` come from the rollup manager's
  `getTimestampAndBlockHash(batch.blockNumber)`, fetched once per rollup. With
  `blockNumber == 0` the reference manager returns `(0, bytes32(0))`; `type(uint64).max`
  binds `(block.timestamp, blockhash(block.number-1))`; any other value binds
  `blockhash(blockNumber)` (and reverts `BlockHashUnavailable` if 0).
- The inner fold uses `abi.encode` (positional); the final wrap uses `abi.encodePacked`.
- `crossProofSystemInteractions` is consumed as a raw `bytes32` domain separator. The
  contract assigns it no internal structure — it is opaque input the orchestrator supplies
  (see Discrepancies).

Verification is atomic: `IProofSystem(proofSystems[k]).verify(proofs[k], publicInputsHash[k])`
must return true for **every** `k`, else the whole `postAndVerifyBatch` reverts `InvalidProof`.
All verifier calls are `view` (STATICCALL).

---

## D.6 Attestation / threshold (as implemented)

The deployed source realizes "N-of-M" as **one proof system per attester**, NOT as N
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
- This PS is single-signer. M-of-N with this verifier means deploying M `ECDSAProofSystem`
  instances (one signer each), listing the chosen N in the batch, and setting the rollup's
  `threshold = N`.

---

## D.7 DA payload grammar (tag 0x00)

The v0 DA payload (posted as L1 calldata by default; blobs are the production channel):

```
payload  := 0x00 ‖ rlp([ blockTxCounts, transactions, l2_entries ])
```

| element | type | meaning |
|---|---|---|
| `blockTxCounts` | `uint16[]` | one entry per L2 block in `(fromBlock, toBlock]`; `blockTxCounts[i]` = user-tx count of block `fromBlock + 1 + i`; length `== toBlock − fromBlock` |
| `transactions` | `bytes[]` | flat, **block-major** list of EIP-2718 signed user transactions |
| `l2_entries` | `bytes[]` | ABI-encoded L2-shape `ExecutionEntry`s for followers; empty for non-value batches |

Decode invariants (MUST):
- leading byte `== 0x00` else reject;
- `sum(blockTxCounts) == transactions.length`;
- each count fits `uint16`.

Ordering: `transactions` is block-major (all of block `fromBlock+1`, then block `fromBlock+2`,
…). `blockTxCounts[i]` partitions that flat list per block.

**Sync block:** `toBlock` is the Sync block. Its user-transaction list is **empty** in the
payload — the Sync block's system transactions (D.8) are reconstructed deterministically from
the batch entries, not transported. Because `blockTxCounts.length == toBlock − fromBlock`
spans through the Sync block, the Sync block's slot is present and carries `0` (a trailing
`0` count). See Discrepancies for the explicit-vs-implied status and for the RLP integer
width.

RLP integer note: `blockTxCounts` entries are `uint16`-valued. The byte-level RLP integer
encoding (canonical minimal big-endian per standard RLP, vs a fixed 2-byte width) is NOT
pinned by the contract source (the payload codec is not on-chain) and is only value-range
constrained by the spec. Implementations MUST agree on canonical minimal-length RLP integers
(the RLP default) unless a future revision says otherwise.

---

## D.8 Inbound delivery & the type-0x7E system transaction

L2 inbound delivery entry point (`EEZL2.executeIncomingCrossChainCall`), full resolved
signature (was elided as `…` in the spec body):

```solidity
function executeIncomingCrossChainCall(
    address destination,
    uint256 value,
    bytes   calldata data,
    address sourceAddress,
    uint256 sourceRollup,
    ExecutionEntry[] calldata entries,
    LookupCall[]     calldata _lookupCalls
) external payable onlySystemAddress returns (bytes memory result);
```

On-chain behavior (normative): callable only by `SYSTEM_ADDRESS`; reverts `EmptyEntries` if
`entries.length == 0`; reverts `ValueMismatch` unless `msg.value == value` (strict equality —
the system mints exactly `value`); atomically replaces the execution table
(`_loadExecutionTable`); computes
`crossChainCallHash = computeCrossChainCallHash(ROLLUP_ID, destination, value, data,
sourceAddress, sourceRollup)`, reverts `EntryHashMismatch` unless `entries[0].proxyEntryHash`
equals it; drives `entries[0]` through `_processNCalls`; checks
`_rollingHash == entry.rollingHash`, `_currentCallNumber == entry.L2ToL1Calls.length`,
`_lastNestedActionConsumed == entry.expectedL1ToL2Calls.length`; sets `executionIndex = 1`;
returns `entries[0].returnData`. Emits `IncomingCrossChainCallExecuted`.

**Type-0x7E transaction envelope:** the system transaction that invokes the above is a
type-`0x7E`, unsigned, deterministically-reconstructible transaction from `SYSTEM_ADDRESS`,
placed at the head of the Sync block. **Its byte/RLP envelope serialization is NOT defined in
the `sync-rollups-protocol` contract source** — it is an execution-client-side / execution-layer
artifact (reconstructed identically by operator and followers from the batch entries, and not
carried in the DA payload). This annex therefore does not specify the 0x7E envelope byte layout;
it is marked out-of-source and MUST be pinned by the execution-layer specification rather than
inferred from these contracts.

---

## D.9 `postAndVerifyBatch` selector

```
selector = 0x51dd0af6
```

Canonical function-signature string (verified `cast sig` == `cast keccak`[:4] == `0x51dd0af6`):

```
postAndVerifyBatch((((uint256,bytes32,bytes32,int256)[],bytes32,uint256,(address,uint256,bytes,address,uint256,uint256)[],(bytes32,uint256,bytes)[],uint256,bytes,bytes32)[],(bytes32,uint256,bytes,bool,uint64,uint64,(address,uint256,bytes,address,uint256,uint256)[],bytes32)[],uint256,uint256,address[],(uint256,uint64[])[],bytes32,uint256[],bytes,bytes[],uint64))
```

The single argument is one `ProofSystemBatchPerVerificationEntries` struct (outer tuple); the
nested tuples are, in order, `ExecutionEntry[]` and `LookupCall[]` as expanded in D.1.

---

## D.10 Conformance vectors

All values below were computed by running `script/WireVectors.s.sol` (saved alongside this
spec as `companion-docs/wire-vectors.s.sol`) against the deployed contracts.

Reproduce:

```
git -C sync-rollups-protocol rev-parse HEAD   # fe7bf6644dacd64bb41707feae2d84699a97afb4
cd sync-rollups-protocol
forge script script/WireVectors.s.sol -vvv
```

solc 0.8.34, `via_ir = true`, `optimizer = true`, `optimizer_runs = 200` (the project
`foundry.toml`). The proxy CREATE2 vector uses a fixed manager address
`0x00000000000000000000000000000000000ee200` (real `EEZ` code etched there) so the address is
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
keccak256(creationCode) = 0xb674ac54ef248bfe921085a167b225ed55b29a26f4d16538d568a88244d7c4af
bytecodeHash          = 0xc9400233a674b91a20b7dbeef0f767ff00795d47254a65ec4eedb379028792fe
proxyAddress          = 0xF29a3823d1BA0BF93A46fAA6e919Ff01D9E15006
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
`L2ToL1Calls = [ (target 0x…deadbeef, value 0, data 0xdeadbeef, source 0x…c0ffee, sourceRollupId 0, revertSpan 0) ]`,
`expectedL1ToL2Calls = []`, `callCount = 1`, `returnData = 0x`, `rollingHash = <Vector 3 final>`.

```
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

entryHash = keccak256(abi.encode(entry))
          = 0xf55a0b2f661170eb3d02881188f6fc27ce192d6653a2c45c3d6b9bc8e368ce39
```

### Vector 5 — `publicInputsHash` (1 rollup, 1 proof system)
Batch: `entries = [<Vector 4 entry>]`, no lookup calls, no blobs, `callData = 0x`,
`crossProofSystemInteractions = bytes32(0)`; single rollup `rollupId = 1` with `vkey = 0x100`,
single PS `k = 0`, `blockNumber = 0` ⇒ `(timestamp, blockHash) = (0, bytes32(0))`.

```
keccak256(callData = 0x)   = 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
sharedPublicInput          = 0x9c4e7a3a4b9037140a02de516a8b3200968754093f4e585e1fd742b26adcb790
acc (single rollup folded)  = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]        = 0xdcd57c2f57d42af6165678f3adbb7e07e0b4ba60765bd2e4c4a76921e8daa891
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
sharedPublicInput      = 0x9c4e7a3a4b9037140a02de516a8b3200968754093f4e585e1fd742b26adcb790

# PS0 (k=0): folded only by rollup 1 (vk 0x100)
acc(PS0)               = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]    = 0xdcd57c2f57d42af6165678f3adbb7e07e0b4ba60765bd2e4c4a76921e8daa891

# PS1 (k=1): folded by rollup 1 (vk 0x101) THEN rollup 2 (vk 0x201), in ascending rollupId order
acc(PS1)               = 0x1d1754cd9a1ce70d42038aeb1110bad91b9500d6a586e07f93ffb690a18222e6
publicInputsHash[1]    = 0x8821cb36904d46326985e8800791e6da3536634a68905c8823199772a2ba6643
```

`acc(PS1) = keccak256(abi.encode( keccak256(abi.encode(bytes32(0), uint256(1),
bytes32(0x101), bytes32(0), uint256(0))), uint256(2), bytes32(0x201), bytes32(0),
uint256(0)))`. (PS0's `acc`/`publicInputsHash` are identical to Vector 5 — same single-rollup
fold — a built-in cross-check.)

### Vector 7 — `sharedPublicInput`, non-empty `callData` + 1 lookup call
Exercises the non-empty `abi.encode(bytes32[])` packing for `lookupCallHashes` and a non-empty
`callData`. `entries = [<Vector 4 entry>]`; one `LookupCall` `{ crossChainCallHash = 0x1234,
destinationRollupId = 1, returnData = 0xabcd, failed = true, callNumber = 0,
lastNestedActionConsumed = 0, calls = [], rollingHash = 0 }`; `callData = 0xcafebabe`;
`crossProofSystemInteractions = keccak256("xpsi")`; single rollup 1 / single PS, `vk = 0x100`,
`blockNumber = 0`.

```
lookupCallHash               = 0x30690221b19c8bbd95cd1379a35163a58e1c340e5689618d62583084ae4e0d43
keccak256(callData=0xcafebabe) = 0x6fe2683bd1d27cbb7a05c570693bea39e0c082ed16722e5ecadcfb7cfdbd20db
crossProofSystemInteractions = 0x6043818a14fa81cd43674dca578863f795ae1551407871464d237744a4ac209e
sharedPublicInput            = 0x0c75410a2dca7acce877a745705bde1721f360436e4732068d0e013c4bbd96d8
acc (rollup1, vk 0x100)      = 0x3b75d0aa6402ebada19a4aee44555af338742741e95ea3973d14aad60255d700
publicInputsHash[0]          = 0x5b37b84b0735b32baf70818d318fdba9ab43eaa16eb4cb8f9eb3fee990f7736d
```

`lookupCallHash = keccak256(abi.encode(lookupCall))` — same per-element commitment the
contract uses for `lookupCallHashes[i]`.

### Vector 8 — DA tag-0x00 payload RLP round-trip (CODEC-AUTHORED)
**Not contract-authored.** The DA payload codec is an off-chain / execution-layer artifact;
the contracts at this commit do not implement the RLP grammar. This fixture is produced by a
self-contained canonical-minimal RLP encoder (`companion-docs/da-rlp-fixture.py`), as a
reference for the grammar in D.7.

Sample batch: `(fromBlock, toBlock]` spans 2 L2 blocks — block `fromBlock+1` has 2 user txs,
block `fromBlock+2` (the Sync block, `toBlock`) has 0 → `blockTxCounts = [2, 0]` (trailing 0
for the Sync block). 2 sample EIP-2718 user txs (block-major), 1 sample ABI-encoded
`l2_entry`.

```
blockTxCounts = [2, 0]            # uint16-valued, canonical-minimal RLP integers
transactions  = [ 0x02f8650180808094000000000000000000000000000000000000dead80c0,
                  0x02f8650180018094000000000000000000000000000000000000beef80c0 ]
l2_entries    = [ 0x00000000000000000000000000000000000000000000000000000000deadbeef ]

rlp([blockTxCounts, transactions, l2_entries]) =
0xf865c20280f83e9e02f8650180808094000000000000000000000000000000000000dead80c09e02f8650180018094000000000000000000000000000000000000beef80c0e1a000000000000000000000000000000000000000000000000000000000deadbeef

payload = 0x00 ‖ rlp(...) =
0x00f865c20280f83e9e02f8650180808094000000000000000000000000000000000000dead80c09e02f8650180018094000000000000000000000000000000000000beef80c0e1a000000000000000000000000000000000000000000000000000000000deadbeef

payload length = 104 bytes
```

Decode invariants checked on the round trip (all hold): leading byte `== 0x00`; top RLP list
has exactly 3 items `[counts, txs, entries]`; `sum(blockTxCounts) == transactions.length`
(`2 + 0 == 2`); each count fits `uint16`; decode of `transactions` / `l2_entries` reproduces
the inputs byte-for-byte. Note the `0` count for the Sync block RLP-encodes as `0x80` (the
empty-string encoding of integer zero), visible as the `…c20280…` prefix of the counts list
(`0xc2` = 2-byte list, `0x02` = count 2, `0x80` = count 0).

### Vectors not generated
- **Proxy creation-code raw bytes**: now fully embedded in D.3 (1111 bytes;
  `keccak256 = 0xb674…c4af`). Proxy CREATE2 addresses are derivable from the spec alone.
- **Type-0x7E transaction envelope vector**: not generated — the envelope serialization is not
  in the contract source (D.8), so no authoritative value can be computed from this codebase.
  Must be pinned by the execution-layer specification.

---

## Discrepancies found (spec body vs. deployed source)

Source = `sync-rollups-protocol@fe7bf66`. As of this revision the spec body has been
reconciled against the source on every point this annex previously flagged; the items below
are retained as a resolved log so reviewers can confirm the reconciliation rather than re-open
it. No open body↔source discrepancy remains.

**Resolved in the body** (verified against the current §3/§5/§7/§8 text):

1. *N-of-M attestation model* (§8.1/§8.2) — body now states the v0 PS is a **single-signer
   ECDSA verifier** and that N-of-M is **N independent proof systems**, threshold enforced
   per-rollup (`ThresholdNotMet`). Matches source (no multi-sig packing in `proofs[k]`).
2. *`crossProofSystemInteractions`* (§8.3) — body now defines it as an **opaque
   orchestrator-supplied domain separator** the contract folds raw (cross-refs App. C.1).
   Matches source.
3. *`vkey` semantics* (§8.3) — body now states `vkey[r][k]` is the **opaque `bytes32` the
   rollup manager stores**, explicitly *not* the verifier's recovered signer address. Matches
   source (`Rollup.verificationKey` ≠ `ECDSAProofSystem.signer`).
4. *`blockTxCounts` RLP integer width* (§7.1, A) — body now pins **canonical minimal-length
   RLP integers** (not fixed 2-byte). Confirmed by the codec fixture (Vector 8): count `0`
   encodes as `0x80`.
5. *Sync-block trailing `0`* (§7.1, A) — body now states the Sync block contributes an
   explicit **trailing `0`** count and an empty tx list. Confirmed by Vector 8
   (`blockTxCounts = [2, 0]`).
6. *Type-0x7E envelope* (§3, §9) — body now gives the qualitative envelope (unsigned,
   deterministic, head of Sync block), cross-refs the **full `executeIncomingCrossChainCall`
   signature in D.8**, and marks the envelope byte/RLP serialization as an **execution-layer
   artifact** pinned by the EL spec (out of source / out of this annex).
7. *Struct definitions* (§5, §7.3) — body now uses the current names and references App. D for
   the authoritative `ExpectedL1ToL2Call` / `LookupCall` / `RollupIdWithProofSystems` layouts.
8. *`proofs[k]` packing* (§7.3) — body now annotates `proofs[]` as **one per `proofSystems`
   entry; ECDSA PS = 65-byte `r‖s‖v`**. Matches source.

**Standing note (not a body discrepancy):** `sync-rollups-protocol/CLAUDE.md` still uses the
*old* struct names (`CrossChainCall`/`NestedAction`/`ProofSystemBatch`) and old field names.
That file contradicts the current `IEEZ.sol` and the spec body; the contract source
(`src/interfaces/IEEZ.sol`) and this annex are authoritative.
