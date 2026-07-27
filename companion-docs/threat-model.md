# Implementation Threat Catalog

> **Informative companion material.** The normative model is
> [Rollup0 §9 — Security and Trust](../docs/rollup0-network-spec/09-security-trust-model.md).
> This catalog describes the reviewed
> `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` implementation and its
> recorded older contract binding. It does not define Rollup0's target network
> model. In particular, Rollup0 candidate admission is open: any composer may
> submit a valid candidate, validators/provers sign any candidate they determine
> is correct, and the first applicable Ethereum settlement transaction wins.
> References below to a single operator, Chiado settlement, or the old
> permissioned-attestation deployment describe an implementation configuration
> or historical review assumption. They are not normative production choices.

## 14.1 Audit scope and adversaries

The inspected development configuration is centralized and uses permissioned
proof-system membership. Producer admission and proof-system membership are
different controls. The target Rollup0 network does not authorize one composer;
the implementation is expected to accept competing externally posted batches.
The implementation controls audited here are conditional:

| Party or component | Relevant authority | Failure consequence |
|---|---|---|
| **Manager owner/governance** | Changes proof systems, vkeys, and threshold; can replace a registered root. | Can remove effective validity checking, install an arbitrary commitment, halt settlement, and affect custody policy. |
| **Validators and verifier administrators** | Decide whether a digest is accepted; the ECDSA verifier administrator can replace its signer. | A malicious threshold or compromised verifier can authorize invalid state or value movement, subject only to limited contract checks. |
| **Any composer** | May produce an unsafe candidate, calldata, batch, and transaction bundle. | A composer can publish invalid or unavailable data, but validity checking MUST reject it. A local composer can still censor its own RPC users. |
| **Relay/builder** | Supplies all-or-none, ordered, same-block inclusion outside the EVM. | A successful transaction prefix remains on L1; follower repair cannot reverse it. |
| **Ethereum settlement chain** | Supplies canonical execution, receipts, DA, ordering, and finality. | Reorganizations move the safe head; Ethereum consensus failure is outside Rollup0. Chiado substitutes for Ethereum only in development. |
| **Reviewed development `SYSTEM_ADDRESS` key holders** | Sign historical deterministic legacy system transactions from a prefunded EOA. | Can forge development system operations and drain or reallocate that reserve. |
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
4. **Follower replay.** A follower can reject an invalid endpoint or rebuild a unique applied
   prefix. It cannot undo an accepted root, return pooled funds, or submit a fraud proof.
5. **Bundle relay.** The transaction pair is synchronous only when an external relay includes
   both transactions, in order, in one block, or neither. The proof digest does not commit to the
   trigger hash or bundle membership.

The resulting evidence is graded: operator output is unsafe; EEZ execution establishes an
L1-accepted root; matching reconstruction establishes a follower-safe view; and Ethereum finality
protects that view from ordinary reorganization. None removes manager, validator, custody, or
exit assumptions.

## 14.3 Ranked threat catalogue

### 14.3.1 [HISTORICAL, RESOLVED] Same-nonce L1 race stalled the settlement bundle

**Historical mechanism.** After ingress admitted an L1-bound trigger, its sender could land a
different L1 transaction with the same nonce. The held trigger then had
`nonce < account_nonce`. Earlier recovery checked only for a receipt under the held transaction's
own hash, so it could not identify the different-hash nonce burn and could rebuild the same
failing all-or-nothing bundle until bounded retry eviction. The result was a repeatable settlement
stall while L2 cadence continued.

**Resolution at the reviewed revision.** Candidate construction now checks canonical source-account
state before it derives effects. For inbound triggers it reads the L1 account nonce; for outbound
triggers it reads the Sync parent-state nonce. `partition_stale` removes every held transaction
whose nonce is lower than the successfully read source nonce, and the pool releases those stale
reservations before simulation. A different-hash same-nonce transaction is therefore detected by
account state. It is not rebuilt for three slots merely because `receipt_exists(held_hash)` is
false.

The recovery path still uses the exact held hash to decide whether that exact transaction received
a receipt. That check is appropriate for inclusion recovery and no longer carries sole
responsibility for stale-nonce detection: every subsequent candidate construction repeats the
account-state preflight.

**Residual.** A source-nonce read failure logs a warning and fails open for that sender. The
composer proceeds to fresh simulation without adding a nonce value to `source_nonces`. This removes
the deterministic preflight guarantee for that attempt. A stale or inconsistent provider can
therefore cause a bundle drop or settlement delay until a later successful read or simulation
classifies the transaction. This is a narrower provider-availability and consistency risk, not the
verified different-hash three-slot loop above.

**Required hardening.** Treat a canonical source-nonce read failure as transient and exclude that
sender from the candidate until the read succeeds. Continue to remove stale triggers before
deriving effects, and never submit a post whose committed effect list names an excluded trigger.
The exact post and all selected triggers must still form the consecutive all-or-none operation in
[Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md).

**Code evidence.** Inbound nonce reads:
`crates/eez-composer/src/composer.rs:182-210`; outbound parent-state reads: `:212-240`;
stale partition: `:242-250`; compose-time removal and release: `:1197-1217`. The fail-open warning
paths are `:198-206,228-236`. Exact-hash recovery remains at `:900-923`.

---

The remaining threats are grouped by category.

### Composer and inclusion

### 14.3.2 [HIGH] No forced transaction inclusion or trustless exit

**Scenario.** The reviewed implementation has no Ethereum inbox,
force-inclusion mechanism, or trustless exit. One local composer can decline a
user transaction. Under the target protocol, that composer is not privileged:
the user can submit to another composer or run one, and validators/provers must
evaluate any correct candidate. There is still no protocol mechanism that
forces a particular transaction into a candidate or guarantees proof
availability for it.

**Preconditions.** Network-wide censorship requires all reachable composers,
the required proof providers, or Ethereum inclusion to exclude the
transaction. Censorship by one RPC endpoint requires only that endpoint.

**Impact.** A local composer can censor its users. If every viable candidate
path is unavailable or censoring, L2 liveness stops. Without a selected
trustless exit, bridged funds can remain unavailable even though no individual
composer has protocol authorization.

**Current mitigation.** Open candidate admission removes the single-composer
gate. It does not itself create a forced inclusion path, guarantee proofs, or
recover custody.

