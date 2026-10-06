# 1. Overview and Scope

Rollup0 uses EEZ to settle synchronous cross-network execution on Ethereum. The
[EEZ specification](../eez-protocol-spec/index.md) defines behavior shared by EEZ networks. This
specification defines the choices made by Rollup0.

## 1.1 Rollup0 Choices

Rollup0 selects:

- Ethereum as its settlement network;
- ETH as its native currency;
- a strict 2-second L2 block interval;
- six L2 block positions for every Ethereum slot, including a missed slot;
- open block production and candidate composition with no composer or sequencer allowlist;
- producer-signed unsafe-block announcements, without restricting which producer keys Rollup0
  accepts; and
- open syncing, relay, and RPC service for producer-signed unsafe blocks and canonically settled
  blocks;
- a permissioned validator set that operates on a best-effort basis;
- signing of valid sibling candidates without slashing or an equivocation penalty;
- canonical Ethereum transaction order as the candidate-selection rule;
- unsigned protocol-derived transactions for successful inbound actions;
- blob data availability; and
- standard execution-layer peer-to-peer block and state synchronization.

The fixed 2-second cadence continues when an Ethereum slot is missed. The corresponding six L2
positions still exist, but no synchronous transaction can settle in the missed Ethereum slot.

Every Rollup0 block can contain pure-L2 transactions. The block at the sixth position is a Sync
block, whether or not synchronous execution occurs. A Sync block places all pure-L2 transactions
before its zero or more successful synchronous actions. Each successful action is represented by
an unsigned transaction derived from its Ethereum trigger. A failed action is represented on
Ethereum by an EEZ failed lookup and adds no Rollup0 transaction.

Every anchor contains every L2 block after the previous settled endpoint through its new endpoint,
including empty blocks. A synchronous action can settle only as part of a live anchor; Rollup0
cannot compel a composer or Ethereum builder to provide that service. Composers SHOULD also
propose an anchor when 15 minutes have elapsed since the Ethereum inclusion of the latest anchor.

Rollup0 has two anchor forms:

- a **live anchor** ends at the Sync position whose timestamp equals the containing Ethereum
  block's timestamp. It can contain synchronous actions; and
- a **catch-up anchor** ends at an older Sync position. It contains only pure-L2 execution and
  lets Rollup0 publish a backlog over several Ethereum blocks.

Both forms extend the current settled cursor without skipping a Rollup0 block. A catch-up anchor
is submitted and signed for the current Ethereum slot even though its Rollup0 endpoint is older.
It cannot process a synchronous action. Synchronous service resumes when a live anchor reaches the
current Ethereum timestamp.

!!! success "DECISION: 15-minute anchor target"
    Fifteen minutes avoids forcing frequent Ethereum publications when Rollup0 has no synchronous
    work, while bounding the backlog during normal operation.

    This is an operational target, not a validity rule. Failure to publish or include an anchor
    within 15 minutes does not make a later valid anchor invalid. Chapter 7 defines historical
    catch-up when the target is missed for longer.

## 1.2 Sequencers, Composers, and L2 Views

The role distinction is:

- a **sequencer** builds, signs, and announces unsafe Rollup0 blocks;
- a **composer** constructs anchor candidates from blocks it builds or adopts; and
- a peer may sync, relay, or serve blocks over RPC without being their sequencer or composer.

One party can perform several roles. A sequencer can also compose and submit candidates, and a
composer can also sequence the blocks it proposes.

Neither role has an allowlist. A composer can adopt pure-L2 blocks received from any sequencer or
build them while also performing the sequencer role. Different sequencers can build different
valid L2 views, and peers can serve different views. A user can follow any peer's unsafe view,
knowing that it might never become canonical.

An anchor candidate extends the Rollup0 safe head whose block hash is currently stored by EEZ. The
candidate's first block must name that safe head as its parent and use the next block number. The
candidate contains the complete chain from that parent through its terminal Sync position.

Let `n` be the number of actions in a candidate's ordered action manifest and `s` its number of
successful actions. An optional failure must be terminal, so `s` is either `n` or `n - 1`. The
candidate defines terminal block variants `B[0]` through `B[s]`. Let `H[k]` be the block hash of
`B[k]` and `R[k]` its EVM state root. `B[k]` contains the fixed pure-L2 prefix followed by its first
`k` successful protocol transactions. A failed action adds no Rollup0 transaction or block variant.
The Ethereum outcome selects one of these variants as the candidate's exact endpoint.

