# 8. Proving and Settlement

## 8.1 Proof Policy

Rollup0 uses a permissioned set of `M` validators/provers over openly produced candidates. A
candidate needs attestations from at least `N` members.

Each member is represented by an independent single-signer ECDSA proof system in the EEZ batch.
Each signs the EEZ public-input hash for that proof-system slot. The Rollup0 manager selects the
accepted proof systems, verification keys, and threshold. The
[EEZ proving specification](../eez-protocol-spec/04-proving-and-settlement.md) defines the proof
interface and digest. [EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines the
encoding and proof-system fold.

The production values of `M`, `N`, the member keys, and the rotation procedure are not yet fixed.

Rollup0 realizes `N`-of-`M` as `N` distinct accepted single-signer proof systems, not as one proof
system containing `N` signatures. The Rollup0 manager rejects a submitted subset with fewer than
`N` accepted proof systems. The proof-system list and each Rollup0 proof-system index list are
strictly increasing, so one verifier cannot count twice.

For each ECDSA proof system:

- the proof is exactly 65 bytes, `r || s || v`;
- `r` and `s` are 32-byte values and `v` is one byte;
- `s` MUST be in the low half of the curve order;
- `v` MUST be `27` or `28`;
- the signed message is the raw EEZ `publicInputsHash`, with no EIP-191 prefix and no EIP-712
  domain; and
- the recovered address MUST equal that proof system's configured signer.

The opaque EEZ verification key returned by the Rollup0 manager is separate from the signer
address configured in the ECDSA proof-system contract. Clients MUST NOT substitute one for the
other.

## 8.2 Producer-Neutral Validation

Each validator/prover MUST:

1. authenticate the complete candidate and its referenced Ethereum and Rollup0 data;
2. independently execute it;
3. check the EEZ batch, Rollup0 blocks, DA payload, Sync transaction, and intended bundle;
4. sign or prove it if and only if it is valid; and
5. continue checking other candidates for the same parent.

Signing two valid siblings is allowed. A signature states that a candidate is valid; it does not
state that the candidate is canonical.

## 8.3 Permissionless Submission

Any relayer MAY submit a candidate that carries the required proof or signatures. The settlement
contract MUST NOT require the relayer to be the composer or a validator/prover.

Changing any candidate field covered by the EEZ public-input hash invalidates the proof or
signatures. Appendix C tracks the domain binding of fields outside that hash.

## 8.4 Settlement Rule

Process candidate settlements in canonical Ethereum transaction order.

A candidate is applicable only when:

- its exact named Rollup0 parent is the current settled cursor;
- its proof or signatures satisfy the Rollup0 proof policy;
- its EEZ batch is valid;
- its Rollup0 DA and range are valid; and
- its Ethereum execution produces the required settlement evidence.

The first applicable candidate advances the Rollup0 cursor to the endpoint established by that
evidence. Later candidates are evaluated against the updated cursor.

A stale or invalid candidate does not advance the cursor. A reverted submission does not reserve a
position or prevent a later candidate from winning.

A candidate is settled only when its Ethereum inclusion emits
`L2ExecutionPerformed(rollupId, newState)` for Rollup0 and `newState` equals the state root of the
candidate's Sync block. Inclusion of the settlement transaction alone is insufficient. A follower
filters evidence by EEZ contract address and Rollup0 ID.

## 8.5 Safety Boundary

The permissioned validator/prover policy is the validity trust assumption. Independent derivation
detects a candidate that does not reproduce the published Rollup0 chain, but it cannot reverse
canonical Ethereum state.

The Rollup0 manager is trusted to supply the configured proof policy and to exercise any EEZ
manager powers assigned to it.

---

*Next: [Chapter 9, Ethereum to Rollup0 Flow](09-l1-to-l2.md).*
