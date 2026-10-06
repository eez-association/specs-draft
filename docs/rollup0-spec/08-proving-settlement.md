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

The active set can change. Let `M` be the number of accepted single-signer proof systems in the
Rollup0 manager when `postAndVerifyBatch` executes. Rollup0 requires:

```text
M >= 1
N = floor(2M / 3) + 1
```

This is an authorization threshold: it is the smallest integer strictly greater than two thirds
of `M`. It does not by itself promise BFT availability or fault tolerance. In particular, the
formula requires unanimity for `M = 1`, `M = 2`, and `M = 3`; it first permits one unavailable
member at `M = 4`, where `N = 3`. Operational availability therefore depends on the selected set
size and on its members being independently operated. Rollup0 defines no protocol-wide minimum
above `M >= 1`; the initial `M` is a launch parameter.

The threshold proof or signature set covers one complete candidate. The authenticated candidate
data commits the ordered action manifest and all deterministic terminal variants `B[0]` through
`B[s]`, where `s` is the candidate's successful-action count. Rollup0 does not require a separate
proof or signature set for each possible prefix.

The EEZ team Safe controls membership, signer rotation, verification keys, and the manager's stored
threshold. An update that changes `M` must also set `N` to the formula above in the same Ethereum
transaction. A replacement or key rotation must not temporarily count both the old and new signer
unless both are intended to be independent active members. The new configuration takes effect at
its position in canonical Ethereum transaction order. Settlement always uses the configuration
active when `postAndVerifyBatch` executes; candidate protocol V1 has no grace period or separately
encoded committee epoch. A pending candidate whose submitted proof-system subset, verification
keys, configured signers, or signature count is incompatible with the new configuration must be
re-signed under the new configuration and rebound to a still-current settlement context.

This can interrupt anchoring but cannot select an ambiguously authorized candidate. If a
configuration update executes before a candidate in the same Ethereum block, that candidate must
satisfy the new configuration or its settlement reverts and the Rollup0 cursor remains unchanged.
If the update executes after a successful candidate, the old configuration authorized that
candidate and the new configuration applies thereafter. Operators SHOULD have the new signer set
ready before activation. With a coordinated rotation, the candidate can normally be rebuilt for
the next Ethereum child slot; the protocol does not guarantee that the interruption is limited to
one anchor.

!!! warning "TRUST ASSUMPTION: validator configuration"
    The current Rollup manager stores membership and threshold separately. It permits a zero
    threshold, a threshold above `M`, and non-atomic updates through separate calls. It does not
    enforce the strict-two-thirds formula.

    Rollup0 trusts the EEZ team Safe to submit each configuration change atomically and preserve
    `M >= 1` and `N = floor(2M / 3) + 1`. A Safe transaction can group the existing manager calls,
    so no separate Ethereum transaction can execute between them. A future Rollup0 manager could
    enforce the formula directly.

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

Each configured signer MUST use a key dedicated to Rollup0 validator attestations. It MUST NOT use
that key for Ethereum transactions, personal-sign messages, EIP-712 applications, another proof
system, or another protocol's bare-hash signatures. The candidate domain prevents accidental
cross-network replay inside Rollup0, while key separation prevents an external signing interface
from being asked to sign an already-computed Rollup0 `publicInputsHash` under another pretext.

The opaque EEZ verification key returned by the Rollup0 manager is separate from the signer
address configured in the ECDSA proof-system contract. Clients MUST NOT substitute one for the
other.

The production Rollup0 manager supplies the candidate domain defined in Appendix D through
`getCustomData`. EEZ folds it into every applicable `publicInputsHash`. This binds a signature to
the Rollup0 protocol version, Ethereum chain, EEZ deployment, manager, active settlement wrapper,
EEZ rollup ID, Rollup0 chain ID, target Ethereum timestamp, and parent Ethereum block hash. A proof
created for another domain does not verify even when its entries and blob payload are otherwise
identical.

This is not an extra signature wrapper. Each ECDSA validator still signs the raw
`publicInputsHash`. The domain is already part of that hash.

## 8.2 Producer-Neutral Validation

When a validator/prover accepts a candidate for full validation, it:

1. authenticates the complete candidate and its referenced Ethereum and Rollup0 data;
2. independently executes it;
3. checks the EEZ batch, Rollup0 blocks, DA payload, pure-L2 prefix, every terminal variant
   `B[0]` through `B[s]`, and each corresponding `H[k]` and `R[k]`;
4. separately simulates every proposed prefix bundle supplied with the request and verifies that it
   realizes the claimed ordered prefix under the trigger-carrier rules;
5. signs or proves the candidate if and only if the candidate is valid and the supplied delivery
   request passes those checks; and
6. remains free to check other candidates for the same parent.

A request that proposes a nonzero synchronous prefix MUST provide the corresponding signed trigger
transactions for this simulation. This is a validation-service check on the proposed delivery plan,
not an additional object authenticated by the resulting signature. The trigger bytes and
transaction hashes are not part of candidate identity. A signature over the candidate therefore
remains valid if canonical Ethereum uses different carrier transactions that realize the same
ordered calls, subject to the on-chain carrier and prefix rules in Chapter 7.

