# 9. Security and Trust Model

This chapter adds Rollup0's network choices to the
[EEZ security model](../eez-protocol-spec/06-security-model.md). Rollup0 has open candidate
production and permissioned validity attestations. Gnosis Chain is a separate peer network with a
different admission policy.

## 9.1 Security-relevant states

- **Candidate-valid** means a candidate passes the active Rollup0 execution, DA, and construction
  rules.
- **Attested** means the configured proof threshold accepted the candidate.
- **EEZ-accepted** means an Ethereum transaction applied the transition under the selected EEZ
  contracts.
- **Safe** means a local follower reconstructed the transition from canonical Ethereum data and
  exact per-effect evidence.
- **Finalized** means safe and contained in finalized Ethereum history.

These terms are not interchangeable. An attestation does not select among valid siblings.
Canonical Ethereum transaction order selects the first candidate whose exact named parent is still
the current settled cursor.

## 9.2 Open candidate production

Any party MAY produce a Rollup0 candidate. Producer identity is not a validity input. A validator
or prover:

- MUST evaluate every candidate it receives through a supported candidate interface;
- MUST apply the same checks regardless of producer;
- MUST sign or prove every candidate that is valid under its declared service policy;
- MAY sign several valid siblings from the same parent; and
- MUST NOT claim that its signature gives a sibling priority.

The protocol does not require a validator to support every transport or proof backend. Its
supported interface and availability policy MUST be public and producer-neutral. Selective
service, private allowlists disguised as validity checks, or producer-dependent ordering violates
the Rollup0 admission rule.

Open production improves censorship resistance only when candidates can reach enough validators
and an Ethereum submitter. It does not remove proof-threshold, relay, or Ethereum fee dependencies.

## 9.3 Trusted authorities and dependencies

| Actor | Authority or dependency | Main failure |
|---|---|---|
| Manager governance | Selects proof policy and exercises any binding-defined administrative state authority. | Can weaken validity, install an underivable state, or halt settlement. |
| Accepted validators and provers | Attest candidate validity under the selected threshold. | A malicious or compromised threshold can accept invalid state. |
| Candidate producers | Construct unsafe blocks, DA, proofs, and settlement candidates. | Can censor their own feed, equivocate, or withhold data before publication, but have no identity-based priority. |
| Ethereum submitter or builder | Places candidates and companion transactions on Ethereum. | Can censor, reorder, split, front-run, or fail exact-target inclusion unless the activated mechanism prevents it. |
| Ethereum | Supplies canonical execution, ordering, calldata availability, receipts, and finality. | Reorganizations move the safe view; consensus failure is outside Rollup0 recovery. |
| System-transaction authority | Authorizes Rollup0 calls to `EEZL2` and may supply inbound value. | Compromise can forge system actions, drain reserves, or violate deterministic derivation. |
| Follower implementation | Reconstructs the safe and finalized L2 views. | A bug can accept the wrong chain or halt; a correct follower still cannot reverse Ethereum state. |
| Upgrade and recovery governance | Changes deployments, code, profiles, and exceptional recovery points. | A bad activation can replace every assumption above. |

Production MUST identify these authorities, separate compromise domains where practical, and
publish rotation, delay, threshold, and emergency rules.

## 9.4 Proof-policy boundary

The selected EEZ contracts check the configured proof policy; they do not independently execute
the Rollup0 state transition. Security therefore requires a threshold of accepted validators or
provers to bind their attestations to:

- the exact parent height, block hash, and state root, and every selectable endpoint identity;
- the complete batch calldata;
- every execution entry and lookup;
- transient routing counts and their semantics;
- the Rollup0 profile and binding version;
- the intended Ethereum contract and chain domain; and
- any companion-transaction construction on which settlement depends.

