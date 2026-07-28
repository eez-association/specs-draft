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

!!! note "TO BE DEFINED"
    The production values of `M`, `N`, the member keys, and the rotation procedure are not yet
    selected.

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

When a validator/prover accepts a candidate for full validation, it:

1. authenticates the complete candidate and its referenced Ethereum and Rollup0 data;
2. independently executes it;
3. checks the EEZ batch, Rollup0 blocks, DA payload, pure-L2 prefix, every synchronous prefix, and
   intended prefix bundles;
4. signs or proves it if and only if it is valid; and
5. remains free to check other candidates for the same parent.

This is a best-effort service. The list above defines the checks performed before signing; it does
not create an availability or response-time guarantee.

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

The first applicable candidate advances the Rollup0 cursor to the exact block variant selected by
Ethereum execution. If `k` synchronous actions were processed, the cursor becomes the number,
block hash, and state root of `B[k]`. Later candidates are evaluated against this updated cursor.

A stale or invalid candidate does not advance the cursor. A reverted submission does not reserve a
position or prevent a later candidate from winning.

!!! caution "TO BE DEFINED: one settlement per Ethereum block"
    Rollup0 permits at most one settled candidate for a Rollup0 Sync timestamp. The current EEZ
    contract stores the Rollup0 state root but not its block hash or number. It can accept a second
    same-rollup batch in one Ethereum block when the expected state root still matches, for example
    after an empty or reverting first candidate.

    Candidate proofs cannot resolve this after several valid siblings have already been signed.
    The team must decide how the settlement contract enforces the rule. The direct options are to
    reject a second Rollup0 batch in the same Ethereum block or to store and check the exact
    Rollup0 cursor.

A candidate is settled only when its Ethereum inclusion establishes `R0` for Rollup0. A successful
Rollup0 action is evidenced by its retained EEZ consumption and state update. A caught Rollup0
revert is evidenced by deterministic replay of the exact Ethereum trigger against the canonical L1
state. The final settled endpoint is `B[k]`, not necessarily the candidate's full intended variant.

Inclusion of the settlement transaction or a matching state-root event alone is insufficient. A
follower filters evidence by EEZ contract address and Rollup0 ID, preserves transaction and log
order, replays the trigger transactions, and verifies the processed action sequence.

## 8.5 Safety Boundary

The permissioned validator/prover policy is the validity trust assumption. Independent derivation
detects a candidate that does not reproduce the published Rollup0 chain, but it cannot reverse
canonical Ethereum state.

The Rollup0 manager is trusted to supply the configured proof policy and to exercise any EEZ
manager powers assigned to it.

---

*Next: [Chapter 9, Ethereum to Rollup0 Flow](09-l1-to-l2.md).*
