# 15. Related Work

> **Informative.** Comparisons and future-system descriptions in this companion chapter have no
> conformance effect. This chapter has been corrected to the target network
> model. Older implementation configurations used one local composer and
> Chiado; those are development facts, not Rollup0 production policy.

This chapter situates Rollup0 and the unselected possibilities in
[Rollup0 §10](../docs/rollup0-network-spec/10-future-design.md) within the contemporary rollup
landscape. Rollup0 uses synchronous,
single-settlement-block composition and permits competing composers. Its exact
production proof-system membership and threshold remain release blockers; this
chapter therefore does not compare an assumed committee configuration as though
it were selected protocol. Its current implementation uses calldata DA and
development proof configurations. It is
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

**(a) Candidate-production model — who proposes L2 transactions.** The spectrum runs from a *single
centralized sequencer* (one operator orders and produces blocks), through *based*
(L1-sequenced) designs (the L1 proposer schedule drives ordering, so the rollup inherits
L1 liveness), to *shared / decentralized sequencer networks* (an external BFT validator set
orders transactions for many rollups at once). Rollup0 has no authorized
composer: multiple composers may construct valid sibling candidates, and the
first applicable candidate settled in canonical Ethereum order wins
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md),
[Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)). This is
open competitive production, but it is not identical to based sequencing: an
Ethereum proposer orders settlement transactions rather than constructing the
Rollup0 block directly. The future-design list in §10 does not select a based
sequencing model.

**(b) Data availability — where the data to reconstruct L2 state is published.** The
choices are *settlement-chain calldata*, *EIP-4844 blobs*, or an *external DA layer* (Celestia, EigenDA,
Avail). Post-Cancun, the live question for an L1-DA rollup is calldata-versus-blob
*selection*, since the two are priced in independent fee markets. The Rollup0
draft selects a tag-`0x00` RLP payload in Ethereum calldata for its production
target, but no production activation exists. The reviewed development profile
uses Chiado. A blob codec is future design, not a fallback selected by this edition
([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)). It does not target an external DA layer
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md)).

**(c) Proving / settlement — how L1 is convinced the posted state root is correct.** The
three established models are *optimistic fraud proofs* (post the root unproven, allow a
challenge window), *validity (ZK) proofs* (post a SNARK/STARK that L1 verifies
immediately), and *attestation* (a set re-executes and signs). Rollup0
validators/provers sign any candidate they determine is correct; producer
identity is not an acceptance condition. The production proof systems,
membership, threshold, verifier deployments, and administrator controls are
not yet selected, so stronger claims would be premature
([EEZ Framework overview](../docs/eez-protocol-spec/index.md),
[EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).

**(d) Cross-chain / cross-rollup atomic composability — whether two chains can commit
a single interaction all-or-nothing.** Rollup0 is most distinctive here. The deployed norm is
*asynchronous message passing*: a message emitted on one chain is consumed by a *separate, later*
transaction on the other, and the initiating call cannot use the remote result
([EEZ Framework overview](../docs/eez-protocol-spec/index.md)). Rollup0 instead selects one flat
*synchronous cross-network action* per producing interaction between Rollup0 and Ethereum. The
action is coordinated through one Ethereum settlement block, with the remote result available to
local control flow because it was precomputed and proven before settlement. This edition does not
define direct execution-network-to-execution-network composition
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md)). The only published design targeting the same guarantee class is
Taiko's Gwyneth (§15.3).

These axes are not fully orthogonal — synchronous composability (d) is far easier
when settlement ordering and candidate production cooperate — but holding them apart is the right lens for
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

Rollup0 instead permits any composer to construct a candidate and relies on
validity checking plus Ethereum transaction order to select the winner. It has
no selected preconfirmation mechanism and does not inherit based-rollup
liveness merely because its settlement relay is permissionless
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md),
[§14](threat-model.md)). The possibilities in §10 do not specify a future
based-proposer design.

## 15.3 Taiko and Gwyneth

**Taiko** is a useful comparison for production based-rollup architecture. Its execution layer
is a **Type-1 zkEVM** — "the highest level of Ethereum
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
This staged decentralization — *permissioned now, permissionless target* — is useful context,
but it is not evidence that Rollup0 has selected the same transition.

