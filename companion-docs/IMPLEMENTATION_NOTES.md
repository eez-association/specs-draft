# Appendix A. Implementation Deviations

> **How to read this appendix.** The EEZ and network specifications under `docs/` identify their
> normative requirements. **This companion appendix is not normative.** It ranks every place
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
> threat model is [§14](threat-model.md), with the code-verified threat catalog
> underlying the Critical/High tier at [§14.3](threat-model.md).

## A.0 Summary table

| # | Deviation | Severity | Body § | Status |
|---|---|---|---|---|
| C-1 | Mock proof system does not bind to the batch | **Critical** | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | devnet-only; forbid off-devnet |
| H-1 | Cross-chain inspector dispatches on any call scheme | **High** | [EEZ Framework §3 — EVM Binding](../docs/eez-protocol-spec/03-evm-binding.md) | unmitigated; needs scheme gate |
| H-2 | `SYSTEM_ADDRESS` key sprawl (signed legacy system txs) | **High** | [Rollup0 Appendix C — System Transactions](../docs/rollup0-network-spec/C-system-transactions.md) | active v0; shared-key custody risk |
| H-3 | Same-nonce bundle DoS / burned-nonce undetected | **High** | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md), §14.3.1 | bounded, self-heals after 3 slots |
| H-4 | L1 deep-reorg (>62) halt, no automated recovery | **High** | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | operator-intervention halt |
| H-5 | `getTimestampAndBlockHash` ABI/selector mismatch (no-arg vs `uint64`) breaks real-PS verify | **High** | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | fold matches Rust; resolver ABI must add `blockNumber` |
| H-6 | Live batches retain the zero L1-context sentinel | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | release blocker; bind a recent host block |
| H-7 | Deriver fast path does not validate full reconstructed headers | **High** | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | release blocker; compare sealed header and body |
| H-8 | Nested outbound ETH is omitted from entry accounting | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | reject reachable nested value flow until fixed |
| H-9 | Deriver attributes applied roots by per-block set membership | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | preserve exact receipt and log order |
| M-1 | Calldata-only v0 DA; follower omits the empty-`blobIndices` guard | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | producer enforced; follower guard required |
| M-2 | Ingress admission skipped when no `l1_provider` | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | fail-open; needs fail-closed |
| M-3 | Zero beneficiary; operator/system-account funded fees | Medium | [Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md) | accepted v0 economics; no operator revenue |
| M-4 | Cross-chain sub-call gas unmetered in simulation | Medium | [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md), [Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md) | sim-vs-on-chain divergence |
| M-5 | Overlay diff-apply drops code/nonce, fails on `SELFDESTRUCT` | Medium | [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md) | partial; needs forbid-or-extend |
| M-6 | Mempool-fallback path loses bundle atomicity | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | deployment constraint |
| M-7 | `observe()` has no timeout (stuck-Pending DoS) | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | needs a ceiling verdict |
| M-8 | `reconcile_batch_blocks` non-transactional | Medium | [Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md) | half-state on mid-loop failure |
| M-9 | `drain_matching` (external-composer case) not wired to `BatchPosted` | Medium | [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) | dormant in single-sequencer Rollup0 |
| M-10 | Genesis `chainId = 1` placeholder | Medium | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | L2 chainId unpinned |
| M-11 | Exact bundle target is not post-validated from canonical inclusion | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | request pins; observer does not verify |
| M-12 | Empty DA block range is accepted as a no-op | Medium | [Rollup0 Appendix B — DA Codec](../docs/rollup0-network-spec/B-da-codec.md) | reject non-positive range |
| L-1 | `prev_randao` hardcoded zero (PREVRANDAO predictable) | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | stage-1 placeholder |
| L-2 | Signature malleability (mitigated, residual) | Low | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | mitigated both sides |
| L-3 | `slot_number` always `None` | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | inactive on stage-1 chains |
| L-4 | Aggregator is scaffolding only | Low | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | single-rollup today |
| L-5 | `build_batch` purity not runtime-asserted | Low | [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) | relies on `ChainProtocol` contract |
| L-6 | Witness path stubbed (Phase-2 zk) | Low | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | dead capacity, future |
| L-7 | Scheduler/header timestamp arithmetic is not checked | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | boundary conformance hardening |

---

## A.1 Critical

### C-1. The mock proof system does not bind to the batch

