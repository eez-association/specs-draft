# Appendix A. Implementation Deviations

> **How to read this appendix.** The EEZ and network specifications under `docs/` identify their
> normative requirements. **This companion appendix is not normative.** It ranks every place
> the reviewed `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`
> code, with recorded contract submodule
> `5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`, does **not** meet that
> target — for auditors (what
> is guaranteed today vs on paper) and implementers (the punch-list). Each entry names the
> deviated spec requirement, what the code does instead, the `file:line` evidence, the impact,
> and the recommended fix. The target network uses open composer admission and
> `eez-evm@0.2-draft`; a statement about one local composer or the older ABI is
> implementation evidence, not a normative network choice.
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
| C-1 | Mock proof system does not bind to the batch | **Critical** | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | default development deployment only; bound remote path exists |
| H-1 | Cross-chain inspector dispatches on any call scheme | **High** | [EEZ Framework §3 — EVM Binding](../docs/eez-protocol-spec/03-evm-binding.md) | unmitigated; needs scheme gate |
| H-2 | `SYSTEM_ADDRESS` key sprawl (signed legacy system txs) | **High** | [Rollup0 Appendix C — System Transactions](../docs/rollup0-network-spec/C-system-transactions.md) | reviewed development path; production authorization blocked |
| H-4 | L1 reorg beyond the retained ring causes a persistent retry stall | **High** | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | retries automatically; no reseed or recovery |
| H-5 | Reviewed client uses the retired 0.1 manager and proof-input binding | **High** | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | port client to `getCustomData` and the 0.2 shared fold |
| H-6 | Live batches retain the zero L1-context sentinel | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | release blocker; bind a recent Ethereum block |
| H-7 | Deriver fast path does not validate full reconstructed headers | **High** | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | release blocker; compare sealed header and body |
| H-8 | Recorded 0.1 binding omits nested outbound ETH from entry accounting | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | fixed in latest core; reviewed client still pins 0.1 |
| H-9 | Deriver attributes applied roots by per-block set membership | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | preserve exact receipt and log order |
| H-10 | Equal-root siblings remain applicable because settlement stores no exact L2 cursor | **High** | [Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md) | production cursor guard required |
| H-11 | One held inbound trigger can produce several effects but appears once in the bundle | **High** | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | enforce one distinct trigger per effect |
| M-1 | Calldata-only DA; follower omits the empty-`blobIndices` guard | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | composer emits empty by construction; follower guard required |
| M-3 | Zero beneficiary; operator/system-account funded fees | Medium | [Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md) | development economics; production fee policy blocked |
| M-4 | Cross-chain sub-call gas unmetered in simulation | Medium | [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md), [Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md) | sim-vs-on-chain divergence |
| M-5 | Overlay diff-apply drops code/nonce, fails on `SELFDESTRUCT` | Medium | [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md) | partial; needs forbid-or-extend |
| M-6 | Mempool-fallback path loses bundle atomicity | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | deployment constraint |
| M-7 | Observer lacks `Unknown` and misuses relay terminality on fallback | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | transport-specific verdicts required |
| M-8 | `reconcile_batch_blocks` non-transactional | Medium | [Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md) | half-state on mid-loop failure |
| M-9 | External candidates do not reconcile the local held pool | Medium | [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) | blocks correct open-composer operation |
| M-10 | Genesis `chainId = 1` placeholder | Medium | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | L2 chainId unpinned |
| M-11 | Exact bundle target is not post-validated from canonical inclusion | Medium | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | request pins; observer does not verify |
| M-12 | Empty DA block range is accepted as a no-op | Medium | [Rollup0 Appendix B — DA Codec](../docs/rollup0-network-spec/B-da-codec.md) | reject non-positive range |
| L-1 | `prev_randao` hardcoded zero (PREVRANDAO predictable) | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | stage-1 placeholder |
| L-2 | ECDSA mock accepts high-`s` signature malleations | Low | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | adapter-specific hardening; not an EEZ-wide rule |
| L-3 | `slot_number` always `None` | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | inactive on stage-1 chains |
| L-4 | Aggregator is scaffolding only | Low | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) | single-rollup today |
| L-6 | Checkpoint witness field is reserved and unused | Low | [EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md) | real witnesses use the proving feed |
| L-7 | Scheduler/header timestamp arithmetic is not checked | Low | [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md) | boundary conformance hardening |

The historical H-3 same-nonce race is not a current deviation at the reviewed revision. Its
mechanism and compose-time fix remain recorded in [threat §14.3.1](threat-model.md).

---

## A.1 Critical

### C-1. The mock proof system does not bind to the batch