**Gwyneth** is the Taiko research that matters most here: the **closest published analog to
Rollup0's synchronous atomic composability mechanism**. Gwyneth describes a network of identical
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

Rollup0 and Gwyneth occupy the same broad mechanism class: precompute a cross-network result, then
settle atomically in one Ethereum block with proposer cooperation. Rollup0 permits one flat action
per producing interaction between Rollup0 and Ethereum, while nested, reentrant, and
execution-network-to-execution-network actions are excluded. Gwyneth publishes a based-sequencing,
real-time-ZK direction. Rollup0 instead selects open competing composers and leaves its production
proof systems, membership, threshold, deployments, and activation unresolved
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md)). The reviewed mock and ECDSA
development paths do not justify classifying Rollup0 as committee-based or production-ready.

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
finishes. This is the asynchronous two-transaction pattern of [EEZ Framework overview](../docs/eez-protocol-spec/index.md).

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
transaction." Rollup0 is *synchronous and atomic*: a flat cross-network action, including local
control flow that branches on the remote return value, either commits through one Ethereum
settlement block or not at all
([Rollup0 Network overview](../docs/rollup0-network-spec/index.md)). The two answer different
questions: Superchain interop scales messaging across many chains; Rollup0 specifies synchronous
composition between Rollup0 and Ethereum. A future Rollup0 edition would need additional combined
candidate, proof, DA, admission, and partial-settlement rules before it could support peer EEZ
execution networks.

### 15.4.1 Mechanical comparison: block headers & sequencer (Rollup0 vs OP Stack)

Rollup0 uses ordinary EVM execution behavior instead of OP Stack-specific deviations. The draft
selects a zero beneficiary, a 30-million block gas limit, and tag-`0x00` calldata DA. Production
base fee, system-transaction envelope and authorization, system gas policy, and funding remain
release blockers. Signed legacy values are reviewed development behavior only.

| Aspect | OP Stack | Rollup0 |
|---|---|---|
| **`prev_randao`** | Copied from the **L1 origin block's `prev_randao`** (EIP-4399, since Bedrock). | Fixed zero in the current draft; settlement-derived randomness requires a versioned change ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)). |
| **L1 context into L2** | **L1-attributes deposited tx** (type `0x7E`), the first tx of every L2 block, → `L1Block` predeploy `0x42…0015`. | No `L1Block` predeploy; the composer/deriver reconstruct L1 context, and the Sync-block system tx delivers *cross-chain calls* (not generic L1 attributes) ([EEZ Framework §3 — EVM Binding](../docs/eez-protocol-spec/03-evm-binding.md), [Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)). |
| **`parentBeaconBlockRoot`** | The L1 origin's beacon root (Ecotone+). | `Some(0x0)` when Cancun-active — the L2 has no beacon chain ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)). |
| **Inbound / system tx** | **Unsigned** deposit tx, type `0x7E`, fields `(sourceHash, from, to, mint, value, gas, isSystemTx, data)`; mints via `mint`, backed by L1 `OptimismPortal` escrow. | Production envelope, authorization, nonce, fees, and value source are unresolved. The reviewed development client uses EIP-155-signed legacy transactions from a prefunded `SYSTEM_ADDRESS` ([Rollup0 Appendix C](../docs/rollup0-network-spec/C-system-transactions.md)). |
| **EIP-1559** | Elasticity `6`, denominator `250` (Holocene: operator-configurable via `eip1559Params` in `extraData`). | Ordinary EIP-1559 accounting is selected; production fork activation and genesis base fee remain unresolved. The 1 gwei value is development-only ([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)). |
| **Gas limit** | Set via `SystemConfig`. | `BUILDER_GAS_LIMIT = 30_000_000`, a shared compile-time constant ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)). |
| **Sequencer architecture** | **op-node** (derivation + Engine API) + **op-geth** (execution) + **op-batcher** (posts DA batches to L1) + **op-proposer** (posts output roots). | Each composer drives stock reth through the Engine API and can submit a candidate; no composer identity is privileged by the Rollup0 admission rule. The current implementation normally runs one local composer but also observes competing external batches ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)). |
| **DA framing** | Channels / frames / **span batches**; **version-0 blob encoding** (4096 field elements, high byte dropped). | Normative tag-`0x00` RLP calldata payload. A blob path and its codec require a later profile version ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)). |
| **Fees** | `BaseFeeVault` / `SequencerFeeVault` / `L1FeeVault` predeploys + an L1-data-fee oracle (`GasPriceOracle`). | Standard base-fee burn; priority fees credited to the zero beneficiary; no fee vaults or L1-data-fee oracle ([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)). |
| **Settlement** | **Fraud proofs** (Cannon fault-proof; permissionless via the dispute game). | Validators/provers sign every candidate they determine is correct. The production proof systems, membership, threshold, and deployments are release blockers ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)). |
| **Cross-chain composability** | **Asynchronous** two-tx interop (§15.4). | **Synchronous, single-L1-block atomic** ([Rollup0 Network overview](../docs/rollup0-network-spec/index.md)) — the differentiator. |