- **Spec requirement.** A batch's proof must cryptographically attest *that exact batch* —
  the `publicInputsHash` fold binds every entry hash, lookup hash, the `callData` hash, and
  the per-PS `(rollupId, vkey, blockHash, timestamp)` accumulator, and the verifier recovers a
  signature **over that hash** ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md), [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
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
  `threshold = 1` single signer ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)) — threshold is enforced
  on-chain by `Rollup.sol`, not in the composer's batch shape.

---

## A.2 High

### H-1. Cross-chain inspector dispatches on *any* call scheme

- **Spec requirement.** Only `CALL` may trigger a state-mutating cross-chain dispatch; a
  cross-chain `STATICCALL` must resolve as a read-only **lookup** (no mutation), and
  `DELEGATECALL`/`CALLCODE` to a proxy are forbidden — the 6-field source/target attribution is
  undefined under a borrowed storage context ([EEZ Framework §3 — EVM Binding](../docs/eez-protocol-spec/03-evm-binding.md),
  [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md)).
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

### H-2. `SYSTEM_ADDRESS` key sprawl permits forged signed system operations

- **Normative v0 rule.** The outbound `loadExecutionTable` and inbound
  `executeIncomingCrossChainCall` operations are deterministic EIP-155-signed legacy
  transactions. The load has zero envelope value. Inbound value is debited from the prefunded
  `SYSTEM_ADDRESS`; `msg.value == value` does not mint value
  ([Rollup0 Appendix C](../docs/rollup0-network-spec/C-system-transactions.md)).
- **Current behavior.** The composer and every cross-chain deriver must hold the same private key
  to produce byte-identical transaction bytes. Anyone holding the key can authorize forged table
  loads or inbound calls. Because the key controls an ordinary prefunded EOA, it can also sign
  arbitrary transfers of that account's existing balance.
- **Evidence.** `crates/eez-evm/src/system_tx.rs` defines the shared `SystemTxContext`,
  `build_cross_chain_sync_pairs`, both calldata builders, and `sign_legacy_system_tx`; the deriver
  calls the same canonical pair builder. `EEZL2` at
  `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` restricts both functions to
  `SYSTEM_ADDRESS` and enforces inbound `msg.value == value`.
- **Impact.** Key compromise forges arbitrary system operations and drains or reallocates the
  prefunded reserve. The inbound equality check ties the transferred amount to calldata but not to
  a genuine L1 lock. A node without the configured key cannot reproduce a cross-chain Sync block
  and must halt instead of substituting bytes.
- **Recommended fix.** Design and fully specify a key-free envelope before assigning any new
  transaction type. Under signed-legacy v0, tightly control the necessarily shared key and enforce
  prefunded-reserve backing against `RollupConfig.etherBalance` and
  `StateDelta.etherDelta`.

### H-3. Same-nonce bundle DoS — a burned nonce on a different-hash tx goes undetected

- **Spec requirement.** A user L1 transaction that becomes invalid must not be able to stall
  *settlement*: burned nonces should be detected by **account state**, and the `postAndVerifyBatch` must
  be able to land **independently** of any user transaction that fails simulation
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md); seed threat [§14.3.1](threat-model.md)).
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
  in-flight-batch cleanup procedure to this appendix ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
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
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md), [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
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

### H-6. Live batches retain the zero L1-context sentinel

- **Spec requirement.** A production batch binds a recent canonical host block N with
  `0 < N < type(uint64).max`. The manager and posting paths reject sentinel values so a reorg or
  expired block hash fails closed
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** The explicit resolver path can fold `(blockNumber, l1BlockHash)`, but the
  live builder does not supply that pair. Builders initialize `blockNumber = 0`,
  `prepare_post_batch_raw` does not replace it, and the reference manager maps zero to
  `(timestamp, blockHash) = (0, 0)`.
- **Evidence.** Defaults and entry constructors:
  `crates/eez-evm/src/batch.rs:54` and
  `crates/eez-evm/src/entries/mod.rs:235,354,630,747,793,884`; live preparation:
  `crates/eez-composer/src/composer.rs:1693-1930`; manager sentinel behavior:
  `sync-rollups-protocol/src/rollupContract/Rollup.sol:131-149`.
- **Impact.** The signed digest is not bound to the observed host-chain context that schedules
  settlement. A binding proof system would authenticate this timeless digest rather than repair
  the missing domain.
- **Recommended fix.** Reject zero and `type(uint64).max`; choose and validate N before proof
  construction; assign it to the exact posted batch; and rebuild after a reorg or expiry.

### H-7. Deriver fast path does not validate full reconstructed headers

- **Spec requirement.** A deriver reconstructs every execution-header field and the body. It may
  reuse a local block only when the complete sealed header and body match
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md),
  [Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)).
