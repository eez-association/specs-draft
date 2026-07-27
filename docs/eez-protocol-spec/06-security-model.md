# 6. Security and Trust Model

This chapter defines the reusable security boundary of the EEZ EVM binding. A network profile can
add guarantees, but it cannot describe a property as contract-enforced when the binding delegates
that property to a manager, proof system, execution layer, or external service.

## 6.1 Contract-enforced properties

Subject to correct EVM execution and the exact binding in this specification, `EEZ` enforces:

- structural routing sets and proof-system indices before external verification calls;
- verification of every proof-system entry listed by a structurally valid batch;
- a live pre-state check before each L1 `StateDelta` is applied;
- ordered entry, flat-call, expected-call, and lookup replay;
- declared rolling-hash and complete-cursor endpoints;
- the signed per-entry L1 accounting equation in §4.11.1;
- non-underflow of each recorded rollup `etherBalance`; and
- caller restrictions and current-block gates stated in §4.

These properties do not establish that a `newState` is the result of a correct rollup
state-transition function. They also do not establish that every proved entry executed, that L2
value is backed, that profile data is available, or that a transaction outside the current
`postAndVerifyBatch` frame was included atomically with it.

## 6.2 Proof and manager authority

The selected proof policy is the validity trust root. An honest proof producer is expected to
check the complete transition that its proof statement claims. `EEZ` checks only the proof-system
contract's `verify` result and its own local invariants. A verifier that ignores
`publicInputsHash`, an unsound validity verifier, or a threshold of compromised attestation
adapters can authorize an incorrect but locally self-consistent root.

Proof authorization does not cover every execution-routing input in `eez-evm@0.2-draft`.
`transientExecutionEntryCount`, `transientLookupCallCount`, and `msg.sender` are absent from the
proof public inputs, and `postAndVerifyBatch` is permissionless. A third party can copy a valid
batch transaction, change either in-range count, and submit the same proofs from another address.
That can change which zero-hash entries execute immediately, which entries are exposed to the
caller's meta hook, which unconsumed transient objects cleanup discards, and which suffixes enter
persistent queues. If the new caller is a contract, it also selects a different meta hook.

Structural bounds prevent out-of-range partitions; they do not bind the intended partition.
Consequently, a production rollup profile selecting this binding MUST specify a versioned external
mechanism that authenticates the submitting identity and exact counts before execution. The
profile MUST describe front-running and proof-reuse prevention and MUST treat failure of that
mechanism as a validity or availability failure, as applicable. The current `EEZ` contract has no
allowlist, nonce, or count commitment that provides this property. A contract-level correction
requires a new binding edition.

The registered rollup manager is also an authority. It selects accepted proof systems, verification
keys, and threshold under its own implementation and can replace the recorded root through
`setStateRoot` outside the binding's active-execution and same-block restrictions. Those
restrictions are not a timelock, validity check, or dispute window.

Administration of a proof-system contract can change effective validity policy even when manager
configuration is unchanged. For example, replacing the signer of an ECDSA adapter changes who can
authorize its proof slot. A deployment that places `EEZ`, a manager, or a proof system behind an
upgrade proxy adds that proxy's administrators to the trusted set.

`registerRollup` is permissionless. Registration does not endorse the manager or proof systems.
Consumers MUST identify an intended deployment by the host chain, `EEZ` address and code
commitment, rollup ID, manager address and code commitment, proof-system addresses and code
commitments, and applicable administrator set. A rollup ID alone is insufficient.

## 6.3 Accepted state versus valid state

The following concepts are distinct:

| Concept | Evidence | Meaning |
|---|---|---|
| **Recorded root** | Current `EEZ` storage for the rollup | The commitment currently accepted by the deployed contract. It may have been written by entry consumption or `setStateRoot`. |
| **Applied batch endpoint** | Genuine, ordered `L2ExecutionPerformed` logs from a successful receipt | A state delta that actually committed during entry execution. `BatchPosted` alone does not prove this. |
| **Valid rollup state** | The profile's proof, execution, DA, and derivation requirements | A state that satisfies the network's complete transition rule. EEZ cannot establish this independently of the selected proof policy. |
| **Safe or finalized state** | Profile-defined host inclusion and finality evidence | A network consensus conclusion outside this reusable binding. |

A consumer MUST NOT infer a valid, safe, or finalized rollup block from `BatchPosted`. It MUST
filter events by the exact host chain, deployed `EEZ` address, transaction receipt, rollup ID, and
log order. It MUST also handle manager root replacement and same-block queue replacement according
to the network profile.

Independent re-execution can detect disagreement between published inputs and a claimed endpoint.
It does not reverse host-chain state, override manager authority, create a fraud proof, or provide
an exit.