**Recommended mitigation.** A possible future revision could add an L1 force-inclusion inbox and
a permissionless withdrawal or exit path that does not require a composer. No such design is
selected or specified; §10 lists the possibility only. Rollup0 currently has **no** trustless
exit, so bridged-fund availability still depends on the complete candidate, proof, and Ethereum
inclusion path.

**Code-evidence.** Design-level (verified by *absence*): no force-include/inbox/escape-hatch
code in the composer or deriver; deposits/withdrawals flow only through composer-built system
txs (`crates/eez-protocol/src/system_tx.rs:65-197`) and operator-posted entries.

### 14.3.3 [LOW] Unknown ancestry is optimistically accepted

**Scenario.** A follower polls the sequencer RPC `eth_getBlockByNumber(Latest)` and advances
only the **unsafe** head. A malicious/buggy sequencer (**A-OP**) publishes a branch not
descending from the L1-confirmed safe anchor. `check_extends_safe` classifies it:
same-height-different-hash or below-safe ⇒ `Conflicts` (rejected before the engine); otherwise it
walks the candidate's `parent_hash` chain down to safe height. A missing parent returns
`Unverifiable` immediately, at **any** distance above safe. A fully available walk that exceeds
`MAX_ANCESTRY_WALK = 1024` is also `Unverifiable`. `advance` rejects only `Conflicts`, so both
`Unverifiable` cases are passed optimistically to the engine.

**Preconditions.** An equivocating branch with any parent that the follower has not synced, or a
fully known branch whose safe-ancestry walk exceeds 1024.

**Impact.** Transient acceptance of a stale/equivocating *unsafe* head until the deriver corrects
it from L1. **Safe/finalized are owned solely by the deriver** (L1-derived), so safety is **not**
violated — the head is reorged back. A brief optimistic-acceptance surface, not a persistent
compromise.

**Current mitigation.** `check_extends_safe` rejects `Conflicts` heads before the engine; the
deriver owns safe/finalized from L1 and reorgs the unsafe head back; `advance_unsafe_head` leaves
safe/finalized untouched. The local producer's configurable
`DEFAULT_MAX_SPECULATIVE_DEPTH = 64` does not constrain a remote sequencer observed by the
follower and can be disabled.

**Recommended mitigation.** Fetch and verify the missing ancestry before advancing, or reject all
`Unverifiable` candidates. If the 1024 cap remains, specify it as a resource limit rather than as
the boundary at which unknown ancestry first becomes acceptable.

**Code-evidence.** Verified Rust:
`crates/eez-node/src/follower.rs:143-157,218-263`; local producer limit:
`crates/eez-node/src/main.rs:398-405`.

### 14.3.4 [LOW] Timing-configuration and L1-clock dependence

**Scenario.** The reviewed client does **not** give a composer per-block timestamp discretion.
Ordinary blocks use the configured `l2_block_time` increment, implemented with saturating
addition. The result equals `parent.timestamp + l2_block_time` except at `uint64` overflow, where
the missing checked error is a known deviation. A Sync-slot target is derived from the observed L1
header timestamp plus the configured L1 block time. The operator still selects the startup timing
configuration and the L1 RPC source.

**Impact.** Incorrect timing configuration or a bad L1-head source can produce timestamps that do
not match the intended network profile. This is configuration/source trust, not arbitrary
per-block timestamp manipulation. With matching inputs, sequencer, composer, and deriver
reconstruct the same timestamps.

**Current mitigation.** The producer and deriver both enforce the configured cadence, and the
Sync-slot scheduler derives its target from an observed L1 header.

**Recommended mitigation.** Pin the timing parameters in each network profile, validate the
runtime configuration against that profile, and define the required L1-head source and
canonicality checks. Applications should treat L2 time as profile-derived settlement time.

**Code-evidence.** Verified Rust:
`crates/eez-driver/src/sequencer.rs:747-761`;
`crates/eez-driver/src/slot.rs:270-298,342-368`;
`crates/eez-deriver/src/deriver.rs:460-497`.

### Cross-chain composition

### 14.3.5 [HIGH] STATICCALL (and DELEGATECALL/CALLCODE) to a proxy triggers a state-mutating dispatch

**Scenario.** `SessionInspector::call` computes `inputs.scheme`
(`CALL`/`CALLCODE`/`DELEGATECALL`/`STATICCALL`) but uses it **only in a tracing log** — no scheme
gate. On **every** CALL-family frame whose target is a registered `authorizedProxy`, it builds an
`ExecutionRequest` and dispatches a cross-chain call regardless of scheme. A **`STATICCALL`** to a
proxy thus initiates an ordinary target simulation that can mutate staged remote state from a
context the source EVM guarantees is read-only. The `STATICCALL` itself carries zero value.
`DELEGATECALL`/`CALLCODE` to a proxy bind the proxy's cross-chain identity under the *caller's*
storage context, semantically undefined for the 6-field source/target attribution. Adversary:
**A-USER** crafting a contract whose read path targets a proxy.

**Impact.** Cross-chain side effects (remote calls and `stateDelta` accrual) can be
induced from a context that should be side-effect-free, breaking EVM static-context guarantees —
enabling read-path-triggered remote mutation or simulation-versus-replay desynchronization;
soundness of dispatch from non-`CALL` schemes is unspecified.

**Current mitigation.** None in code — the scheme is logged only.

**Recommended mitigation.** Gate dispatch on scheme: refuse (return `None` / synthesize a revert)
for `StaticCall`; define or forbid `DelegateCall`/`CallCode`-to-proxy. At minimum a `STATICCALL`
to a proxy must **not** dispatch a state-mutating cross-chain call — specify that only
`CallScheme::Call` may dispatch.

**Code-evidence.** Verified:
`crates/eez-evm-inspector/src/inspector.rs:489-540,641-719`; scheme is converted to a label at
`:526-531` and logged at `:693`. No `CallScheme` dispatch gate exists.

### 14.3.6 [MEDIUM] Overlay diff-apply drops code/nonce changes and hard-fails SELFDESTRUCT

**Scenario.** The overlay diff-apply for nested cross-chain dispatch applies **only** storage
writes and balance changes back onto the source journal. **Code installation and nonce changes
are silently deferred/skipped**, transient storage is ignored, and `SELFDESTRUCT` raises a loud
`OverlayError::Selfdestruct`. A nested cross-chain call that deploys a contract
(`CREATE`/`CREATE2`) or bumps a nonce **mis-simulates** versus on-chain replay; one that
selfdestructs **cannot compose at all**. Adversary: **A-USER** with a composition whose nested
call deploys code, changes a nonce, uses transient storage cross-call, or selfdestructs.
Successful nested re-entry is implemented. Unsupported nested failed/static lookup lowering and
cyclic non-entry re-entry fail closed with typed `Unsupported` or `InvalidReentry` errors.