- **Current behavior.** `local_block_matches` compares only EIP-2718 transaction bytes, and
  `local_batch_boundary_matches` checks only the first parent hash. Matching transactions skip
  replay, while the final state-root check does not authenticate intermediate header fields.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:1242-1288,1439-1496`.
- **Impact.** Clients can agree on transactions and final state while retaining different
  intermediate headers and hashes.
- **Recommended fix.** Build and compare the complete expected sealed block for every range
  element, or replay unconditionally. Combine this with transactional range rollback (M-8).

### H-8. Nested outbound ETH is omitted from entry accounting

- **Spec requirement.** Entry accounting includes every successful value transfer at every
  nesting depth and preserves `address(EEZ).balance >= sum(rollups[r].etherBalance)`
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** `_applyAndExecute` records the value returned by its outer
  `_processNCalls`, but `_consumeNestedAction` discards the recursive return. A nested successful
  value transfer can reduce physical custody without entering the total checked against
  `StateDelta.etherDelta`.
- **Evidence.** Nested return discarded at
  `sync-rollups-protocol/src/EEZ.sol:769-785`; outer-only comparison at `:890-908`;
  local accumulator at `:914-942`.
- **Impact.** The implemented equation can pass while aggregate custody is under-backed. The
  current deposit-only shape may narrow reachability, but the selected contract exposes nested
  value-bearing entries.
- **Recommended fix.** Add entry-scoped, revert-safe value accounting across nested frames.
  Until fixed, validators and posting paths must reject all nested value-bearing entries.

### H-9. Deriver attributes applied roots by per-block set membership

- **Spec requirement.** Partial-settlement repair preserves receipt and log order, associates
  each delta with its exact batch and entry, and retains duplicate-root multiplicity
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** The scanner stores `L2ExecutionPerformed.newState` values in per-block
  `HashSet`s. Each batch in the block reuses that set, and `attribute_settlement` selects the
  deepest claimed root by membership. This discards order, multiplicity, and batch identity.
- **Evidence.** `crates/eez-l1/src/scan.rs:136-205,236-260`;
  `crates/eez-deriver/src/deriver.rs:1092-1098,1151-1168`.
- **Impact.** Multiple batches, duplicate roots, or non-prefix skips can be misattributed as an
  applied prefix, even when later state-root replay cannot authenticate the exact system
  transaction and receipt history.
- **Recommended fix.** Preserve ordered logs with transaction and log indices, count events
  rather than unique roots, and reject ambiguous or non-prefix patterns. If current events cannot
  identify batches exactly, constrain the profile to one batch per rollup per host block.

---

## A.3 Medium

### M-1. Calldata-only v0 DA; follower still needs the empty-`blobIndices` guard

- **Spec profile.** Tag `0x00` calldata is the only v0 DA channel and `blobIndices` must be empty
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** The producer rejects non-empty `blobIndices`, but the scanner forwards
  only `callData` and raw transaction input. Live and catch-up derivers decode `callData` without
  checking the omitted field.
- **Evidence.** Producer guard:
  `crates/eez-evm-inspector/src/post_batch_submitter.rs:154-168,354-363`; scanner:
  `crates/eez-l1/src/scan.rs:185-203`; deriver:
  `crates/eez-deriver/src/deriver.rs:297,688-752`.
- **Impact.** A landed generic-contract batch with valid tag `0x00` calldata and non-empty
  `blobIndices` can be followed even though the selected profile requires rejection. The active
  calldata payload itself remains fully available on L1.
- **Disposition.** Add the guard to live and catch-up derivation before payload decoding.
  `blobIndices` must remain empty until a versioned blob extension ships end to end.

### M-2. Ingress admission skipped when no `l1_provider` is wired

- **Spec requirement.** Cross-chain intents must pass nonce-contiguity and L1-balance admission
  before entering the held pool, so poison cannot ride the all-or-nothing bundle
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md), [§14.3.1](threat-model.md)).
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

### M-3. Zero beneficiary; no priority-fee or DA-cost recovery

- **Spec profile.** Standard EIP-1559 burns the base fee, priority fees accrue to the zero
  beneficiary, and no L1-data-fee mechanism reimburses the operator
  ([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)).
- **Current behavior.** `suggested_fee_recipient` is hard-coded `Address::ZERO`. No L1 fee oracle
  or L1-data-fee component exists, so the operator absorbs posting cost. Signed legacy system
  transactions use `gasLimit = 2_000_000` and fixed `gasPrice = 1_000_000_000` wei, paid from
  the prefunded `SYSTEM_ADDRESS`.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:496`,
  `crates/eez-composer/src/composer.rs:570`, `crates/eez-driver/src/sequencer.rs:118`;
  `crates/eez-node/src/main.rs:704-705,968-969`.