- **Spec requirement.** A selected proof system must attest the exact
  `publicInputsHash` that the activated EEZ binding computes for the batch. The selected proof
  policy is the trust root for whether an internally consistent `newState` is a correct execution
  result
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
- **Mock-configured behavior.** `MockECDSAProofSystem.verify` **ignores** `publicInputsHash` and
  recovers an ECDSA signature over the fixed constant `MOCK_PROVER_DIGEST =
  keccak256("eez-mock-prover")`; the Rust `MockEcdsaProver` signs exactly that constant. So
  **one** valid 65-byte signature over the fixed digest verifies every otherwise structurally
  admissible batch that selects the registered mock. The default deployment script and README use
  that mock configuration.
- **Other reviewed path.** The composer does not hardwire the mock. `EEZ_PROVER_URL` selects a
  remote prover, and `EEZ_ECDSA_PROOF_SYSTEM_ADDRESS` selects the proof-system address carried in
  the batch. The remote prover re-executes the window, checks its settlement gates, and signs the
  recomputed public-input hash. The in-tree production-style `ECDSAProofSystem` verifies that
  signature over the supplied hash. This path still uses the retired 0.1 batch binding described
  in H-5; it is binding, but it is not yet `eez-evm@0.2-draft` compatible.
- **Evidence.** Mock verifier and signer:
  `contracts/src/MockECDSAProofSystem.sol:51-80` and
  `crates/eez-prover/src/lib.rs:118-166`; default mock deployment:
  `scripts/deploy.sh:106-112` and `README.md:28-31,85-87`. Path and address selection:
  `crates/eez-node/src/main.rs:438-459,709-716` and
  `crates/eez-composer/src/composer.rs:2121-2125`. Bound remote path:
  `crates/eez-proverd/src/main.rs:130-194` and
  `contracts/src/ECDSAProofSystem.sol:43-78`. The manager enforces threshold and membership in
  `sync-rollups-protocol/src/rollupContract/Rollup.sol:98-125`.
- **Impact.** A mock-configured deployment has no proof-level execution-integrity guarantee.
  EEZ still enforces structural routing, live root chaining, and entry-local accounting, but a
  reusable mock signature can authorize a self-consistent wrong `newState`. A follower detects
  this as `LocalDiverged`. Boot catch-up then refuses startup; during live derivation the client
  retries resynchronization after later events, but it has no automatic rollback or fraud
  correction for the invalid Ethereum root. The defect is catastrophic outside development.
- **Recommended fix.** Make it a **deploy-time invariant** that
  `MockECDSAProofSystem` is forbidden on any non-development chain (fail closed
  at startup). Mark mock proofs **non-normative**. Select exact production
  proof systems, verifier code, membership, threshold, administrator controls,
  and activation in the Rollup0 profile. Validators/provers must evaluate any
  competing candidate without using composer identity as an admission rule.
  Threshold enforcement belongs to the selected manager/proof contracts, not
  the composer's batch shape
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).

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
  scheme. A contract that `STATICCALL`s a proxy thus initiates an ordinary target simulation that
  can mutate staged remote state, even though the source context is read-only. A `STATICCALL`
  carries zero value. `DELEGATECALL`/`CALLCODE` bind the proxy's cross-chain identity under the
  caller's storage, which is semantically undefined.
- **Evidence.** `crates/eez-evm-inspector/src/inspector.rs:489-540,641-719`; scheme is converted
  to a log label at `:526-531` and logged at `:693`. There is no dispatch gate on `CallScheme`.
- **Impact.** Cross-chain side effects (remote calls and `StateDelta` accrual) can
  be induced from a side-effect-free context, breaking EVM static-context guarantees and the
  "reads cannot mutate cross-chain state" assumption. This enables read-path-triggered remote
  mutation and simulation-versus-replay desynchronization. Dispatch soundness from non-`CALL`
  schemes is unspecified.
- **Recommended fix.** Gate dispatch on scheme: for `StaticCall`, route to the read-only
  `staticCallLookup` path (or synthesize a revert) — never dispatch a mutating call; explicitly
  reject `DelegateCall`/`CallCode` to a proxy. Specify that **only** `CallScheme::Call` may
  dispatch.

### H-2. `SYSTEM_ADDRESS` key sprawl permits forged signed system operations

- **Selected target.** The production envelope, authorization, sender, nonce, fee fields, gas
  limit, and inbound value source are release blockers
  ([Rollup0 Appendix C](../docs/rollup0-network-spec/C-system-transactions.md)). The signed legacy
  values below are historical development evidence, not production selections.
- **Reviewed behavior.** Every cross-chain-enabled composer and follower must receive the same
  private key to produce byte-identical signed legacy transaction bytes. A follower without
  `EEZ_L2_SYSTEM_KEY` disables cross-chain system-transaction reconstruction. Anyone holding the
  key can authorize forged table loads or inbound calls. Because the key controls an ordinary
  prefunded EOA, it can also sign arbitrary transfers of that account's existing balance.