## 6.4 Atomicity and partial execution

Batch structure checks and all proof verifications occur in one `postAndVerifyBatch` transaction.
A failure during those stages reverts the complete transaction.

Entry execution has narrower boundaries:

1. A leading immediate entry executes through an isolated self-call. Failure rolls back that entry,
   emits `ImmediateEntrySkipped`, advances the transient cursor, and permits later immediate
   attempts.
2. A contract-caller meta hook can consume all, some, or none of the remaining transient prefix.
   If the hook returns successfully, cleanup deletes every unconsumed transient entry and lookup.
   If the hook reverts, the complete batch transaction reverts.
3. Entries after the transient prefix are routed to per-rollup persistent queues. They can remain
   unconsumed and become unusable after the current host block.
4. A later verification for the same rollup in the same block replaces its unconsumed persistent
   queues.

Successful earlier entries and their state deltas remain applied when another immediate entry is
skipped or a persistent entry is never consumed. A profile MUST define how it associates actual
entry effects with its blocks and what it does with skipped, discarded, replaced, or unconsumed
entries. An external list of host transactions is not made atomic by this contract. Any
cross-transaction atomicity claim requires a separately specified inclusion mechanism and failure
rule.

## 6.5 ETH custody and cross-side backing

On L1, the `EEZ` contract is the physical ETH custodian. A proxy forwards its full call value to
`EEZ`; the proxy does not retain it. All registered rollup book balances share the one physical
contract balance.

Let:

```text
B = address(EEZ).balance
L = sum(rollups[r].etherBalance for all registered rollups r)
I = all value entering EEZ during one consumed entry
O = all successful non-static value leaving EEZ during that entry
```

For every successfully consumed entry, the binding enforces:

```text
sum(entry.stateDeltas[i].etherDelta) = I - O
```

The accumulator includes top-level and reentrant flows. Failed calls and reverted frames do not
contribute to `O`. Each negative delta is checked against that rollup's recorded balance.

The binding does not iterate over all rollups and does not enforce aggregate solvency. A
value-bearing profile MUST define an initial and continuing backing rule. A common required
condition is:

```text
B >= L
```

Forced or unsolicited ETH can produce `B > L` without creating a recorded claim.
`etherBalance` is protocol accounting, not segregated custody or a direct user withdrawal claim.
Manager and proof-policy control can authorize an entry that spends pooled ETH, so those
authorities are custody assumptions for a value-bearing network.

`EEZL2` has no corresponding book ledger and does not mint value. It only requires inbound
`msg.value` to equal the explicit action value. EEZ does not define the rule that connects an L1
deposit or book delta to an L2 value supply, an L2-originated transfer to an L1 outflow, residual
manager balances, or a withdrawal. A profile MUST specify and test those relations for every
success and failure path before it can claim backing.

## 6.6 Replay and deployment domains

The core encodings do not provide complete deployment-level domain separation:

- `crossChainCallHash` contains the two rollup IDs, two addresses, value, and data, but no host
  chain ID, manager address, protocol version, or per-call nonce;
- the CREATE2 salt contains only the remote rollup ID and original address;
- the batch has no explicit monotonic nonce;
- the transient prefix counts and batch submitter are absent from the proof public inputs; and
- `getCustomData(batch.blockNumber)` is opaque manager output whose contents EEZ does not constrain.

The manager address still affects the final CREATE2 proxy address. State-root preconditions and
manager-supplied custom data can also prevent a replay in a particular deployment. Neither fact is
a universal domain rule.

A profile MUST specify how its manager binds proofs to the intended host chain, `EEZ` deployment,
binding version, and batch position. It MUST state stale-resubmission behavior and any assumptions
that remain across forks or deployments. A profile MUST NOT claim that an opaque custom-data value
provides a domain unless its construction and enforcement are specified.

## 6.7 Guarantees owned by a network profile

EEZ does not define:

- sequencing authority, ordering fairness, or force inclusion;
- the L2 transaction envelope or system-call value source;
- the cross-side lowering between L1 and L2 tuple families;
- data-availability publication and reconstruction;
- a block-to-settlement mapping, safe head, finality rule, or reorg procedure;
- an atomic builder or relay;
- fee charging or economic sustainability;
- governance delays, emergency legitimacy, or key recovery; or
- withdrawals, trustless exits, or user compensation.

The required profile in [§7](07-network-profile.md) makes these boundaries explicit. A production
profile has no unresolved release-blocker selection and MUST state its trusted authorities and the
consequence of each authority failing. A production rollup profile selecting
`eez-evm@0.2-draft` must additionally satisfy the proof-routing mitigation requirement in §7.2.

---

*Next: [§7 Required Network Profile](07-network-profile.md).*
