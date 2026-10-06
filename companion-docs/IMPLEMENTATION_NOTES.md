# Appendix A. Implementation Deviations

> [!WARNING]
> **Superseded as of 2026-08-25.** These notes compare code with a retired Rollup0 draft and use its
> former chapter numbering. They do not identify conformance with the
> [current Rollup0 specification](../docs/rollup0-spec/index.md). Treat the file only as historical
> implementation-audit material until it is rewritten against a pinned current code revision.

> **How to read this appendix.** Chapters 1–16 (the **body**) are 100% normative — the
> intended-correct Rollup0 design. **This appendix is not normative.** It ranks every place
> the *current code, at the pinned commit,* does **not** meet that target — for auditors (what
> is guaranteed today vs on paper) and implementers (the punch-list). Each entry names the
> deviated spec requirement, what the code does instead, the `file:line` evidence, the impact,
> and the recommended fix.
>
> Severity is operational: **Critical** = a guarantee the body asserts is *absent*, and the
> absence can corrupt or forge state in a plausible (mis)configuration; **High** = a real
> soundness/liveness gap reachable by an adversary or likely operator error; **Medium** = a
> divergence-, griefing-, or sustainability-class gap not breaking safety by itself; **Low** =
> a placeholder, scaffolding stub, or mostly-mitigated residual. Body chapters link by section;
> threat model is [§14](14-security-threat-model.md), with the code-verified threat catalog
> underlying the Critical/High tier at [§14.3](14-security-threat-model.md).

## A.0 Summary table

| # | Deviation | Severity | Body § | Status |
|---|---|---|---|---|
| C-1 | Mock proof system does not bind to the batch | **Critical** | [§9](09-proving-settlement.md) | devnet-only; forbid off-devnet |
| H-1 | Cross-chain inspector dispatches on any call scheme | **High** | [§4.6](04-evm-and-proxies.md) | unmitigated; needs scheme gate |
| H-2 | `SYSTEM_ADDRESS` key sprawl (signed legacy inbound tx) | **High** | [§4.4](04-evm-and-proxies.md), §16.6 | interim; 0x7E envelope is the fix |
| H-3 | Same-nonce bundle DoS / burned-nonce undetected | **High** | [§8.5.3](08-da-and-bundles.md), §14.3.1 | bounded, self-heals after 3 slots |
| H-4 | L1 deep-reorg (>62) halt, no automated recovery | **High** | [§8.7](08-da-and-bundles.md) | operator-intervention halt |
| H-5 | `getTimestampAndBlockHash` ABI/selector mismatch (no-arg vs `uint64`) breaks real-PS verify | **High** | [§9.6](09-proving-settlement.md) | fold matches Rust; resolver ABI must add `blockNumber` |
| M-1 | EIP-4844 blob DA unimplemented (calldata-only) | Medium | [§8.4](08-da-and-bundles.md) | reserved; `blobIndices` must be `[]` |
| M-2 | Ingress admission skipped when no `l1_provider` | Medium | [§8.5.3](08-da-and-bundles.md) | fail-open; needs fail-closed |
| M-3 | Fee recipient `Address::ZERO` (fees burned) | Medium | [§13](13-gas-economics.md) | placeholder; no operator revenue |
| M-4 | Cross-chain sub-call gas unmetered in simulation | Medium | [§6.6](06-execution-model.md), [§13](13-gas-economics.md) | sim-vs-on-chain divergence |
| M-5 | Overlay diff-apply drops code/nonce, fails on `SELFDESTRUCT` | Medium | [§6.7](06-execution-model.md) | partial; needs forbid-or-extend |
| M-6 | Mempool-fallback path loses bundle atomicity | Medium | [§8.5.2](08-da-and-bundles.md) | deployment constraint |
| M-7 | `observe()` has no timeout (stuck-Pending DoS) | Medium | [§8.6](08-da-and-bundles.md) | needs a ceiling verdict |
| M-8 | `reconcile_batch_blocks` non-transactional | Medium | [§12](12-derivation-following.md) | half-state on mid-loop failure |
| M-9 | `drain_matching` (external-composer case) not wired to `BatchPosted` | Medium | [§7.4](07-composer.md) | dormant in single-sequencer Rollup0 |
| M-10 | Genesis `chainId = 1` placeholder | Medium | [§5](05-block-production.md) | L2 chainId unpinned |
| L-1 | `prev_randao` hardcoded zero (PREVRANDAO predictable) | Low | [§5.5](05-block-production.md) | stage-1 placeholder |
| L-2 | Signature malleability (mitigated, residual) | Low | [§9](09-proving-settlement.md) | mitigated both sides |
| L-3 | `slot_number` always `None` | Low | [§5](05-block-production.md) | inactive on stage-1 chains |
| L-4 | Aggregator is scaffolding only | Low | [§8](08-da-and-bundles.md) | single-rollup today |
| L-5 | `build_batch` purity not runtime-asserted | Low | [§7](07-composer.md) | relies on `ChainProtocol` contract |
| L-6 | Witness path stubbed (Phase-2 zk) | Low | [§9](09-proving-settlement.md) | dead capacity, future |

---

## A.1 Critical

### C-1. The mock proof system does not bind to the batch