Validators and followers check the parent block hash and number from the published block data. The
proof system must enforce the same rule before accepting the candidate. For Rollup0, the value in
EEZ's `stateRoot` storage field is this parent block hash. The contract does not store the Rollup0
block number separately.

!!! success "DECISION: derive the parent from the first block"
    The blob does not contain a separate parent record. The candidate's first block header carries
    `parentHash`, and its block number identifies the preceding number. Validators and followers
    compare the hash with EEZ's stored Rollup0 commitment and the number with the locally recovered
    settled cursor.

    A separate parent record would duplicate the same values and create another equality check
    without adding security. The proof system still checks the exact parent hash and number.

A candidate is applicable when it:

1. extends the current Ethereum-confirmed Rollup0 safe head;
2. follows the EEZ and Rollup0 rules;
3. has the required validator signatures; and
4. can establish `H[0]` and `R[0]` and defines every possible synchronous prefix correctly.

The first applicable candidate in canonical Ethereum transaction order advances Rollup0. Ethereum
block builders therefore control the ordering between valid candidates. This is intentional.
Sibling candidates for the old parent then become stale.

!!! success "DECISION: validator transport is not part of consensus"
    Rollup0 defines the complete candidate, the checks that validators perform, and the signature
    accepted by the settlement contract. It does not require a particular transport between a
    composer and a validator.

    The current reference implementation uses its existing `prove.v1` gRPC stream as a starting
    point. Its production successor needs a new API version because it carries a materially
    different candidate. Another implementation may use a different private RPC or perform
    validation locally. When the validation request includes proposed signed Ethereum trigger
    transactions, its transport must provide confidentiality, integrity, and validator-endpoint
    authentication.
    Framing, errors, retries, admission controls, and multi-validator coordination are
    implementation choices.

## 1.3 Validation

Validators provide a best-effort service. They can reject malformed or oversized messages before
full validation. They can rate limit or ban parties that waste resources.

After fully checking a candidate, a validator signs it when it is valid. A validator can sign
several valid siblings and can finish signing a candidate after another sibling arrives. This is
not equivocation and carries no slashing risk.

Each signature is bound to the fixed Rollup0 candidate domain defined in Appendix D and to one
intended Ethereum settlement context: the target child-slot timestamp and the known parent
Ethereum block hash. The domain identifies the protocol, both chain IDs, the EEZ deployment,
manager, and EEZ rollup ID. The future child block hash is not known when validators sign.

The first applicable candidate that lands in that context wins. The context always names the
current Ethereum slot; it is separate from the Rollup0 endpoint timestamp of a catch-up anchor. A
missed target or changed parent requires a new candidate and new signatures. Signatures for
candidates that still name an old Rollup0 parent can no longer advance Rollup0.

Rollup0 has no force-inclusion path. A valid empty candidate can win while excluding pending
transactions. Force inclusion and TEE-backed validators are possible features for Rollup0.x, not
this version.

## 1.4 Cross-Network Scope

Each proposed trigger transaction makes exactly one top-level cross-chain call into Rollup0. A
candidate can contain several proposed triggers. Under ordered-call identity, a different carrier
transaction may replace one of them, but the production L1 EEZ guard permits that transaction to
consume at most one successful Rollup0 action.

For synchronous transactions, the composer submits this ordered Ethereum bundle through
`eth_sendBundle`:

```text
[submitCandidate, trigger1, trigger2, ...]
```

`submitCandidate` calls the permissionless Rollup0 settlement wrapper. The wrapper enforces the
initial batch policy and calls EEZ to publish and verify the possible results of all Rollup0 calls
before the trigger transactions execute. Each following trigger transaction can then call its
proxy and receive its precomputed result.

The composer proposes bundles containing `submitCandidate` and a strict prefix of its ordered
trigger transactions in one Ethereum block. Every accepted outer trigger transaction must succeed
and execute the next expected proxy call; ordered-call identity also permits a different
transaction carrying the same call. Chapter 7 discusses how the composer can submit the proposed
prefix choices through atomic bundles. If an included trigger catches a Rollup0 failure, it must be
the final transaction in that candidate's reached trigger prefix.

`eth_sendBundle` requests this ordering from a builder. It is a delivery mechanism, not the rule
that makes the ordering valid.