- **Evidence.** Composer and follower configuration:
  `crates/eez-node/src/main.rs:683-688,1007-1051`. Shared construction and signing:
  `crates/eez-protocol/src/system_tx.rs:40-63,270-384`. The recorded historical
  `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` binding restricts both
  functions to `SYSTEM_ADDRESS` and enforces inbound `msg.value == value` at
  `sync-rollups-protocol/src/L2/EEZL2.sol:126-144,227-247`.
- **Impact.** Key compromise forges arbitrary system operations and drains or reallocates the
  prefunded reserve. The inbound equality check ties the transferred amount to calldata but not to
  a genuine L1 lock. A follower without the configured key cannot reproduce a cross-chain Sync
  block. The reviewed code disables reconstruction and can enter its pure-user fallback; later
  state validation may surface divergence, but this is not a clean fail-closed startup check.
- **Recommended fix.** Activate only after the profile pins the complete mechanism. If it retains
  a signed envelope, specify the exact byte rule, key custody, funding, and backing against
  `RollupConfig.etherBalance` and `StateDelta.etherDelta`. A key-free envelope remains an
  unselected future option. A profile that requires signed reconstruction must reject a missing
  key at startup.

### H-4. L1 reorg beyond the retained ring causes a persistent retry stall

- **Spec requirement.** A deep reorg must not be silently treated as ordinary catch-up. The
  network profile needs a deterministic recovery or operator procedure for restoring canonical L1
  and L2 cursors
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** The `L1Watcher` keeps a `(number, hash)` ring bounded by
  `reorg_max_depth` (default **62**). A full ring retains the tip through `tip - 61`, and
  `walk_back_to_common` checks at most 62 cursor positions. A depth-62 reorg can therefore already
  lack a retained common ancestor. Such a reorg, or a catch-up-gap reorg with no in-ring ancestor,
  makes the poll cycle return `L1Error::ReorgTooDeep`. The watcher task logs the error and retries
  on the next tick with unchanged state. It does not terminate, but it has no automatic reseed or
  recovery, so event advancement stalls while the condition persists. Shallower in-ring reorgs
  are handled (cursor retreat + `reorg_to`). The state of in-flight `Pending` optimistic batches
  during the stall is unspecified. Separately, `reconcile_batch_blocks` is non-transactional
  (see M-8).
- **Evidence.** Retry loop and deep-reorg errors:
  `crates/eez-l1/src/l1_watcher.rs:134-138,172-176,240-268,350-355,464-481,663-692,722-753`;
  shallow retreat:
  `crates/eez-deriver/src/deriver.rs:928-992`. Deep-reorg in-flight cleanup: no code path
  (design-level gap).
- **Impact.** Derivation/composition stalls (liveness) on a deep reorg; in-flight optimistic
  Sync blocks may have anchored against rolled-out batches with no defined cleanup. A
  shallowly-reorged-out settled batch is handled by commit-then-repair; the deep case repeats
  without making progress until external recovery changes the state.
- **Recommended fix.** Define a normative deep-reorg recovery procedure: on `ReorgTooDeep`,
  quiesce production, drop all `Pending`/`Settled` optimistic entries above the new common
  ancestor, re-derive from genesis or the deploy block, and gate restart on operator ack. (Make
  `reconcile_batch_blocks` transactional — see M-8.)

### H-5. Reviewed client uses the retired 0.1 manager and proof-input binding

- **Selected target.** `eez-evm@0.2-draft` calls
  `IRollupContract.getCustomData(uint64)` once per rollup and folds each ordered
  `(rollupId, customData)` pair into the shared public input. Its batch has no
  `crossProofSystemInteractions` member
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
- **Reviewed behavior.** `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`
  still uses `getTimestampAndBlockHash(uint64)` and
  `crossProofSystemInteractions`. That shape matches its recorded
  `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`
  submodule, but it does not match the selected 0.2 binding. The resolver currently
  calls the old manager API with `0` on its dormant path; fixing that argument alone
  would not make the client compatible with 0.2.
- **Evidence.** Reviewed Rust:
  `crates/eez-protocol/src/proof_resolver.rs:67-76,182-205` and
  `crates/eez-protocol/src/public_inputs.rs:108-141,276-343`. Recorded older
  binding: `sync-rollups-protocol/src/EEZ.sol`. Selected binding:
  `eez-core-protocol/src/EEZ.sol:637-700`,
  `eez-core-protocol/src/interfaces/IRollup.sol:46`, and
  `eez-core-protocol/src/rollupContract/Rollup.sol:137`.
- **Impact.** Proofs produced from the reviewed client's old public-input preimage are not valid
  0.2 proofs. The client cannot claim `eez-evm@0.2-draft` conformance until its ABI, batch types,
  and both sides of the fold are ported together.
- **Recommended fix.** Update the contract binding and Rust ABI/types, remove
  `crossProofSystemInteractions`, implement `getCustomData(uint64)`, mirror the exact shared fold,
  and add byte-exact cross-language vectors.

### H-6. Live batches retain the zero L1-context sentinel