**Impact.** Off-chain composition can diverge from on-chain re-derivation for these mutation
classes, breaking commit-then-repair — caught only **later** as a state-root divergence →
`LocalDiverged`. On a live event, that error triggers catch-up; failed resync is retried after the
next L1 event. Boot catch-up can refuse startup. This is a repeated liveness failure, not silent
corruption. SELFDESTRUCT-bearing cross-chain flows are unsupported.

**Current mitigation.** SELFDESTRUCT and unsupported re-entry shapes fail with typed errors;
successful nested re-entry is lowered; storage and balance changes are applied. Other overlay
divergence surfaces as `LocalDiverged` and enters the live recovery path rather than becoming
silent corruption.

**Recommended mitigation.** Either extend overlay diff-apply to handle code-install and nonce
changes (and define transient-storage semantics), or **normatively forbid** nested cross-chain
calls that deploy code / change nonces / selfdestruct, **rejecting such compositions at compose
time** rather than mis-simulating. Specify the supported nested failed/static lookup behavior.

**Code-evidence.** Verified: overlay diff-apply
`crates/eez-evm-inspector/src/overlay.rs:149-180,195-287`; nested lowering and typed failures
`crates/eez-protocol/src/entries/mod.rs:130-184,1831-1873`; cyclic re-entry guard
`crates/eez-protocol/src/composition.rs:748-835`; live deriver recovery
`crates/eez-deriver/src/deriver.rs:607-688`.

### 14.3.7 [INFORMATIONAL] Permissionless deterministic proxy registration is intentional

**Scenario.** In the selected 0.2 core, `createCrossChainProxy` is permissionless. Any caller can
create the canonical proxy for a chosen remote `(originalRollupId, originalAddress)` tuple, except
for a tuple on the local network. Creation uses `CREATE2` with fixed `CrossChainProxy` bytecode and
immutable identity fields. Proxy detection reads the registration mapping from **live journal
state**, so a canonical proxy created earlier in the same transaction is immediately usable.

**Impact.** A caller can pre-create or use a canonical proxy but cannot substitute
attacker-controlled proxy bytecode for that tuple. Authorization of the represented remote
identity remains the responsibility of the destination application.

**Current status.** Same-transaction creation and use conform to the selected permissionless
factory design. There is no `onlySystemAddress` or owner gate on proxy creation.

**Recommended mitigation.** Specify permissionless deterministic creation, the exact proxy
bytecode and address derivation, and destination-side authorization requirements. A network
profile that intends restricted registration needs a different selected contract.

**Code-evidence.** Selected core:
`eez-core-protocol/src/base/EEZBase.sol:145-170`;
`eez-core-protocol/src/base/CrossChainProxy.sol:26-33`; live inspector lookup:
`crates/eez-evm-inspector/src/inspector.rs:246-272,511-539`.

### Gas griefing

### 14.3.8 [MEDIUM] Cross-chain sub-call gas is unmetered in simulation

**Scenario.** When the inspector synthesizes a cross-chain `CallOutcome` it passes
`Gas::new(inputs.gas_limit)` and the target's `gas_used` is **logged but not deducted** from the
caller frame. The composer's CCM-verify session further disables the block gas limit and sets
`tx_gas_limit_cap = u64::MAX`. So a cross-chain sub-call costs the caller **nothing** in
simulation, while on-chain replay executes inside an EVM-metered transaction. Adversary:
**A-USER** crafting compositions cheap/free to simulate but expensive on-chain.

**Impact.** Sim-vs-on-chain gas divergence can make a batch that simulated clean revert /
out-of-gas on L1 (bundle drop, settlement stall); unbounded cheap-in-sim cross-chain calls let an
attacker inflate the operator's posting cost without paying. The `POST_BATCH_GAS_LIMIT =
4_000_000` and approximately 2M inbound limit are not contract constants: they are gas-limit selections in the
off-chain transaction builders. They bound the submitted transaction envelopes but do not define
a protocol-level cross-chain sub-call budget or repair the accounting mismatch. The stale-nonce
retry loop in §14.3.1 is resolved separately.

**Current mitigation.** The off-chain builder selects an approximately 2M L2 system-transaction
gas limit and a 4M `postAndVerifyBatch` transaction gas limit. On-chain EVM execution is metered,
but these envelope choices do not charge nested target gas to the simulated caller frame.

**Recommended mitigation.** Meter cross-chain sub-call gas in the off-chain composer against the
caller frame so simulation matches the on-chain `postAndVerifyBatch` replay; define a normative
gas budget for cross-chain sub-calls; classify gas-divergence sim failures as deterministic
poison and evict the offending tx **before** bundling.

**Code-evidence.** Verified Rust: synthesized outcome uses `inputs.gas_limit`, not metered
against the caller (`crates/eez-evm-inspector/src/inspector.rs:677-719`); sim relaxations
(`crates/eez-composer/src/local/session.rs:613-620`);
off-chain gas-limit configuration
`crates/eez-composer/src/composer.rs:67-74,2521-2526` and
`crates/eez-protocol/src/system_tx.rs:50-59`. On-chain replay path:
`sync-rollups-protocol/src/L2/EEZL2.sol:442`.

### Mempool / nonce / admission

### 14.3.9 [RESOLVED] Provider-less ingress admission (historical)

**Historical behavior.** An earlier ingress accepted a cross-chain transaction without nonce or
balance validation when no L1 provider was configured. That fail-open path amplified the
same-nonce seed threat.

**Resolution at the reviewed revision.** The ingress context and `run_cross_chain_front` require
a concrete source-chain `RootProvider`. `gate_and_hold` fails closed when balance or pending-nonce
lookup fails and calls `HeldPool::push_contiguous` only after both checks pass. There is no
provider-less admission branch at
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`.

**Code-evidence.** `crates/eez-node/src/ingress.rs:46-113,116-157,260-275`.

### Proof system / validator set

### 14.3.10 [CRITICAL] A mock-configured proof system does not bind to the batch