- **Spec requirement.** A batch's proof must cryptographically attest *that exact batch* —
  the `publicInputsHash` fold binds every entry hash, lookup hash, the `callData` hash, and
  the per-PS `(rollupId, vkey, blockHash, timestamp)` accumulator, and the verifier recovers a
  signature **over that hash** ([§9.1](09-proving-settlement.md), [§9.2](09-proving-settlement.md)).
- **Current behavior.** `MockECDSAProofSystem.verify` **ignores** `publicInputsHash` and
  recovers an ECDSA signature over the fixed constant `MOCK_PROVER_DIGEST =
  keccak256("eez-mock-prover")`; the Rust `MockEcdsaProver` signs exactly that constant. So
  **one** valid 65-byte signature over the fixed digest is accepted as a "proof" for **any**
  `postAndVerifyBatch` contents — arbitrary `stateDeltas`, `entries`, `callData`. Zero binding
  between proof and batch. The wired composer hardwires `proofSystems = [mock]` and
  `proofSystemIndex = [0]`, the only verification path Rollup0 exercises today. (`threshold` is
  **not** a composer batch field — it lives on-chain in the per-rollup manager
  `rollupContract/Rollup.sol`, enforced by `checkProofSystemsAndGetVkeys`.)
- **Evidence.** `contracts/src/MockECDSAProofSystem.sol:55-80` (ignores `publicInputsHash`,
  recovers fixed digest); `crates/eez-prover/src/lib.rs:101-114` (signs `MOCK_PROVER_DIGEST`);
  composer wiring `crates/eez-composer/src/composer.rs:1521-1527` (`proofSystems =
  [mock_proof_system_address]`, `rollupIdsWithProofSystems[0].proofSystemIndex = [0]`). The
  binding `ECDSAProofSystem.sol` **is present** in the checked-out submodule at
  `sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:17,29-32` — it recovers over the
  raw `publicInputsHash` (no EIP-191 prefix) and compares against the configured `signer`, i.e.
  it *does* bind proof to batch. `threshold` enforcement:
  `sync-rollups-protocol/src/rollupContract/Rollup.sol` (`checkProofSystemsAndGetVkeys` reverts
  below threshold).
- **Impact.** Mock-config proof verification provides **no** integrity guarantee; the stored
  `stateRoot` can be advanced to a wrong value by a single signature. Safety rests *entirely*
  on commit-then-repair (a follower re-derives from L1 and rejects a bad batch via the deriver's
  `check_claimed_state` → `LocalDiverged`), and that divergence is **terminal** (no auto-repair,
  see H-4 / M-8). Catastrophic beyond devnet.
- **Recommended fix.** Make it a **deploy-time invariant** that `MockECDSAProofSystem` is
  forbidden on any non-devnet `chainId` (fail-closed at startup). Mark mock proofs **non-normative**;
  require the binding `ECDSAProofSystem` (raw `publicInputsHash` recovery, no EIP-191 prefix) for
  any value-bearing deployment. Pin the Rollup0 validator set to the binding PS with the manager's
  `threshold = 1` single signer ([§9.1.2](09-proving-settlement.md)) — threshold is enforced
  on-chain by `Rollup.sol`, not in the composer's batch shape.

---

## A.2 High

### H-1. Cross-chain inspector dispatches on *any* call scheme

- **Spec requirement.** Only `CALL` may trigger a state-mutating cross-chain dispatch; a
  cross-chain `STATICCALL` must resolve as a read-only **lookup** (no mutation), and
  `DELEGATECALL`/`CALLCODE` to a proxy are forbidden — the 6-field source/target attribution is
  undefined under a borrowed storage context ([§4.6](04-evm-and-proxies.md),
  [§6.5](06-execution-model.md)).
- **Current behavior.** `SessionInspector::call` computes `inputs.scheme` but uses it **only**
  in a tracing log. On *every* `CALL` frame whose target is a registered `authorizedProxy` it
  builds an `ExecutionRequest` and dispatches via `Dispatcher::dispatch_call`, regardless of
  scheme. A contract that `STATICCALL`s a proxy thus initiates a state-mutating, value-bearing
  cross-chain dispatch from an EVM-guaranteed read-only context; `DELEGATECALL`/`CALLCODE` bind
  the proxy's cross-chain identity under the caller's storage, which is semantically undefined.
- **Evidence.** `crates/eez-evm-inspector/src/inspector.rs:489-540` (dispatch proceeds after
  proxy detection, no scheme gate); scheme consumed only in the `tracing::info!` at
  `crates/eez-evm-inspector/src/inspector.rs:693` (logged at `:526-531`). No `CallScheme` guard
  anywhere in `inspector.rs`.
- **Impact.** Cross-chain side effects (value movement, remote calls, `StateDelta` accrual) can
  be induced from a side-effect-free context, breaking EVM static-context guarantees and the
  "reads cannot mutate cross-chain state" assumption. Enables read-path-triggered value flows
  and sim-vs-on-chain desync. Dispatch soundness from non-`CALL` schemes is unspecified.
