# 2. Architecture

EEZ separates reusable EVM contracts from the actors and policies selected by a network profile.

## 2.1 Contract roles

- **`EEZ` (settlement host)** — the registry and L1 execution manager. It holds, per registered
  rollup, a state root, book balance, and replaceable persistent entry/lookup queues; verifies
  batches; and replays cross-chain calls through deterministic proxies.
- **Rollup manager (settlement host)** — the policy authority for one registered rollup. It
  selects accepted proof systems, verification keys, and a threshold; provides the block context
  folded into proof inputs; and holds the `setStateRoot` authority described in §5.6.
- **Proof system (settlement host)** — a contract implementing
  `verify(bytes proof, bytes32 publicInputsHash) → bool`. EEZ does not require one proof
  construction; a network profile selects concrete contracts and trust assumptions.
- **`EEZL2` (rollup EVM)** — the distinct L2 execution manager used for inbound delivery and
  proxy routing. It has no rollup registry, proof registry, state-root ledger, or per-rollup book
  balance. A profile-selected immutable `SYSTEM_ADDRESS` replaces and drives its tables.
- **Cross-chain proxy (both EVMs)** — the deterministic local representative of a remote
  `(rollupId, address)` pair.

The two managers share proxy identity, action hashes, replay tags, and lookup concepts. They do
not share one ABI data model. L1 objects include state deltas, routing IDs, and root pins; L2
objects omit those fields and use their own expected-outgoing and incoming-call types.

The settlement-host profile pins the deployed L1 contracts. The rollup profile pins its registered
rollup ID, exact compatible binding edition, L2 predeploy addresses, delivery mechanism, cross-side
construction, value/custody mapping, and proof policy.

## 2.2 External actors

EEZ exposes behavior to three abstract actor classes:

- a **batch submitter** constructs and submits a batch;
- one or more **proof producers** produce proofs accepted by the selected proof-system contracts;
  and independently check the transition claimed by their proof policy; and
- a **consumer** invokes a proxy or another consumption entry point while the verified execution
  table is live.

A network MAY assign several classes to one operator or decentralize them independently. EEZ
therefore does not normatively define “the operator,” a sequencing protocol, a follower, or an
Engine API. For example, Rollup0 selects one permissioned operator and a host-derived follower in
the [Rollup0 Network Specification](../rollup0-network-spec/index.md).

In `eez-evm@0.2-draft`, the contract does not authenticate the batch submitter, and the proof does
not bind the transient prefix counts. The submitter is therefore an execution-routing authority
unless the network profile supplies the external mitigation required by §7.2.

## 2.3 Interfaces

The reusable EVM interface consists of:

- registration and state: `registerRollup`, `setStateRoot`;
- verification and publication: `postAndVerifyBatch`;
- consumption: `executeCrossChainCall`, `executeL2TX`, `staticCallLookup`;
- L2 delivery: `loadExecutionTable`, `executeIncomingCrossChainCall`; and
- proof and manager callbacks: `IProofSystem` and the per-rollup manager interface.

Canonical tuple layouts, selectors, hashing rules, and conformance vectors are in
[Appendix B](B-wire-formats.md).

The registered manager and proof-system administrators are security authorities, not merely
configuration providers. Their reusable trust boundary is in [§6](06-security-model.md).

---

*Next: [§3 EVM Binding](03-evm-binding.md).*