**Scenario.** `MockECDSAProofSystem.verify` **ignores `publicInputsHash`** and recovers an ECDSA
signature over the *fixed constant* `MOCK_PROVER_DIGEST = keccak256("eez-mock-prover")`; the Rust
`MockEcdsaProver` signs exactly that constant. So a **single** valid 65-byte signature over the
fixed digest verifies every otherwise structurally admissible batch that selects the registered
mock. EEZ still applies its structural, root-chain, and accounting checks; the mock supplies no
execution-validity binding for a self-consistent claimed `newState`.

**Preconditions.** A deployment using `MockECDSAProofSystem` (what `DeployMockECDSAProofSystem.s.sol`
deploys), holding/compromising the single authorized signer key.

**Impact.** In a mock configuration, a reusable signature can authorize a self-consistent wrong
state transition. A follower detects the mismatch as `LocalDiverged`. Boot catch-up refuses to
start on that error; live derivation retries resynchronization after later events, but there is no
automatic rollback or fraud correction for the invalid Ethereum root. The defect is catastrophic
outside development.

**Current mitigation.** The default deployment script and README identify the mock development
path. The composer does not hardwire it: `EEZ_PROVER_URL` selects the bound remote prover and
`EEZ_ECDSA_PROOF_SYSTEM_ADDRESS` selects the carried proof-system address. The remote prover
re-executes the window and signs the recomputed public-input hash, and the in-tree
`ECDSAProofSystem` verifies over that hash. This binding path still targets the retired 0.1 ABI in
§14.3.11 and does not select Rollup0's production proof policy.

**Recommended mitigation.** Make it a **deploy-time invariant** that
`MockECDSAProofSystem` is forbidden outside development. Production activation must select
batch-binding proof systems, membership, verification keys, threshold, administrator controls,
and exact proof-input compatibility with `eez-evm@0.2-draft`.

**Code-evidence.** Mock path:
`contracts/src/MockECDSAProofSystem.sol:51-80` and
`crates/eez-prover/src/lib.rs:118-166`. Path selection:
`crates/eez-node/src/main.rs:438-459,709-716`. Bound path:
`crates/eez-proverd/src/main.rs:130-194` and
`contracts/src/ECDSAProofSystem.sol:43-78`.

### 14.3.11 [HIGH] Reviewed Rust proof inputs target the retired binding