- **Recommended fix.** Gate dispatch on scheme: for `StaticCall`, route to the read-only
  `staticCallLookup` path (or synthesize a revert) — never dispatch a mutating call; explicitly
  reject `DelegateCall`/`CallCode` to a proxy. Specify that **only** `CallScheme::Call` may
  dispatch.

### H-2. `SYSTEM_ADDRESS` key sprawl — forge-able value-minting inbound delivery

- **Spec requirement.** Inbound cross-chain delivery should be a **deterministic, un-signed**
  type-`0x7E` envelope that any follower can reconstruct from L1 *without a private key*
  ([§4.4](04-evm-and-proxies.md), §16.6). On-chain, `executeIncomingCrossChainCall` mints
  exactly `value` (`msg.value == value`) — it is the L2 ETH-minting source
  ([§6.10](06-execution-model.md)).
- **Current behavior.** Inbound delivery is a **signed legacy** transaction from
  `SYSTEM_ADDRESS` (type-`0x7E` deferred), with `.value = outer.value`, so it mints L2 ETH.
  Both composer **and** deriver must hold the `SYSTEM_ADDRESS` private key to produce
  byte-identical txs (the deriver re-signs on replay). Anyone holding the key can sign an
  `executeIncomingCrossChainCall` delivering arbitrary value to an arbitrary L2 address,
  minting L2 ETH unbacked by any real L1 deposit/`StateDelta`.
- **Evidence.** `crates/eez-evm/src/system_tx.rs:14-18` (0x7E deferred), `:39-43` (signer must
  equal `SYSTEM_ADDRESS`), `:104-165` (`value = outer.value`, `sign_legacy_system_tx`);
  follower wires `system_tx_cfg = None` so it cannot even follow cross-chain batches
  (`crates/eez-follower/src/main.rs:91-110`). On-chain `msg.value == value` enforcement **is
  present** in the checked-out submodule at `sync-rollups-protocol/src/L2/EEZL2.sol:194`
  (`executeIncomingCrossChainCall` reverts `ValueMismatch` on any drift).
- **Impact.** Key compromise forges minting of L2 ETH and arbitrary inbound calls. The strict
  `msg.value == value` ties the minted amount to the entry but **not** to a genuine L1 lock.
  Key sprawl across composer + deriver widens the compromise surface; the safety backstop (L1
  re-derivation) itself requires the follower to hold the key, which the Rollup0 follower does
  not — so it fails the per-block hash check loudly instead of following.
- **Recommended fix.** Prioritize the type-`0x7E` system-tx envelope so the deriver reconstructs
  system txs without the key (removing key sprawl). Until then, keep `SYSTEM_ADDRESS` in an
  HSM/remote signer, never on follower nodes, and specify mint accounting (how `SYSTEM_ADDRESS`'s
  value is backed) as a normative conservation invariant cross-checked against
  `RollupConfig.etherBalance` / `StateDelta.etherDelta`.

### H-3. Same-nonce bundle DoS — a burned nonce on a different-hash tx goes undetected

- **Spec requirement.** A user L1 transaction that becomes invalid must not be able to stall
  *settlement*: burned nonces should be detected by **account state**, and the `postAndVerifyBatch` must
  be able to land **independently** of any user transaction that fails simulation
  ([§8.5.3](08-da-and-bundles.md); seed threat [§14.3.1](14-security-threat-model.md)).
- **Current behavior.** A held-pool cross-chain intent rides the same all-or-nothing bundle as
  `postAndVerifyBatch`. If the user (or colluder) lands a **same-nonce** L1 tx first, the held
  tx's nonce is burned and the bundle fails simulation forever. Recovery checks `receipt_exists`
  on the **held tx's own hash** — but the external tx has a *different* hash, so `receipt_exists`
  returns `false`, the burn goes **undetected**, the held tx is re-queued, and the same failing
  bundle is rebuilt next slot — repeating for `MAX_BUNDLE_ATTEMPTS = 3` slots before eviction.
- **Evidence.** ingress admit `crates/eez-node/src/ingress.rs:112-124,163-181`; held-pool drain
  `crates/eez-composer/src/composer.rs:589-605`; bundle assembly `:1224-1227`; all-or-nothing
  (empty `revertingTxHashes`/`droppingTxHashes`) `crates/eez-l1/src/submitter.rs:511-526`;
  `Dropped` verdict `:413-418`; recovery `receipt_exists`-on-own-hash
  `crates/eez-composer/src/composer.rs:803-846` (the gap); `MAX_BUNDLE_ATTEMPTS = 3` `:127,835`;
  eviction + nonce-cascade `:861-892`.
- **Impact.** For ~3 consecutive sync slots the rollup's `postAndVerifyBatch` cannot land: L1's
  stored `stateRoot` stops advancing while L2 cadence continues (empty Sync block committed
  unconditionally), so L2-vs-L1 diverge in time. Cheap (one L2 RPC submission + one L1 tx) and
  repeatable — a griefer holds L1 settlement hostage indefinitely paying only L1 base fees. A
  settlement/liveness DoS, **not** a permanent brick (self-heals per poison tx after 3 slots).