- **Impact.** The operator has no protocol revenue against posting costs. If the L2 base fee
  exceeds the fixed system gas price or the system account lacks its up-front balance, system
  delivery stops.
- **Disposition.** This is an explicit v0 limitation. Deployments must provision and monitor the
  system reserve. Operator revenue or L1-cost recovery requires a versioned profile change.

### M-4. Cross-chain sub-call gas unmetered in off-chain simulation

- **Spec requirement.** Off-chain simulation must match on-chain `postAndVerifyBatch` replay; cross-chain
  sub-calls have a defined gas budget so simulated and on-chain costs agree
  ([EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md), [Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)).
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
  `SELFDESTRUCT` ([EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md)).
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
  to rely on ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
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
  permanently-unreachable target-tip RPC loops without a verdict ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
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
  failure must not leave local L2 in a half-applied state ([Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)).
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
  must `drain_matching` the consumed tx-hash set (the external-composer case; [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md), [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)).
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
  be pinned, with a defined EIP-155 replay-protection story across L1/L2 ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** `genesis.json` sets `chainId = 1` (Ethereum mainnet id); runtime uses
  `chain_spec.chain().id()`. How `chainId = 1` is overridden at deploy time, and the
  authoritative Rollup0 L2 chainId, are unpinned — a replay/EIP-155 ambiguity.
- **Evidence.** `genesis.json:3`; `crates/eez-node/src/main.rs:630,788`.
- **Impact.** Ambiguous replay protection; a placeholder mainnet chainId in genesis is a
  foot-gun for cross-chain tx routing and signature domain separation.
- **Recommended fix.** Pin the authoritative L2 chainId in genesis (not `1`) and document the
  EIP-155 domain for L1↔L2 transactions.

### M-11. Exact bundle target is requested but not post-validated

- **Spec requirement.** A rich batch settles only when its receipt is canonically included at
  the requested host block and endpoint Sync timestamp
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** `eth_sendBundle` pins `blockNumber` and equal minimum/maximum timestamps.
  `observe` later accepts a receipt from any block number and does not validate the canonical
  inclusion block hash or timestamp.
- **Evidence.** Request: `crates/eez-l1/src/submitter.rs:507-551`; observation:
  `crates/eez-l1/src/submitter.rs:390-432`.
- **Impact.** Relay, RPC, or fallback deviations can be marked settled outside the temporal
  anchor that supports the synchronous claim.
- **Recommended fix.** Require the receipt block to equal the target, fetch its canonical header,
  and validate its hash and timestamp before accepting the settlement event.

### M-12. Empty DA block range is treated as a successful no-op

- **Spec requirement.** `blockTxCounts.length = toBlock - fromBlock` is positive; an empty list
  is invalid ([Rollup0 Appendix B — DA Codec](../docs/rollup0-network-spec/B-da-codec.md)).
- **Current behavior.** The source codec accepts empty `blockTxCounts`, and the live
  `on_batch_posted` path returns success when `block_count == 0`.
- **Evidence.** `crates/eez-payload-codec/src/lib.rs:91-93`;
  `crates/eez-deriver/src/deriver.rs:753-756`.
- **Impact.** A malformed settled event can be silently ignored, obscuring cursor or L1-state
  divergence.
- **Recommended fix.** Reject empty counts in the codec and every live/historical derivation path
  before state or cursor handling.

---

## A.4 Low

