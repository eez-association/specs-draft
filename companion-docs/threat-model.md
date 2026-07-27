# Implementation Threat Catalog

> **Informative companion material.** The normative model is
> [Rollup0 §9 — Security and Trust](../docs/rollup0-network-spec/09-security-trust-model.md).
> This catalog preserves implementation evidence. Earlier claims that the defenses are
> independent, the operator affects liveness only, or no scenario can cause fund loss are
> superseded. Manager and verifier authority, external bundle atomicity, the unsafe-head
> boundary, and EEZ custody must be evaluated together.

## 14.1 Audit scope and adversaries

The inspected system is centralized and permissioned. Its controls are conditional:

| Party or component | Relevant authority | Failure consequence |
|---|---|---|
| **Manager owner/governance** | Changes proof systems, vkeys, and threshold; can replace a registered root. | Can remove effective validity checking, install an arbitrary commitment, halt settlement, and affect custody policy. |
| **Validators and verifier administrators** | Decide whether a digest is accepted; the ECDSA verifier administrator can replace its signer. | A malicious threshold or compromised verifier can authorize invalid state or value movement, subject only to limited contract checks. |
| **Operator/composer** | Produces the unsafe head, calldata, batches, and transaction pair. | Can equivocate, censor, withhold data, and choose a non-atomic submission path. |
| **Relay/builder** | Supplies all-or-none, ordered, same-block inclusion outside the EVM. | A successful transaction prefix remains on L1; follower repair cannot reverse it. |
| **Settlement host** | Supplies canonical execution, receipts, DA, ordering, and finality. | Reorganizations move the safe head; host consensus failure is outside Rollup0. |
| **`SYSTEM_ADDRESS` key holders** | Sign deterministic legacy system transactions from a prefunded EOA. | Can forge system operations and drain or reallocate that reserve. |
| **Follower/deriver** | Reconstructs the local safe view and detects disagreement. | Can halt on ambiguity; cannot revert EEZ state or create an exit. |

Adversary labels:

- **A-OP**: malicious or compromised operator;
- **A-VAL**: malicious validators or proof-system administrators;
- **A-USER**: ordinary user or griefer;
- **A-KEY**: system-transaction or proof-signer key holder; and
- **A-NET**: malicious or faulty relay, builder, or network path.

## 14.2 How the controls compose

1. **Proof-policy gate.** Structure validation and proof verification happen before entry
   execution. Soundness depends on manager configuration, verifier behavior, administrator
   authority, and an honest threshold.
2. **Local entry checks.** EEZ checks live pre-roots, rolling call commitments, recorded-balance
   underflow, and its implemented ETH-delta equation. It does not execute the L2 STF, validate
   opaque DA, prove deposit correspondence, or prevent a self-consistent malicious root. The
   nested-value defect also prevents treating its equation as a general solvency proof
   (§14.3.22).
3. **Non-atomic entry execution.** Immediate entries can be skipped in isolated self-calls and
   deferred entries can remain unconsumed. `BatchPosted` does not mean the full table applied.
4. **Follower replay.** A follower can reject an invalid endpoint or rebuild a unique applied v0
   prefix. It cannot undo an accepted root, return pooled funds, or submit a fraud proof.
5. **Bundle relay.** The transaction pair is synchronous only when an external relay includes
   both transactions, in order, in one block, or neither. The proof digest does not commit to the
   trigger hash or bundle membership.

The resulting evidence is graded: operator output is unsafe; EEZ execution establishes an
L1-accepted root; matching reconstruction establishes a follower-safe view; and host finality
protects that view from ordinary reorganization. None removes manager, validator, custody, or
exit assumptions.

## 14.3 Ranked threat catalogue

### 14.3.1 [HIGH] Same-nonce L1 race bricks the settlement bundle — the SEED threat

The canonical Rollup0 attack, specified at mechanism level because every robustness behavior in
[Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) and the coupling hazard in [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md) exist to
survive it. Adversary: **A-USER** (one user with one key, or any party who can front-run that
account).

**The mechanism, step by step.**

1. A user submits a cross-chain intent as an **L1-bound** raw transaction to the *L2* RPC.
   Because its `chainId` is in `cross_chain_source_chain_ids`, the ingress classifier routes
   it `CrossChain` ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)), and ingress admits it after a **point-in-time**
   nonce-contiguity check (`nonce == on_chain + held`) and balance check
   ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)), pushing `HeldTx{ sender, nonce, hash }` into the FIFO held pool.
2. The same user (or a colluder with the key) submits a **different** L1 transaction with the
   **same nonce** directly to L1, and it lands first. The held intent's nonce is now **burned**
   on L1.
3. At the next sync slot the composer drains the held intent (`pop_n`, capped at
   `MAX_USER_TXS_PER_BUNDLE = 3`) and assembles the **all-or-nothing** bundle
   `[postAndVerifyBatch_raw, held_user_tx]` (`revertingTxHashes`/`droppingTxHashes` empty,
   [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md)).
4. The builder simulates the bundle. `held_user_tx` now has `nonce < account_nonce` (burned
   by the external tx) → it reverts in simulation → all-or-nothing → the **whole bundle never
   lands**, so `postAndVerifyBatch` never lands.
5. The observer returns `Dropped` only once `head > target_block` ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md));
   the ledger entry is `mark_failed`.
6. **Recovery is where the burn goes undetected.** `recover_failed_batch`
   ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)) re-pushes survivors but skips any whose nonce already burned by
   checking `receipt_exists(held_user_tx.hash)` — i.e. it checks for a receipt under the
   **held tx's own hash**. The *external* same-nonce tx has a **different hash**, so
   `receipt_exists` returns **false**: the burn is **not detected**, the held tx is re-queued
   (`attempts++`), and the *same failing bundle* is rebuilt next slot.
7. This repeats for `MAX_BUNDLE_ATTEMPTS = 3` slots before the held tx is finally evicted as
   poison (+ nonce-cascade), after which `postAndVerifyBatch` can land alone again.