This is a best-effort service. The list above defines the checks performed before signing; it does
not create an availability or response-time guarantee.

Signing two valid siblings is allowed. A signature states that a candidate is valid; it does not
state that the candidate is canonical.

## 8.3 Permissionless Submission

Any relayer MAY submit a candidate that carries the required proof or signatures through the active
Rollup0 settlement wrapper. The wrapper MUST NOT require the relayer to be the composer or a
validator/prover. A direct call to EEZ that includes Rollup0 is invalid because the manager has not
authorized it for the current transaction.

Changing any candidate field covered by the EEZ public-input hash invalidates the proof or
signatures. This includes the manager-generated domain and the selected blob versioned hashes.

Candidate protocol V1 uses Rollup0-only batches and MUST set `crossProofSystemInteractions` to
`bytes32(0)`. EEZ treats this field as an opaque value and includes it in the public-input hash, but
Rollup0 V1 defines no cross-proof-system interaction for it to identify. A nonzero value is invalid.

## 8.4 Settlement Rule

Process candidate settlements in canonical Ethereum transaction order.

A candidate is applicable only when:

- its exact named Rollup0 parent is the current settled cursor;
- its target timestamp and parent Ethereum block hash match the current settlement context;
- it was submitted through the active Rollup0 settlement wrapper under the signed candidate
  domain;
- its terminal Sync timestamp follows the live or catch-up rule in Chapter 4;
- its proof or signatures satisfy the Rollup0 proof policy;
- its EEZ batch is valid;
- its Rollup0 DA and range are valid; and
- its Ethereum execution produces the required settlement evidence.

The first applicable candidate advances the Rollup0 cursor to the exact block variant selected by
Ethereum execution. Let `k` be the number of successful Rollup0 actions consumed in order. The
cursor becomes the number, block hash `H[k]`, and EVM state root `R[k]` of `B[k]`. EEZ stores
`H[k]`; the number and `R[k]` come from the header authenticated by that hash. A caught terminal
failure creates no additional Rollup0 variant and need not be classified during Rollup0 derivation.
A catch-up candidate always advances to `B[0]`. Later candidates are evaluated against this updated
cursor.

A stale or invalid candidate does not advance the cursor. A reverted submission does not reserve a
position or prevent a later candidate from winning.

!!! success "DECISION: one Rollup0 settlement per Ethereum block"
    At most one EEZ batch that contains Rollup0 may execute in each Ethereum block, whether its
    candidate is a live or catch-up anchor. The Rollup0 manager enforces this with the persistent
    `lastSettlementBlock` gate defined in Appendix D. Direct submission to EEZ cannot bypass the
    manager's transaction-scoped settlement authorization.

    A first valid anchor changes the Rollup0 block-hash commitment, including when it has no user
    transaction. A later sibling therefore cannot apply its stale leading commitment transition. A
    chained second candidate is also invalid because validators may sign only from the
    Ethereum-confirmed cursor, not from the result of an earlier transaction in the same
    unconfirmed Ethereum block.

    Without this manager gate, a second proven EEZ batch for Rollup0 could execute in the same
    Ethereum block, emit `BatchPosted`, delete the first batch's unconsumed execution and lookup
    queues, and publish its own queues even when its leading anchor transition was skipped. The
    block-hash cursor alone prevents the stale state transition but does not prevent that queue
    replacement. Trusting a builder not to include the second batch is not acceptable.

A candidate is settled only when its Ethereum inclusion establishes `H[0]` for Rollup0. A successful
Rollup0 action is evidenced by its retained EEZ consumption and commitment update. A caught Rollup0
revert has no Rollup0 effect and is not settlement evidence. An L1 indexer may replay it to report
the inner failure, but Rollup0 derivation ignores it. The final settled endpoint is `B[k]`, not
necessarily the candidate's full intended variant.

Inclusion of the settlement transaction or an event carrying a matching block hash alone is
insufficient. A follower authenticates Ethereum receipts and filters their retained logs by EEZ
contract address and Rollup0 ID. Starting with the accepted `Hparent -> H[0]` transition, it
processes the successful EEZ consumption and commitment-update logs that follow in the same
Ethereum block, in transaction and log order, and matches them against the candidate's action
manifest. The candidate blobs define the possible Rollup0 actions and variants; the canonical logs
select the successful prefix that actually occurred. A Rollup0 follower does not re-execute the
outer Ethereum carrier transactions.

## 8.5 Safety Boundary

The permissioned validator/prover policy is the validity trust assumption. Independent derivation
detects a candidate that does not reproduce the published Rollup0 chain, but it cannot reverse
canonical Ethereum state. If the required threshold authorizes an invalid candidate, ordinary
followers independently execute it, detect the mismatch, and halt instead of accepting the
fabricated Rollup0 history. That detection does not protect Ethereum-side effects: the accepted
candidate can make EEZ return results that are not justified by valid Rollup0 execution, corrupt
dependent applications, and drain assets controlled through those applications. Threshold
compromise is therefore catastrophic even though it cannot silently fool a conforming follower.

The Rollup0 manager is trusted to supply the configured proof policy and to exercise any EEZ
manager powers assigned to it.

---

*Next: [Chapter 9, Ethereum to Rollup0 Flow](09-l1-to-l2.md).*
