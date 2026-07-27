# 12. Open Issues & Limitations

A consolidated register of v0's accepted limitations, deployment parameters still to be pinned, and
tradeoffs of the future variants.

## 12.1 Accepted v0 limitations

- **Centralized, permissioned operator; no escape hatch.** v0 has a single operator. There is **no
  L1 force-inclusion and no trustless exit**: a hostile or unavailable operator can censor or halt
  the chain, and bridged funds cannot be withdrawn without operator cooperation. Safety does not
  depend on the operator (§5.4, §8, §10); liveness does. Removed under Rollup1 (§13).
- **The per-rollup manager is fully trusted (Rollup0/GC).** The manager defines the validator set
  and threshold and holds `setStateRoot`, which can overwrite the L2 state root outside the L1 block
  a batch locked it (§5.6 H.1, §5.8). For Rollup0/GC this is an **accepted trust assumption**; it can
  be replaced with a stronger scheme, or have these powers revoked/burned, under Rollup1 (§13).
- **L1→L2 only, single return.** Synchronous L2→L1 and multi-call/reentrant cross-chain flows are
  not in v0 (§1.2, §9); they are general-model (§13).
- **`prev_randao` is not secure randomness.** It is predictable to the operator and
  L1-proposer-biasable (§4.3); unpredictable in-block randomness is impossible under synchronous
  deterministic execution. Applications needing randomness must use a VRF or commit-reveal.
- **Deep-L1-reorg recovery is manual.** A reorg deeper than L1 finality is outside automatic
  recovery and requires operator intervention (§10.4).
- **Simulation/on-chain gas parity.** The operator's simulation MUST match on-chain execution
  semantics including gas (§6 R2); a divergence makes an apparently-valid batch revert on-chain.
  The simulation environment is responsible for matching the on-chain gas schedule exactly.

## 12.2 Deployment parameters to pin

The following are deployment choices, not yet fixed; until pinned the development defaults apply
(see [Appendix A](A-reference.md)):

- **L2 `chainId`** — must be a unique id, distinct from any L1 it settles to.
- **EIP-1559 parameters** — elasticity multiplier, base-fee-change denominator, initial base fee.
- **`prev_randao` anchor** — which confirmed L1 block supplies the RANDAO (§4.3), and that it is
  constant across the slot.
- **Fee recipients** — the base-fee / priority-fee / L1-data-fee vault recipients, and whether the
  L1 DA cost is charged to L2 users (§11).
- **Blob DA format** — specified separately (§7.1); all EEZ chains conform.
- **`SYSTEM_ADDRESS` value + funding** — the production key, and how minted value is backed by
  L1-locked value (§9.3, §11.5).
- **Validator set `M` and threshold `N`** — the member count (≤ 20 in v0) and quorum (§8).
- **Bundle user-transaction bound** — the max user transactions per bundle, tied to L1 block-gas
  headroom (§7.4, §11.3).
- **Genesis-timestamp grid alignment** — the genesis timestamp should align to the L2 block-time
  grid so slot heights land cleanly (§4.2).

## 12.3 Future-variant tradeoffs

- **Proof-window / pre-building (a sequencer + ZK variant).** v0 needs no proof-window because it
  has no ZK proving (§4.2). A future variant that adds a sequencer and ZK validity proofs needs
  proving time before L1 submission: the operator would have to **pre-build the slot's trailing
  blocks and the Sync block ahead of wall-clock** (roughly the proving time plus L1 block-building
  time — on the order of seconds) or **skip** those trailing blocks. This adds latency and
  block-building complexity and is the main cost of moving to ZK; it is not present in v0.
- **Open/based sequencing & state-root chaining (Rollup1).** Under v0's single sequencer, one
  `postAndVerifyBatch` per L1 block publishes the whole slot, so batch *chaining* never arises.
  Under Rollup1's open/based sequencing (§13), independent parties may post multiple batches for
  one L2 in one L1 block; those batches must **chain** (`entries[k].currentState ==
  entries[k-1].newState`), which in turn requires that each batch commit a *stable end-of-block*
  state — i.e. the L2 must have **no post-block / end-of-block state mutations**. This constraint
  is a Rollup1 concern, not a v0 one.

---

*Next: [§13 Rollup1 & the General Model](13-rollup1-general-model.md).*