- **Spec requirement.** A production batch binds a recent canonical Ethereum proof-context
  block N with
  `0 < N < type(uint64).max`. The manager and posting paths reject sentinel values so a reorg or
  expired block hash fails closed
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** The explicit resolver path can fold `(blockNumber, l1BlockHash)`, but the
  live builder does not supply that pair. Builders initialize `blockNumber = 0`,
  and `prepare_post_batch_raw` does not replace it. The recorded 0.1 manager maps zero to
  `(timestamp, blockHash) = (0, 0)`. The selected 0.2 core instead returns empty `customData` for
  zero and folds that empty blob with the `rollupId`. Both forms omit canonical L1 context.
- **Evidence.** Entry constructors set `blockNumber: 0` at
  `crates/eez-protocol/src/entries/mod.rs:232,346,620,732,776,865`. The live proof context
  explicitly supplies `l1_block_hash: None` for the timeless batch at
  `crates/eez-composer/src/composer.rs:2330-2337`; the full preparation path is `:1892-2369`.
  Recorded 0.1 sentinel behavior:
  `sync-rollups-protocol/src/rollupContract/Rollup.sol:127-151`. Selected 0.2 behavior:
  `eez-core-protocol/src/rollupContract/Rollup.sol:127-153` and
  `eez-core-protocol/src/EEZ.sol:676-700`.
- **Impact.** The signed digest is not bound to the observed Ethereum context that schedules
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
- **Evidence.** `crates/eez-deriver/src/deriver.rs:1247-1289,1443-1500`.
- **Impact.** Clients can agree on transactions and final state while retaining different
  intermediate headers and hashes.
- **Recommended fix.** Build and compare the complete expected sealed block for every range
  element, or replay unconditionally. Combine this with transactional range rollback (M-8).

### H-8. The recorded 0.1 binding omits nested outbound ETH from entry accounting

- **Spec requirement.** Entry accounting includes every successful value transfer at every
  nesting depth and preserves `address(EEZ).balance >= sum(rollups[r].etherBalance)`
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Reviewed 0.1 behavior.** The contract recorded by
  `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` calls `_processNCalls` recursively from
  `_consumeNestedAction` and discards that recursive call's local `etherOut`. Only the outer
  `_processNCalls` return is compared with `StateDelta.etherDelta`. A nested successful value
  transfer can therefore reduce physical custody without entering that comparison.
- **Latest-core behavior.** `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c`
  fixes this defect. It uses the transaction-transient `_entryEtherDelta` accumulator and subtracts
  every successful outbound value in `_processNCalls`, including nested calls. Reverted frames
  revert their accumulator changes.
- **Evidence.** Recorded 0.1 binding:
  `sync-rollups-protocol/src/EEZ.sol:801-816,916-945,963-969`. Latest core:
  `eez-core-protocol/src/EEZ.sol:119-133,799-808,882-902,1003-1035,1068`.
- **Impact.** A deployment of the recorded 0.1 binding can pass its implemented equation while
  aggregate custody is under-backed. This is not a defect in latest core, but the reviewed client
  remains pinned to the affected 0.1 binding.
- **Recommended fix.** Port Rollup0 to the selected latest core binding. Until then, validators
  and posting paths for the recorded binding must reject nested value-bearing entries.

### H-9. Deriver attributes applied roots by per-block set membership

- **Spec requirement.** Partial-settlement repair preserves receipt and log order, associates
  each delta with its exact batch and entry, and retains duplicate-root multiplicity
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** The scanner stores `L2ExecutionPerformed.newState` values in per-block
  `HashSet`s. Each batch in the block reuses that set, and `attribute_settlement` selects the
  deepest claimed root by membership. This discards order, multiplicity, and batch identity.
- **Evidence.** `crates/eez-l1/src/scan.rs:136-205,236-260`;
  `crates/eez-deriver/src/deriver.rs:1098-1174`.
- **Impact.** Multiple batches, duplicate roots, or non-prefix skips can be misattributed as an
  applied prefix, even when later state-root replay cannot authenticate the exact system
  transaction and receipt history.
- **Recommended fix.** Preserve ordered logs with transaction and log indices, count events
  rather than unique roots, and reject ambiguous or non-prefix patterns. If current events cannot
  identify batches exactly, constrain the profile to one batch per rollup per Ethereum block.

### H-10. Equal-root siblings remain applicable without an exact settled-cursor commitment

- **Spec requirement.** Candidate applicability compares the exact named parent height, block hash,
  and state root with the current settled cursor. Applying a candidate atomically advances that
  identity, even when the selected endpoint has the same state-root value
  ([Rollup0 §9 — Security](../docs/rollup0-network-spec/09-security-trust-model.md)).
- **Current behavior.** `EEZ._applyStateDeltas` compares only
  `StateDelta.currentState` with the stored root and writes `newState`. The settlement state has no
  Rollup0 height, block hash, or candidate-sequence commitment. After an `A -> A` candidate wins,
  a sibling naming the old Rollup0 parent can still pass the root check and apply.