**Scenario.** The reviewed Rust client mirrors the recorded
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`
binding: it uses `getTimestampAndBlockHash(uint64)` and includes
`crossProofSystemInteractions`. The selected `eez-evm@0.2-draft` binding instead calls
`getCustomData(uint64)` and folds ordered `(rollupId, customData)` values into the shared input.
The 0.2 batch has no `crossProofSystemInteractions` member.

**Impact.** A proof over the reviewed client's old preimage is not a valid 0.2 proof. Activating
the client against the selected contracts would fail verification or, with incorrectly mixed
types, bind the wrong data.

**Current mitigation.** The specification and companion corpus identify the two bindings
separately. The old Rust and contract fold have regression vectors, but those vectors are
historical diagnostics and do not establish 0.2 conformance.

**Recommended mitigation.** Port the client ABI, batch types, manager call, and fold to
`eez-evm@0.2-draft` together. Then assert byte equality against the selected core-contract
vectors in CI and gate every binding revision change on that check.

**Code-evidence.** Reviewed client:
`crates/eez-protocol/src/proof_resolver.rs:67-76,182-205` and
`crates/eez-protocol/src/public_inputs.rs:108-141,276-343`. Selected binding:
`eez-core-protocol/src/EEZ.sol:637-700`,
`eez-core-protocol/src/interfaces/IRollup.sol:46`, and
`eez-core-protocol/src/rollupContract/Rollup.sol:137`.

### 14.3.12 [HIGH] `SYSTEM_ADDRESS` key compromise forges signed system operations

**Scenario.** The reviewed development implementation uses deterministic EIP-155-signed legacy
transactions for table loads and inbound calls. The inbound envelope value comes from the
prefunded system EOA, and the recorded older contract requires `msg.value == value`. Every
cross-chain-enabled composer and follower holds the same key so it can reproduce identical bytes.
An **A-KEY**
attacker can sign forged table loads, inbound calls, or ordinary transfers from that reserve.
Rollup0 has not selected this envelope or authorization method for production.

**Impact.** A compromise can forge system behavior and drain or reallocate the prefunded balance.
The value equality check binds envelope value to calldata, but does not prove corresponding
settlement-side custody or backing. A key-less follower cannot reproduce a cross-chain Sync block;
the reviewed code disables reconstruction and can enter its pure-user fallback rather than failing
at startup. A keyed follower re-incurs the shared-key compromise domain.

**Current mitigation.** In the reviewed development binding, `onlySystemAddress` restricts
callers, deterministic derivation detects unsupported history, and the reserve bounds direct
value loss.

**Recommended mitigation.** Treat the production envelope, authorization, nonce, fee rule, and
value source as release blockers. If the activated mechanism keeps a signing key, specify its
custody, reconstruction, recovery, and backing controls. A key-free envelope is an unselected
future option.

**Code evidence.** Composer/follower key loading:
`crates/eez-node/src/main.rs:683-688,1007-1051`; shared construction:
`crates/eez-protocol/src/system_tx.rs:40-63,270-384`. The recorded historical
`sync-rollups-protocol/src/L2/EEZL2.sol:126-144,227-247` enforces `onlySystemAddress` and
`msg.value == value`. See
[Rollup0 Appendix C](../docs/rollup0-network-spec/C-system-transactions.md).

### 14.3.13 [MEDIUM] A reverting deferred entry stalls the current queue

**Scenario.** A deferred entry that reverts mid-execution (`StateRootMismatch` /
`RollingHashMismatch`) reverts the **whole** consuming tx **without advancing the cursor** —
**blocking later entries in that queue for the same verified block** rather than being skipped.
Only the immediate prefix is `try/catch`-skippable. Consumption is block-scoped, and every later
verified batch replaces the queue and resets its cursor, including a second verification in the
same block.

**Impact.** The revert stalls or drops the remainder of one bundle/block for that rollup. It does
not permanently wedge the deposit/withdrawal pipeline. **Not safety:** the
`StateDelta.currentState` backstop forces a stale entry to fail its own check rather than corrupt
other state, and per-rollup queues isolate the failure.

**Current mitigation.** Per-rollup queue isolation, the `currentState` backstop, immediate-prefix
skippability, block-scoped consumption, and queue replacement on the next verified batch.

**Recommended mitigation.** Specify replacement/re-post behavior and how the bundle or prefix rule
handles a failed deferred trigger. Document that later entries in the same queue cannot skip a
reverting predecessor.

**Code-evidence.** Selected core queue replacement:
`eez-core-protocol/src/EEZ.sol:723-738`; block-scoped consumption:
`:788-835`; cursor advance inside the reverting transaction:
`:964-999`; immediate-prefix skip:
`:410-435`.

### 14.3.14 [LOW] The mock verifier accepts high-`s` proof signatures

**Scenario.** ECDSA proof signatures are 65-byte `abi.encodePacked(r,s,v)`. The Rust signer emits
canonical low-`s` signatures with `v ∈ {27,28}`, but `MockECDSAProofSystem` verifies with bare
`ecrecover` and has no low-`s` check. A valid signature can therefore be transformed into its
high-`s` counterpart with flipped `v` and still recover the configured signer.

**Impact.** The development mock accepts two encodings of one proof signature. This is low impact
beside §14.3.10's absence of batch binding. It differs from the reference ECDSA adapter's
canonical-signature behavior; EEZ itself treats proof bytes as opaque and has no universal
low-`s` rule.

**Current mitigation.** The Rust `EcdsaProofSigner` normalizes to low-`s` and `v = 27+recid`,
refusing `recid > 1`. The recorded production-style proof system uses OpenZeppelin
`ECDSA.recover`, which rejects high-`s` and invalid `v`. Those controls do not make the mock
canonical.

**Recommended mitigation.** Use OpenZeppelin `ECDSA.recover` or add explicit low-`s` and
`v ∈ {27,28}` checks to an ECDSA-selecting profile's mock. Require and test those checks for
profiles and verifier adapters that select ECDSA, not for every possible `IProofSystem`.

**Code-evidence.** Rust canonicalization:
`crates/eez-protocol/src/signer.rs:106-173`; mock verifier:
`contracts/src/MockECDSAProofSystem.sol:55-79`. Binding PS uses OZ `ECDSA.recover` over the raw
`publicInputsHash` (no EIP-191), with the `v ∈ {27,28}` requirement documented in the contract:
`sync-rollups-protocol/src/proofSystems/ECDSAProofSystem.sol:13-15,17,29-32`. Framework
proof-policy boundary:
[EEZ Framework §5 — Proving & Settlement](../docs/eez-protocol-spec/05-proving-settlement.md).

### Data availability

### 14.3.15 [INFORMATIONAL] Calldata is selected; the blob proposal is unimplemented

**Scenario.** The current Rollup0 profile mandates tag-`0x00` calldata and requires empty
`blobIndices`. The live composer emits an empty list by construction. A separate
`PostBatchSubmitter` helper rejects a non-empty list with `UnsupportedBlobIndices`, but that helper
has no production call site. The follower forwards `callData` and raw transaction input without
checking `blobIndices` or independently recomputing blob-bound proof inputs. There is no
KZG/sidecar/4844-tx construction. Blob support is an informative future proposal, not a
requirement of `rollup0@0.2-draft`. No L2 user is currently charged any settlement-DA fee.

**Impact.** Canonically included calldata cannot be withheld after inclusion.
A composer can still delay or omit publication before settlement. All DA rides
settlement-chain calldata, bearing the full
calldata cost on the operator EOA with **no L2-side reimbursement**. Under high Ethereum base
fee, the operator may stop posting (liveness — feeds §14.3.18). That is an unresolved fee-policy
risk, not a blob-conformance failure.

**Current mitigation.** Canonically included calldata is available. The
live composer conforms by constructing `blobIndices = []`; follower-side enforcement remains a
known gap for externally posted batches.

**Future mitigation.** A later profile may specify EIP-4844 blob payload framing (tag byte, body reuse),
the `blobIndices → blob` binding, the off-chain `blobhash` resolution mirroring the on-chain
walk, and the cost comparator that picks the channel. Production fee policy must define who pays
Ethereum DA cost independently of that future choice.

**Code-evidence.** Live composer construction:
`crates/eez-composer/src/composer.rs:1918-1928,2121-2125,2274-2276,2330-2349`; unused helper
guard: `crates/eez-evm-inspector/src/post_batch_submitter.rs:153-167,352-362`; follower scan:
`crates/eez-l1/src/scan.rs:177-209`; calldata codec:
`crates/eez-payload-codec/src/lib.rs:48`. DA-fee oracle absent (design-level). See
[Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md),
[Appendix A](IMPLEMENTATION_NOTES.md).

### 14.3.16 [HIGH] Partial or interleaved bundle inclusion

**Scenario.** The settlement operation requires the post and every exact inbound trigger at
consecutive transaction indices. A relay or fallback path can instead omit, reorder, or interleave
a trigger after landing `postAndVerifyBatch`. The source comment reports that one Chiado builder
dropped a reverting transaction when its hash was listed in `revertingTxHashes`; that behavior is
relay-specific. Permitting a transaction to revert while remaining included is not itself
omission. The public-mempool fallback loses the all-or-none and consecutive-index guarantees
regardless of whitelist semantics.

**Impact.** The post can establish a deferred queue that a different transaction consumes or
replaces. A missing trigger also destroys one-to-one effect attribution. If an immediate effect is
skipped and a later effect has an equal precondition root, the current EEZ binding can apply the
later effect across a prefix hole. A follower can detect and halt on this invalid history but
cannot undo the Ethereum transition.

**Current mitigation.** The implementation sends empty `revertingTxHashes` and
`droppingTxHashes` arrays and drains at most `EEZ_MAX_USER_TXS_PER_BUNDLE` held transactions per
bundle (default three). Admission to the held pool is not capped at three. This requests strict
bundle behavior from the configured relay. It is not a protocol guarantee, and the mempool
fallback remains non-atomic. An exact trigger that is included with a status-`0` receipt is a
valid non-applied effect only when the activated prefix rule is enforced; it was not dropped.

**Recommended mitigation.** Select an enforceable `BUNDLE` construction that guarantees complete
inclusion at consecutive transaction indices with no queue-changing interleaving. Separately
select an enforceable `PREFIX_GUARD` that prevents any later effect from applying after a
non-applied anchor or effect, including equal-root cases. Disable the mempool fallback in a
conforming deployment.

**Code-evidence.** Verified Rust: `crates/eez-l1/src/submitter.rs:529-537` (empty whitelist
request and the relay-specific Chiado observation);
`crates/eez-l1/src/submitter.rs:311-375` (non-atomic mempool fallback);
`crates/eez-composer/src/composer.rs:776-786,1690-1705` (per-bundle drain and bundle
construction); `crates/eez-composer/src/held_pool.rs:140-200` (admission).

### 14.3.17 [LOW] Event-selector spoofing is filtered; receipt cardinality is not checked

**Scenario.** A rogue contract called inside the `postAndVerifyBatch` transaction emits a
**colliding `BatchPosted` / `L2ExecutionPerformed` selector** to spoof `rollupCount` or inject a
fake `L2ExecutionPerformed`, fooling the off-chain outcome parser into a false `Settled` verdict.
Adversary: **A-USER** deploying such a contract into the bundle's execution path.

**Impact.** A spoofed `Settled` could make the composer drop recovery prematurely. The active
address-and-topic filter prevents the stated rogue-contract collision. The active path does not
apply the separate exactly-one-`BatchPosted` receipt check.

**Current mitigation.** The live composer uses `eez-l1::Submitter`.
`settlement_in_block` filters by the pinned `EEZ` address, event signature, and `rollupId` topic,
then requires an `L2ExecutionPerformed` carrying the expected final root. A rogue contract's
collision is ignored. `decode_outcome` in the unused `PostBatchSubmitter` also requires exactly
one `BatchPosted`, but that check is not active.

**Recommended mitigation.** Keep the address+topic filter as a normative requirement of any
outcome parser; add a regression test asserting a colliding-selector log from a non-`EEZ` address
is ignored. If receipt-level `BatchPosted` cardinality is required, enforce it in the active
submitter rather than citing the unused helper.

**Code-evidence.** Active path:
`crates/eez-composer/src/composer.rs:2415-2468`;
`crates/eez-l1/src/submitter.rs:472-503`; unused decoder:
`crates/eez-evm-inspector/src/post_batch_submitter.rs:550-623`.

### Economic

### 14.3.18 [MEDIUM] Zero beneficiary and system-account fee exhaustion

**Scenario.** The selected draft beneficiary is `Address::ZERO`: base fees burn and priority fees
are economically inaccessible. There is no L1-data-fee reimbursement. In the reviewed
development path, system transactions pay a fixed 1 gwei gas price with a 2,000,000 gas limit
from the prefunded `SYSTEM_ADDRESS`; delivery halts when the account cannot cover up-front gas or
when the block base fee exceeds the fixed price. Those system-transaction fee values are not
production selections.

**Impact.** The operator has no protocol income against Ethereum posting costs, and system
balance or fee-market drift can halt cross-chain delivery.

**Current mitigation.** Development genesis prefunds the account. Deployments can monitor its
balance and base-fee headroom.

**Recommended mitigation.** Pin production base fee, fee funding, and system-envelope gas
policy. If the activated mechanism uses a system reserve, specify its provisioning, monitoring,
and top-up rules. A non-zero beneficiary or L1-cost recovery requires a versioned profile change
([Rollup0 §7 — Gas & Economics](../docs/rollup0-network-spec/07-gas-economics.md)).

**Code evidence.** `crates/eez-deriver/src/deriver.rs:496`,
`crates/eez-composer/src/composer.rs:684`, `crates/eez-driver/src/sequencer.rs:118`;
`crates/eez-node/src/main.rs:749-750,1048-1049`.

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

**Code-evidence.** Verified: `crates/eez-driver/src/sequencer.rs:145-147`;
`crates/eez-deriver/src/deriver.rs:480`; `crates/eez-composer/src/local/build.rs:92-103`
(all `B256::ZERO`, must match byte-for-byte).

### Derivation / recovery (cross-cutting)

### 14.3.20 [HIGH] L1 recovery has inconclusive-state and false-terminal gaps

These are related recovery defects. Adversary: **A-NET** / environmental (a deep L1 reorg) or
**A-OP** (timing).

**(a) Deep-reorg retry stall.** The `L1Watcher` keeps a ring of `(number, hash)` bounded by
`reorg_max_depth` (default **62**). A full ring retains the tip through `tip - 61`, and the
walk checks at most 62 cursor positions. A depth-62 reorg can therefore already lack a retained
common ancestor. A reorg at or beyond that retained boundary, or one across a catch-up gap with no
in-ring common ancestor, makes that poll cycle return `ReorgTooDeep`. The watcher task does not
terminate: its run loop logs the error and retries on the next tick with unchanged state. There is
no automatic reseed or recovery, so canonical event advancement stalls while the condition
persists. For shallower in-ring reorgs the deriver retreats the cursor and `reorg_to`s the head.
The deriver's
`reconcile_batch_blocks` is also explicitly **non-transactional**: a mid-loop replay failure
leaves earlier blocks committed (a half-state).

**(b) False-death verdict / recovery-vs-deriver war.** For an exact-target relay bundle,
`head > target_block` without inclusion is a terminal observation. The public-mempool fallback,
however, submits raw transactions and then uses the same target-based observer. A transaction can
remain pending and land after the target, so target passage does **not** prove that fallback
transaction dead. A false `Dropped` verdict can trigger rollback while the original transaction
remains live, producing the recovery-versus-deriver loop this rule was intended to prevent.

**(c) Inconclusive finality audit.** On an L1 `Finalized` event, the composer removes finalized
ledger entries before asynchronously checking their receipts. A successful lookup is audited, and
a missing receipt recovers the held transactions. An RPC error instead logs that the entry was
dropped unaudited and releases its in-flight reservation. The inconclusive record is not retained
for retry.

**Impact.** (a) Derivation/composition stalls (liveness) on a deep reorg; in-flight optimistic
Sync blocks may have anchored against rolled-out batches with no defined cleanup; the
non-transactional reconcile can leave a half-advanced local L2. (b) A late fallback inclusion can
cause an oscillating reorg war and persistently wrong anchored roots. (c) A transient RPC failure
can permanently discard the audit record that would have detected a rolled-out batch. These are
**liveness/consistency** defects; L1 remains the arbiter.

**Current mitigation.** `reorg_max_depth` is configurable and defaults to 62; shallow reorgs are
handled by `retreat_l2_to_cursor` + `reorg_to`; old-tip canonicality is verified before a
catch-up reseed. For (b), exact-target relay submission makes target passage meaningful;
`resolve_below_cursor` overrides a false `Failed → Settled`;
`recover_failed_batch` re-checks `cursor ≥ sync_height` under the reconcile lock and **drops
recovery** (the stale-verdict guard) — the Deriver cursor is the stronger oracle
([Rollup0 §3 — Composer](../docs/rollup0-network-spec/03-composer.md)).

**Recommended mitigation.** Define a **normative deep-reorg recovery procedure**: on
`ReorgTooDeep`, quiesce production, drop all Pending/Settled optimistic entries above the new
common ancestor, re-derive from genesis (or the deploy block), and gate restart on operator ack.
Make `reconcile_batch_blocks` **transactional** (snapshot the canonical head pre-loop, roll back
on any per-block failure). Disable the mempool fallback for conforming deployments, or use
nonce-, receipt-, and replacement-aware terminality rather than the relay target for that path.
Keep an audit entry pending and retry when a receipt lookup is inconclusive.

**Code-evidence.** Verified Rust:
`crates/eez-l1/src/l1_watcher.rs:134-138,172-176,240-268,350-355,464-481,663-692,722-753`
(ring bound, walk, retry loop, and `ReorgTooDeep`);
`crates/eez-deriver/src/deriver.rs:928-992,1052-1065`
(shallow-reorg retreat and non-transactional reconcile);
`crates/eez-l1/src/submitter.rs:311-379,384-435` (relay/fallback and target-based verdict);
`crates/eez-composer/src/composer.rs:504-577` (remove-before-audit and unaudited error branch).
Deep-reorg in-flight cleanup: no code path (design-level gap,
[Appendix A](IMPLEMENTATION_NOTES.md)).

### Replay, custody, and governance

### 14.3.21 [HIGH] Zero block context removes the intended replay domain

**Scenario.** Live builders initialize `blockNumber = 0`, and the posting path does not replace
it. In the recorded 0.1 contract, zero maps to `(timestamp, blockHash) = (0, 0)`. In the selected
0.2 core, `getCustomData(0)` instead returns an empty byte string, which EEZ folds with the
`rollupId` into the shared public input. Either representation is timeless: a posted batch is not
tied to a nonzero canonical settlement block.

**Impact.** The intended recent-block replay bound and fork-context check are absent. A binding
verifier would still authenticate a timeless digest unless construction is fixed.

**Mitigation.** Reject both sentinels; select and validate a recent explicit settlement block
before proof construction; and rebuild after a reorg or expiry.

**Code evidence.** Entry defaults:
`crates/eez-protocol/src/entries/mod.rs:232,346,620,732,776,865`; live timeless proof context:
`crates/eez-composer/src/composer.rs:2330-2337`; recorded 0.1 manager:
`sync-rollups-protocol/src/rollupContract/Rollup.sol:127-151`; selected 0.2 core:
`eez-core-protocol/src/rollupContract/Rollup.sol:127-153` and
`eez-core-protocol/src/EEZ.sol:676-700`.

### 14.3.22 [HIGH] The recorded 0.1 binding omits nested outbound ETH from entry accounting

**Scenario.** In the contract recorded by
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`, `_applyAndExecute` receives the value total
only from its outer `_processNCalls`. `_consumeNestedAction` invokes the function recursively and
discards its returned outbound total.

