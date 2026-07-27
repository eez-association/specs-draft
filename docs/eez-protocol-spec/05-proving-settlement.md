# 5. Proving and Settlement

## 5.1 Proof-system interface and policy

A proof system is a contract implementing:

```solidity
verify(bytes proof, bytes32 publicInputsHash) external view returns (bool);
```

`EEZ` does not select one proof construction. Each registered rollup manager selects accepted
proof-system addresses, their opaque `bytes32` verification keys, and a threshold. A network
profile MUST identify the manager, proof systems, keys, threshold, administrator set, and resulting
trust assumption.

For every rollup in a batch, `EEZ` resolves the proof-system addresses selected by that rollup's
`proofSystemIndex[]` and calls:

```solidity
checkProofSystemsAndGetVkeys(address[] proofSystems)
    external view returns (bytes32[] vkeys);
```

The returned vector MUST have exactly the requested length. The manager is responsible for
membership and threshold policy. A manager revert, a malformed vector, a proof-system revert, or a
`false` verification result reverts the complete batch transaction.

These calls are static at the EVM boundary. A revert from
`checkProofSystemsAndGetVkeys`, `getCustomData`, or `verify` is forwarded without a core wrapper.
A successful response with invalid ABI encoding reverts during Solidity decoding. `EEZ` rejects a
verification-key vector only when its length differs from the requested length; it folds every
returned `bytes32`, including zero, verbatim. `verify(...) == false` is the one verifier failure
translated to `InvalidProof()`.

External-call order is also observable on failure. `EEZ` first calls every participating manager's
key-vector function in rollup-ID order. It then calls every participating manager's
`getCustomData` in the same order. Finally, it calls proof systems in global proof-system-array
order. A failure stops at that call and prevents every later call.

The reproduced source snapshot includes a single-signer ECDSA adapter. A profile that selects it
supplies an exact 65-byte `r || s || v` signature over the raw `publicInputsHash`: there is no
EIP-191 prefix or EIP-712 domain. The adapter enforces canonical low `s` and `v` in `{27, 28}`.
One adapter recovers one configured signer. An N-of-M committee therefore uses separate adapter
instances rather than packing M signatures into one proof. This adapter is available to profiles;
it is not an EEZ-wide proof-policy requirement.

The snapshot's `Rollup` manager and `ECDSAProofSystem` adapter are reference implementations, not
normative contracts of `eez-evm@0.2-draft`. A profile that uses either MUST pin its complete ABI,
runtime bytecode, constructor/configuration values, and administrator behavior. In particular, the
reference manager permits threshold zero or a threshold above its current proof-system count, and
the reference adapter permits signer replacement without a signer-change event or zero-address
check. Its OpenZeppelin signature decoder reverts on malformed signatures instead of returning
`false`. A client MUST obtain these behaviors from the pinned network component, not infer them
from the three core-contract ABIs.

## 5.2 Batch structural validation