- **Recommended fix.** Detect a burned nonce by **account state**: at recovery (and ideally at
  compose time before bundling) read `get_transaction_count(sender)` and drop/replace any held
  tx whose nonce `< on_chain`. Better: **do not** bundle user L1 txs all-or-nothing with the
  `postAndVerifyBatch` — it carries the leading-immediate entry and must land independently; if a
  survivor sim-fails, drop it and still send `[postAndVerifyBatch]`. Classify nonce-too-low as
  deterministic poison and evict on the **first** drop, not the third.

### H-4. L1 deep reorg (>`reorg_max_depth = 62`) halts with no automated recovery

- **Spec requirement.** A reorg deeper than the ring halts with `ReorgTooDeep` and requires
  operator intervention; the body acknowledges *no automated deep-reorg recovery* and defers the
  in-flight-batch cleanup procedure to this appendix ([§8.7](08-da-and-bundles.md)).
- **Current behavior.** The `L1Watcher` keeps a `(number, hash)` ring bounded by
  `reorg_max_depth` (default **62**). A reorg deeper than the ring — or across a catch-up gap
  with no in-bounds common ancestor — **halts** with `L1Error::ReorgTooDeep`. Shallow reorgs are
  handled (cursor retreat + `reorg_to`), but on a deep-reorg halt the behavior of in-flight
  `Pending` optimistic batches and the cursor is **unspecified**. Separately, the deriver's
  `reconcile_batch_blocks` is non-transactional (see M-8).
- **Evidence.** `crates/eez-l1/src/l1_watcher.rs:9-12,127-131` (`ReorgTooDeep` halt),
  `:333-428` (catch-up-gap reseed path); shallow retreat
  `crates/eez-deriver/src/deriver.rs:901-966`. Deep-reorg in-flight cleanup: no code path
  (design-level gap).
- **Impact.** Derivation/composition stalls (liveness) on a deep reorg; in-flight optimistic
  Sync blocks may have anchored against rolled-out batches with no defined cleanup. A
  shallowly-reorged-out settled batch is handled by commit-then-repair; the deep case is an
  operator-intervention halt with an undefined recovery state.
- **Recommended fix.** Define a normative deep-reorg recovery procedure: on `ReorgTooDeep`,
  quiesce production, drop all `Pending`/`Settled` optimistic entries above the new common
  ancestor, re-derive from genesis or the deploy block, and gate restart on operator ack. (Make
  `reconcile_batch_blocks` transactional — see M-8.)

### H-5. `getTimestampAndBlockHash` ABI/selector mismatch — Rust resolver omits the `blockNumber` arg

- **Spec requirement.** The normative Rollup0 `publicInputsHash` fold places `(blockHash,
  timestamp)` **in the per-PS accumulator** alongside `(rollupId, vkey)`, read via
  `getTimestampAndBlockHash(uint64 blockNumber)`; the shared input is `H(entryHashes,
  lookupCallHashes, blobHashes, H(callData), crossProofSystemInteractions)` with
  `crossProofSystemInteractions = bytes32(0)` in single-PS Rollup0
  ([§9.2.4](09-proving-settlement.md), [§9.6](09-proving-settlement.md)).
- **Current behavior.** The deployed fold **matches** the Rust: the checked-out
  `sync-rollups-protocol/src/EEZ.sol` per-PS fold of `(acc, rollupId, vkey, blockHash,
  timestamp)` (with the shared input above) is mirrored byte-for-byte by Rollup0's
  `crates/eez-evm/src/public_inputs.rs` — the residual is a **CI byte-equality obligation**, not
  an unverifiable gap. **The real divergence** is the resolver's ABI: the Rust
  `EvmProofPlanResolver` declares `getTimestampAndBlockHash()` as a **no-arg** view, but the
  deployed interface and impl require `getTimestampAndBlockHash(uint64 blockNumber)`, and
  `EEZ.sol` invokes it with `batch.blockNumber`. A no-arg call computes a **different 4-byte
  selector** than the on-chain one, so the resolver's read would not match the deployed function
  — and the binding (real-PS / ECDSA) verification path depending on the fetched `(timestamp,
  blockHash)` would fail. (Separately, a *sibling* tree at `/root/projects/eez/eez-core-protocol`
  carries a **divergent, not-yet-deployed** `customDataAcc` fold — a future design line, **not**
  the deployed contract; not authoritative for Rollup0.)
- **Evidence.** Deployed/Rust fold match: `sync-rollups-protocol/src/EEZ.sol:553-627` ⇕
  `crates/eez-evm/src/public_inputs.rs:194-218` (per-PS fold) and `:120-137` (shared input).
  ABI mismatch: resolver `crates/eez-evm/src/proof_plan.rs:81-85` declares
  `getTimestampAndBlockHash()` (no args), whereas the deployed interface requires
  `getTimestampAndBlockHash(uint64 blockNumber)`
  (`sync-rollups-protocol/src/interfaces/IRollup.sol:37`,
  `sync-rollups-protocol/src/rollupContract/Rollup.sol:133`) and `EEZ.sol:607-609` calls it with
  `batch.blockNumber`. The divergent non-deployed line is
  `/root/projects/eez/eez-core-protocol/src/EEZ.sol` (`customDataAcc` shape).
