# 8. Proving & Settlement

## 8.1 The validator-set proof model

A batch is attested by a **permissioned set of validators**. Each validator is an independent
**proof system** — a contract implementing `verify(proof, publicInputsHash) → bool` — that
independently verifies the batch (re-executes it, checks the result) before attesting. In v0 each
proof system is a **single-signer ECDSA verifier**: it recovers one signature over the **raw
`publicInputsHash`** (§8.3) — no message prefix, low-`s`, `v ∈ {27,28}` — and checks it against its
one configured signer address. `verify` returns a bool; it does **not** recover a set of signers.

"N-of-M" is therefore realised as **N independent proof systems, not one verifier recovering N
signatures.** The batch lists the attesting proof systems in `proofSystems[]`, each carrying its own
`proofs[k]` (for the ECDSA verifier, a 65-byte `r‖s‖v` signature), and **each rollup selects the
subset of proof systems it accepts.** Per-rollup policy — the accepted proof systems, their
verification keys, and the **threshold** — lives in a per-rollup **manager** contract; settlement
requires at least `threshold` of the rollup's accepted proof systems to attest (the manager reverts
`ThresholdNotMet` otherwise). The `EEZ` registry consults the manager per batch and holds no policy
of its own. A validator MUST attest only a batch it has independently verified correct. Byte-exact
proof and fold layouts are in [Appendix D](D-wire-formats.md).

## 8.2 Multi-prover / threshold

The construction is uniform: a batch carries one or more proof systems, each attesting the same
logical batch over its own `publicInputsHash[k]`, with per-rollup accepted subsets and thresholds
enforced by each rollup's manager. v0's multisig **is** this construction — **one single-signer
ECDSA proof system per validator**, with the rollup's threshold set to the required quorum.
Swapping in a ZK validity proof (Rollup1, §13) is the same fold with a proof-system slot whose
`verify` checks a succinct proof instead of a signature.

## 8.3 Public-inputs hash

The prover and the contract MUST compute the same `publicInputsHash` byte-for-byte, or
verification fails. Construction:

```
entryHashes[i]      = keccak256(abi.encode(entries[i]))
lookupCallHashes[i] = keccak256(abi.encode(l1ToL2lookupCalls[i]))   // v0: proven STATICCALL reads
blobHashes[i]       = blobhash(blobIndices[i])                      // empty in v0 (calldata DA)

sharedPublicInput = keccak256(abi.encodePacked(
    abi.encode(entryHashes),
    abi.encode(lookupCallHashes),
    abi.encode(blobHashes),
    keccak256(callData),
    crossProofSystemInteractions))

for each proof system k:
    acc_k = bytes32(0)
    for each attesting rollup r (rollupId-ascending) that lists k:
        acc_k = keccak256(abi.encode(acc_k, rollupId_r, vkey[r][k], blockHash_r, timestamp_r))
    publicInputsHash[k] = keccak256(abi.encodePacked(sharedPublicInput, acc_k))
```

`(blockHash_r, timestamp_r)` are the rollup's L1-context, fetched once per rollup via the manager's
`getTimestampAndBlockHash(batch.blockNumber)`. `vkey[r][k]` is the **opaque `bytes32` the rollup's
manager stores for proof system `k`** — for the v0 ECDSA verifier this is *not* the signer address
the verifier recovers against, but a separate manager-held value. `crossProofSystemInteractions` is
an **opaque domain-separator supplied by the orchestrator**; the contract folds it raw and gives it
no internal structure (see [Appendix C](C-open-questions.md) C.1 on domain separation). The
per-proof-system fold walks rollups in canonical **rollupId-ascending order, which the contract
enforces** (out-of-order or duplicate rollups revert), and indexes each rollup's local proof-system
subset — a global vkey index is wrong. `abi.encode` (positional) and `abi.encodePacked` (raw
concatenation) are used exactly as shown; byte-exact in [Appendix D](D-wire-formats.md).

## 8.4 Entry points

- **`registerRollup(manager, initialState) → rollupId`** — permissionless. Assigns a fresh
  `rollupId`, binds the per-rollup manager, and records the initial state root.
- **`postAndVerifyBatch(batch)`** — verifies and settles a batch: validate structure → fetch each
  rollup's accepted proof systems, vkeys, and threshold, and verify each proof system's proof over
  its `publicInputsHash[k]` — requiring at least the rollup's threshold (any failure reverts the
  whole call) → mark each touched rollup verified this block → execute the batch's entries (§5.5).
  Emits `BatchPosted` and, per consumed entry, `L2ExecutionPerformed`.
- **`setStateRoot(rollupId, newRoot)`** — manager-only escape hatch; locked for the L1 block in
  which a batch already touched that rollup.

## 8.5 Settlement rule

A batch is **settled** for a rollup only when its `postAndVerifyBatch` lands on L1 **and** the
inclusion emits `L2ExecutionPerformed(rollupId, newState)` whose `newState` equals the L2 state
root the operator committed for that batch's Sync block. Inclusion alone is insufficient. A
follower/operator that does not observe a matching `L2ExecutionPerformed` from the `EEZ` address
treats the batch as not settled and (for the operator) rolls back the optimistic Sync block (§4.4,
§6). Verdicts MUST filter logs by the `EEZ` contract address and `rollupId`, so a colliding event
from another contract cannot spoof settlement.

## 8.6 Safety basis

Settlement rests on three complementary layers, not on the validators alone:

1. the **N-of-M attestation** is the trust root for the *honesty* of a state transition: at least
   `threshold` accepted proof systems must attest it (§8.1);
2. **on-chain invariants** enforced regardless of any proof (§5.4: pre-state binding, ether
   conservation, rolling-hash integrity) make whole classes of fraud impossible *independently* of
   layer 1 — even a fully-malicious validator set cannot land a transition that breaks the state
   chain or conjures ether (the contract reverts regardless), and the inbound mint corresponds to
   L1-locked ether (§9.3) — modulo the open inbound-out-of-gas edge ([Appendix C](C-open-questions.md) C.2);
3. **re-derivation** by any follower (§10) ensures the operator cannot serve a head other than the
   one L1 settled: a follower replays the L1 data and rejects any divergence (equivocation). Note
   re-derivation *reproduces* a transition faithfully — it does not, by itself, establish that a
   validator-attested, self-consistent transition is honest; that is what layer 1 is for (a
   Rollup0/GC property; §6 R6). Cross-deployment replay and stale re-submission remain open
   ([Appendix C](C-open-questions.md) C.1).

Cost analysis for the signature scheme (ECDSA vs BLS) is in [Appendix B](B-gas-cost-analysis.md).

---

*Next: [§9 L1 → L2: the cross-chain flow](09-l1-to-l2.md).*
