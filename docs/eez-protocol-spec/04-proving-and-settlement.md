# 4. Proving and Settlement

EEZ supports one or more proof systems. Each proof system implements:

```text
verify(proof, publicInputsHash) -> bool
```

A batch carries one proof per listed proof system. Each rollup selects the subset it accepts. The
rollup's manager supplies the verification keys and enforces that rollup's proof policy. The `EEZ`
registry holds no proof policy of its own.

## 4.1 Batch

`postAndVerifyBatch` takes one `ProofSystemBatchPerVerificationEntries`:

```solidity
struct ProofSystemBatchPerVerificationEntries {
    ExecutionEntry[] entries;
    LookupCall[] l1ToL2lookupCalls;
    uint256 transientExecutionEntryCount;
    uint256 transientLookupCallCount;
    address[] proofSystems;
    RollupIdWithProofSystems[] rollupIdsWithProofSystems;
    bytes32 crossProofSystemInteractions;
    uint256[] blobIndices;
    bytes callData;
    bytes[] proofs;
    uint64 blockNumber;
}

struct RollupIdWithProofSystems {
    uint256 rollupId;
    uint64[] proofSystemIndex;
}
```

`callData` is opaque to the contract. It is hashed into the public inputs. The meaning and
availability of those bytes are network rules.

## 4.2 Multi-proof-system model

The construction is uniform: a batch carries one or more proof systems, each attesting the same
logical batch over its own `publicInputsHash[k]`, with per-rollup accepted subsets enforced by each
rollup's manager.

`proofSystems[]` is a batch-global list in strictly increasing address order.
`proofs[k]` is the proof from proof system `k`. Each
`RollupIdWithProofSystems.proofSystemIndex[]` is a strictly increasing list of indices into that
global array.

The proof type and acceptance policy are not fixed by EEZ.

## 4.3 Public-inputs hash

The prover and the contract MUST compute the same `publicInputsHash` byte-for-byte:

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

for each proof system k:
    acc_k = bytes32(0)
    for each rollup r in ascending rollupId order that lists k:
        acc_k = keccak256(abi.encode(
            acc_k,
            rollupId_r,
            vkey[r][k],
            blockHash_r,
            timestamp_r))

    publicInputsHash[k] =
        keccak256(abi.encodePacked(sharedPublicInput, acc_k))
```

`(blockHash_r, timestamp_r)` is the rollup's settlement context, fetched once per rollup through:

```text
getTimestampAndBlockHash(batch.blockNumber)
```

With `blockNumber == 0`, the manager returns zero timestamp and zero block hash. With
`blockNumber == type(uint64).max`, it binds the current timestamp and previous block hash. Any
other value binds the requested block hash and reverts `BlockHashUnavailable` when that hash is
zero.

`vkey[r][k]` is the opaque `bytes32` returned by the rollup manager for proof system `k`.
`crossProofSystemInteractions` is an opaque domain separator supplied with the batch; EEZ assigns
it no internal structure.

The per-proof-system fold walks rollups in canonical ascending rollup-ID order. The inner fold
uses `abi.encode`; the shared input and final wrap use `abi.encodePacked`.

Verification is atomic. Every listed proof system MUST return true for its proof and public-input
hash, or the complete `postAndVerifyBatch` call reverts `InvalidProof`.

## 4.4 Entry points

- **`registerRollup(manager, initialState) -> rollupId`** — permissionless. Assigns a fresh rollup
  ID, binds the per-rollup manager, and records the initial state root.
- **`postAndVerifyBatch(batch)`** — validates structure, fetches accepted proof systems and
  verification keys from each manager, verifies every proof, marks each touched rollup verified in
  the current block, and executes or publishes the batch entries.
- **`setStateRoot(rollupId, newRoot)`** — manager-only escape hatch; locked for the settlement
  block in which a batch already touched that rollup.

`postAndVerifyBatch` emits `BatchPosted` and, per consumed state delta,
`L2ExecutionPerformed`.

## 4.5 Settlement rule

A batch is settled for a rollup only when `postAndVerifyBatch` lands on the settlement layer and
the inclusion emits:

```text
L2ExecutionPerformed(rollupId, newState)
```

with the expected `rollupId` and state root. Inclusion alone is insufficient. A settlement verdict
MUST filter logs by the `EEZ` contract address and `rollupId`, so an event from another contract
cannot spoof settlement.

The mapping between that state root and a network block is a network rule.

## 4.6 Safety basis

Settlement combines:

1. the proof systems selected by the registered rollup manager; and
2. on-chain invariants enforced independently of the proof: pre-state binding, ether conservation,
   sequential consumption, and rolling-hash integrity.

The first establishes the validity claim chosen by the network. The second prevents a batch from
breaking the accepted state chain or the per-entry ether equation, even when a proof verifies.

---

*Next: [Wire Formats and Conformance Vectors](05-wire-formats.md).*