!!! success "DECISION: ordered-call prefix enforcement"
    For triggers `A`, `B`, and `C`, the composer may authorize only these bundle shapes:

    ```text
    [submitCandidate]
    [submitCandidate, A]
    [submitCandidate, A, B]
    [submitCandidate, A, B, C]
    ```

    Ethereum does not verify that a builder used one of those submitted bundles unchanged. Rollup0
    therefore identifies an action by its authenticated manifest position and EEZ call hash, not by
    the exact signed transaction proposed for delivery. The successful EEZ queue accepts only the
    next matching call and advances only when its outer transaction succeeds. A different outer
    transaction that produces that next call is intentionally the same Rollup0 action.

    A caught failure can occur only as the final manifest action and creates no Rollup0 transition.
    The production manager and wrapper enforce the leading anchor and permit only one candidate
    activation per Ethereum block. Chapter 7 defines the complete ordered-call rule. It cannot stop
    Ethereum from applying the ordinary L1 effects of a leaked or substituted transaction.

Let `R[0]` be the EVM state root after the fixed pure-L2 prefix and before any synchronous action.
Let `H[k]` and `R[k]` be the block hash and state root after `k` successful synchronous actions. A
caught terminal failure creates no Rollup0 transaction or additional variant, so the L2 endpoint
remains `B[k]` and a Rollup0 follower need not establish whether that failure occurred on L1.

The wrapper's internal `postAndVerifyBatch` call establishes `H[0]` in EEZ. The canonical endpoint
is `B[k]`, where `k` is the number of successful Rollup0 actions, and EEZ ends with `H[k]`. A trigger
outside the reached prefix does not remove the pure-L2 transactions or earlier successful actions.
Chapter 7 defines this processing, including identical ordered calls.

This is the synchronous property: each trigger transaction receives the Rollup0 result while it
executes, after the result has been prepared earlier in the same Ethereum block.

The call returns arbitrary bytes. A revert is also a result and includes its revert data. The
Ethereum transaction can make ordinary local calls and reads before and after its cross-chain call.
The Rollup0 target can make ordinary local Rollup0 calls and reads.

Cross-chain reads, including cross-chain `STATICCALL`, are not part of the initial Rollup0 rules.
Rollup0.x may enable them as part of full nested composability in both directions.

Synchronous calls originating on Rollup0 and direct calls between execution networks are outside
this version. A candidate can contain ordinary Rollup0 transactions without any cross-chain call.

## 1.5 Data and Reconstruction

Rollup0 publishes anchored chain data in Ethereum blobs.

!!! danger "PRODUCTION BLOCKER: blob format"
    Appendix G records the selected V0 encoding, versioning, and natural-capacity rules. The
    normative linear codec is consolidated in Appendix D. The complete action-manifest,
    transaction-bearing, and derivation conformance suite remains unfinished; a client cannot claim
    production interoperability until those vectors are complete.

A follower can reconstruct recent anchors directly while their blobs remain available. Rollup0
does not require peers to archive or serve expired blob sidecars.

!!! success "DECISION: standard block and state synchronization"
    A late follower uses the standard Ethereum execution-layer peer-to-peer protocols supported by
    Rollup0 clients. It downloads headers and bodies through the `eth` protocol and may obtain state
    through `snap`. The block hash stored by EEZ identifies the exact settled header. The header's
    state root authenticates the complete downloaded execution state, including accounts, storage,
    and contract bytecode through each account's code hash.

    Peers need to retain only normal block, receipt, and state data according to their pruning
    mode. They do not need to retain historical Rollup0 blobs. A follower treats peer data as
    untrusted. Snap sync authenticates the checkpoint state but does not replay execution before
    that checkpoint. A follower verifies earlier header ancestry and header commitments, then
    executes every block it follows after the checkpoint. A full-sync follower can instead replay
    the complete history.

## 1.6 Conventions

The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY mark protocol requirements.

Terms defined by EEZ keep their EEZ meaning. Rollup0 terms are listed in
[Appendix A](A-reference.md).

Status labels have these meanings:

- **Decision:** selected behavior and its rationale;
- **Production blocker:** unresolved work required for a safe, interoperable launch;
- **Open interoperability:** an unresolved network or API interface;
- **Genesis parameter:** an exact value fixed in the final genesis specification;
- **Trust assumption:** accepted behavior that is not enforced cryptographically; and
- **Future design:** work for a later Rollup0 version that does not block initial Rollup0.

Other admonition titles, such as **Deployment policy**, **Finality failure**, or **Legacy
terminology**, are explanatory topic headings. They do not introduce additional status categories.

---

*Next: [Chapter 2, Architecture](02-architecture.md).*