- **Impact.** A no-arg ABI selector will **not** match the on-chain selector, so once the
  binding `ECDSAProofSystem` replaces the mock, the per-rollup `(timestamp, blockHash)` read the
  fold depends on cannot be performed against the deployed contract and **real settlement
  verification breaks**. A concrete byte/ABI incompatibility on the real-PS path (the mock path
  masks it today by ignoring `publicInputsHash` — see C-1).
- **Recommended fix.** Change the resolver's `IRollupReader.getTimestampAndBlockHash` to take
  `uint64 blockNumber` and pass `batch.blockNumber`, matching the deployed selector. Assert at
  **CI** that resolver ABI selectors equal the deployed `IRollup` selectors, and that the
  `EEZ.sol` fold matches `public_inputs.rs` byte-for-byte against the Foundry vectors. Keep the
  divergent `customDataAcc` shape (`eez-core-protocol` sibling) out of Rollup0 until finalized
  as a versioned upgrade.

---

## A.3 Medium

### M-1. EIP-4844 blob DA entirely unimplemented (calldata-only)

- **Spec requirement.** Blobs are the default DA channel, calldata used when cheaper, with the
  chosen channel bound into the proof's public inputs via `blobHashes[i] =
  blobhash(blobIndices[i])` ([§8.4](08-da-and-bundles.md)).
- **Current behavior.** Only `TAG_CALLDATA = 0x00` exists. The submitter **hard-rejects** any
  non-empty `blobIndices` with `UnsupportedBlobIndices` (the off-chain fold would hash an empty
  `blob_hashes` slice and mismatch the on-chain `blobhash` fold). No KZG/sidecar/4844-tx
  construction and no blob-vs-calldata cost comparator.
- **Evidence.** `crates/eez-evm-inspector/src/post_batch_submitter.rs:154-168,354-363`
  (`UnsupportedBlobIndices` reject); `crates/eez-payload-codec/src/lib.rs:44-48` (only tag
  `0x00`). DA-fee oracle: absent (design-level).
- **Impact.** All DA rides L1 calldata, bearing full calldata cost on the operator EOA with no
  L2-side reimbursement (see M-3); under high L1 base fee the operator may stop posting
  (liveness). The reserved second tag is undefined — a forward-compat hole. No data-withholding
  risk on calldata (fully public on L1).
- **Recommended fix.** Specify the blob payload framing (tag-byte assignment, RLP-body reuse vs
  field-element packing), the `blobIndices → blob` binding (one blob per batch / per block /
  fold), the off-chain `blobhash` resolution mirroring the on-chain walk, and the cost
  comparator (`blob_gas × blob_bytes` vs `calldata_gas × 16/byte`). `blobIndices` **must remain
  `[]`** until shipped.

### M-2. Ingress admission skipped when no `l1_provider` is wired

- **Spec requirement.** Cross-chain intents must pass nonce-contiguity and L1-balance admission
  before entering the held pool, so poison cannot ride the all-or-nothing bundle
  ([§8.5.3](08-da-and-bundles.md), [§14.3.1](14-security-threat-model.md)).
- **Current behavior.** The nonce/balance checks run only inside `if let Some(provider) =
  l1_provider.as_ref()`. If `l1_provider` is `None`, a cross-chain tx is pushed to the held pool
  with **no** validation (the push runs unconditionally). The deployment condition under which
  `l1_provider` is `None` is unbounded.
- **Evidence.** `crates/eez-node/src/ingress.rs:162-202` (validation gated on `Some(provider)`),
  `:209-225` (push runs regardless).
- **Impact.** Unvalidated cross-chain txs (bad nonce, insufficient balance) enter the held pool
  and ride the bundle, failing builder sim and evicting innocent bundle-mates — the exact
  poison-pill + nonce-cascade the admission check prevents. Amplifies H-3 (first line of defense
  absent).
- **Recommended fix.** Make `l1_provider` **mandatory** for any deployment that admits
  cross-chain txs (fail-closed at startup if absent), or refuse to admit `CrossChain`
  classifications when no provider is available. An `l1_provider`-less composer is not a valid
  Rollup0 cross-chain deployment.

### M-3. L2 fee recipient is `Address::ZERO` — fees burned, no DA-cost recovery

- **Spec requirement.** The body pins a fee recipient and an economic model that recovers L1 DA
  cost ([§13](13-gas-economics.md)).
- **Current behavior.** `suggested_fee_recipient` is hard-coded `Address::ZERO` on every
  production path; `with_fee_recipient` exists but is never wired. All L2 priority and base-fee
  revenue accrue to `0x0` (lost). No OP-stack-style L1 fee oracle / L1-data-fee component, so no
  L2 user is charged L1 DA cost and the operator absorbs the full posting cost.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:479`,
  `crates/eez-composer/src/composer.rs:522`, `crates/eez-driver/src/sequencer.rs:118`; genesis
  coinbase `0x0` (`genesis.json:27`); operator-absorbed posting cost
  `crates/eez-composer/src/composer.rs:1801-1809`.
- **Impact.** No sequencer revenue / fee-market capture and no income against real L1/L2 costs —
  the centralized operator's economic sustainability is unspecified. Under sustained L1 base fee
  the operator may stop posting (liveness, not safety).