**Preconditions.** An admitted L1-bound cross-chain intent, plus the ability to land a
same-nonce L1 tx first (the user's own key, trivially). If `l1_provider` is **not** wired for
ingress, admission validation is skipped entirely and the window widens (§14.3.9, amplifier).
Requires the `eth_sendBundle` relay path; the mempool-fallback path drops atomicity and may
partially include instead (§14.3.16).

**Impact.** For ~3 consecutive sync slots the `postAndVerifyBatch` cannot land: L1's stored
`stateRoot` stops advancing (the leading immediate entry never settles), the one-in-flight gate
churns Failed → recovery → retry, and L1↔L2 diverge in time. This is a **settlement/liveness
DoS, not a full chain halt**: the empty Sync block is committed **unconditionally**
([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md), [Rollup0 §2 — Block Production](../docs/rollup0-network-spec/02-block-production.md)), so L2 cadence continues. It is
**cheap** (one L2 RPC submission + one L1 tx at L1 base fee) and **repeatable** — a griefer keeps
one poison intent in flight to hold L1 settlement hostage indefinitely, self-healing only
per-poison-tx after 3 slots.

**Current mitigation.** Point-in-time ingress nonce check (cannot prevent a *later* same-nonce
L1 tx); `MAX_BUNDLE_ATTEMPTS = 3` bounds each stall and eventually evicts; nonce-cascade
eviction prevents the gapped tail from poisoning future bundles; the unconditional empty Sync
block keeps L2 cadence alive.

**Recommended mitigation (required fix).**

1. **Detect burned nonces by ACCOUNT STATE, not by the held tx's own receipt.** At recovery —
   and ideally at compose time *before* bundling — read `provider.get_transaction_count(sender)`
   and drop/replace any held tx whose `nonce < on_chain`. This closes the
   `receipt_exists`-on-own-hash gap directly.
2. **Do not bundle user L1 transactions all-or-nothing with the `postAndVerifyBatch`.** The
   `postAndVerifyBatch` carries the leading immediate entry and **must be able to land
   independently** of any user-supplied L1 tx. If a survivor sim-fails, drop the survivor and
   still send `[postAndVerifyBatch]`.
3. **Re-simulate survivors against fresh L1 state each slot** and exclude stale-nonce ones
   before assembling the bundle.
4. **Classify `nonce-too-low` as deterministic poison** and evict on the **first** drop, not
   the third (`sim_error_is_poison` should treat it as deterministic).

**Code-evidence.** Rust path fully verified: ingress classify/admit (`ingress.rs:112-124,163-225`);
held-pool drain (`composer.rs:589-605`); bundle assembly (`composer.rs:1224-1227`);
all-or-nothing send (`submitter.rs:511-526`); `Dropped` verdict (`submitter.rs:413-418`);
`mark_failed` (`optimistic.rs:172-176`); the recovery gap — `receipt_exists` on the **own** hash,
cannot detect a different-hash external burn (`composer.rs:803-846`); `MAX_BUNDLE_ATTEMPTS=3`
(`composer.rs:127,835`). Cross-refs: [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md), [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md),
[Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md). Fix tracked in [Appendix A](IMPLEMENTATION_NOTES.md).

---

The remaining threats are grouped by category.

### Sequencer / operator

### 14.3.2 [HIGH] No L1 force-inclusion / escape hatch — indefinite censorship, no trustless exit

**Scenario.** Rollup0 has a single sequencer/composer and **no L1 inbox or force-include
mechanism**: a user cannot compel inclusion of an L2 tx or cross-chain call by posting to L1.
Deposits arrive only as composer-built system transactions; withdrawals land on L1 only when the
composer posts the entry. Adversary: **A-OP**, by declining to include. A grep for
force-include/inbox/escape-hatch across the composer and deriver finds nothing (verified by
absence).

**Preconditions.** A malicious or unavailable operator. Nothing more.

**Impact.** Complete censorship of targeted users and, in the limit, total L2 liveness loss,
with **no trustless exit** — bridged funds cannot be withdrawn without operator cooperation; a
stalled or hostile operator can freeze funds indefinitely. The central *accepted* Rollup0
limitation: liveness depends on the operator, safety does not.

**Current mitigation.** L1 is source of truth, so **safety** (no theft of correctly-attributed
funds) does not depend on the operator; followers re-derive from L1. Liveness is *deliberately*
traded to the operator — mitigated only socially.

**Recommended mitigation.** An L1 force-inclusion inbox + a permissionless withdrawal/exit path
not requiring the composer, with a timeout after which any party can post the entry. Deferred to
Rollup1 (§14.5). For Rollup0 the spec states there is **no** trustless exit and bridged funds are
operator-liveness-dependent.

**Code-evidence.** Design-level (verified by *absence*): no force-include/inbox/escape-hatch
code in the composer or deriver; deposits/withdrawals flow only through composer-built system
txs (`eez-evm/src/system_tx.rs:62-120`) and operator-posted entries.

### 14.3.3 [LOW] Sequencer ↔ follower equivocation — the `Unverifiable > 1024` window

**Scenario.** A follower polls the sequencer RPC `eth_getBlockByNumber(Latest)` and advances
only the **unsafe** head. A malicious/buggy sequencer (**A-OP**) publishes a branch not
descending from the L1-confirmed safe anchor. `check_extends_safe` classifies it:
same-height-different-hash or below-safe ⇒ `Conflicts` (rejected before the engine); otherwise it
walks the candidate's `parent_hash` chain down to safe height (cap `MAX_ANCESTRY_WALK = 1024`),
rejecting unless it lands on the safe hash. A candidate **> 1024 blocks above safe** with
non-local ancestry is `Unverifiable` and **optimistically accepted**.

**Preconditions.** An equivocating branch; for the bypass, deep (> 1024 blocks above safe) with
ancestry the follower has not synced.

**Impact.** Transient acceptance of a stale/equivocating *unsafe* head until the deriver corrects
it from L1. **Safe/finalized are owned solely by the deriver** (L1-derived), so safety is **not**
violated — the head is reorged back. A brief optimistic-acceptance surface, not a persistent
compromise.

**Current mitigation.** `check_extends_safe` rejects `Conflicts` heads before the engine; the
deriver owns safe/finalized from L1 and reorgs the unsafe head back; `advance_unsafe_head` leaves
safe/finalized untouched. The cap `DEFAULT_MAX_SPECULATIVE_DEPTH = 64` should keep the legitimate
sequencer-ahead distance well below 1024.

**Recommended mitigation.** Document `MAX_ANCESTRY_WALK = 1024` as a security parameter that must
exceed the max legitimate sequencer-ahead-of-safe distance; consider **rejecting** (not
optimistically accepting) `Unverifiable` heads above the cap, or syncing ancestry first. Verify
the unsafe head can never legitimately exceed 1024 above safe.

**Code-evidence.** Verified Rust: `follower.rs:133` (`Conflicts` rejected before engine),
`:186-254` (`check_extends_safe` verdicts), `:33,235-243` (`MAX_ANCESTRY_WALK=1024` →
`Unverifiable` optimistic accept).

### 14.3.4 [MEDIUM] Operator timestamp manipulation

**Scenario.** The centralized sequencer (**A-OP**) chooses block timestamps; the only constraint
is strict monotonicity (a `parent+1` floor) plus an advisory drift `WARN`. The operator can stall
or run timestamps ahead of wall-clock.

**Impact.** Time-dependent L2 logic can be skewed within the operator's discretion. **Not a
safety issue:** the deriver enforces `parent + l2_block_time` on replay and L1 is source of
truth, so block hashes still re-derive deterministically.

**Current mitigation.** Deriver replay enforces the cadence (`deriver.rs:444`); monotonicity
floor + drift `WARN` (`sequencer.rs:566-578`).

**Recommended mitigation.** Bound allowed forward drift normatively and reject blocks exceeding
it at follower ingest; document `block.timestamp` as operator-influenced for app developers.

**Code-evidence.** Verified Rust: `sequencer.rs:566-578` (monotonicity + drift WARN);
`deriver.rs:444` (replay cadence enforcement).

### Cross-chain composition

### 14.3.5 [HIGH] STATICCALL (and DELEGATECALL/CALLCODE) to a proxy triggers a state-mutating dispatch

**Scenario.** `SessionInspector::call` computes `inputs.scheme`
(`CALL`/`CALLCODE`/`DELEGATECALL`/`STATICCALL`) but uses it **only in a tracing log** — no scheme
gate. On **every** CALL-family frame whose target is a registered `authorizedProxy`, it builds an
`ExecutionRequest` and dispatches a cross-chain call regardless of scheme. A **`STATICCALL`** to a
proxy thus initiates a state-mutating, value-bearing cross-chain dispatch from a context the EVM
guarantees read-only. `DELEGATECALL`/`CALLCODE` to a proxy bind the proxy's cross-chain identity
under the *caller's* storage context, semantically undefined for the 6-field source/target
attribution. Adversary: **A-USER** crafting a contract whose read path (a view function, or a
`STATICCALL` inside a `try`) targets a proxy.

**Impact.** Cross-chain side effects (value movement, remote calls, `stateDelta` accrual) can be
induced from a context that should be side-effect-free, breaking EVM static-context guarantees —
enabling read-path-triggered value flows or sim-vs-on-chain desync; soundness of dispatch from
non-`CALL` schemes is unspecified.

**Current mitigation.** None in code — the scheme is logged only.

**Recommended mitigation.** Gate dispatch on scheme: refuse (return `None` / synthesize a revert)
for `StaticCall`; define or forbid `DelegateCall`/`CallCode`-to-proxy. At minimum a `STATICCALL`
to a proxy must **not** dispatch a state-mutating cross-chain call — specify that only
`CallScheme::Call` may dispatch.

**Code-evidence.** Verified: `eez-evm-inspector/src/inspector.rs:489-540` (dispatch proceeds
after proxy detection with **no** scheme gate); scheme consumed only in `tracing::info!` at
`inspector.rs:693`. No `CallScheme` guard anywhere in `inspector.rs`.

### 14.3.6 [MEDIUM] Overlay diff-apply drops code/nonce changes and hard-fails SELFDESTRUCT

**Scenario.** The overlay diff-apply for nested cross-chain dispatch applies **only** storage
writes and balance changes back onto the source journal. **Code installation and nonce changes
are silently deferred/skipped**, transient storage is ignored, and `SELFDESTRUCT` raises a loud
`OverlayError::Selfdestruct`. A nested cross-chain call that deploys a contract
(`CREATE`/`CREATE2`) or bumps a nonce **mis-simulates** versus on-chain replay; one that
selfdestructs **cannot compose at all**. Adversary: **A-USER** with a composition whose nested
call deploys code, changes a nonce, uses transient storage cross-call, or selfdestructs. The KB
also notes `build_batch` panics (`unimplemented!`) when a rollup both originates and receives
traffic in one composition (nested re-entry L1→L2→L1).

**Impact.** Off-chain composition can diverge from on-chain re-derivation for these mutation
classes, breaking commit-then-repair — caught only **later** as a state-root divergence →
`LocalDiverged` halt (liveness, not silent corruption). SELFDESTRUCT-bearing cross-chain flows
are unsupported.

**Current mitigation.** SELFDESTRUCT fails loudly; storage+balance applied; divergence surfaces
as a `LocalDiverged` deriver halt rather than silent corruption.

**Recommended mitigation.** Either extend overlay diff-apply to handle code-install and nonce
changes (and define transient-storage semantics), or **normatively forbid** nested cross-chain
calls that deploy code / change nonces / selfdestruct, **rejecting such compositions at compose
time** rather than mis-simulating. Implement or forbid nested-reentry compositions instead of
panicking.

**Code-evidence.** Verified: overlay diff-apply specifics (`eez-evm-inspector/src/overlay.rs:93-287`,
consistent with the verified inspector dispatch path); the `build_batch` nested-reentry panic in
`entries/mod.rs`. Inspector dispatch/overlay wiring verified present. On-chain replay metering:
`_processNCalls` (`sync-rollups-protocol/src/L2/EEZL2.sol:343`).

### 14.3.7 [MEDIUM] `authorizedProxies` live-state poisoning within one transaction

**Scenario.** Proxy detection reads `authorizedProxies[target]` from **live journal state**, so a
proxy registered earlier in the **same tx/block** is honored. A malicious tx (**A-USER**) that
registers an attacker-controlled proxy and then calls it could redirect cross-chain dispatch
within one transaction.

**Impact.** Same-tx self-registration could redirect dispatch to an attacker-chosen identity if
registration were not gated. Bounded by the on-chain registration gates.

**Current mitigation.** Registration is gated by `EEZ`/`EEZL2` contract logic
(`onlySystemAddress` / owner paths in the predeploy bytecode); the inspector trusts whatever the
contract stored at slot 0. The on-chain gate is the defense.

**Recommended mitigation.** Confirm proxy registration cannot be triggered by arbitrary callers
within a composition (the on-chain `onlySystemAddress` / owner gates in
`sync-rollups-protocol/src/EEZ.sol` and `src/L2/EEZL2.sol`); specify the registration authority
normatively.

**Code-evidence.** Verified: inspector reads the live `authorizedProxies` slot; on-chain
registration gate in `sync-rollups-protocol/src/EEZ.sol` / `src/L2/EEZL2.sol`
(`onlySystemAddress` / owner paths).

### Gas griefing

### 14.3.8 [MEDIUM] Cross-chain sub-call gas is unmetered in simulation

**Scenario.** When the inspector synthesizes a cross-chain `CallOutcome` it passes
`Gas::new(inputs.gas_limit)` and the target's `gas_used` is **logged but not deducted** from the
caller frame. The composer's CCM-verify session further disables the block gas limit and sets
`tx_gas_limit_cap = u64::MAX`. So a cross-chain sub-call costs the caller **nothing** in
simulation, while on-chain replay (`executeIncomingCrossChainCall` at ~2M, `_processNCalls` on
L1) is metered. Adversary: **A-USER** crafting compositions cheap/free to simulate but expensive
on-chain.

**Impact.** Sim-vs-on-chain gas divergence can make a batch that simulated clean revert /
out-of-gas on L1 (bundle drop, settlement stall); unbounded cheap-in-sim cross-chain calls let an
attacker inflate the operator's posting cost without paying. The on-chain `POST_BATCH_GAS_LIMIT =
4M` and ~2M inbound cap bound the **on-chain** damage, but the off-chain mismatch is real (and
feeds the seed threat's bundle-drop loop, §14.3.1).

**Current mitigation.** On-chain `EXECUTE_INCOMING_GAS_LIMIT` (~2M) caps the system tx;
`POST_BATCH_GAS_LIMIT = 4M` caps the batch; sim relaxation is simulation-only, not consensus.

**Recommended mitigation.** Meter cross-chain sub-call gas in the off-chain composer against the
caller frame so simulation matches the on-chain `postAndVerifyBatch` replay; define a normative
gas budget for cross-chain sub-calls; classify gas-divergence sim failures as deterministic
poison and evict the offending tx **before** bundling.

**Code-evidence.** Verified Rust: synthesized outcome uses `inputs.gas_limit`, not metered
against the caller (`inspector.rs:677-719`); sim relaxations (`session.rs:613-620`). On-chain
`_processNCalls` metering: `sync-rollups-protocol/src/L2/EEZL2.sol:343`.

### Mempool / nonce / admission

### 14.3.9 [MEDIUM] Ingress admission skipped without an L1 provider (amplifies the seed threat)

**Scenario.** The ingress nonce-contiguity and L1-balance checks run **only** inside `if let
Some(provider) = l1_provider.as_ref()`. If `l1_provider` is `None`, a cross-chain tx is pushed to
the held pool with **no** nonce or balance validation. Adversary: any **A-USER** against a node
deployed without an ingress `l1_provider`.

**Impact.** Unvalidated cross-chain txs (bad nonce, insufficient balance) enter the held pool and
ride the all-or-nothing bundle, failing builder sim and evicting innocent bundle-mates / breaking
their nonce chains — the poison-pill + nonce-cascade the admission check exists to prevent.
**Directly amplifies the seed threat** (§14.3.1) by removing its first line of defense.

**Current mitigation.** When `l1_provider` **is** wired, precise nonce/balance rejection at the
door; `MAX_BUNDLE_ATTEMPTS` + nonce-cascade as a downstream backstop.

**Recommended mitigation.** Make `l1_provider` **mandatory** (fail-closed at startup) for any
deployment that admits cross-chain txs; a provider-less composer that admits cross-chain
classifications is **not** a conformant Rollup0 deployment ([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) normative
requirement).

**Code-evidence.** Verified Rust: `ingress.rs:162-202` (validation gated on `Some(provider)`),
`:209-225` (push runs regardless).

### Proof system / validator set

### 14.3.10 [CRITICAL] Mock proof system does not bind to the batch (devnet-only) — one signature authorizes ANY batch

**Scenario.** `MockECDSAProofSystem.verify` **ignores `publicInputsHash`** and recovers an ECDSA
signature over the *fixed constant* `MOCK_PROVER_DIGEST = keccak256("eez-mock-prover")`; the Rust
`MockEcdsaProver` signs exactly that constant. So a **single** valid 65-byte signature over the
fixed digest is accepted as a "proof" for **any `postAndVerifyBatch` contents whatsoever** —
**zero** cryptographic binding between the proof and the batch's entries/stateDeltas/callData. An
operator or anyone holding the single signer key (**A-KEY**) can post a batch with arbitrary
claimed `stateDeltas` and it passes verification. The permissioned *N*-of-*M* threshold is not
enforced in the mock (the wired composer uses `proofSystems=[mock]`, `proofSystemIndex=[0]`, a
single signer).

**Preconditions.** A deployment using `MockECDSAProofSystem` (what `DeployMockECDSAProofSystem.s.sol`
deploys), holding/compromising the single authorized signer key.

**Impact.** In the mock configuration, on-chain proof verification provides **no** integrity
guarantee (Layer 1 is defeated). Safety then rests **entirely** on Layers 2 and 3: Layer 2 still
blocks any batch violating the chained state roots or ether conservation, and Layer 3 catches a
self-consistent-but-dishonest chain — **but the on-chain stored `stateRoot` can be advanced to a
wrong value by a single signature until a follower diverges, and divergence is terminal (no
auto-repair)**. **Devnet-only** in intent; catastrophic if used beyond devnet.

**Current mitigation.** Documented as devnet-only / not a real proof system; the binding
`ECDSAProofSystem` (which recovers over the raw `publicInputsHash`) is the production system;
L1 re-derivation (Layer 3) is the backstop, not the proof.

**Recommended mitigation.** Make it a **deploy-time invariant** that `MockECDSAProofSystem` is
forbidden on any non-devnet chainId; mark mock proofs explicitly **NON-NORMATIVE** and require
the binding `ECDSAProofSystem` (raw `publicInputsHash` recovery) for any value-bearing
deployment. Pin the validator set to the binding PS and specify the *N*-of-*M* threshold (the
multi-prover threshold path is currently unimplemented in the wired composer).

**Code-evidence.** Verified: `contracts/src/MockECDSAProofSystem.sol:55-80` (ignores
`publicInputsHash`, recovers fixed digest); `crates/eez-prover/src/lib.rs:101-114` (signs
`MOCK_PROVER_DIGEST`). The binding `ECDSAProofSystem` recovers over the raw `publicInputsHash`
(no EIP-191): `sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:17,29-32`.

### 14.3.11 [MEDIUM] CI must assert the Rust public-inputs fold matches the deployed `EEZ.sol` fold byte-for-byte

**Scenario.** The authoritative on-chain protocol (`EEZ.sol`, `L2/EEZL2.sol`, `base/EEZBase.sol`,
`interfaces/IEEZ.sol`, `proofSystems/ECDSAProofSystem.sol`, `rollupContract/Rollup.sol`) lives in
the selected `sync-rollups-protocol` binding at
`5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`, so the on-chain
threats analyzed elsewhere are verifiable against source and the contracts match the Rust
expectations per audit. The one residual obligation is **continuous**, not analytical: the
off-chain `publicInputsHash` fold (Rust `public_inputs.rs`) and the on-chain fold (`EEZ.sol`)
must stay byte-identical, else every real-PS proof would fail verification (or, worse,
mis-verify).

**Impact.** Silent drift between the two folds — e.g. a field added or reordered on one side —
would break real-PS settlement (proofs no longer verify) or, worst case, mis-bind a proof to the
wrong public inputs. A build/CI-hygiene risk, not an unbounded attack surface: the contracts are
present and the folds currently agree.

**Current mitigation.** The Rust side mirrors the on-chain fold and is byte-locked against a
Foundry oracle (`public_inputs_hash_vectors.rs`); the profile pins the tested revision to prevent
silent drift.

**Recommended mitigation.** Assert at CI that the deployed `EEZ.sol` fold matches the Rust
`public_inputs.rs` fold **byte-for-byte**, and gate any submodule gitlink bump on re-running that
equality check. Pin which `EEZ.sol` fold shape is authoritative.

**Code-evidence.** Verified present: `sync-rollups-protocol/src/EEZ.sol`, `src/L2/EEZL2.sol`,
`src/base/EEZBase.sol`, `src/interfaces/IEEZ.sol`, `src/proofSystems/ECDSAProofSystem.sol`,
`src/rollupContract/Rollup.sol` at the selected `5c51e02` revision; Rust fold byte-locked
against the Foundry oracle (`public_inputs_hash_vectors.rs`).

### 14.3.12 [HIGH] `SYSTEM_ADDRESS` key compromise forges signed system operations

**Scenario.** Rollup0 v0 uses deterministic EIP-155-signed legacy transactions for both table
loads and inbound calls. The inbound envelope value comes from the prefunded system EOA, and the
contract requires `msg.value == value`. Composer and cross-chain derivers hold the same key so
they can reproduce identical bytes. An **A-KEY** attacker can sign forged table loads, inbound
calls, or ordinary transfers from that reserve.

**Impact.** A compromise can forge system behavior and drain or reallocate the prefunded balance.
The value equality check binds envelope value to calldata, but does not prove a corresponding
host-chain lock. A key-less follower cannot reproduce a cross-chain Sync block; a keyed follower
re-incurs the shared-key compromise domain.

**Current mitigation.** `onlySystemAddress` restricts callers, deterministic derivation detects
unsupported history, and the reserve bounds direct value loss.

**Recommended mitigation.** Use strict key custody and monitor the reserve and backing invariant.
Design and fully specify a key-free typed envelope before assigning any future transaction type.

**Code evidence.** `eez-evm/src/system_tx.rs` contains the shared context, calldata builders, and
legacy signer; `eez-node/src/main.rs:762-793` wires the follower context. The selected
`EEZL2.sol` enforces `onlySystemAddress` and `msg.value == value`. See
[Rollup0 Appendix C](../docs/rollup0-network-spec/C-system-transactions.md).

### 14.3.13 [HIGH] Stuck persistent queue blocks a rollup's deposits/withdrawals

**Scenario.** A persistent entry that reverts mid-execution (`StateRootMismatch` /
`RollingHashMismatch`) reverts the **whole** consuming tx **without advancing the cursor** —
**blocking** the queue rather than being skipped. A crafted or stale entry could wedge a rollup's
execution queue. (Only the *immediate* prefix is `try/catch`-skippable via
`ImmediateEntrySkipped`; the persistent path has exactly one valid consumption order.)

**Impact.** Liveness DoS on a single rollup's deposit/withdrawal pipeline. **Not safety:** the
`StateDelta.currentState` backstop (Layer 2) forces a stale entry to fail its *own* check rather
than corrupt others, and per-rollup queues isolate the wedge.

**Current mitigation.** Per-rollup queue isolation; the `currentState` backstop; immediate-prefix
skippability for the system-driven prefix.

**Recommended mitigation.** Specify a recovery procedure for a wedged persistent queue (e.g. an
operator-driven re-post that replaces the rollup's entries via wipe-on-verify, [EEZ Framework §4 — Execution Model](../docs/eez-protocol-spec/04-execution-model.md)
step 3); document that a persistent revert is non-skippable by design.

**Code-evidence.** Verified: the immediate prefix is `try/catch`-skippable via
`ImmediateEntrySkipped` (`sync-rollups-protocol/src/EEZ.sol:379-391`), whereas the persistent
path advances its cursor **only on success** — a reverting persistent entry reverts the whole
consuming tx and wedges the queue. On-chain consumption: `_processNCalls`
(`sync-rollups-protocol/src/L2/EEZL2.sol:343`).

### 14.3.14 [LOW] Signature malleability / v-range on proof signatures (mitigated, residual)

**Scenario.** ECDSA proof signatures are 65-byte `abi.encodePacked(r,s,v)`. A non-canonical
signer could attempt high-`s` or `v` outside `{27,28}` to produce malleable signatures or pass
one verifier but not another.

**Impact.** Minimal in current code — both the Rust signer and on-chain checks reject
non-canonical signatures. Residual risk only if a *future* verifier (or custom proof system)
omits the low-`s` / v-range checks.

**Current mitigation.** The Rust `EcdsaProofSigner` normalizes to low-`s` and `v = 27+recid`,
**refusing `recid > 1`** (`signer.rs:132-179`); the mock's bare `ecrecover` returns
`address(0)` on malformed inputs and the non-zero-signer check rejects those
(`MockECDSAProofSystem.sol:75-79`); OZ `ECDSA.recover` in the real PS rejects high-`s` and `v`
not in `{27,28}`.

**Recommended mitigation.** Make low-`s` + `v ∈ {27,28}` a **normative** requirement for every
`IProofSystem` verifier and add a conformance test for any new proof system contract. Document
the exact signed digest (raw `publicInputsHash`, no EIP-191) as authoritative.

**Code-evidence.** Verified: `crates/eez-evm/src/signer.rs:132-179`;
`contracts/src/MockECDSAProofSystem.sol:75-79`. Binding PS uses OZ `ECDSA.recover` over the raw
`publicInputsHash` (no EIP-191), with the `v ∈ {27,28}` requirement documented in the contract:
`sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:13-15,17,29-32`.

### Data availability

### 14.3.15 [INFORMATIONAL] Calldata is selected; the blob proposal is unimplemented

**Scenario.** The current Rollup0 profile mandates tag-`0x00` calldata and requires empty
`blobIndices`. The implementation matches that choice and **hard-rejects** any non-empty
`blobIndices` with `UnsupportedBlobIndices` (the off-chain fold would hash an empty
`blob_hashes` slice and mismatch the on-chain `blobhash(blobIndices[i])` fold). There is no
KZG/sidecar/4844-tx construction. Blob support is an informative future proposal, not a missing
requirement of `rollup0-chiado@0.1-draft`. No L2 user is currently charged any L1 DA fee.

**Impact.** **No data-withholding attack exists on calldata** — it is on L1 and fully public, so
there is nothing to withhold (a *positive* property). All DA rides L1 calldata, bearing the full
calldata cost on the operator EOA with **no L2-side reimbursement**. Under high host base fee the
operator may stop posting (liveness — feeds §14.3.18). That is an unresolved fee-policy risk, not
a blob-conformance failure.

**Current mitigation.** Calldata is fully available (no withholding possible); `blobIndices`
forced empty and rejected if non-empty (loud fail).

**Future mitigation.** A later profile may specify EIP-4844 blob payload framing (tag byte, body reuse),
the `blobIndices → blob` binding, the off-chain `blobhash` resolution mirroring the on-chain
walk, and the cost comparator that picks the channel. Production fee policy must define who pays
host DA cost independently of that future choice.

**Code-evidence.** Verified: `eez-evm-inspector/src/post_batch_submitter.rs:154-168,354-363`
(`UnsupportedBlobIndices` reject); `eez-payload-codec/src/lib.rs:48` (only tag `0x00`). DA-fee
oracle absent (design-level). See [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md),
[Appendix A](IMPLEMENTATION_NOTES.md).

### 14.3.16 [HIGH] Partial bundle inclusion (relay honoring reverting whitelists)

**Scenario.** A relay that honors `revertingTxHashes` could drop a *reverting* user_tx and land
`postAndVerifyBatch` + a prefix, advancing L1 to a **mid-chain prefix root** and desyncing the
composer (observed on Chiado). Adversary: **A-NET** (the relay) or a misconfigured submitter. The
mempool-fallback path (`eth_sendRawTransaction` when the relay lacks `eth_sendBundle`) drops the
all-or-nothing guarantee entirely.

**Impact.** L1 advances to a partial prefix while L2 committed the full Sync block → L1↔L2
desync. **Not safety:** the reconcile endpoint is the *last-applied* `newState` (L1's actual
post-batch root) and commit-then-repair / re-derivation correct the divergence; but settlement
stalls and recovery churns.

**Current mitigation.** **Strict all-or-nothing** — empty `revertingTxHashes`/`droppingTxHashes`
whitelists, so the builder must include the whole bundle in order or drop it — plus
`MAX_USER_TXS_PER_BUNDLE = 3`. Settlement uses the last-applied root, not the claimed full-chain
end ([Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md), [Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)).

**Recommended mitigation.** Treat a relay lacking `eth_sendBundle` (or honoring reverting
whitelists) as **not providing atomicity** — a deployment constraint, not a fallback. Combine
with the seed-threat fix (§14.3.1) of landing `postAndVerifyBatch` independently of user txs.

**Code-evidence.** Verified Rust: `submitter.rs:511-526` (strict all-or-nothing);
`composer.rs:589-596`. Mempool fallback (`submitter.rs:296-365`) drops atomicity.

### 14.3.17 [LOW] Event-selector / receipt spoofing of the settlement verdict

**Scenario.** A rogue contract called inside the `postAndVerifyBatch` transaction emits a
**colliding `BatchPosted` / `L2ExecutionPerformed` selector** to spoof `rollupCount` or inject a
fake `L2ExecutionPerformed`, fooling the off-chain outcome parser into a false `Settled` verdict.
Adversary: **A-USER** deploying such a contract into the bundle's execution path.

**Impact.** A spoofed `Settled` could make the composer drop recovery prematurely. **Mitigated:**
the parser filters strictly.

**Current mitigation.** `decode_outcome` filters logs to `log.address() == eez_address` and
requires exactly one `BatchPosted`; `settlement_in_block`/scan filter by the `EEZ` address **and**
the `rollupId` topic — so a rogue contract's collision is ignored
(`post_batch_submitter.rs:575-607`; `submitter.rs:471-476`). See [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md).

**Recommended mitigation.** Keep the address+topic filter as a normative requirement of any
outcome parser; add a regression test asserting a colliding-selector log from a non-`EEZ` address
is ignored.

**Code-evidence.** Verified Rust: `post_batch_submitter.rs:575-607`; `submitter.rs:471-476`.

### Economic

### 14.3.18 [MEDIUM] Zero beneficiary and system-account fee exhaustion

**Scenario.** The v0 beneficiary is `Address::ZERO`: base fees burn and priority fees are
economically inaccessible. There is no L1-data-fee reimbursement. System transactions pay a
fixed 1 gwei gas price with a 2,000,000 gas limit from the prefunded `SYSTEM_ADDRESS`; delivery
halts when the account cannot cover up-front gas or when the block base fee exceeds the fixed
price.

**Impact.** The operator has no protocol income against host-chain posting costs, and system
balance or fee-market drift can halt cross-chain delivery.

**Current mitigation.** Development genesis prefunds the account. Deployments can monitor its
balance and base-fee headroom.

**Recommended mitigation.** Specify provisioning, monitoring, and top-up operations for the
system reserve. Any non-zero beneficiary, dynamic gas-price rule, or L1-cost recovery must be a
versioned profile change
([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)).

**Code evidence.** `deriver.rs:496`, `composer.rs:570`, `sequencer.rs:118`;
`eez-node/src/main.rs:704-705,968-969`.

### Application-layer (informative)

### 14.3.19 [MEDIUM] Predictable `prev_randao`

**Scenario.** `prev_randao` (mixHash) is hard-coded `B256::ZERO` in **all three** STF paths
(sequencer, deriver, Sync-block composer). Any L2 contract reading `block.prevrandao` observes a
constant zero, so any RNG/lottery/commit-reveal relying on `PREVRANDAO` is fully predictable and
gameable by **A-USER**.

**Impact.** Predictable on-chain randomness at the application layer. **Not a protocol-state
safety issue** (state still re-derives deterministically), but a real app-layer vulnerability —
and a divergence risk if the value ever becomes non-zero without all three paths agreeing
byte-for-byte.

**Current mitigation.** All three paths agree on ZERO so block hashes do not diverge; a comment
asserts "no security depends on `prev_randao` yet."

**Recommended mitigation.** Either fix `prev_randao = 0` as a permanent normative Rollup0 choice
and **warn app developers** that `PREVRANDAO` is unusable for randomness, or implement the
deferred L1-derivation (define which L1 field, sampled at which L1 block, constant-per-sync-slot
vs per-block) and bind it identically across sequencer/deriver/composer.

**Code-evidence.** Verified: `sequencer.rs:145-147`; `deriver.rs:480`; `local/build.rs:92-103`
(all `B256::ZERO`, must match byte-for-byte).

### Derivation / recovery (cross-cutting)

### 14.3.20 [HIGH] L1 deep reorg halt + false-death verdict / recovery-vs-deriver war

The most subtle pair in the catalogue. Adversary: **A-NET** / environmental (a deep L1 reorg) or
**A-OP** (timing).

**(a) Deep-reorg halt.** The `L1Watcher` keeps a ring of `(number, hash)` bounded by
`reorg_max_depth` (default **62**). A reorg **deeper than the ring**, or one across a catch-up
gap with no in-bounds common ancestor, **halts** with `ReorgTooDeep`. For shallower reorgs the
deriver retreats the cursor and `reorg_to`s the head, and the composer's finality audit
re-verifies each Settled `postAndVerifyBatch` receipt before dropping; but on a deep-reorg halt
there is **no automated recovery** — the behavior of in-flight Pending optimistic batches and the
cursor during the halt is **unspecified**, requiring operator intervention. The deriver's
`reconcile_batch_blocks` is also explicitly **non-transactional**: a mid-loop replay failure
leaves earlier blocks committed (a half-state).

**(b) False-death verdict / recovery-vs-deriver war.** The settlement observer returns `Dropped`
**only** when `head > target_block` without the `postAndVerifyBatch` appearing ("provably dead") —
**never** a wall-clock timeout, *precisely because* a false-death verdict would trigger a rollback
that fights the Deriver re-canonicalizing the batch from L1: the observer marks Failed, recovery
reorgs out a block the Deriver canonicalized from L1, the Deriver restores it, loop — every
interim `postAndVerifyBatch` anchoring the wrong root.

**Impact.** (a) Derivation/composition stalls (liveness) on a deep reorg; in-flight optimistic
Sync blocks may have anchored against rolled-out batches with no defined cleanup; the
non-transactional reconcile can leave a half-advanced local L2. (b) A naive timeout-based verdict
would cause an oscillating reorg war and persistently wrong anchored roots. Both are
**liveness/consistency**, not theft — L1 remains the arbiter.

**Current mitigation.** `reorg_max_depth = 62` matches the Ethereum finality bound; shallow
reorgs handled by `retreat_l2_to_cursor` + `reorg_to`; the finality audit re-verifies receipts
before dropping; "never swallow a reorg" (old-tip canonicality verified before reseed). For (b):
`Dropped` is *provably-dead-only*; `resolve_below_cursor` overrides a false `Failed → Settled`;
`recover_failed_batch` re-checks `cursor ≥ sync_height` under the reconcile lock and **drops
recovery** (the stale-verdict guard) — the Deriver cursor is the stronger oracle
([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md), [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)).

**Recommended mitigation.** Define a **normative deep-reorg recovery procedure**: on
`ReorgTooDeep`, quiesce production, drop all Pending/Settled optimistic entries above the new
common ancestor, re-derive from genesis (or the deploy block), and gate restart on operator ack.
Make `reconcile_batch_blocks` **transactional** (snapshot the canonical head pre-loop, roll back
on any per-block failure).

**Code-evidence.** Verified Rust: `l1_watcher.rs:9-12,127-131` (`ReorgTooDeep` halt);
`deriver.rs:901-966` (shallow-reorg retreat path); `deriver.rs:1032-1037` (non-transactional
reconcile); `submitter.rs:413-418` (provably-dead-only `Dropped`); `optimistic.rs` /
`composer.rs:803-846` (stale-verdict guard). Deep-reorg in-flight cleanup: no code path
(design-level gap, [Appendix A](IMPLEMENTATION_NOTES.md)).

### Replay, custody, and governance

### 14.3.21 [HIGH] Zero block context removes the intended replay domain

**Scenario.** Live builders initialize `blockNumber = 0`, and the posting path does not replace
it. The reference manager accepts zero and returns `(timestamp, blockHash) = (0, 0)`. A posted
batch is therefore not tied to a nonzero canonical host block.

**Impact.** The intended recent-block replay bound and fork-context check are absent. A binding
verifier would still authenticate a timeless digest unless construction is fixed.

**Mitigation.** Reject both sentinels; select and validate a recent explicit host block before
proof construction; and rebuild after a reorg or expiry.

**Code evidence.** `crates/eez-evm/src/batch.rs:54`;
`crates/eez-composer/src/composer.rs:1693-1930`;
`sync-rollups-protocol/src/rollupContract/Rollup.sol:131-149`.

### 14.3.22 [HIGH] Nested outbound ETH is omitted from entry accounting

**Scenario.** `_applyAndExecute` receives the value total only from its outer `_processNCalls`.
`_consumeNestedAction` invokes the function recursively and discards its returned outbound total.

**Impact.** A nested successful outflow can reduce physical EEZ custody without an equal reduction
in recorded liabilities. Individual underflow checks and the implemented entry equation can pass
while aggregate custody is under-backed.

**Mitigation.** Accumulate value across every nesting depth with revert-safe entry-scoped
accounting. Reject nested value-bearing entries until that is implemented.

**Code evidence.** `sync-rollups-protocol/src/EEZ.sol:769-785,890-942`.

### 14.3.23 [CRITICAL] Manager and verifier administrators can replace validity policy

**Scenario.** The manager owner can change proof systems, vkeys, threshold, and the registered
root. The ECDSA verifier owner can replace its signer. There is no protocol delay or dispute
window.

**Impact.** These roles control validity, availability, and effective custody. A follower can
detect and halt, but cannot stop the policy change, reverse an applied outflow, or exit.

**Mitigation.** Publish the complete deployment, code, and admin tuple; separate compromise
domains; use threshold governance and observable delays; and remove unneeded escape or signer
rotation powers.

**Code evidence.** `sync-rollups-protocol/src/rollupContract/Rollup.sol:173-216`;
`sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:18-31`.

### 14.3.24 [HIGH] Per-block root-set attribution can invent an applied prefix

**Scenario.** The scanner groups all applied roots for a rollup into a per-block `HashSet`, then
credits each batch in that block by set membership. It loses receipt order, duplicate
multiplicity, and the association between a deferred trigger and its batch.

**Impact.** A follower can reconstruct the wrong system-transaction or receipt prefix while
selecting a root that appeared elsewhere in the block. Root replay does not authenticate exact
history for root-preserving operations.

**Mitigation.** Preserve transaction/log order and multiplicity, bind each applied entry to its
batch or trigger, and halt on non-prefix or ambiguous patterns.

**Code evidence.** `crates/eez-l1/src/scan.rs:136-205,236-260`;
`crates/eez-deriver/src/deriver.rs:1092-1098,1151-1168`.

## 14.4 Residual-risk summary

| # | Threat | Category | Severity | Status | Where addressed |
|---|---|---|---|---|---|
| 14.3.1 | Same-nonce L1 race bricks the bundle (SEED) | mempool/nonce | **HIGH** | open (mitigated partial) | Fix in [App. A](IMPLEMENTATION_NOTES.md); §14.3.1 |
| 14.3.2 | No force-inclusion / escape hatch | sequencer/operator | **HIGH** | **accepted** (Rollup0) | Rollup1 ([Rollup0 §10 — Future Design](../docs/rollup0-network-spec/10-future-design.md)) |
| 14.3.3 | Sequencer↔follower equivocation (`Unverifiable>1024`) | sequencer/operator | LOW | mitigated | §14.3.3; harden cap |
| 14.3.4 | Operator timestamp manipulation | sequencer/operator | MEDIUM | mitigated (safety) | §14.3.4 |
| 14.3.5 | STATICCALL/DELEGATECALL-to-proxy dispatch | cross-chain | **HIGH** | open | Fix in [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.6 | Overlay drops code/nonce, hard-fails selfdestruct | cross-chain | MEDIUM | open | Fix/forbid in [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.7 | `authorizedProxies` live-state poisoning | cross-chain | MEDIUM | mitigated (on-chain gate) | §14.3.7 (on-chain registration gate) |
| 14.3.8 | Cross-chain sub-call unmetered in sim | gas griefing | MEDIUM | open | §14.3.8 |
| 14.3.9 | Admission skipped without `l1_provider` | mempool/nonce | MEDIUM | open (amplifies SEED) | [Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md) normative; [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.10 | Mock PS does not bind to batch | proof-system | **CRITICAL** | **devnet-only / accepted** | Binding PS; Rollup1 ZK (§14.5) |
| 14.3.11 | CI fold-equality (Rust ↔ `EEZ.sol`) | proof-system | MEDIUM | open (CI obligation) | CI fold-equality; gate gitlink bumps |
| 14.3.12 | `SYSTEM_ADDRESS` key sprawl forges system operations | cross-chain | **HIGH** | open | Appendix C; future key-free envelope |
| 14.3.13 | Stuck persistent queue (deposit/withdrawal DoS) | proof-system | **HIGH** | mitigated (isolation) | §14.3.13 recovery proc |
| 14.3.14 | Signature malleability / v-range | proof-system | LOW | **mitigated** | §14.3.14 |
| 14.3.15 | Calldata selected; blob proposal unimplemented | DA | INFORMATIONAL | conforms; future proposal | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md); [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.16 | Partial bundle inclusion | DA | **HIGH** | mitigated (strict bundle) | §14.3.16; SEED fix |
| 14.3.17 | Event-selector / receipt spoofing | DA | LOW | **mitigated** | §14.3.17 |
| 14.3.18 | Zero beneficiary + system reserve exhaustion | economic | MEDIUM | open | §14.3.18 |
| 14.3.19 | Predictable `prev_randao` | application | MEDIUM | open (app-layer) | §14.3.19 |
| 14.3.20 | Deep-reorg halt + recovery-vs-deriver war | derivation | **HIGH** | mitigated (b) / open (a) | Deep-reorg proc in [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.21 | Zero L1 proof context | replay/domain | **HIGH** | open | §14.3.21; [App. A H-6](IMPLEMENTATION_NOTES.md#h-6-live-batches-retain-the-zero-l1-context-sentinel) |
| 14.3.22 | Nested value omitted from accounting | custody | **HIGH** | open | §14.3.22; [App. A H-8](IMPLEMENTATION_NOTES.md#h-8-nested-outbound-eth-is-omitted-from-entry-accounting) |
| 14.3.23 | Manager/verifier admin authority | governance | **CRITICAL** | accepted trust assumption | §14.3.23 |
| 14.3.24 | Root-set settlement attribution | derivation | **HIGH** | open | §14.3.24; [App. A H-9](IMPLEMENTATION_NOTES.md#h-9-deriver-attributes-applied-roots-by-per-block-set-membership) |

**Status legend.** *mitigated* means a mechanism reduces the threat; *accepted* is an explicit
trust assumption or limitation; *open* is a known gap. Detection by a follower can reduce the
accepted view to a halt, but it cannot reverse host-chain effects or guarantee custody recovery.

## 14.5 What Rollup1 changes for security

Rollup1 ([Rollup0 §10 — Future Design](../docs/rollup0-network-spec/10-future-design.md)) is not a feature release; it is the retirement of three
whole threat *classes* that Rollup0 accepts by construction.

- **Force-inclusion + trustless exit kills the censorship / no-exit class.** An L1
  force-inclusion inbox and a permissionless withdrawal path remove §14.3.2 (and defang the
  liveness edge of §14.3.13, §14.3.18): a censored or stalled operator can no longer freeze
  funds, because any party can drive inclusion/exit through L1 after a timeout. Liveness stops
  depending on the single operator.
- **A ZK validity proof kills the committee-trust + mock-binding class.** Replacing the
  permissioned *N*-of-*M* ECDSA attestation with a zkEVM validity proof removes the *entire*
  reliance on Layer 1 being honest: §14.3.10 (mock binds to nothing) and §14.3.14 (signature
  malleability) become moot, and the committee-collusion residual behind §14.2 disappears — the
  proof *is* the binding, and Layer 3 re-derivation becomes a redundancy check rather than the
  load-bearing safety backstop.
- **A key-free envelope removes `SYSTEM_ADDRESS` key sprawl.** A future deterministic envelope
  could let a deriver reconstruct system transactions without a private key. Type `0x7E` is an
  unselected design option, not the active v0 envelope.

The architecture is already shaped for these swaps: the proof-system interface is
mechanism-agnostic ([EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md)), the deriver reconstructs state
deterministically ([Rollup0 §6 — Derivation](../docs/rollup0-network-spec/06-derivation-following.md)), and the sequencing role is structurally
separable from settlement. The Rollup0 compromises catalogued here are therefore **deliberate
and temporary** — the threats marked *accepted* in §14.4 are exactly the ones §16 retires.

---

*Next: [Chapter 15 — Related Work](related-work.md).*