- **Evidence.** `eez-core-protocol/src/EEZ.sol:1103-1120`; no exact Rollup0 cursor commitment exists
  in the reviewed client settlement path.
- **Impact.** Canonical Ethereum order no longer implements first-applicable-candidate-wins for
  equal-root transitions. Followers advance to one L2 block identity while Ethereum can accept a
  stale range from another identity.
- **Recommended fix.** Select the `R0-CURSOR-SAFETY` mechanism before production. It must bind the
  candidate's exact parent identity, reject stale siblings on chain, and atomically commit every
  possible selected prefix endpoint identity.

### H-11. One held inbound trigger can produce several effects

- **Spec requirement.** Every inbound effect has one distinct Ethereum trigger transaction. The
  post and those triggers occupy consecutive transaction indices with no interleaving
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** The composer flattens every target entry produced by one held inbound
  transaction into `pending_in`, but it appends that raw held transaction to the Ethereum bundle
  only once. The outbound path already rejects more than one settlement entry from one held
  transaction; the inbound path has no corresponding guard.
- **Evidence.** Inbound flattening and bundle construction:
  `crates/eez-composer/src/composer.rs:1390-1413,1690-1705`. Existing outbound guard:
  `:1299-1321`.
- **Impact.** Candidate inbound-effect count and trigger count can differ. Exact queue consumption,
  receipt attribution, and prefix repair are then undefined.
- **Recommended fix.** Reject any inbound composition that does not yield exactly one supported
  target effect for its trigger, or define a new versioned lowering and trigger construction that
  preserves a one-to-one transaction/effect mapping.

---

## A.3 Medium

### M-1. Calldata-only DA; follower still needs the empty-`blobIndices` guard

- **Spec profile.** The selected Rollup0 draft uses tag `0x00` calldata and requires
  `blobIndices` to be empty
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** The live composer leaves `blobIndices` empty by construction; it does not
  run an explicit rejection guard. An unused `PostBatchSubmitter` helper rejects non-empty
  indices. The scanner forwards only `callData` and raw transaction input, and live and catch-up
  derivers decode `callData` without checking the omitted field.
- **Evidence.** Live composer:
  `crates/eez-composer/src/composer.rs:1918-1928,2121-2125,2274-2276,2330-2349`; unused helper:
  `crates/eez-evm-inspector/src/post_batch_submitter.rs:153-167,352-362`; scanner:
  `crates/eez-l1/src/scan.rs:177-209`; deriver:
  `crates/eez-deriver/src/deriver.rs:297,692-761`.
- **Impact.** A landed generic-contract batch with valid tag `0x00` calldata and non-empty
  `blobIndices` can be followed even though the selected profile requires rejection. The active
  calldata payload itself remains fully available on L1.
- **Disposition.** Add the guard to live and catch-up derivation before payload decoding.
  `blobIndices` must remain empty until a versioned blob extension ships end to end.

### M-3. Zero beneficiary; no priority-fee or DA-cost recovery

- **Spec profile.** Standard EIP-1559 burns the base fee, priority fees accrue to the zero
  beneficiary, and no L1-data-fee mechanism reimburses the operator. The production base fee,
  fee funding, and system-envelope fee policy remain release blockers
  ([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)).