Sources: [specs.optimism.io — deposits](https://specs.optimism.io/protocol/deposits.html),
[exec-engine](https://specs.optimism.io/protocol/exec-engine.html),
[predeploys](https://specs.optimism.io/protocol/predeploys.html),
[holocene/exec-engine](https://specs.optimism.io/protocol/holocene/exec-engine.html).
The net picture is a comparison, not a dependency: Rollup0 shares some EVM/header mechanisms with
OP, but its fee, DA, and inbound-transaction rules are separately owned. It differs on
**settlement** (a not-yet-activated validity policy, not fraud proofs) and on
**composability** (synchronous cross-network execution, not asynchronous messaging).

## 15.5 Arbitrum Nitro

Arbitrum Nitro is useful context for calldata and blob DA, but its
single-sequencer admission model differs from Rollup0's open candidate
competition.

On **sequencing**, Nitro "uses a single centralized sequencer operated by Offchain Labs"
that orders transactions first-come-first-served by default and issues immediate soft
confirmations via a real-time feed (~1–2 s), with hard finality on Ethereum typically taking
10–20 minutes; the Nitro whitepaper records an intent to "transition to a committee-based
sequencer" in future
([docs.arbitrum.io — inside Nitro](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro);
[Nitro whitepaper](https://docs.arbitrum.io/nitro-whitepaper.pdf)). This is not
Rollup0's target admission model: Rollup0 allows competing composers and
selects the first applicable valid Ethereum settlement. The current Rollup0
implementation can still expose a local composer's unsafe head. (Nuance for the 2026 reader: since
April 2025, Arbitrum One's live ordering is no longer pure FCFS but *Timeboost*, with an auctioned
~200 ms express lane; FCFS remains the documented default but no longer the complete live picture.)

On **DA**, Nitro posts batched transaction data to Ethereum "using EIP-4844 blob
transactions by default … when supported by Ethereum," with calldata as a fallback "even if
blob fees rise or EIP-4844 blobs are unavailable," after Brotli compression whose level is
dynamically adjusted (0–11) with congestion
([docs.arbitrum.io](https://docs.arbitrum.io/how-arbitrum-works/inside-arbitrum-nitro);
[research.arbitrum.io — compression](https://research.arbitrum.io/t/compression-in-nitro/20)).
Rollup0 fixes tag-`0x00` calldata and leaves blobs to a future version
([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).

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
That permissioned-to-permissionless validation trajectory is useful context,
but Rollup0's production proof-system membership and threshold are not yet
selected. A comparison that assigns Rollup0 a fixed committee would invent a
profile value. Nitro and Rollup0 also differ in candidate production: Nitro
uses its sequencer, while Rollup0 admits any valid competing candidate.

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
composes one flat, return-value-carrying action between Rollup0 and Ethereum inside one Ethereum
block. Direct peer-network composition is outside this edition. AggLayer's contribution —
provable, ecosystem-wide solvency across
heterogeneous chains — is largely orthogonal to Rollup0's synchronous-composability problem, so
it appears here as a *cross-chain model* contrast rather than a synchronous-composability peer.

> *Confidence note.* The AggLayer claims in this subsection rest on **single-source
> extraction** from Polygon's own documentation and blog, and are therefore a lower
> confidence tier than the cross-checked Taiko/OP/Arbitrum claims elsewhere in this chapter
> (which were each verified across three independent sources).

## 15.7 Shared sequencer networks (Espresso, Astria)

Shared sequencer networks decentralize the *sequencing* axis by interposing an external BFT
validator set that orders transactions for many rollups at once. Among *deployed* designs they
come closest to offering cross-rollup atomicity, though under a separate sequencer-set trust
assumption.

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
co-inclusion, not the synchronous, return-value-carrying composition Rollup0 specifies. Rollup0
does not select an external shared-sequencer set. Its open composers construct candidates, and
canonical Ethereum transaction order selects the first applicable valid settlement. Section 10
does not select either based or shared sequencing as a future design.

> *Confidence note.* The Espresso/Astria characterizations here rest largely on **single-source
> extraction** (each project's own writing plus the arXiv survey) and sit at a lower
> confidence tier than the cross-checked Taiko/OP/Arbitrum claims, which were each verified
> across three independent sources.

## 15.8 Gnosis Chain as a peer EEZ network

Gnosis Chain is not Rollup0's settlement host. It is a separate EEZ execution
network with its own profile. Both networks settle on Ethereum and can import
the same exactly versioned Rollup0 common execution rules.

The material difference is candidate admission. Rollup0 accepts a candidate
from any composer when it is valid. Gnosis Chain additionally requires an
authorized composer signature, checked by its proof contract on Ethereum.
Relaying an already signed candidate remains permissionless. The exact
signature digest, replay domain, authorized-set representation, rotation rule,
and proof-contract deployment remain explicit release blockers in the
[Gnosis Chain EEZ Network Specification](../docs/gnosis-chain-eez-spec/index.md).

Chiado is only a development settlement environment. Its nominal 5-second
interval corresponds to five 1-second execution-network timestamp positions.
The production target uses a nominal 12-second Ethereum interval and six
2-second positions.

## 15.9 Where Rollup0 differs

Rollup0's most distinctive property is synchronous, return-value-carrying
composition that settles in one Ethereum block. Arbitrum and the OP Stack use
asynchronous messaging; AggLayer provides aggregated settlement; shared
sequencers can provide atomic co-inclusion. Taiko's Gwyneth is the closest
published design in this comparison.

Rollup0 also differs from single-sequencer rollups because composer admission is
open. That fact alone does not establish based-rollup censorship resistance:
proof availability, Ethereum inclusion, data availability, and recovery rules
still determine liveness.

No honest comparison can assign Rollup0 a production proof guarantee yet. The
proof systems, verifier deployments, membership, threshold, administrator
controls, and activation point are unresolved. Development mock proofs are
unsound for production, and the older ECDSA implementation binding is not the
`eez-evm@0.2-draft` binding selected by this edition.

| System | Candidate production | Data availability | Proving / settlement | Cross-chain composability |
|---|---|---|---|---|
| **Rollup0** | Open competing composers; first applicable valid Ethereum settlement wins | Ethereum calldata, tag-`0x00` canonical RLP; Chiado in development | Production proof policy is a release blocker; validators/provers sign any correct candidate | **Synchronous, single-Ethereum-block atomic composition** |
| **Gnosis Chain EEZ** | Authorized composer signature plus validity; permissionless relay | Same imported common rule unless its profile overrides it | Authorization checked by the Ethereum proof contract; exact mechanism is a release blocker | Same imported common rule unless its profile overrides it |
| **Taiko / Gwyneth** | Based; preconfirmers | Ethereum blobs | ZK validity proofs | Gwyneth targets synchronous L1/L2 composition |
| **OP Stack / Superchain interop** | Per-chain sequencer | Ethereum blobs or configurable external DA | Optimistic fault proofs | Asynchronous message passing |
| **Arbitrum Nitro** | Single sequencer | Ethereum blobs, calldata fallback | Optimistic interactive fraud proofs | Asynchronous messaging |
| **Polygon AggLayer** | Per-chain | Per-chain | Pessimistic proof over a unified bridge | Aggregated settlement, not synchronous execution |
| **Espresso / Astria** | Shared sequencer | Chain-dependent | Inherited from each rollup | Atomic inclusion, not synchronous execution |

---

*Next: [Rollup0 §10 — Future Design](../docs/rollup0-network-spec/10-future-design.md).*