**Impact.** A nested successful outflow can reduce physical EEZ custody without an equal reduction
in recorded liabilities. Individual underflow checks and the implemented entry equation can pass
while aggregate custody is under-backed.

**Current status.** `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` fixes the
defect with transaction-transient `_entryEtherDelta` accounting that every nested
`_processNCalls` updates. Reverted frames revert those updates. The reviewed Rollup0 client still
pins the affected 0.1 contract, so its deployed-binding risk remains.

**Mitigation.** Port Rollup0 to latest core. Until then, reject nested value-bearing entries when
using the recorded binding.

**Code evidence.** Recorded 0.1 binding:
`sync-rollups-protocol/src/EEZ.sol:801-816,916-945,963-969`. Latest core:
`eez-core-protocol/src/EEZ.sol:119-133,799-808,882-902,1003-1035,1068`.

### 14.3.23 [CRITICAL] Manager and verifier administrators can replace validity policy

**Scenario.** The manager owner can change proof systems, vkeys, threshold, and the registered
root. The ECDSA verifier owner can replace its signer. There is no protocol delay or dispute
window.

**Impact.** These roles control validity, availability, and effective custody. A follower can
detect and halt, but cannot stop the policy change, reverse an applied outflow, or exit.

**Mitigation.** Publish the complete deployment, code, and admin tuple; separate compromise
domains; use threshold governance and observable delays; and remove unneeded escape or signer
rotation powers.