In `eez-evm@0.2-draft`, transient prefix counts and `msg.sender` are absent from the core proof
public inputs. A production Rollup0 deployment MUST add an external, binding mitigation that
authenticates the submitter-controlled fields, caller, domain, replay, and front-running behavior.
Validator inspection of raw calldata is necessary but is not by itself a cryptographic repair.

Mock proof mode provides no validity security. Remote binding prover mode provides only the
guarantees of its authenticated implementation and selected keys.

## 9.5 Competition and stale siblings

Two valid candidates may extend the same parent, and a validator may attest both. The winner is
the first applicable transition in canonical Ethereum transaction order. Once it changes the
settled cursor identity, a later sibling is stale and MUST NOT advance Rollup0. Applicability
compares the exact parent height, block hash, and state root. Root equality alone does not keep an
old sibling applicable.

Clients MUST NOT choose a winner by:

- first network receipt;
- validator signature time;
- producer identity;
- highest fee observed off chain;
- a lexicographic hash rule; or
- a root found anywhere in the Ethereum block.

Those rules would fork followers that observe messages or RPC results in different orders.

The current EEZ binding stores only the state root. Production therefore needs the separate
cursor-applicability mechanism selected by the profile. It must reject old-parent siblings and
atomically commit the selected endpoint identity, including for `A -> A` transitions.

## 9.6 Per-effect settlement evidence

Every potential state-changing effect needs occurrence-preserving evidence bound to its exact
transaction and receipt. The applied effects MUST form one prefix of the candidate's ordered
effects.

A final-root set is unsafe because:

- equal roots can occur at several positions;
- an immediate entry can be skipped;
- a later companion transaction can consume or fail independently;
- two sibling candidates can advertise equal endpoints; and
- roots alone lose transaction, log, and receipt boundaries.

Followers MUST use the §4.5 classification, including the relevant skip and consumption events,
then replay the selected prefix. Historical behavior that collapsed roots into a set is not
conforming and can attribute the wrong transition.

Follower classification does not prevent an invalid settlement outcome. The activated
applied-prefix mechanism MUST stop the Ethereum operation from completing if the anchor or an
earlier effect does not apply but a later effect does. The mechanism must remain sound when state
roots at adjacent effect positions are equal. Without that enforcement, production activation is
blocked.

## 9.7 System-address risk

The selected EVM binding authorizes `EEZL2` system calls by `SYSTEM_ADDRESS`, but a network must
also prevent that authority from executing arbitrary code paths that can reenter `EEZL2`, replace
tables, or deliver several inbound calls in one transaction.

A production profile MUST select either:

- contract-enforced guards; or
- a node-enforced, non-reentrant system transaction mechanism whose validity is checked by every
  producer, validator, prover, and follower.

An ordinary shared EOA key is problematic: permissionless followers need deterministic
reconstruction data, while publishing the private key destroys authorization. The current public
development key resolves neither production requirement.

## 9.8 DA, relay, and recovery risk

Ethereum calldata gives post-inclusion availability but does not force timely publication. The
EEZ contract treats Rollup0 DA bytes as opaque, so validators and followers must enforce strict
RLP, complete transaction and ABI decoding, entry correspondence, reserved-sender rules, and
execution validity.

Separately signed Ethereum transactions are not atomic merely because a composer calls them a
bundle. Production needs a specified builder, contract, or protocol rule that enforces the
required consecutive ordering, one distinct trigger per inbound effect, failure behavior, and
applied-prefix safety.

Follower disagreement is detection, not prevention. A follower halts on invalid or ambiguous
canonical data. It cannot submit a fraud proof, undo an accepted EEZ transition, or guarantee a
trustless exit.

## 9.9 Production claim boundary

No production security claim is valid until every blocker in §8.2 is resolved and the resulting
profile validates against the EEZ profile schema. In particular, the current mock prover,
development genesis, public system key, historical binding submodule, and non-atomic submission
fallback MUST NOT be used to describe a production deployment.

---

*Next: [§10 Future Design](10-future-design.md).*
