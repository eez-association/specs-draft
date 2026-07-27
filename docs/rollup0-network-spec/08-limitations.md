# 8. Limitations and Release Blockers

`rollup0@0.2-draft` defines intended protocol behavior. It is not a production activation record.
This chapter distinguishes design limitations, unresolved production choices, and known
implementation deviations.

## 8.1 Draft limitations

- **No force inclusion.** Anyone may produce a candidate, but the draft has no protocol that
  guarantees Ethereum inclusion.
- **Permissioned validity attestations.** Candidate production is open. The accepted prover or
  validator set and its threshold are selected by governance.
- **Sibling signatures are not consensus.** Validators may sign several valid candidates from the
  same parent. Canonical Ethereum transaction order selects the first still-applicable transition.
- **No trustless exit.** A correct follower can halt on an invalid or ambiguous history but cannot
  reverse EEZ settlement or force a withdrawal.
- **Flat cross-network calls.** The selected profile does not support nested or reentrant
  cross-network actions.
- **Calldata-only DA.** Tag `0x00` is the only selected channel. No blob codec or alternate DA
  fallback is defined.
- **Optimistic unsafe state.** Locally produced state can be replaced when canonical settlement
  selects a sibling or only a prefix applies.
- **No protocol fee reimbursement.** Candidate production, proofs, DA, and Ethereum submission can
  cost more than any application payment.
- **Manual exceptional recovery.** Finalized-settlement displacement or a reorganization beyond
  local history requires an authenticated operational decision.
- **Unresolved system mechanism.** A production authorization and value-supply design for L2
  system transactions has not been selected.

## 8.2 Production release blockers

Production activation MUST resolve and publish:

- the Rollup0 EIP-155 chain ID, EEZ rollup ID, native asset, genesis commitment, and fork schedule;
- the Ethereum activation block and the EEZ, manager, and proof-system deployments with bytecode
  commitments;
- the exact manager proof-context encoding and authentication rule;
- deterministic field-by-field lowering from each supported action to its L1 entry, L2 sidecar,
  explicit inbound arguments, and system transaction;
- accepted proof systems, verification keys, validator or prover identities, threshold, and key
  rotation;
- proof-routing protection for caller-controlled transient counts, replay, and front-running;
- an atomic or equivalently binding Ethereum submission construction;
- an enforceable exact-cursor mechanism that rejects stale siblings and advances the selected
  height, block hash, and root atomically even when roots repeat;
- an enforceable applied-prefix mechanism that remains sound for caught immediate failures and
  equal consecutive roots;
- the proof budget, submission slack, maximum candidate range, maximum bundle size, and capacity
  limits;
- the production system address, authorization rule, non-reentrancy enforcement, envelope, gas
  policy, reserve or value source, and backing rules;
- the production base fee and complete economic configuration;
- manager, upgrade, emergency, and recovery authorities; and
- an activation procedure that makes every selection unambiguous before the first production
  block.

The release-blocker IDs and machine-readable state are in
[`network-profile.json`](network-profile.json).

Production release also requires candidate-dissemination interfaces, proof-service availability,
and accepted conformance vectors for `A`, `Z`, every `R[k]`, and deterministic repaired Sync
headers at every proper effect prefix. These are software and test-artifact gates over fixed
rules, not unresolved profile values.

The corpus MUST also cover two siblings with one exact parent when the first selected endpoint has
the same state-root value as that parent. The second sibling must be rejected by cursor identity.

## 8.3 Binding and implementation status

The normative EVM binding is `eez-evm@0.2-draft`, with evidence from
`eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c`.

The current Rollup0 implementation evidence is
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`. Its checked-in
contract gitlink is `5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`, not the selected evidence. Until that dependency
is updated and all ABI, selector, tuple, hash, and state-machine tests pass, the implementation is
not evidence of `eez-evm@0.2-draft` conformance.

The client also has these known deviations:

- no authenticated production activation record;
- no producer-neutral candidate validation interface that enforces evaluation of every supported
  valid candidate;
- timeless `blockNumber = 0` batches with no authenticated Ethereum proof-context hash;
- incomplete canonical log ordering and transaction-hash authentication;
- collapsed per-block root sets instead of per-effect prefix evidence;
- no on-chain commitment to the settled Rollup0 cursor height and block hash, so a stale sibling
  can still pass the EEZ state-root check after an equal-root transition;
- no enforceable applied-prefix guard, allowing a later effect to apply after an earlier caught
  failure when the root preconditions happen to be equal;
- a rich-candidate anchor that ends at the pre-Sync parent root instead of zero-effect Sync root
  `Z`, causing the first effect delta to absorb mandatory Sync pre-execution changes;
- acceptance of domain-separated synthetic interior roots and value-based membership for generic
  interior-root provenance in the remote settlement gate; its exact indexed effect-prefix check
  does not remove that broader provenance gap;
- partial derivation that truncates effect entries but appends the omitted outbound users as a
  terminal tail instead of rebuilding exactly the selected effect-group prefix;
- permissive outer RLP and incomplete ABI or transaction consumption checks;
- incomplete `blobIndices`, sidecar correspondence, and tuple-version checks;
- collection of several inbound effects from one held Ethereum transaction while transporting that
  trigger only once;
- non-transactional multi-block replay;
- a transaction-only local fast path;
- unchecked or saturating timestamp and height arithmetic in scheduler, sequencer, and derivation
  paths where this profile requires checked arithmetic and failure on overflow;
- optional system-key and pure-user fallback behavior;
- incomplete reserved-sender enforcement;
- non-atomic public-mempool submission fallback;
- bounded unsafe ancestry forwarding; and
- automatic common-ancestor search limited to 62 settlement blocks by default.

The exact derivation deviations are listed in §6.8. These are defects relative to this draft, not
alternate network rules.

The composer at that revision emits an empty Sync body for anchor-only candidates. The protocol
also permits an anchor-only candidate to carry an effect-free user body; emitting only the empty
form is a supported subset, not a prohibition on the nonempty form.

## 8.4 Proof modes and production target

Current software exposes two materially different modes:

- **mock proof mode:** the default development path; it provides no production validity claim;
- **remote binding prover mode:** optional integration bound to the retired 0.1 ABI selected by the
  reviewed client; its endpoints, authentication, supported inputs, and operational failure
  behavior are not a production policy.

The required production mode is not implemented. It must use the selected `eez-evm@0.2-draft`
binding and the activated membership, verification keys, threshold, binding tests, and governance
listed above.

Documentation and clients MUST label these modes distinctly. A mock acceptance result MUST NOT be
presented as a proof.

---

*Next: [§9 Security and Trust Model](09-security-trust-model.md).*