**Code evidence.** Selected core:
`eez-core-protocol/src/rollupContract/Rollup.sol:177-220`;
`eez-core-protocol/src/proofSystems/ECDSAProofSystem.sol:18-31`.

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

### 14.3.25 [HIGH] Equal-root siblings bypass root-only staleness

**Scenario.** Two valid siblings name the same Rollup0 parent. Ethereum selects a candidate whose
derived endpoint has the same state-root value as its parent but a later height and different block
hash. Because `EEZ` stores and checks only the root, the old sibling remains applicable on chain
and can publish another range or replace the deferred queue.

**Impact.** Canonical Ethereum order does not select one Rollup0 block identity. Followers advance
their cursor after the first candidate while the contract accepts a transition from the old cursor.
The resulting settlement history is not uniquely derivable.

**Mitigation.** Production requires `R0-CURSOR-SAFETY`: an enforceable commitment to the current
Rollup0 height, block hash, and state root, exact comparison with each candidate parent, and atomic
advancement to every possible selected prefix endpoint. A follower-side stale check cannot repair
an accepted Ethereum transition.

**Code evidence.** `eez-core-protocol/src/EEZ.sol:1103-1120` checks and stores only state roots.
No reviewed settlement path commits the Rollup0 cursor height and block hash.

### 14.3.26 [HIGH] One trigger can be claimed for several inbound effects

**Scenario.** One held Ethereum transaction can produce several target entries. The composer puts
all entries into the candidate but appends the raw transaction to the bundle once.

**Impact.** There is no one-to-one mapping from inbound effect indices to trigger transactions and
receipts. Queue consumption, prefix classification, and deterministic repair become ambiguous.