- **Recommended fix.** Decide and pin the L2 fee recipient (operator/treasury vs deliberate
  burn) and wire `with_fee_recipient`. Specify who pays L1 DA cost in production (an L2 user-
  facing L1-data-fee vs operator-absorbed liveness cost).

### M-4. Cross-chain sub-call gas unmetered in off-chain simulation

- **Spec requirement.** Off-chain simulation must match on-chain `postAndVerifyBatch` replay; cross-chain
  sub-calls have a defined gas budget so simulated and on-chain costs agree
  ([§6.6](06-execution-model.md), [§13](13-gas-economics.md)).
- **Current behavior.** The synthesized cross-chain `CallOutcome` always passes
  `Gas::new(inputs.gas_limit)`; the target's `gas_used` is **logged but not deducted** from the
  caller frame. The composer's CCM-verify session further disables the block gas limit and sets
  `tx_gas_limit_cap = u64::MAX`. So a cross-chain sub-call costs the caller **nothing** in
  simulation, while on-chain replay runs the metered `_processNCalls` loop. The deviation is the
  **off-chain composer** not metering sub-call gas against the caller frame — not an on-chain
  gap: `_processNCalls` **is present** on both submodule sides
  (`sync-rollups-protocol/src/L2/EEZL2.sol:343`, `sync-rollups-protocol/src/EEZ.sol:920`).
- **Evidence.** `crates/eez-evm-inspector/src/inspector.rs:677-680,716-719` (unmetered
  outcome); sim relaxation `crates/eez-composer/src/local/session.rs:613-620`; on-chain metering
  `sync-rollups-protocol/src/EEZL2.sol:343` / `sync-rollups-protocol/src/EEZ.sol:920`
  (`_processNCalls`). Note `EXECUTE_INCOMING_GAS_LIMIT` (~2M) is an **off-chain** Rust
  system-tx gas budget (`crates/eez-composer/src/composer.rs:66`,
  `crates/eez-evm/src/system_tx.rs:52`), **not** an on-chain metering constant — it does not
  exist in the submodule.
