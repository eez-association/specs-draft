# 15. Related Work

> [!WARNING]
> **Superseded as of 2026-08-25.** This comparison describes an earlier Gnosis-settled, centralized
> Rollup0 design with different DA, transaction, fee, and role choices. It is not current project
> documentation and many internal links target retired chapters. Use the
> [current Rollup0 specification](../docs/rollup0-spec/index.md) for protocol claims.

This chapter situates Rollup0 — and its successor Rollup1 ([§16](16-rollup1-roadmap.md)) —
within the contemporary rollup landscape. It states plainly where Rollup0 is *ahead* of deployed
systems (its synchronous, single-L1-block atomic composability is more ambitious than any
production leader), *behind* them (its committee attestation is a weaker settlement guarantee
than either fraud proofs or validity proofs), and where it *matches* the state of the art
(its centralized-sequencer and blob-default DA postures match Arbitrum Nitro today). It is
organized around four axes (§15.1), applied system-by-system, closing (§15.9) with a summary table.

External claims are cited inline to primary sources. Where a system's published design and its
*deployed* status diverge — a recurring theme, since several relevant mechanisms (synchronous
composability, shared sequencing, permissionless preconfirmations) are roadmap items rather than
mainnet realities — the gap is flagged explicitly: Rollup0's honest peer set is "published
designs," not "shipped products."

## 15.1 The four comparison axes

A rollup's architecture decomposes along four largely independent axes. Treating
them separately makes a fair comparison possible: two systems can share a
sequencing model while differing entirely in how they prove state, and the marketing
category ("optimistic," "ZK," "based") usually fixes only one axis.

**(a) Sequencing model — who orders L2 transactions.** The spectrum runs from a *single
centralized sequencer* (one operator orders and produces blocks), through *based*
(L1-sequenced) designs (the L1 proposer schedule drives ordering, so the rollup inherits
L1 liveness), to *shared / decentralized sequencer networks* (an external BFT validator set
orders transactions for many rollups at once). Rollup0 sits firmly at the centralized end:
a single operator runs the composer and produces every L2 block ([§1.3.1](01-introduction.md),
[§7](07-composer.md)). Rollup1 moves to the based end ([§16](16-rollup1-roadmap.md)).

**(b) Data availability — where the data to reconstruct L2 state is published.** The
choices are *L1 calldata*, *EIP-4844 blobs*, or an *external DA layer* (Celestia, EigenDA,
Avail). Post-Cancun, the live question for an L1-DA rollup is calldata-versus-blob
*selection*, since the two are priced in independent fee markets ([§2.3](02-background.md)).
Rollup0 publishes everything to its L1 (Gnosis Chain), blobs by default and calldata when
cheaper ([§8](08-da-and-bundles.md)); it does not target an external DA layer
([§1.3.1](01-introduction.md)).

**(c) Proving / settlement — how L1 is convinced the posted state root is correct.** The
three established models are *optimistic fraud proofs* (post the root unproven, allow a
challenge window), *validity (ZK) proofs* (post a SNARK/STARK that L1 verifies
immediately), and *permissioned committee / multisig attestation* (a trusted set
re-executes and signs). Rollup0 occupies the third, weakest category — an ECDSA *N*-of-*M*
validator-set attestation, backstopped by full re-derivation
([§2.1](02-background.md), [§9](09-proving-settlement.md)). Rollup1 replaces it with a ZK
validity proof.

**(d) Cross-chain / cross-rollup atomic composability — whether two chains can commit
a single interaction all-or-nothing.** Rollup0 is most distinctive here. The deployed norm is
*asynchronous message passing*: a message emitted on one chain is consumed by a *separate, later*
transaction on the other, and the initiating call cannot use the remote result
([§2.5](02-background.md)). Rollup0 instead provides *synchronous* composability: an L1↔L2
interaction commits atomically within a *single L1 block*, with the remote return value available
to local control flow because it was precomputed and proven before settlement
([§1.2](01-introduction.md)). The only published design targeting the same guarantee class is
Taiko's Gwyneth (§15.3).