- **Current behavior.** `suggested_fee_recipient` is hard-coded `Address::ZERO`. No L1 fee oracle
  or L1-data-fee component exists, so the operator absorbs posting cost. Signed legacy system
  transactions in the reviewed development path use `gasLimit = 2_000_000` and fixed
  `gasPrice = 1_000_000_000` wei, paid from the prefunded `SYSTEM_ADDRESS`.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:496`,
  `crates/eez-composer/src/composer.rs:684`, `crates/eez-driver/src/sequencer.rs:118`;
  `crates/eez-node/src/main.rs:749-750,1048-1049`.
- **Impact.** The operator has no protocol revenue against posting costs. If the L2 base fee
  exceeds the fixed system gas price or the system account lacks its up-front balance, system
  delivery stops.
- **Disposition.** The zero beneficiary and absence of an L1-data fee are selected draft
  limitations. The development gas price and prefunded system reserve are not production values.
  Production base fee, system-transaction funding, and envelope fee policy must be pinned before
  activation.

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
  (`sync-rollups-protocol/src/L2/EEZL2.sol:442`, `sync-rollups-protocol/src/EEZ.sol:945`).
- **Evidence.** `crates/eez-evm-inspector/src/inspector.rs:677-680,716-719` (unmetered
  outcome); sim relaxation `crates/eez-composer/src/local/session.rs:613-620`; on-chain metering
  `sync-rollups-protocol/src/L2/EEZL2.sol:442` / `sync-rollups-protocol/src/EEZ.sol:945`
  (`_processNCalls`). The approximately 2M inbound system-transaction budget is an **off-chain**
  configuration (`crates/eez-composer/src/composer.rs:67-74`,
  `crates/eez-protocol/src/system_tx.rs:50-59`), not an on-chain contract constant.
- **Impact.** A batch that simulated clean can revert/out-of-gas on L1 (bundle drop, settlement
  stall), and an attacker can craft cheap-in-sim, expensive-on-chain compositions (griefing the
  operator's posting cost). The off-chain `4M POST_BATCH_GAS_LIMIT`
  (`crates/eez-composer/src/composer.rs:2521`) caps the L1 tx, but the off-chain-vs-on-chain
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
  mis-simulates vs on-chain; one that selfdestructs cannot compose. Successful nested re-entry is
  implemented. Unsupported nested failed/static lookup lowering and cyclic non-entry re-entry
  fail closed with typed `Unsupported` or `InvalidReentry` errors.
- **Evidence.** Overlay:
  `crates/eez-evm-inspector/src/overlay.rs:149-180,195-287`; nested lowering and typed failures:
  `crates/eez-protocol/src/entries/mod.rs:130-184,1831-1873`; cyclic re-entry guard:
  `crates/eez-protocol/src/composition.rs:748-835`; live deriver recovery:
  `crates/eez-deriver/src/deriver.rs:607-688`.
- **Impact.** Off-chain composition can diverge from on-chain re-derivation for these mutation
  classes, breaking the commit-then-repair guarantee. A live `LocalDiverged` error triggers
  catch-up; a failed resync remains eligible for retry on the next L1 event instead of terminating
  the deriver. Boot catch-up can refuse startup. `SELFDESTRUCT`-bearing flows and the explicitly
  rejected nested shapes are unsupported.
- **Recommended fix.** Either extend the overlay to handle code-install + nonce changes (and
  define transient-storage semantics), or normatively **forbid** cross-chain nested calls that
  deploy code / change nonces / selfdestruct and **reject** them at compose time rather than
  mis-simulating. Specify the supported nested failed/static lookup behavior.

### M-6. Mempool-fallback path loses bundle atomicity

- **Spec requirement.** The L1 bundle is strictly all-or-nothing; a deployment whose relay lacks
  `eth_sendBundle` has **no** atomic-bundle guarantee — a deployment constraint, not a fallback
  to rely on ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** If the relay returns `-32601` (no `eth_sendBundle`), the submitter
  degrades to ordered `eth_sendRawTransaction` mempool submission (`postAndVerifyBatch` first),
  which **loses atomicity**: the `postAndVerifyBatch` can land without a user tx or vice versa,
  reintroducing the partial-inclusion desync risk.
- **Evidence.** `crates/eez-l1/src/submitter.rs:296-365`.
- **Impact.** On the fallback path the
  [Rollup0 §4.4 bundle rule](../docs/rollup0-network-spec/04-da-batches-bundles.md#44-ethereum-bundle)
  does not hold; a partial land can advance Ethereum to a mid-chain prefix root and desync the
  composer.
- **Recommended fix.** State normatively that a relay without `eth_sendBundle` is not a valid
  atomic-bundle Rollup0 deployment; gate cross-chain settlement on bundle support (fail-closed),
  or restrict the fallback to dev/anvil only.

### M-7. `observe()` has no inconclusive verdict and misuses relay terminality on fallback

- **Spec requirement.** An exact-target relay bundle may be declared dropped after its target
  passes. An inconclusive provider state and a public-mempool transaction require different,
  non-terminal handling
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** `observe()` loops indefinitely on transient RPC errors; only
  `head > target` ends it. The relay and public-mempool fallback both use that observer even though
  a mempool transaction can remain pending and land after the target. A permanently unreachable
  target-tip provider leaves the composer's optimistic gate `Pending` with no escape; a healthy
  provider can instead produce a false `Dropped` verdict for the fallback.
- **Evidence.** Relay/fallback dispatch:
  `crates/eez-l1/src/submitter.rs:311-379`; shared observer:
  `:384-468`.
- **Impact.** Provider failure can freeze the one-in-flight gate. A late fallback inclusion after
  a false `Dropped` verdict can race recovery and produce the recovery-versus-deriver conflict in
  threat §14.3.20.
- **Recommended fix.** Add an explicit operator-actionable `Unknown`/`Stalled` verdict for
  inconclusive RPC state. Disable the mempool fallback in conforming deployments, or give it
  nonce-, receipt-, and replacement-aware terminality instead of the relay target rule.

### M-8. `reconcile_batch_blocks` is non-transactional

- **Spec requirement.** Re-derivation of a batch's L2 blocks must be all-or-nothing: a replay
  failure must not leave local L2 in a half-applied state ([Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)).
- **Current behavior.** `reconcile_batch_blocks` is explicitly **not** transactional — a replay
  failing partway leaves earlier blocks committed to reth's canonical chain (a half-state).
  Rollback-to-pre-loop-snapshot is an open item.
- **Evidence.** `crates/eez-deriver/src/deriver.rs:1059-1065`.
- **Impact.** A mid-loop failure advances local L2 partway onto new ancestry with no snapshot
  rollback; recovery relies on `recovery_resync` re-anchoring on the next L1 event.
- **Recommended fix.** Make it transactional: snapshot the canonical head pre-loop and roll back
  on any per-block failure.

### M-9. External candidates do not reconcile the local held pool

- **Spec requirement.** When an external composer's batch consumes our held txs, the held pool
  must remove the consumed triggers before constructing another candidate
  ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)).
- **Current behavior.** `on_l1_event` treats an external `BatchPosted` as diagnostic-only and
  logs it. No path derives the consumed trigger hashes or removes matching queued transactions.
  `L1Event::BatchPosted` carries `rollup_count`, not a per-rollup identifier or a consumed-trigger
  list, and `HeldPool` has no matching-drain operation.
- **Evidence.** Diagnostic-only handler:
  `crates/eez-composer/src/composer.rs:416-470`; event shape:
  `crates/eez-l1/src/l1_watcher.rs:73-115`; held-pool mutation API:
  `crates/eez-composer/src/held_pool.rs:136-319`.
- **Impact.** The target Rollup0 admission rule permits external composers, so
  this is load-bearing. A node can retain held transactions already consumed by
  a winning external candidate and submit them again.
- **Recommended fix.** Derive the exact consumed-trigger set from authenticated canonical
  inclusion data and remove those transactions from the queued and in-flight held-pool state.
  If the event interface cannot carry enough attribution, define another authenticated index.
  A deployment MUST NOT disable the external-candidate case by treating one composer as
  authorized.

### M-10. Genesis `chainId = 1` placeholder

- **Spec requirement.** The authoritative Rollup0 L2 `chainId` must
  be pinned, with a defined EIP-155 replay-protection story across L1/L2 ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** `genesis.json` sets `chainId = 1` (Ethereum mainnet id); runtime uses
  `chain_spec.chain().id()`. How `chainId = 1` is overridden at deploy time, and the
  authoritative Rollup0 L2 chainId, are unpinned — a replay/EIP-155 ambiguity.
- **Evidence.** `genesis.json:3`; `crates/eez-node/src/main.rs:748,1047`.
- **Impact.** Ambiguous replay protection; a placeholder mainnet chainId in genesis is a
  foot-gun for cross-chain tx routing and signature domain separation.
- **Recommended fix.** Pin the authoritative L2 chainId in genesis (not `1`) and document the
  EIP-155 domain for L1↔L2 transactions.

### M-11. Exact bundle target is requested but not post-validated

- **Spec requirement.** A rich batch settles only when its receipt is canonically included at
  the requested Ethereum block and endpoint Sync timestamp
  ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
- **Current behavior.** A steady-state `BundleTarget::Exact` request pins `blockNumber` and equal
  minimum/maximum timestamps. Catch-up uses `BundleTarget::NextBlock`, resolves it to
  `latest + 2`, and omits the timestamp bounds. In both cases, `observe` accepts a receipt from
  any block number and does not validate the canonical inclusion block hash or timestamp.
- **Evidence.** Target selection and request construction:
  `crates/eez-l1/src/submitter.rs:32-49,152-168,507-549`; steady-state versus catch-up selection:
  `crates/eez-composer/src/composer.rs:621-635`; observation:
  `crates/eez-l1/src/submitter.rs:384-427`.
- **Impact.** Relay, RPC, or fallback deviations can be marked settled outside the temporal
  anchor that supports the synchronous claim. Catch-up requests do not carry that timestamp
  anchor in the first place.
- **Recommended fix.** Require the receipt block to equal the target, fetch its canonical header,
  and validate its hash and timestamp before accepting the settlement event. Define and enforce
  the authenticated endpoint rule for catch-up candidates as well.

### M-12. Empty DA block range is treated as a successful no-op

- **Spec requirement.** `blockTxCounts.length = toBlock - fromBlock` is positive; an empty list
  is invalid ([Rollup0 Appendix B — DA Codec](../docs/rollup0-network-spec/B-da-codec.md)).
- **Current behavior.** The source codec accepts empty `blockTxCounts`, and the live
  `on_batch_posted` path returns success when `block_count == 0`.
- **Evidence.** `crates/eez-payload-codec/src/lib.rs:107-123,135-152`;
  `crates/eez-deriver/src/deriver.rs:758-761`.
- **Impact.** A malformed settled event can be silently ignored, obscuring cursor or L1-state
  divergence.
- **Recommended fix.** Reject empty counts in the codec and every live/historical derivation path
  before state or cursor handling.

---

## A.4 Low

### L-1. `prev_randao` is normative zero — PREVRANDAO predictable

- **Spec requirement.** The current Rollup0 draft fixes `prev_randao = bytes32(0)`. Any
  host-derived value
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
- **Disposition.** The implementation conforms to this draft rule. Applications must not use
  PREVRANDAO for
  randomness. A future derivation rule must change all three paths under a new profile version.

### L-2. The ECDSA mock accepts high-`s` signature malleations

- **Adapter requirement.** EEZ treats proof bytes as opaque. A profile that selects the reference
  ECDSA adapter should require low-`s` and `v ∈ {27,28}` for that adapter; this is not an
  EEZ-wide requirement for every `IProofSystem`
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
- **Current behavior.** Proof signatures are 65-byte `(r, s, v)`. The Rust `EcdsaProofSigner`
  emits low-`s` and `v = 27 + recid`, refusing `recid > 1`. The mock verifier uses bare
  `ecrecover` with no explicit low-`s` check. It therefore accepts a valid high-`s` malleation
  with the corresponding flipped `v` when it recovers the configured signer. The recorded
  production-style binding uses OpenZeppelin `ECDSA.recover`, which rejects high-`s`.
- **Evidence.** Rust canonicalization:
  `crates/eez-protocol/src/signer.rs:106-173`; mock verifier:
  `contracts/src/MockECDSAProofSystem.sol:55-79`. The recorded binding
  `sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:29-32` uses OZ `ECDSA.recover`
  (which rejects high-`s`) over the raw `publicInputsHash` and compares against `signer`; note
  it does **not** normalize `v` (must be 27/28 — see its dev comment at `:13-15`), so the caller
  must supply canonical `v`, which the Rust signer already does.
- **Impact.** The development mock accepts two encodings of one valid proof signature. This is
  low impact beside C-1's complete lack of batch binding, but differs from the reference ECDSA
  adapter's canonical-signature behavior.
- **Recommended fix.** Use OpenZeppelin `ECDSA.recover` or add explicit low-`s` and
  `v ∈ {27,28}` checks to an ECDSA-selecting profile's mock. Test the rule for ECDSA verifier
  contracts, and document the exact signed digest (raw `publicInputsHash`, no EIP-191) as
  authoritative.

### L-3. `slot_number` is absent

- **Spec requirement.** The current Rollup0 draft requires `slotNumber` and
  `blockAccessListHash` to be absent;
  activating Amsterdam requires a versioned change
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** Both fields are absent under the selected schedule.
- **Evidence.** `crates/eez-driver/src/sequencer.rs:158-159`.
- **Impact.** None under the current draft; the implementation conforms.
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

### L-6. The checkpoint witness field is reserved and unused

- **Spec requirement.** The selected proving path must carry the authenticated execution data
  needed by its verifier
  ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)).
- **Current behavior.** `ExecutionCheckpoint.witness` is `None` at every in-tree checkpoint
  construction site, and its `EvmWitness` type is a reserved placeholder. This does **not** mean
  that the proving-witness path is stubbed: the node generates concrete reth
  `ExecutionWitness` values, persists and serves them through a separate witness source, and the
  remote-prover client transmits them on the proving feed.
- **Evidence.** Reserved checkpoint field:
  `crates/eez-protocol/src/checkpoint.rs:29-57` and
  `crates/eez-protocol/src/witness.rs:1-26`; concrete witness generation:
  `crates/eez-driver/src/witness.rs:1-182`; persistent source:
  `crates/eez-node/src/witness_source.rs:1-27,41-137,185-228`; prover transport:
  `crates/eez-prover-client/src/lib.rs:61-100`.
- **Impact.** None on the implemented proving feed. The unused optional field can confuse
  implementers about which witness channel is authoritative.
- **Recommended fix.** Keep the field explicitly reserved or remove it in a versioned checkpoint
  schema change. Specify the separate proving-feed witness as the implemented path.

### L-7. Timing and header additions do not fail on `uint64` overflow

- **Spec requirement.** Scheduling-anchor and parent-derived number/timestamp additions use
  checked `uint64` arithmetic and return an explicit error on overflow
  ([Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)).
- **Current behavior.** The scheduler uses ordinary addition for `head.timestamp + trigger`,
  `head.timestamp + D1`, and `l1_head + 1`; generic and deriver builders use saturating timestamp
  addition.
- **Evidence.** `crates/eez-driver/src/slot.rs:342-343`;
  `crates/eez-driver/src/sequencer.rs:142,635`;
  `crates/eez-deriver/src/deriver.rs:460-463`.
- **Impact.** Normal timestamps are unaffected, but boundary behavior differs by path instead of
  producing one deterministic error.
- **Recommended fix.** Use checked operations, propagate a typed error, and retain
  `uint64::MAX` timing/header vectors.

---

*Next: [EEZ Framework Appendix A — Protocol Reference](../docs/eez-protocol-spec/A-reference.md).*