- **Impact.** A batch that simulated clean can revert/out-of-gas on L1 (bundle drop, settlement
  stall), and an attacker can craft cheap-in-sim, expensive-on-chain compositions (griefing the
  operator's posting cost). The off-chain `4M POST_BATCH_GAS_LIMIT`
  (`crates/eez-composer/src/composer.rs:1809`) caps the L1 tx, but the off-chain-vs-on-chain
  sub-call budget mismatch is real.
- **Recommended fix.** Meter cross-chain sub-call gas in the off-chain composer against the
  caller frame so simulation matches on-chain replay; define a normative cross-chain sub-call
  gas budget; classify gas-divergence sim failures as deterministic poison and evict before
  bundling.

### M-5. Overlay diff-apply drops code-install + nonce changes; fails on `SELFDESTRUCT`

- **Spec requirement.** A nested cross-chain call's state effects must be applied identically
  off-chain and on-chain, including code installation, nonce bumps, and (where supported)
  `SELFDESTRUCT` ([§6.7](06-execution-model.md)).
- **Current behavior.** The overlay diff-apply for nested cross-chain dispatch applies **only**
  storage writes and balance changes; code installation and nonce changes are silently
  *deferred*/skipped, transient storage is ignored, and `SELFDESTRUCT` raises a loud
  `OverlayError::Selfdestruct`. A nested call deploying a contract or bumping a nonce
  mis-simulates vs on-chain; one that selfdestructs cannot compose. Relatedly, `build_batch`
  panics (`unimplemented!`) when a rollup both originates and receives traffic in one
  composition (nested re-entry L1→L2→L1).
- **Evidence.** `crates/eez-evm-inspector/src/overlay.rs:93-101,168-194,204-215`; nested-reentry
  panic `crates/eez-evm/src/entries/mod.rs:114-128`.
- **Impact.** Off-chain composition can diverge from on-chain re-derivation for these mutation
  classes, breaking the commit-then-repair guarantee (surfaced only later as a `LocalDiverged`
  halt). `SELFDESTRUCT`-bearing and nested-reentry cross-chain flows are unsupported.
- **Recommended fix.** Either extend the overlay to handle code-install + nonce changes (and
  define transient-storage semantics), or normatively **forbid** cross-chain nested calls that
  deploy code / change nonces / selfdestruct and **reject** them at compose time rather than
  mis-simulating. Implement or explicitly forbid nested-reentry compositions instead of panicking.

### M-6. Mempool-fallback path loses bundle atomicity

- **Spec requirement.** The L1 bundle is strictly all-or-nothing; a deployment whose relay lacks
  `eth_sendBundle` has **no** atomic-bundle guarantee — a deployment constraint, not a fallback
  to rely on ([§8.5.2](08-da-and-bundles.md)).
- **Current behavior.** If the relay returns `-32601` (no `eth_sendBundle`), the submitter
  degrades to ordered `eth_sendRawTransaction` mempool submission (`postAndVerifyBatch` first),
  which **loses atomicity**: the `postAndVerifyBatch` can land without a user tx or vice versa,
  reintroducing the partial-inclusion desync risk.
- **Evidence.** `crates/eez-l1/src/submitter.rs:296-365`.
- **Impact.** On the fallback path the §8.5.2 atomicity guarantee does not hold; a partial land
  can advance L1 to a mid-chain prefix root and desync the composer.
- **Recommended fix.** State normatively that a relay without `eth_sendBundle` is not a valid
  atomic-bundle Rollup0 deployment; gate cross-chain settlement on bundle support (fail-closed),
  or restrict the fallback to dev/anvil only.

### M-7. `observe()` has no timeout — stuck-`Pending` DoS

- **Spec requirement.** A settlement verdict is `Dropped` only when `head > target_block`
  ("provably dead"), never a wall-clock timeout — but the body flags the residual that a
  permanently-unreachable target-tip RPC loops without a verdict ([§8.6](08-da-and-bundles.md)).
- **Current behavior.** `observe()` loops indefinitely on transient RPC errors; only
  `head > target` ends it. A permanently-unreachable target-tip provider leaves the bundle
  observation — and the composer's optimistic gate — stuck `Pending` with no escape.
- **Evidence.** `crates/eez-l1/src/submitter.rs:391-452`.
- **Impact.** A permanently-unreachable target-tip RPC freezes the composer's one-in-flight gate
  (`Pending` forever), halting settlement progress without a verdict.
- **Recommended fix.** Add a hard upper bound (max blocks polled or wall-clock ceiling) that
  produces an explicit operator-actionable verdict (e.g. `Unknown`/`Stalled`) rather than
  spinning, without reintroducing the false-death risk that strict `head > target` avoids.

### M-8. `reconcile_batch_blocks` is non-transactional

- **Spec requirement.** Re-derivation of a batch's L2 blocks must be all-or-nothing: a replay
  failure must not leave local L2 in a half-applied state ([§12](12-derivation-following.md)).
- **Current behavior.** `reconcile_batch_blocks` is explicitly **not** transactional — a replay
  failing partway leaves earlier blocks committed to reth's canonical chain (a half-state).
  Rollback-to-pre-loop-snapshot is an open item.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:1032-1037`.
- **Impact.** A mid-loop failure advances local L2 partway onto new ancestry with no snapshot
  rollback; recovery relies on `recovery_resync` re-anchoring on the next L1 event.
- **Recommended fix.** Make it transactional: snapshot the canonical head pre-loop and roll back
  on any per-block failure.

### M-9. `drain_matching` (external-composer case) not wired to `BatchPosted`

- **Spec requirement.** When an external composer's batch consumes our held txs, the held pool
  must `drain_matching` the consumed tx-hash set (the external-composer case; [§7.4](07-composer.md), [§7.8](07-composer.md)).
- **Current behavior.** `HeldPool::drain_matching` exists, but `on_l1_event` only **logs** an
  external `BatchPosted`; the `consumed` tx-hash set is never computed or plumbed. `BatchPosted`
  lacks a `rollup_id` field and carries no consumed-tx list.
- **Evidence.** `crates/eez-composer/src/composer.rs:291-335` (logs only);
  `crates/eez-composer/src/held_pool.rs:159-187` (`drain_matching` unwired).
- **Impact.** Dormant in single-sequencer Rollup0 (no external composer sequences our chain), so
  no live exposure today; becomes load-bearing the moment a second sequencer exists.
- **Recommended fix.** Add a `rollup_id` (and ideally a consumed-tx commitment) to `BatchPosted`
  and wire the consumed set into `drain_matching`, or state explicitly that case-c is
  out-of-scope while Rollup0 is single-sequencer.

### M-10. Genesis `chainId = 1` placeholder

- **Spec requirement.** The authoritative L2 `chainId` for the Chiado-anchored deployment must
  be pinned, with a defined EIP-155 replay-protection story across L1/L2 ([§5](05-block-production.md)).
- **Current behavior.** `genesis.json` sets `chainId = 1` (Ethereum mainnet id); runtime uses
  `chain_spec.chain().id()`. How `chainId = 1` is overridden at deploy time, and the
  authoritative Rollup0 L2 chainId, are unpinned — a replay/EIP-155 ambiguity.
- **Evidence.** `genesis.json:3`; `crates/eez-node/src/main.rs:630,788`.
- **Impact.** Ambiguous replay protection; a placeholder mainnet chainId in genesis is a
  foot-gun for cross-chain tx routing and signature domain separation.
- **Recommended fix.** Pin the authoritative L2 chainId in genesis (not `1`) and document the
  EIP-155 domain for L1↔L2 transactions.

---

## A.4 Low

### L-1. `prev_randao` hardcoded zero — PREVRANDAO predictable

- **Spec requirement.** `prev_randao` (mixHash) is L1-derived; this is the stage-1 placeholder,
  with L1-derivation deferred ([§5.5](05-block-production.md)).
- **Current behavior.** `prev_randao` is hardcoded `B256::ZERO` in all three STF paths
  (Sequencer, Deriver, Sync-block composer). Any L2 contract reading `block.prevrandao`/
  `DIFFICULTY` observes constant zero, so any PREVRANDAO-seeded RNG/lottery/commit-reveal is
  fully predictable. All three paths must agree byte-for-byte or block hashes diverge.
- **Evidence.** `crates/eez-driver/src/sequencer.rs:145-147`,
  `crates/eez-deriver/src/deriver.rs:480`, `crates/eez-composer/src/local/build.rs:92-103`.
- **Impact.** Application-layer randomness is gameable. Not a protocol-state-safety issue (state
  still re-derives deterministically), but a divergence risk if the value ever becomes non-zero
  without all three paths agreeing.
- **Recommended fix.** Either fix `prev_randao = 0` as a **permanent** normative Rollup0 choice
  and warn app developers that PREVRANDAO is unusable for randomness, or implement the §5.5
  L1-derivation (which L1 field, at which L1 block, constant-per-sync-slot vs per-block) bound
  identically across all three paths.

### L-2. Signature malleability (mitigated, residual)

- **Spec requirement.** Low-`s` + `v ∈ {27,28}` should be a normative requirement for every
  `IProofSystem` verifier ([§9](09-proving-settlement.md)).
- **Current behavior.** Proof signatures are 65-byte `(r, s, v)`. The Rust `EcdsaProofSigner`
  normalizes to low-`s` and `v = 27 + recid`, refusing `recid > 1`; the mock's bare `ecrecover`
  returns `address(0)` on malformed inputs, rejected by the non-zero-signer check. Risk is
  residual only if a future custom verifier omits the checks.
- **Evidence.** `crates/eez-evm/src/signer.rs:132-179`;
  `contracts/src/MockECDSAProofSystem.sol:75-79`. The binding
  `sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:29-32` uses OZ `ECDSA.recover`
  (which rejects high-`s`) over the raw `publicInputsHash` and compares against `signer`; note
  it does **not** normalize `v` (must be 27/28 — see its dev comment at `:13-15`), so the caller
  must supply canonical `v`, which the Rust signer already does.
- **Impact.** Minimal in current code — both Rust signer and on-chain checks reject
  non-canonical signatures.
- **Recommended fix.** Make low-`s` + `v ∈ {27,28}` a normative conformance requirement for
  every new proof-system contract, and document the exact signed digest (raw `publicInputsHash`,
  no EIP-191) as authoritative.

### L-3. `slot_number` always `None`

- **Spec requirement.** The header `slot_number` (Amsterdam EIP) behavior must be defined for
  chains where Amsterdam is active ([§5](05-block-production.md)).
- **Current behavior.** `slot_number` is always `None` ("not active for stage-1 dev chains");
  behavior on an Amsterdam-active chain is unspecified.
- **Evidence.** `crates/eez-driver/src/sequencer.rs:158-159`.
- **Impact.** None today (Amsterdam inactive); a forward-compat hole.
- **Recommended fix.** Specify the `slot_number` value once Amsterdam is in scope, bound
  identically across sequencer/deriver/composer.

### L-4. Aggregator is scaffolding only

- **Spec requirement.** Multi-rollup window assembly (how N rollups' batches combine into one L1
  bundle, `OnTerminal`/`OnTerminalOrAfter` trigger semantics) is part of the multi-rollup design
  ([§8](08-da-and-bundles.md)).
- **Current behavior.** The `SubmitTrigger` enum exists but the `Aggregator` struct does not;
  multi-rollup assembly and trigger semantics are unspecified for Rollup0.
- **Evidence.** `crates/eez-l1/src/aggregator.rs:1-34`.
- **Impact.** None today (single-rollup Rollup0); blocks multi-rollup until implemented.
- **Recommended fix.** Defer formally to the multi-rollup phase; specify the trigger semantics
  before a second rollup is added.

### L-5. `build_batch` purity not runtime-asserted

- **Spec requirement.** `group_calls_for` + `build_batch` run twice (CCM-verify then emission)
  and must be **pure** — the two batches byte-identical — per the `ChainProtocol` contract
  ([§7](07-composer.md)).
- **Current behavior.** No runtime assertion that the CCM-verified batch and the emitted batch
  are byte-identical; correctness relies on the purity contract. A non-pure impl would silently
  desync CCM-verified roots from emitted roots.
- **Evidence.** `crates/eez-protocol/src/composition.rs:498-688`;
  `crates/eez-protocol/src/protocol.rs:58-71`.
- **Impact.** Latent silent-desync risk if a protocol impl is non-pure; not exploitable with the
  current single impl.
- **Recommended fix.** Add a debug/CI assertion that the two `build_batch` outputs hash equal.

### L-6. Witness path stubbed (Phase-2 zk)

- **Spec requirement.** A witness format for the future zk/validator-set proving path
  ([§9](09-proving-settlement.md)).
- **Current behavior.** `ExecutionCheckpoint.witness` is always `None` outside a Phase-2
  `WitnessRecordingDB` build; `EvmWitness` is a placeholder. The zk path is future; the
  checkpoint type carries dead capacity — consistent with "Rollup0 ≠ zk."
- **Evidence.** `crates/eez-protocol/src/checkpoint.rs:31-37`; `crates/eez-evm/src/lib.rs:15,82`.
- **Impact.** None today (no zk path in Rollup0).
- **Recommended fix.** Define the witness format when the zk/validator proving path is scoped;
  until then, document the field as reserved.

---

*Next: [Appendix B — Constants, Formulae & Glossary](B1-reference.md).*
