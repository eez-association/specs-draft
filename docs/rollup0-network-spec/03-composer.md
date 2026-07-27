# 3. Composer and Candidate Competition

The composer is an open Rollup0 function. It constructs a candidate Rollup0 range and the
corresponding Ethereum settlement bundle. It is not an authority role.

## 3.1 Inputs

For a candidate attempt, a composer uses one consistent snapshot of:

- the selected Rollup0 profile and activation;
- a canonical Ethereum anchor;
- the applicable Rollup0 parent and last settled cursor;
- ordered user transactions and cross-network intents;
- the exact `eez-evm@0.2-draft` binding;
- the validator/prover policy; and
- the intended Ethereum inclusion target and bundle.

A changed parent, cursor, anchor, activation, or deployment tuple makes the attempt stale.

## 3.2 Candidate Construction

A composer MUST:

1. Decode and validate every input transaction before simulation.
2. Simulate admitted interactions sequentially against the state left by preceding candidate
   elements.
3. Reject unsupported static, failed, nested, reentrant, or multi-call interactions.
4. Build the nonterminal blocks and one of the two terminal Sync forms in Appendix C.
5. Execute the complete L2 range and construct every header field under §2.
6. Compute the settled root, zero-effect Sync root, and every effect-prefix root under §3.3.
7. Build one anchor delta and, for a rich candidate, one additional `StateDelta` per effect.
8. Require the delta chain to end at the exact terminal Sync root.
9. Encode the complete positive DA range under §4.
10. Build the EEZ batch using the selected binding, recent Ethereum proof context, empty
    `blobIndices`, and the activated routing mitigation.
11. Obtain every proof required by the activated threshold.
12. Submit the exact intended Ethereum transaction bundle.

A rich candidate has one or more cross-network effects. Its terminal Sync body consists only of
the corresponding effect groups. It MUST NOT contain an unrelated user transaction before,
between, or after those groups. All claimed cross-network effects in the candidate range MUST
occur in those terminal groups.

An anchor-only candidate has no cross-network effect. Its terminal Sync body MAY contain ordered
ordinary user transactions that produce no claimed EEZ effect. Its sole Rollup0 delta starts at
the settled cursor root and ends at the final Sync root.

## 3.3 Exact Prefix Roots

Let:

- `A = header(cursor).stateRoot`, the root accepted before this candidate;
- `S_pre` be the state after executing all nonterminal blocks in the candidate range; and
- `root(B)` be the state root obtained by building the terminal Sync block on `S_pre` with its
  exact environment, applying all mandatory pre-execution changes, and executing transaction body
  `B`.

The zero-effect Sync prefix is:

```text
Z = root([])
```

`Z` includes the terminal Sync block's mandatory pre-execution state changes. It is not the
pre-Sync parent root `S_pre`.

For a rich candidate with ordered effects `E[0..m-1]`, let `G[k]` be the complete transaction
group for `E[k]`:

- an outbound group is `loadExecutionTable` followed immediately by its consuming user
  transaction; and
- an inbound group is one `executeIncomingCrossChainCall` system transaction.

The rich Sync body and effect-prefix roots are:

```text
body = G[0] || G[1] || ... || G[m-1]
R[k] = root(G[0] || G[1] || ... || G[k])
```

Each `root(...)` computation starts from the same pre-Sync parent `S_pre` and uses the same Sync
environment. A client MUST NOT build one prefix as a child block of another prefix.

The Rollup0 state-delta chain MUST be:

```text
anchor          = (rollupId, A,      Z,    0)
effect[0]       = (rollupId, Z,      R[0], etherDelta[0])
effect[k], k>0  = (rollupId, R[k-1], R[k], etherDelta[k])
```

The anchor covers every nonterminal block and the zero-effect Sync prefix. The final `R[m-1]`
MUST equal the rich candidate's Sync root. An intermediate effect MUST NOT jump directly to that
final root.

For an anchor-only candidate, let `U` be its complete ordered Sync user body and let
`F = root(U)`. Its only delta MUST be:

```text
anchor-only = (rollupId, A, F, 0)
```

When `U` is empty, `F = Z`. An anchor-only candidate does not expose separately settleable effect
prefixes.

Historical code assigned the final Sync root to every producing entry. In a mixed-value batch,
that can make an earlier Ethereum-side effect appear to commit state that includes a later
Rollup0-side effect. This enables unsafe value ordering and is invalid in version 0.2.

## 3.4 Validator/Prover Interface

A composer MAY send the same candidate to several validators and MAY send competing siblings.
Validators MUST decide from candidate content and activated policy, never composer identity.

A composer MUST NOT request or rely on:

- exclusive signing rights;
- first-seen locking;
- a validator promise not to sign siblings;
- a privileged poster address; or
- acceptance of a field that the validator did not authenticate.

The proof response MUST identify the candidate and proof-system public input that was evaluated.
The composer MUST reject a response for another candidate, profile, activation, or proof context.

## 3.5 Competition and Ethereum Ordering

Several composers can build from the same parent and can obtain valid proofs. A local composer MAY
serialize its own submissions, but that is not a network rule.

For canonical Ethereum transactions `T[0], T[1], ...`:

1. process candidates in transaction order;
2. apply a candidate only if its first Rollup0 state precondition matches the current registered
   state at that point;
3. update the state and queue according to the selected EEZ binding; and
4. treat a mismatching sibling as stale.

A follower applies the same order. It does not choose by producer, proof arrival time, highest fee,
largest range, or locally preferred candidate.

Two candidates in the same Ethereum block can both advance only when the later candidate starts
from the state produced by the earlier one. Same-parent siblings cannot both advance.

## 3.6 Publication and Observation

The composer MUST publish every byte required for independent validation and derivation. It MUST
authenticate canonical Ethereum receipts before treating its candidate as accepted.

Receipt success alone is insufficient. The composer MUST verify:

- the requested canonical Ethereum block and timestamp constraints;
- exact transaction hashes, indices, order, and receipt status;
- the selected EEZ emitter and event occurrences;
- exact immediate and deferred effect attribution; and
- the uniquely applicable Rollup0 endpoint.

Failure recovery is local. It cannot override a different candidate that canonical Ethereum
ordered first.

## 3.7 Non-Guarantees

Open composition does not guarantee inclusion. Validators can censor by refusing delivery or
proofs, builders can censor Ethereum transactions, and the proof threshold can halt. Rollup0 has
no force-inclusion inbox or trustless exit in this draft.

---

*Next: [§4 Data Availability, Batches, and Ethereum Bundles](04-da-batches-bundles.md).*