These axes are not fully orthogonal — synchronous composability (d) is far easier under based
sequencing (a), which is why Rollup1 couples them — but holding them apart is the right lens for
the survey that follows.

## 15.2 Based rollups and preconfirmations

A **based** (or *L1-sequenced*) rollup is one "whose sequencing is driven by the base L1":
the next L1 proposer can permissionlessly include the next rollup block as part of the next
L1 block, so the rollup has no separate sequencer *layer* and inherits L1 liveness and
censorship resistance directly. This is the canonical definition from Justin Drake's
Ethereum Foundation research
([ethresear.ch — based rollups](https://ethresear.ch/t/based-rollups-superpowers-from-l1-sequencing/15016)).
Ordering still happens as a *function*, but no longer in a privileged off-protocol role.
The headline benefit: a based rollup is exactly as live and censorship-resistant as Ethereum
itself — no sequencer to bribe, halt, or capture.

The headline *cost* is latency. With naive based sequencing, a transaction is only ordered when
the next cooperating L1 proposer builds a block — on the order of L1 block time (~12 s Ethereum,
~5 s Gnosis Chain), too slow for interactive UX. The mitigation is **based preconfirmations**:
L1 proposers opt in as *preconfers* by accepting additional slashing conditions and, in exchange
for *preconf tips*, issue signed promises that a transaction will be included and ordered a
certain way
([ethresear.ch — based preconfirmations](https://ethresear.ch/t/based-preconfirmations/17353/16)).
A preconfer binds itself with **two slashing conditions** — a *liveness* fault (failing to
include a transaction it promised) and a *safety* fault (including it contrary to the promise) —
so a signed preconf is a credibly-backed commitment a user can act on immediately, before the L1
block lands. Preconfirmations thus give sub-second perceived inclusion while preserving
L1-derived settlement security.

This is Rollup1's sequencing model. Rollup0 makes the opposite bootstrap choice — a single
trusted operator with no preconfirmation machinery — accepting the corresponding liveness
weakness (operator-dependent, no escape hatch; [§1.3.1](01-introduction.md),
[§14](14-security-threat-model.md)) for a simpler, shippable system. The based design retires
that weakness, and the proof and settlement interfaces are already shaped so the sequencing role
can be lifted out and handed to L1 proposers without redesign ([§16](16-rollup1-roadmap.md)).

## 15.3 Taiko and Gwyneth

**Taiko** is the leading production based rollup and the most direct architectural relative
of *Rollup1*. Its execution layer is a **Type-1 zkEVM** — "the highest level of Ethereum
compatibility possible," i.e. bytecode-level, Ethereum-equivalent — and its sequencing model
is based by design: "A based rollup is a Layer 2 designed to use Ethereum L1 validators for
transaction sequencing instead of a centralized sequencer"
([taiko.xyz](https://taiko.xyz/guides/what-is-taiko-blockchain)). Based sequencing in
Taiko's framing "unites L1 and L2 proposers" into a single scheduling framework, and the
project layers based preconfirmations on top to deliver sub-second inclusion feedback while
keeping full L1 settlement security
([taiko.mirror.xyz](https://taiko.mirror.xyz/ejciROGOGM9L_DuuqM3KloZan0EQR73fJt8qzTZmVzg)).

Crucially for an honest comparison, Taiko's based sequencing is **not yet fully
permissionless**. As of the cited documentation it relies on *three whitelisted
preconfirmation operators* (Nethermind, Chainbound, Gattaca) for block building, explicitly
framed as a stepping stone toward fully permissionless L1-validator sequencing "when fully
realized"; phase-one preconfirmations launched on mainnet in August 2025 to that
permissioned whitelist (~2 s confirmation), with true sub-second, permissionless preconfs
targeted for early 2026 ([taiko.xyz](https://taiko.xyz/guides/what-is-taiko-blockchain)).
This staged decentralization — *permissioned now, permissionless target* — is the same shape
as Rollup0→Rollup1's narrative; even the field's flagship based rollup is mid-transition.

**Gwyneth** is the Taiko research that matters most here: the **closest published analog to
Rollup0's synchronous L1↔L2 atomic composability**. Gwyneth describes a network of identical
Ethereum-equivalent L2s combining based sequencing, *real-time proving*, and a "booster"
mechanism so that — in the project's words — "all L2s can not only access each other
synchronously but also interact with L1 synchronously when supported by the L1 proposer," that
synchronous composability enabled through the based preconfirmation framework (L1 validators
committing to L2 states)
([taiko.mirror.xyz](https://taiko.mirror.xyz/ejciROGOGM9L_DuuqM3KloZan0EQR73fJt8qzTZmVzg);
[l2beat.com — Gwyneth](https://l2beat.com/scaling/projects/gwyneth)). This is the same
*mechanism class* Rollup0 implements: an interaction spanning L1 and L2 that commits in one
L1 slot, possible because the cross-chain results are determined ahead of settlement
and a cooperating L1 proposer places the settlement transaction in the right block.

Rollup0 and Gwyneth target the *same guarantee* — synchronous, single-L1-block L1↔L2 atomicity —
by the *same structural route* (precompute, then settle atomically in one L1 block with proposer
cooperation). They differ on **two** deliberate axes. *Trust model*: Gwyneth's route to "the
answer is correct before settlement" is real-time ZK proving under based sequencing; Rollup0's is
a permissioned validator-set attestation under a centralized sequencer (the precompute-and-prove
thesis is identical, the *prover* is not; [§1.2](01-introduction.md)). *Maturity*: Gwyneth is a
published / research-stage design, not a deployed system, just as Rollup0's synchronous
composability is specified-and-shippable rather than long-battle-tested. Rollup0's contribution
relative to Gwyneth is to make this mechanism class *concrete and shippable today* by substituting
a committee for a SNARK — a weaker proof in exchange for being buildable now — with Rollup1
converging on the ZK-and-based design Gwyneth also points at.

## 15.4 OP Stack / Superchain interop

The OP Stack's Superchain interoperability is the most important *contrast* case: the deployed
standard for cross-chain interaction, **explicitly asynchronous** — the opposite of Rollup0's
model. Optimism's documentation states that "a cross-chain message takes two transactions: one on
the source chain and one on the destination": the first emits an *initiating message*, which "is
just a log event"; the second is an *executing message* that calls "the `CrossL2Inbox` predeploy
to claim that a specific log event happened," identifying the log by source chain ID, origin
contract, block number, log index, and timestamp
([docs.optimism.io — interop explainer](https://docs.optimism.io/stack/interop/explainer);
[specs.optimism.io](https://specs.optimism.io/interop/overview.html)). Because the
interaction is structurally two transactions across two chains, the initiating call *cannot
use* the result of the remote call — there is no result yet when the source transaction
finishes. This is the asynchronous two-transaction pattern of [§2.5](02-background.md).

Superchain interop reduces *latency* — not the transaction count — by letting a sequencer
optionally accept executing messages that reference still-"unsafe" (pre-L1) initiating messages,
validity enforced by the **fork-choice rule** rather than confirmation depth: "the chain's fork
choice rule will reorg out any blocks that contain an executing message that is not valid," so
integrity is "guaranteed at the application layer without the need for any sort of confirmation
depth" ([specs.optimism.io](https://specs.optimism.io/interop/overview.html)). The lowest-latency
mode carries an explicit trust assumption — the accepting sequencer trusts "that every sequencer
in its transitive dependency set will eventually post the data," and if any equivocates, the
dependent executing-message blocks are reorged out and replaced with deposit-only blocks
([docs.optimism.io](https://docs.optimism.io/stack/interop/explainer)). Marketing framing of
"access within a single block / under 2 seconds" refers to this latency target and a
forward-looking shared-sequencing roadmap, not single-block *atomicity*; the deployed model is
firmly two-transaction message passing.

The contrast is clean. Superchain interop is *asynchronous, latency-optimized, and reorg-backed*:
low-latency messaging that still cannot express "act on the remote return value within this
transaction." Rollup0 is *synchronous and atomic*: the entire cross-chain interaction, including
the L1 control flow that branches on an L2 return value, either commits in one L1 block or not at
all ([§1.1](01-introduction.md)). The two answer different questions — Superchain interop scales
messaging across many chains; Rollup0 scales *composition* between one L2 and its L1.

### 15.4.1 Mechanical comparison: block headers & sequencer (Rollup0 vs OP Stack)

Because Rollup0 adopts **OP-Stack defaults** for its under-pinned parameters
([Appendix B §B.7](B1-reference.md)), a field-level comparison is useful. The striking
convergence: Rollup0's *planned* type-`0x7E` system transaction ([§4.4](04-evm-and-proxies.md))
is exactly OP's deposit-transaction type. OP's L1-origin-derived `prev_randao` is also the closest
deployed comparison for Rollup0's live-anchor-derived seed, although the current Rollup0 draft
domain-separates a distinct value for every L2 block instead of copying the seed unchanged.

| Aspect | OP Stack | Rollup0 |
|---|---|---|
| **`prev_randao`** | Copied unchanged from the **L1 origin block's `prev_randao`**; it repeats for every L2 block in that origin's epoch. | The latest canonical live anchor supplies one seed; the current draft hashes that seed with the chain ID and L2 block number, producing distinct but equally predictable values ([§4.2](../docs/rollup0-spec/04-block-production.md#live-anchor-scoped-prevrandao)). The client still uses `0`. |
| **L1 context into L2** | **L1-attributes deposited tx** (type `0x7E`), the first tx of every L2 block, → `L1Block` predeploy `0x42…0015`. | No `L1Block` predeploy; the composer/deriver reconstruct L1 context, and the Sync-block system tx delivers *cross-chain calls* (not generic L1 attributes) ([§4.4](04-evm-and-proxies.md), [§12](12-derivation-following.md)). |
| **`parentBeaconBlockRoot`** | The L1 origin's beacon root (Ecotone+). | `Some(0x0)` when Cancun-active — the L2 has no beacon chain ([§5.1](05-block-production.md)). |
| **Inbound / system tx** | **Unsigned** deposit tx, type `0x7E`, fields `(sourceHash, from, to, mint, value, gas, isSystemTx, data)`; mints via `mint`, backed by L1 `OptimismPortal` escrow. | **Signed legacy** tx from `SYSTEM_ADDRESS` today (mints via `msg.value`); the **type-`0x7E` unsigned envelope is the planned end-state** that removes the deriver's key dependency ([§4.4](04-evm-and-proxies.md), [§16](16-rollup1-roadmap.md), [App A](A1-implementation-deviations.md)) — i.e. Rollup0 is *converging on OP's exact mechanism*. |
| **EIP-1559** | Elasticity `6`, denominator `250` (Holocene: operator-configurable via `eip1559Params` in `extraData`). | Adopt OP's `6`/`250` as fixed constants ([§B.7](B1-reference.md)); `extraData` stays empty for deterministic re-derivation ([§5.1](05-block-production.md)). |
| **Gas limit** | Set via `SystemConfig`. | `BUILDER_GAS_LIMIT = 30_000_000`, a shared compile-time constant ([§5.1](05-block-production.md)). |
| **Sequencer architecture** | **op-node** (derivation + Engine API) + **op-geth** (execution) + **op-batcher** (posts DA batches to L1) + **op-proposer** (posts output roots). | A **single composer** drives stock reth via the Engine API; the **submitter** is the op-batcher analog ([§8.5](08-da-and-bundles.md)); there is **no separate proposer** — the state root advances inside `postAndVerifyBatch`, not via a periodic output-root tx ([§9.4](09-proving-settlement.md)). |
| **DA framing** | Channels / frames / **span batches**; **version-0 blob encoding** (4096 field elements, high byte dropped). | Guest of the **EEZ Core blob message stream** (`eez-core-protocol/docs/blobs/BLOB_FORMAT_SPEC.md`, 31 data bytes per field element): one opaque `ChainOperation.operations` carrying the Rollup0 columnar V0 span, then EEZ action brackets ([Appendix D](../docs/rollup0-spec/D-wire-formats.md), [Appendix G](../docs/rollup0-spec/G-blob-payload-design.md)). OP's own version-0 blob encoding is not adopted. |
| **Fees** | `BaseFeeVault` / `SequencerFeeVault` / `L1FeeVault` predeploys + an L1-data-fee oracle (`GasPriceOracle`). | Fees burn to `0x0` today; **adopt OP-style fee vaults** ([§B.7](B1-reference.md)); no L1-data-fee oracle yet ([App A](A1-implementation-deviations.md)). |
| **Settlement** | **Fraud proofs** (Cannon fault-proof; permissionless via the dispute game). | **Permissioned ECDSA *N*-of-*M* attestation** ([§9](09-proving-settlement.md)); Rollup1 → ZK validity proof ([§16](16-rollup1-roadmap.md)). |
| **Cross-chain composability** | **Asynchronous** two-tx interop (§15.4). | **Synchronous, single-L1-block atomic** ([§1.1](01-introduction.md)) — the differentiator. |

Sources: [specs.optimism.io — deposits](https://specs.optimism.io/protocol/deposits.html),
[exec-engine](https://specs.optimism.io/protocol/exec-engine.html),
[predeploys](https://specs.optimism.io/protocol/predeploys.html),
[holocene/exec-engine](https://specs.optimism.io/protocol/holocene/exec-engine.html).
The net picture: at the **header, fee-vault, DA-encoding, and inbound-tx** levels Rollup0 can be
a faithful OP-Stack-shaped L2; it *diverges* deliberately on **settlement** (committee attestation
→ ZK, not fraud proofs) and on **composability** (synchronous, not asynchronous).

## 15.5 Arbitrum Nitro

Arbitrum Nitro is Rollup0's closest match on **two** axes at once — sequencing and DA — the best
illustration that those choices are mainstream rather than exotic.

On **sequencing**, Nitro "uses a single centralized sequencer operated by Offchain Labs"
that orders transactions first-come-first-served by default and issues immediate soft
confirmations via a real-time feed (~1–2 s), with hard finality on Ethereum typically taking
10–20 minutes; the Nitro whitepaper records an intent to "transition to a committee-based
sequencer" in future
([docs.arbitrum.io — inside Nitro](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro);
[Nitro whitepaper](https://docs.arbitrum.io/nitro-whitepaper.pdf)). This is the direct analog
of Rollup0's posture: a single operator, fast soft confirmations, slower L1-anchored finality,
and a documented (not-yet-realized) decentralization intent. (Nuance for the 2026 reader: since
April 2025, Arbitrum One's live ordering is no longer pure FCFS but *Timeboost*, with an auctioned
~200 ms express lane; FCFS remains the documented default but no longer the complete live picture.)

On **DA**, Nitro posts batched transaction data to Ethereum "using EIP-4844 blob
transactions by default … when supported by Ethereum," with calldata as a fallback "even if
blob fees rise or EIP-4844 blobs are unavailable," after Brotli compression whose level is
dynamically adjusted (0–11) with congestion
([docs.arbitrum.io](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro);
[research.arbitrum.io — compression](https://research.arbitrum.io/t/compression-in-nitro/20)).
This blob-default / calldata-fallback economics is *essentially identical* to Rollup0's
"blobs by default, calldata when cheaper" rule ([§2.3](02-background.md),
[§8](08-da-and-bundles.md)) — Rollup0 simply targets Gnosis Chain rather than Ethereum.

Nitro and Rollup0 **diverge** on the proving axis. Nitro is an optimistic rollup whose
settlement uses interactive fraud proofs: validators post assertions about L2 state, and
during a ~7-day dispute window challengers and defenders "take turns bisecting their history
commitments until they arrive at a single step of instruction," which Ethereum then verifies
via a one-step proof
([docs.arbitrum.io — BoLD](https://docs.arbitrum.io/how-arbitrum-works/bold/gentle-introduction)).
As of February 2025, **BoLD** (Bounded Liquidity Delay) made this validation *permissionless*
on Arbitrum One and Nova mainnet: "BoLD enables anyone to participate in validating the chain
state (including challenges)," with bonds tied to assertions rather than to an allowlisted
party, replacing a prior protocol that "was limited to a set of allowlisted validators"
because the older 1-versus-1 dispute design "[was] vulnerable to denial-of-service attacks"
([blog.arbitrum.io — BoLD](https://blog.arbitrum.io/bold-permissionless-validation-for-arbitrum-chains/)).
This permissioned→permissionless trajectory parallels Rollup0→Rollup1 exactly — but the endpoints
are asymmetric: Nitro's *fraud-proof* model is already strictly stronger than Rollup0's committee
attestation (a single honest challenger can overturn an invalid root, whereas Rollup0 relies on a
*threshold* of honest attesters plus re-derivation), and Rollup1's planned *validity* proofs are
stronger still. Nitro thus matches Rollup0 on sequencing and DA while sitting a tier above it on
settlement.

## 15.6 Polygon AggLayer

Polygon's **AggLayer** addresses cross-chain interaction at the level of a shared bridge plus
a settlement-layer proof; the contrast with Rollup0 is instructive because both use the word
"atomic" for different things. AggLayer's foundational security mechanism is the
**pessimistic proof**, "a novel ZK-proof … which gives an ecosystem-wide view of token
ownership across connected chains," structured "so that no chain can withdraw more assets
than have been deposited on the unified bridge"
([agglayer.dev](https://www.agglayer.dev/blogs/aggregated-blockchains-a-new-thesis);
[docs.polygon.technology — AggLayer](https://docs.polygon.technology/interoperability/agglayer)).
The design goal is *containment*: a compromised connected chain cannot drain more than its
own deposits, so cross-chain risk is bounded at the bridge rather than propagated. On top of
the **unified bridge**, AggLayer offers cross-chain transactions that "either succeed on all
involved chains or fail entirely [with] no partial states"
([polygon.technology](https://polygon.technology/blog/the-agglayer-will-be-a-particle-accelerator-for-blockchain-use-cases);
[docs.agglayer.dev — bridge-and-call](https://docs.agglayer.dev/agglayer/core-concepts/unified-bridge/bridge-and-call/)).

The distinction from Rollup0's synchronous model is the *scope and timing* of that atomicity.
AggLayer's "all-or-nothing" is an *aggregation-layer* property: a bundle of cross-chain actions
is settled together and the pessimistic proof keeps bridge accounting globally consistent — but
this is not a *single-L1-block, return-value-carrying* interaction in which one chain's contract
calls another's, receives its result, and branches on it before either side commits. AggLayer
composes *value transfers and calls across many chains* with bounded-risk settlement; Rollup0
composes *synchronous execution between one L2 and its L1* with shared, mutually-consistent state
inside one block. AggLayer's contribution — provable, ecosystem-wide solvency across
heterogeneous chains — is largely orthogonal to Rollup0's synchronous-composability problem, so
it appears here as a *cross-chain model* contrast rather than a synchronous-composability peer.

> *Confidence note.* The AggLayer claims in this subsection rest on **single-source
> extraction** from Polygon's own documentation and blog, and are therefore a lower
> confidence tier than the cross-checked Taiko/OP/Arbitrum claims elsewhere in this chapter
> (which were each verified across three independent sources).

## 15.7 Shared sequencer networks (Espresso, Astria)

Shared sequencer networks decentralize the *sequencing* axis by interposing an external BFT
validator set that orders transactions for many rollups at once. Among *deployed* designs they
come closest to offering cross-rollup atomicity — though under a trust assumption Rollup0 and
Rollup1 both aim to avoid.

**Espresso** runs **HotShot**, "a consensus protocol based on HotStuff but modified to be
open and permissionless with a dynamic stake table," distinguishing it from fixed-validator-
set BFT
([hackmd.io — Espresso Sequencer](https://hackmd.io/@EspressoSystems/EspressoSequencer)).
**Astria** is a "lazy sequencer" that "separates ordering from execution: it sequences and
commits transaction data but delays execution, leaving execution to each rollup," preserving
each rollup's sovereignty over its own state machine, and it "can provide guarantees that
transactions are only included as part of an atomic bundle … a tx on one rollup [executes]
only if a transaction on another rollup is also included"
([astria.org](https://www.astria.org/blog/astria-the-shared-sequencer-network)). That bundle
guarantee is genuine cross-rollup atomic *inclusion*.

The crucial limitation is the *basis* of that atomicity. Across shared-sequencer designs
(Espresso, Astria, Radius), the networks "enable certain types of cross-rollup transactions but
crucially trust the sequencer for proper sequencing to guarantee atomicity," rather than
achieving *trustless* atomicity ([arxiv.org — 2502.04659](https://arxiv.org/html/2502.04659v1)).
The shared sequencer can promise atomic inclusion of a cross-rollup bundle, but that promise
rests on the sequencer set behaving correctly; and in the lazy-sequencer model, *ordering* is
committed while *execution* (and the cross-rollup result) is deferred to each rollup — atomic
co-inclusion, not the synchronous, return-value-carrying composition Rollup0 provides. The
relation to Rollup1: based and shared sequencing are *competing answers to the same
decentralization question* (who orders, once the single operator is removed). Rollup1 chooses
based (L1 proposers, inheriting L1 liveness) over a separate shared-sequencer trust domain,
keeping its atomicity guarantee anchored to L1 and its proof rather than to an external sequencer
committee.

> *Confidence note.* The Espresso/Astria characterizations here rest largely on **single-source
> extraction** (each project's own writing plus the arXiv survey) and sit at a lower
> confidence tier than the cross-checked Taiko/OP/Arbitrum claims, which were each verified
> across three independent sources.

## 15.8 Gnosis Chain as the settlement layer

Rollup0 settles to **Gnosis Chain**, not Ethereum mainnet, so a word on the L1's own trust
model is in order — it is the chain whose security Rollup0 inherits, and its validator model is a
useful framing device for Rollup0's own committee.

Gnosis Chain "runs the same client software as Ethereum, with minor parameter tweaks. As
such, Gnosis is a Proof-of-Stake network that uses Ethereum's Beacon Chain consensus"
([docs.gnosischain.com](https://docs.gnosischain.com/node/)). It is an EVM L1 with its own
PoS validator set, tracking Ethereum's forks (post-Merge, post-Shanghai, Cancun-class), with
~5 s block times and xDAI as native gas token ([§2.6](02-background.md)). Two consequences.
First, Rollup0's *settlement security is Gnosis Chain's security* — its validator set, finality,
liveness — the standard rollup relationship to its L1, not weakened by Rollup0's own committee.
Second, more framing observation than security claim: Gnosis Chain is itself secured by a
validator set rather than by Ethereum's economic weight, so a reader comfortable with "an EVM
chain whose safety rests on an honest threshold of a defined validator set" has most of the
mental model for Rollup0's *N*-of-*M* attestation committee ([§9](09-proving-settlement.md)).
The difference in kind still matters — Gnosis Chain's validators are permissionlessly staked PoS
validators running full consensus, whereas Rollup0's committee is a small, *permissioned* ECDSA
attester set — but the framing locates Rollup0's added trust assumption relative to the chain it
settles on, and Rollup1's permissionless, BLS-aggregated set narrows that gap toward an L1-like
model ([§16](16-rollup1-roadmap.md)).

> *Confidence note.* The Gnosis Chain claims in this subsection rest on **single-source
> extraction** from Gnosis's own documentation, a lower confidence tier than the
> cross-checked Taiko/OP/Arbitrum claims, which were each verified across three independent
> sources.

## 15.9 Where Rollup0 is honestly weaker, and where it is stronger

The conclusions of this survey, stated without hedging:

**Rollup0 is weaker than its peers on settlement.** Its permissioned validator-set attestation
is a *weaker* guarantee than both fraud proofs and validity proofs — not a close call. A
fraud-proof system (Arbitrum/BoLD) lets a *single* honest party overturn an invalid state root
through an on-chain dispute; a validity-proof system (Taiko, the Rollup1 target) makes an invalid
root mathematically impossible to settle. Rollup0's committee *advances* the on-chain root on the
strength of a threshold of attesters being honest and correct, and an invalid advance is
*detectable* (any honest follower re-derives and halts; [§2.4](02-background.md),
[§12](12-derivation-following.md)) but not *prevented* or *automatically recovered*. The
re-derivation backstop keeps this from collapsing to "trust the multisig" — it converts the
guarantee into "trust the committee *or* any honest re-deriver," making corruption publicly
evident — but the spec is explicit that this buys *detection, not prevention*, and that closing
the gap is the entire point of Rollup1's ZK proof ([§1.3.1](01-introduction.md),
[§9](09-proving-settlement.md), [§14](14-security-threat-model.md)). On liveness Rollup0 is
weaker still: unlike a based rollup, a single operator and no escape hatch.

**Rollup0 is more ambitious than any deployed leader on composability.** Its synchronous,
single-L1-block, return-value-carrying atomic L1↔L2 composition is *not* offered by any
production system surveyed here. Arbitrum and the OP Stack provide asynchronous, two-transaction
messaging; AggLayer provides bounded-risk aggregated settlement; shared sequencers provide
trusted atomic co-inclusion. None lets an L1 contract call an L2 contract, receive its result,
and branch on it within one block. The **closest peer is Taiko's Gwyneth** — same guarantee by
the same precompute-and-settle route — and Gwyneth is a *published design*, not a shipped
product. Rollup0's distinctive contribution is to make this mechanism class *concrete and
deployable today*, by trading the SNARK for a committee, while building every interface so the
committee can later be swapped for the proof and the centralized sequencer for based sequencing.

The net picture: on sequencing and DA, Rollup0 *matches* the mainstream (the same choices as
Arbitrum Nitro); on settlement it sits *below* the field and is candid about it; on composability
it sits *above* the deployed field and level with the most ambitious published research. The
table below summarizes the four axes; rows reflect the *published designs* compared in this
chapter, with maturity caveats noted in the surrounding text.

| System | Sequencing | Data availability | Proving / settlement | Cross-chain composability |
|---|---|---|---|---|
| **Rollup0** (this spec) | Single centralized sequencer/composer; no escape hatch | L1 (Gnosis): EIP-4844 blobs by default, calldata when cheaper | Permissioned ECDSA *N*-of-*M* committee attestation + full re-derivation backstop | **Synchronous, single-L1-block atomic L1↔L2** (precompute-and-prove) |
| **Rollup1** (target, [§16](16-rollup1-roadmap.md)) | Based (L1-proposer-driven) + preconfirmations | L1 (Gnosis): blobs / calldata (PeerDAS-class as L1 evolves) | ZK validity proof; permissionless, BLS-aggregated set | Synchronous atomic, generalized to many based rollups |
| **Taiko / Gwyneth** | Based; preconfers (whitelisted today → permissionless target) | L1 (Ethereum); blobs | ZK validity proof (Type-1 zkEVM; multi-prover) | Gwyneth: **synchronous L1↔L2 + L2↔L2** (based preconfs + real-time proving) — published design |
| **OP Stack / Superchain interop** | Per-chain sequencer; shared-sequencing roadmap | L1 blobs / external DA (configurable) | Optimistic fraud proofs | **Asynchronous** two-tx message passing (initiating log + `CrossL2Inbox` claim) |
| **Arbitrum Nitro** | Single centralized sequencer (FCFS default; Timeboost live) | L1 (Ethereum): blobs by default, calldata fallback (Brotli) | Optimistic interactive fraud proofs; permissionless via BoLD | Asynchronous cross-chain messaging |
| **Polygon AggLayer** | Per-chain (heterogeneous connected chains) | Per-chain (chain-dependent) | Pessimistic proof (ZK) over a unified bridge | Aggregated all-or-nothing settlement + unified bridge; **not** single-block synchronous |
| **Espresso / Astria** | Shared decentralized sequencer (HotShot BFT; lazy sequencer) | Often external DA; chain-dependent | Inherited from each rollup's own proving | Trusted atomic cross-rollup *inclusion* (atomic bundles); not trustless synchronous execution |

---

*Next: [Chapter 16 — Rollup1: The Roadmap](16-rollup1-roadmap.md).*