### L-1. `prev_randao` is normative zero — PREVRANDAO predictable

- **Spec requirement.** Rollup0 v0 fixes `prev_randao = bytes32(0)`. Any host-derived value
  requires a versioned change
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** `prev_randao` is hardcoded `B256::ZERO` in all three STF paths
  (Sequencer, Deriver, Sync-block composer). Any L2 contract reading `block.prevrandao`/
  `DIFFICULTY` observes constant zero, so any PREVRANDAO-seeded RNG/lottery/commit-reveal is
  fully predictable. All three paths must agree byte-for-byte or block hashes diverge.
- **Evidence.** `crates/eez-driver/src/sequencer.rs:145-147`,
  `crates/eez-deriver/src/deriver.rs:480`, `crates/eez-composer/src/local/build.rs:92-103`.
- **Impact.** Application-layer randomness is gameable. Not a protocol-state-safety issue (state
  still re-derives deterministically), but a divergence risk if the value ever becomes non-zero
  without all three paths agreeing.
- **Disposition.** The implementation conforms to v0. Applications must not use PREVRANDAO for
  randomness. A future derivation rule must change all three paths under a new profile version.

### L-2. Signature malleability (mitigated, residual)

- **Spec requirement.** Low-`s` + `v ∈ {27,28}` should be a normative requirement for every
  `IProofSystem` verifier ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
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

### L-3. `slot_number` is absent

- **Spec requirement.** Rollup0 v0 requires `slotNumber` and `blockAccessListHash` to be absent;
  activating Amsterdam requires a versioned change
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** Both fields are absent under the selected schedule.
- **Evidence.** `crates/eez-driver/src/sequencer.rs:158-159`.
- **Impact.** None in v0; the implementation conforms.
- **Future work.** Specify and activate both fields together in a future profile version.

### L-4. Aggregator is scaffolding only

- **Spec requirement.** Multi-rollup window assembly (how N rollups' batches combine into one L1
  bundle, `OnTerminal`/`OnTerminalOrAfter` trigger semantics) is part of the multi-rollup design
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** The `SubmitTrigger` enum exists but the `Aggregator` struct does not;
  multi-rollup assembly and trigger semantics are unspecified for Rollup0.
- **Evidence.** `crates/eez-l1/src/aggregator.rs:1-34`.
- **Impact.** None today (single-rollup Rollup0); blocks multi-rollup until implemented.
- **Recommended fix.** Defer formally to the multi-rollup phase; specify the trigger semantics
  before a second rollup is added.

### L-5. `build_batch` purity not runtime-asserted

- **Spec requirement.** `group_calls_for` + `build_batch` run twice (CCM-verify then emission)
  and must be **pure** — the two batches byte-identical — per the `ChainProtocol` contract
  ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)).
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
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
- **Current behavior.** `ExecutionCheckpoint.witness` is always `None` outside a Phase-2
  `WitnessRecordingDB` build; `EvmWitness` is a placeholder. The zk path is future; the
  checkpoint type carries dead capacity — consistent with "Rollup0 ≠ zk."
- **Evidence.** `crates/eez-protocol/src/checkpoint.rs:31-37`; `crates/eez-evm/src/lib.rs:15,82`.
- **Impact.** None today (no zk path in Rollup0).
- **Recommended fix.** Define the witness format when the zk/validator proving path is scoped;
  until then, document the field as reserved.

### L-7. Timing and header additions do not fail on `uint64` overflow

- **Spec requirement.** Scheduling-anchor and parent-derived number/timestamp additions use
  checked `uint64` arithmetic and return an explicit error on overflow
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** The scheduler uses ordinary addition for `head.timestamp + trigger`,
  `head.timestamp + D1`, and `l1_head + 1`; generic and deriver builders use saturating timestamp
  addition.
- **Evidence.** `crates/eez-driver/src/slot.rs:342-343`;
  `crates/eez-driver/src/sequencer.rs:142`;
  `crates/eez-deriver/src/deriver.rs:460-463`.
- **Impact.** Normal timestamps are unaffected, but boundary behavior differs by path instead of
  producing one deterministic error.
- **Recommended fix.** Use checked operations, propagate a typed error, and retain
  `uint64::MAX` timing/header vectors.

---

*Next: [EEZ Framework Appendix A — Protocol Reference](../docs/eez-protocol-spec/A-reference.md).*