Before it makes an external call, `postAndVerifyBatch` applies every structural rule in
[§4.5.1](04-execution-model.md#451-structural-validity). In particular:

- proof-system addresses and rollup IDs are non-empty, non-zero, and strictly increasing;
- proof and proof-system arrays have equal length;
- every local proof-system index is non-empty, strictly increasing, and in range;
- entry state-delta sets and lookup state-root-pin sets are non-empty, sorted routing proofs;
- call sources and expected destinations belong to the applicable routing set; and
- both transient prefix counts are in range.

ABI decoding alone is not structural conformance. Call-count partitions, `revertSpan` bounds,
lookup-key uniqueness, static-call metadata, and L2 table structure remain producer obligations
checked during replay or by the invariants in §4.13.

## 5.3 Public-inputs hash

Let `H(x) = keccak256(x)`. For the batch layout in [Appendix B](B-wire-formats.md), the verifier
computes:

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

for each global proof-system index k:
    acc_k = bytes32(0)
    for r in rollupId-ascending batch order where r selects k:
        j = the local position of k in r.proofSystemIndex
        acc_k = H(abi.encode(acc_k, r, vkMatrix[r][j]))
    publicInputsHash_k = H(abi.encodePacked(sharedPublicInput, acc_k))
```

`blobIndices` has no structural sort, uniqueness, or range check. `BLOBHASH` returns zero for an
index outside the transaction's versioned blob-hash list. Empty, repeated, unsorted, and
out-of-range indices therefore remain part of the byte-exact public-input construction.

`getCustomData(uint64)` returns opaque `bytes`. The EVM binding assigns no required internal
encoding. A profile MUST specify the manager implementation and the exact meaning of
`batch.blockNumber` and returned custom data. The reference manager returns empty bytes for block
number `0`; for `type(uint64).max` it returns an encoding of the current timestamp and previous
block hash; and for an available historical block it returns an encoding of zero and that block
hash. These reference behaviors are not universal profile policy.

The custom-data fold includes every participating rollup. The per-proof-system fold includes only
rollups that selected that global index. `vkMatrix[r][j]` uses the local position `j` in the
manager response; using the global index to address a jagged response is wrong.

The batch in this binding has no `crossProofSystemInteractions` member. Implementations MUST NOT
insert that field from an older binding. The two `abi.encode` disciplines, tuple layouts, and
vectors are byte-exact in Appendix B.

The transient prefix counts do not enter `sharedPublicInput`. `msg.sender` also does not enter a
proof input, and `postAndVerifyBatch` has no submitter access check. A submitter can therefore
reuse an otherwise identical proof while changing either count within the structural bounds. The
proved entry and lookup bytes remain unchanged, but their immediate, meta-hook, discarded, and
persistent-queue treatment can change.

This is a routing-integrity limitation of `eez-evm@0.2-draft`, not authority granted by the proof.
A production execution-network profile MUST NOT select this binding unless it also selects a versioned
external submission or inclusion mechanism that authorizes one exact caller and the exact two
counts before `EEZ` executes the transaction. The mechanism MUST define proof-reuse,
front-running, rejection, and partial-inclusion behavior. An off-chain convention that honest
submitters use the intended counts is not a contract-enforced mitigation. Correcting the proof
commitment itself requires a new EVM-binding edition.

## 5.4 Verification and publication

`postAndVerifyBatch(batch)` performs these proof and publication stages:

1. validate structure without external calls;
2. obtain every selected manager verification-key vector and custom-data value;
3. compute every `publicInputsHash_k` and require every selected proof to verify;
4. set `lastVerifiedBlock = block.number` for each participating rollup, replace that rollup's
   persistent queues, and reset its cursor;
5. load and process the transient prefixes under §4.9;
6. publish the non-transient suffix by destination rollup; and
7. emit `BatchPosted`.

All proof checks are atomic with the transaction. Entry execution is not atomic across the entire
batch: an immediate zero-hash entry can fail in its isolated self-call and be skipped, a successful
meta hook can leave transient entries that cleanup discards, and persistent entries can remain
unconsumed. `BatchPosted` therefore means that the batch call completed, not that every proved
entry executed.

The other settlement entry points are:

- `registerRollup(manager, initialState)`: performs the allocation, store, callback, and event
  transition in [§4.3.1](04-execution-model.md#431-rollup-registration-transition);
- `setStateRoot(rollupId, newRoot)`: lets the registered manager replace its root outside active
  replay and outside an Ethereum block that already verified that rollup; and
- the consumption functions in §4.3, which apply state deltas and emit execution events.

## 5.5 Settlement evidence

For this EVM binding, a state delta actually committed only when a surviving
`L2ExecutionPerformed(rollupId, newState)` log was emitted by the profile-pinned `EEZ` deployment.
`BatchPosted` alone is insufficient. Consumers MUST associate logs with the exact Ethereum
settlement chain,
contract address, transaction receipt, rollup ID, and log order. They MUST account for later
same-block queue replacement.

The current on-chain root may also change through the manager-only `setStateRoot` path. A profile
MUST state whether and how consumers accept such a replacement.

EEZ does not map a committed state root to a network block, safe head, or finalized head. A network
profile defines that mapping, its data-availability evidence, its partial-consumption rule, and its
Ethereum finality rule.

## 5.6 Authority and upgrade boundary

The registered manager is the policy authority for one rollup. It can change the effective proof
policy through whatever administration its implementation exposes and can invoke `setStateRoot`
under the restrictions above. The same-block root lock is not a validity proof, timelock, or
dispute window.

Proof-system administration can also change effective validity policy. For example, replacing the
signer in an ECDSA adapter changes who can authorize a transition even when the manager's address
list is unchanged. A network profile MUST identify all manager, proof-system, deployment-proxy,
and upgrade administrators. Registration is permissionless and does not endorse a manager.
Consumers MUST identify a deployment by more than `rollupId`.

## 5.7 Security boundary

The selected proof policy is the trust root for whether an internally consistent `newState` is a
correct execution result. The EVM binding additionally enforces structural routing, live pre-state
roots, replay order and hashes, complete consumption cursors, and entry-local L1 book accounting.
Those checks constrain a proof-authorized transition; they do not execute the rollup
state-transition function, decode profile DA, establish cross-side value backing, or make a
non-binding verifier sound. They also do not authenticate the transient prefix counts or batch
submitter in `eez-evm@0.2-draft`.

Data availability, independent derivation, sequencing, atomic cross-transaction inclusion,
censorship resistance, exits, and Ethereum finality are not supplied by EEZ. The complete reusable
security boundary is in [§6](06-security-model.md). Every network profile MUST state the guarantees
it adds and the authorities on which those guarantees depend.

---

*Next: [§6 Security Model](06-security-model.md).*
