# 8. Proving and Settlement

## 8.1 Proof Policy

Rollup0 uses a permissioned set of `M` ECDSA provers over openly produced candidates. A candidate
needs signatures from at least `N` members.

Each prover is represented by a separate deployed `ECDSAProofSystem` instance configured with that
prover as its sole `authorizedSigner`. For proof-system slot `k`, the prover signs
`publicInputsHash[k]`, and its 65-byte signature occupies the parallel `proofs[k]` slot. The Rollup0
manager selects the accepted proof-system instances, verification keys, and threshold. The
[EEZ proving specification](../eez-protocol-spec/04-proving-and-settlement.md) defines the proof
interface and digest. [EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines the
encoding and proof-system fold.

The threshold set of prover signatures covers one complete candidate. The authenticated candidate
data commits the ordered trigger manifest and all deterministic terminal variants `B[0]` through
`B[n]`. Rollup0 does not require a separate set of prover signatures for each possible prefix.

!!! note "TO BE DEFINED"
    The production values of `M`, `N`, the member keys, and the rotation procedure are not yet
    selected.

Rollup0 realizes `N`-of-`M` using `M` independently configured instances of the single-signer
`ECDSAProofSystem`, one per prover. A candidate supplies signatures for at least `N` accepted
instances. The Rollup0 manager rejects a submitted subset with fewer than `N` accepted instances.
The proof-system list and each Rollup0 proof-system index list are strictly increasing, so one
instance cannot count twice.

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

When a prover accepts a candidate for full validation, it:

1. authenticates the complete candidate and its referenced Ethereum and Rollup0 data;
2. independently executes it;
3. checks the EEZ batch, Rollup0 blocks, DA payload, pure-L2 prefix, every terminal variant
   `B[0]` through `B[n]`, and the intended prefix bundles;
4. signs it if and only if it is valid; and
5. remains free to check other candidates for the same parent.

This is a best-effort service. The list above defines the checks performed before signing; it does
not create an availability or response-time guarantee.

Signing two valid siblings is allowed. A signature states that a candidate is valid; it does not
state that the candidate is canonical.

## 8.3 Permissionless Submission

Any relayer MAY submit a candidate that carries the required prover signatures. The settlement
contract MUST NOT require the relayer to be the composer or a prover.

Changing any candidate field covered by the EEZ public-input hash invalidates the prover signatures.
Appendix C tracks the domain binding of fields outside that hash.

## 8.4 Settlement Rule

Process candidate settlements in canonical Ethereum transaction order.

A candidate is applicable only when:

- its exact named Rollup0 parent is the current settled cursor;
- its target timestamp and parent Ethereum block hash match the current settlement context;
- its terminal Sync timestamp follows the live or catch-up rule in Chapter 4;
- its prover signatures satisfy the Rollup0 proof policy;
- its EEZ batch is valid;
- its Rollup0 DA and range are valid; and
- its Ethereum execution produces the required settlement evidence.

The first applicable candidate advances the Rollup0 cursor to the exact block variant selected by
Ethereum execution. If `k` synchronous actions were processed, the cursor becomes the number,
block hash, and state root of `B[k]`. If action `k` was a caught Rollup0 failure, it must also be
the candidate's final action `n`. A shorter selected prefix with `k < n` contains only successful
Rollup0 actions. A catch-up candidate always advances to `B[0]`. Later candidates are evaluated
against this updated cursor.

A stale or invalid candidate does not advance the cursor. A reverted submission does not reserve a
position or prevent a later candidate from winning.

!!! caution "TO BE DEFINED: one Rollup0 batch per Ethereum block"
    At most one EEZ batch that contains Rollup0 may execute in each Ethereum block, whether its
    candidate is a live or catch-up anchor. The current EEZ contract does not enforce this rule.

    A first valid anchor changes the Rollup0 state root, including when it has no user
    transaction. A later sibling therefore cannot apply its stale leading state transition. A
    chained second candidate is also invalid because provers may sign only from the
    Ethereum-confirmed cursor, not from the result of an earlier transaction in the same
    unconfirmed Ethereum block.

    The remaining problem is queue replacement. A second proven EEZ batch for Rollup0 can still
    execute in the same Ethereum block, emit `BatchPosted`, delete the first batch's unconsumed
    execution and lookup queues, and publish its own queues even when its leading anchor
    transition was skipped. Later trigger transactions can then see different prepared actions.

    The team must either enforce the stronger one-batch rule in a settlement path that cannot be
    bypassed, enforce equivalent queue integrity, or accept compatible builder behavior as an
    explicit trust assumption. Storing and checking an exact Rollup0 cursor is another design only
    if the settlement layer can be changed.

A candidate is settled only when its Ethereum inclusion establishes `R0` for Rollup0. A successful
Rollup0 action is evidenced by its retained EEZ consumption and state update. A caught Rollup0
revert is evidenced by deterministic replay of the exact Ethereum trigger against the canonical L1
state, and it can advance the action prefix only as the candidate's final action. The final settled
endpoint is `B[k]`, not necessarily the candidate's full intended variant.

Inclusion of the settlement transaction or a matching state-root event alone is insufficient. A
follower filters evidence by EEZ contract address and Rollup0 ID, preserves transaction and log
order, replays the trigger transactions, and verifies the processed action sequence.

## 8.5 Safety Boundary

The permissioned prover policy is the validity trust assumption. Independent derivation
detects a candidate that does not reproduce the published Rollup0 chain, but it cannot reverse
canonical Ethereum state.

The Rollup0 manager is trusted to supply the configured proof policy and to exercise any EEZ
manager powers assigned to it.

---

*Next: [Chapter 9, Ethereum to Rollup0 Flow](09-l1-to-l2.md).*
