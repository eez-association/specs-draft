# 2. Architecture

EEZ separates reusable EVM contracts from the actors and policies selected by a network profile.

## 2.1 Conceptual flow

**Informative.** In this binding, the **settlement side** is the Ethereum EVM where `EEZ` runs. An **execution
network** is a registered network such as Rollup0 or Gnosis Chain, with its own EVM state and
blocks. The contract and ABI names also call these sides L1 and L2. A **cross-chain proxy** is a
deterministic local address that represents a contract on another registered network. An
**execution entry** is a precomputed result and replay plan for one action. A **batch** commits a
set of entries and the proofs selected by the participating network profiles. Appendix A contains
the full [glossary](A-reference.md#a4-glossary).

An EEZ interaction has this lifecycle:

1. A network-defined producer executes a proposed transaction range and records every
   cross-network call, nested call, lookup, return value, value movement, and resulting network
   state.
2. The producer encodes that result as side-specific execution entries. An L1 entry can carry
   state-root and book-balance deltas. An L2 entry carries the call tables needed to replay an
   inbound action. The two entry types are related but are not wire-compatible.
3. The network-selected proof systems attest the batch public input. The registered network
   manager selects which proof systems and verification keys count.
4. `EEZ` verifies the selected proofs and loads the proven entries. Immediate entries run during
   the post transaction. Deferred entries remain consumable only under the binding's same-block
   rules.
5. A call to a deterministic cross-chain proxy asks the local manager to consume the next matching
   entry. The manager checks the action identity, state precondition, call order, nested results,
   rolling hash, and value accounting that apply to that path.
6. A network follower uses its network specification to obtain DA, authenticate canonical
   settlement evidence, reconstruct its own blocks, and decide when those blocks are safe or
   finalized.

The settlement contract checks structure, selected proofs, live pre-state conditions, replay, and
book accounting. It does not execute an independent copy of the network's full state transition.
Validity therefore depends on the proof policy selected by the network profile. Candidate
admission, block production, DA, canonical competition, and finality are also network rules, not
implicit EEZ behavior.

## 2.2 Contract roles

- **`EEZ` (Ethereum settlement layer)** — the registry and L1 execution manager. It holds, per registered
  rollup, a state root, book balance, and replaceable persistent entry/lookup queues; verifies
  batches; and replays cross-chain calls through deterministic proxies.
- **Rollup manager (Ethereum settlement layer)** — the policy authority for one registered rollup. It
  selects accepted proof systems, verification keys, and a threshold; provides the block context
  folded into proof inputs; and holds the `setStateRoot` authority described in §5.6.
- **Proof system (Ethereum settlement layer)** — a contract implementing
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

Each EEZ execution-network profile pins its registered rollup ID, exact compatible binding
edition, L2 predeploy addresses, delivery mechanism, cross-side construction, value/custody
mapping, proof policy, and direct Ethereum settlement deployments.

## 2.3 External actors

EEZ exposes behavior to three abstract actor classes:

- a **batch submitter** constructs and submits a batch;
- one or more **proof producers** produce proofs accepted by the selected proof-system contracts;
  and independently check the transition claimed by their proof policy; and
- a **consumer** invokes a proxy or another consumption entry point while the verified execution
  table is live.

A network MAY assign several classes to one authority or decentralize them independently. EEZ
therefore does not normatively define an operator, a sequencing protocol, a follower, or an Engine
API. The network profile separately specifies candidate admission, candidate authentication,
competition, settlement relay, and proof-system membership. Rollup0 accepts a candidate from any
producer when it is valid under the Rollup0 rules. Gnosis Chain uses permissioned candidate
admission. These are peer network choices, not EEZ framework rules.

In `eez-evm@0.2-draft`, the contract does not authenticate the batch submitter, and the proof does
not bind the transient prefix counts. The submitter is therefore an execution-routing authority
unless the network profile supplies the external mitigation required by §7.5.

## 2.4 Interfaces

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