**Mitigation.** Require one distinct, consecutive trigger transaction per inbound effect. Reject a
held inbound composition that yields more than one supported target effect unless a future
versioned lowering defines a different unambiguous construction.

**Code evidence.** `crates/eez-composer/src/composer.rs:1390-1413,1690-1705`.

## 14.4 Residual-risk summary

| # | Threat | Category | Severity | Status | Where addressed |
|---|---|---|---|---|---|
| 14.3.1 | Historical same-nonce L1 bundle stall | mempool/nonce | **HIGH (historical)** | **resolved**; nonce-read failures still fail open | §14.3.1 |
| 14.3.2 | No force-inclusion / escape hatch | sequencer/operator | **HIGH** | **accepted** (Rollup0) | Possible future revision ([Rollup0 §10 — Future Design](../docs/rollup0-network-spec/10-future-design.md)) |
| 14.3.3 | Unknown ancestry optimistically accepted | sequencer/operator | LOW | open at any missing parent | §14.3.3 |
| 14.3.4 | Timing-configuration and L1-clock dependence | configuration/operator | LOW | bounded; profile validation needed | §14.3.4 |
| 14.3.5 | STATICCALL/DELEGATECALL-to-proxy dispatch | cross-chain | **HIGH** | open | Fix in [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.6 | Overlay drops code/nonce, hard-fails selfdestruct | cross-chain | MEDIUM | open | Fix/forbid in [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.7 | Permissionless deterministic proxy registration | cross-chain | INFORMATIONAL | conforms to selected core | §14.3.7 |
| 14.3.8 | Cross-chain sub-call unmetered in sim | gas griefing | MEDIUM | open | §14.3.8 |
| 14.3.9 | Provider-less ingress admission (historical) | mempool/nonce | MEDIUM | **resolved** | Current ingress requires and uses a source-chain provider |
| 14.3.10 | Mock PS does not bind to batch | proof-system | **CRITICAL** | **devnet-only / accepted** | Select and activate a batch-binding proof policy |
| 14.3.11 | Reviewed Rust uses retired proof-input binding | proof-system | **HIGH** | open | Port to 0.2; [App. A H-5](IMPLEMENTATION_NOTES.md#h-5-reviewed-client-uses-the-retired-01-manager-and-proof-input-binding) |
| 14.3.12 | `SYSTEM_ADDRESS` key sprawl forges system operations | cross-chain | **HIGH** | open | Appendix C; future key-free envelope |
| 14.3.13 | Deferred revert stalls current queue remainder | proof-system | MEDIUM | bounded to one verified queue/block | §14.3.13 |
| 14.3.14 | Mock accepts high-`s` signatures | proof-system | LOW | open in ECDSA development mock | §14.3.14; reference ECDSA verifier mitigated |
| 14.3.15 | Calldata selected; blob proposal unimplemented | DA | INFORMATIONAL | composer conforms; follower guard open | [Rollup0 §4 — DA & Bundles](../docs/rollup0-network-spec/04-da-batches-bundles.md); [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.16 | Partial bundle inclusion | DA | **HIGH** | open (relay request only) | §14.3.16; `R0-ATOMIC-INCLUSION` |
| 14.3.17 | Event-selector / receipt spoofing | DA | LOW | selector collision mitigated; cardinality check dormant | §14.3.17 |
| 14.3.18 | Zero beneficiary + system reserve exhaustion | economic | MEDIUM | open | §14.3.18 |
| 14.3.19 | Predictable `prev_randao` | application | MEDIUM | open (app-layer) | §14.3.19 |
| 14.3.20 | Deep-reorg retry stall and false terminal verdicts | derivation | **HIGH** | open | §14.3.20; [App. A](IMPLEMENTATION_NOTES.md) |
| 14.3.21 | Zero L1 proof context | replay/domain | **HIGH** | open | §14.3.21; [App. A H-6](IMPLEMENTATION_NOTES.md#h-6-live-batches-retain-the-zero-l1-context-sentinel) |
| 14.3.22 | Recorded 0.1 binding omits nested value | custody | **HIGH** | open for reviewed pin; fixed in latest core | §14.3.22; [App. A H-8](IMPLEMENTATION_NOTES.md#h-8-the-recorded-01-binding-omits-nested-outbound-eth-from-entry-accounting) |
| 14.3.23 | Manager/verifier admin authority | governance | **CRITICAL** | accepted trust assumption | §14.3.23 |
| 14.3.24 | Root-set settlement attribution | derivation | **HIGH** | open | §14.3.24; [App. A H-9](IMPLEMENTATION_NOTES.md#h-9-deriver-attributes-applied-roots-by-per-block-set-membership) |
| 14.3.25 | Equal-root sibling bypasses staleness | settlement | **HIGH** | open | §14.3.25; `R0-CURSOR-SAFETY` |
| 14.3.26 | One trigger claimed for several inbound effects | settlement | **HIGH** | open | §14.3.26; [App. A H-11](IMPLEMENTATION_NOTES.md#h-11-one-held-inbound-trigger-can-produce-several-effects) |

**Status legend.** *resolved* means the reviewed revision closes the stated historical mechanism;
any narrower residual is stated separately. *Mitigated* means a mechanism reduces the threat;
*accepted* is an explicit trust assumption or limitation; *open* is a known gap. Detection by a
follower can reduce the accepted view to a halt, but it cannot reverse Ethereum effects or
guarantee custody recovery.

## 14.5 Unselected future security changes

[Rollup0 §10](../docs/rollup0-network-spec/10-future-design.md) lists possible revisions. It does
not define a named successor protocol or select concrete future algorithms, actors, or guarantees.
The following effects are conditional:

- A precisely specified force-inclusion and trust-minimized exit mechanism could reduce the
  censorship and no-exit risk in §14.3.2.
- A key-free system transaction could remove the shared-key risk in §14.3.12 if it also pins the
  envelope, authorization, non-reentrancy, nonce, fee, and value rules.
- Revised proof inputs could bind currently omitted routing and replay fields. The production
  proof policy, verifier deployments, membership, and activation remain release blockers.

Each change requires a new version, an activation boundary, and byte-exact fixtures where it
affects serialization or hashing. The list is not an implementation specification and creates no
current guarantee.

---

*Next: [Chapter 15 — Related Work](related-work.md).*
