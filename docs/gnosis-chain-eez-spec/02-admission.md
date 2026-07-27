# 2. Candidate Admission and Canonical Selection

## 2.1 Actors

- A **composer** constructs a candidate from a settled Gnosis parent.
- An **authorized signer** authorizes one exact candidate. A composer and signer may be the same
  operator, but the protocol does not assume that they are.
- A **validator** independently checks every Gnosis validity rule.
- A **prover** produces the proof required by the selected proof policy.
- The **Gnosis authorization proof contract** checks the active
  sequencer/composer signature.
- The **Ethereum settlement path** verifies full validity and Gnosis
  authorization. The exact contract composition is profile data.
- A **relayer** submits an authorized, proven batch. Relayers are permissionless.
- A **follower** derives the canonical Gnosis chain from canonical settlement data.

Authorization applies to candidates. It does not grant a relayer exclusive submission rights and
MUST NOT depend on the relayer being the composer or signer.

## 2.2 Candidate

A Gnosis candidate MUST identify, directly or through cryptographic commitments:

- the Gnosis protocol and profile versions;
- the activation epoch;
- the Gnosis chain ID and rollup ID;
- the Ethereum settlement domain and selected contract deployments;
- the exact settled parent block hash, number, and state root;
- the complete ordered proposed Gnosis block range and terminal state root;
- the complete DA commitment and the exact `eez-evm@0.2-draft` batch;
- every proof-routing field and transient prefix count;
- the proof policy and proof-contract domain; and
- any expiry, sequence, or authorization-set identifier required by the activated signature
  scheme.

The activated signature digest MUST commit to a canonical encoding of all fields whose alteration
could change execution, settlement attribution, proof routing, data availability, replay, or
canonical selection. It MUST domain-separate production from development and MUST prevent reuse
across chain IDs, rollup IDs, profiles, activation epochs, settlement contracts, proof contracts,
and parent states.

The exact envelope, canonical encoding, hash, signature algorithm, accepted signature form,
low-`s` rule where relevant, replay domain, expiry/nonce rule, and test vectors are unresolved
release blockers. Until they are fixed, no candidate is production conforming.

## 2.3 Admission Predicate

At settlement position `p`, define:

```text
Admissible(candidate, p) =
    FullyValid(candidate, p)
    AND Authorized(candidate, p)

SettlementReady(candidate, p) =
    Admissible(candidate, p)
    AND PROOF_POLICY(candidate, p)

Selectable(candidate, p) =
    Applicable(candidate, p)
    AND SettlementReady(candidate, p)
```

`Applicable` means that the candidate selects the active profile and its exact parent height, block
hash, and state root equal the Gnosis cursor settled immediately before `p`. It also satisfies the
activated range, version, and replay conditions. Equal state roots do not make different parent
blocks interchangeable.

`FullyValid` means that independent re-execution and every EEZ, EVM, header, DA, batch, proof, value,
and derivation rule succeeds. This is the same complete validity predicate required by the imported
shared execution rules. An authorization signature does not waive, replace, or weaken any validity
check.

`Authorized` means that the Ethereum proof contract verifies the activated candidate signature and
that its signer belongs to the authorization set active immediately before `p`.

In the imported notation, `ADMIT(candidate, p) = Authorized(candidate, p)` and
`CommonValid(candidate, p) = FullyValid(candidate, p)`. Applicability is checked separately by
the activated cursor guard against the exact identity settled immediately before `p`. The
authorization proof contract and Ethereum settlement path MUST bind to this same comparison.

An authorized invalid candidate MUST be rejected. A valid but unauthorized candidate MUST be
rejected. A proof that establishes validity but omits authorization MUST be rejected.

## 2.4 Proof and Submission

The selected Ethereum settlement path MUST verify both the full validity
statement and `Authorized`. The Gnosis authorization proof contract MUST check
the activated signature. It MAY be the validity verifier or a separate
contract, as fixed by the production profile. The authorization result MUST be
bound to the same candidate and batch accepted by the EEZ settlement call. A
caller MUST NOT be able to combine a validity proof for one candidate with an
authorization signature, DA payload, transient count, or settlement call for
another.

Any Ethereum account or contract may relay the exact authorized, proven batch. The relayer's
`msg.sender` is not the candidate signer and is not an admission authority. A conforming deployment
MUST NOT reject an otherwise admissible candidate solely because an unlisted relayer submits it.

The exact proof-contract address, runtime-code hash, verification key, public-input layout,
authorization check, and EEZ call path are unresolved release blockers.

## 2.5 Competing Candidates

Several authorized signers may authorize different fully valid candidates for the same settled
parent. Authorization does not itself choose among them.

Process candidate applications in canonical Ethereum execution order. A candidate wins when it is
the first candidate in that order for which `Selectable(candidate, p)` is true and whose anchor
applies. Its exact selected endpoint under
[common §5.3](../rollup0-network-spec/common-execution.md#53-canonical-evidence-and-competition)
and [common §6](../rollup0-network-spec/common-execution.md#6-derivation) becomes the settled parent
for the next application. That endpoint can be `Z`, an effect-prefix root `R[q-1]`, the full rich
Sync root, or anchor-only root `F`. Any later candidate that names the old parent is stale and not
applicable, even if it remains valid and correctly signed or has the same parent-root value as the
new cursor.

Canonical execution order is the order in which the activated Ethereum settlement contract applies
calls in canonical blocks. The activation record MUST pin the contract entry point and event
evidence that followers use to identify each successful application. Mempool arrival, signature
time, proof time, relay receipt time, peer count, and candidate hash do not select the winner.

Before Ethereum finality, a reorg can replace the winner. Followers MUST rewind applications removed
from the canonical branch and process the replacement branch in canonical execution order.

## 2.6 Authorization Set and Rotation

The authorization set is independent of validator, prover, relayer, and governance membership
unless an activation record explicitly makes two sets equal.

A production activation MUST specify:

- the initial authorized signer keys or the contract/state root that defines them;
- the threshold, if one candidate needs more than one signature;
- how the proof contract obtains the set active at settlement position `p`;
- addition, removal, compromise, suspension, and emergency procedures;
- notice and activation delays;
- the exact boundary at which a rotation becomes active;
- behavior for signatures created before but submitted after a rotation; and
- historical verification and reorg behavior across the boundary.

Rotation MUST NOT be retroactive and MUST be deterministic from canonical Ethereum state. The exact
authorized set and rotation mechanism are unresolved release blockers.

---

*Next: [§3 Security and Trust Model](03-security-trust-model.md).*
