# Rollup0 Spec — Consolidated Review Findings

Synthesis of four independent spec-only reviews (execution-client implementer, L1/prover/DA
implementer, devil's advocate, spec editor), de-duplicated, with a disposition applied to each.

**Disposition legend**
- **GAP** — genuine spec gap; the spec should change.
- **CLARIFY** — the mechanism likely exists in the design (and the contracts), but the spec doesn't
  state it, so a spec-only reader reasonably concludes a flaw. Fix = articulate it.
- **DEFER** — a deployment parameter already acknowledged in §12.2; blocks a *byte-conforming*
  client until pinned, but is a known open, not a surprise.
- **DESIGN?** — a real design question to confirm (may be intentional under v0's trust model).
- **EDIT** — editorial / consistency fix.

The headline: **all four reviews converge that the spec is sufficient to understand the
architecture but NOT sufficient to build a byte-conforming client**, because the consensus-critical
wire formats are given as *named pseudocode*, not byte-exact layouts + test vectors. See §E and
Decision 2.

---

## A. Structural / load-bearing (need a decision)

### A1 — Sync-block ordering & `toBlock` framing — DECISION (see Decision 1)
§1.2 says the slot is "1 **Sync** block followed by 5 pure-L2 blocks" (Sync **first**); §4.2, §3.4,
§7.2, §9, §10.1 and Appendix A say "5 Live then 1 **Sync** (last block of slot)" and `toBlock` = the
Sync block (Sync **last-in-range**). Same physical chain, two bracketings. The new
**same-timestamp rule** (Sync block timestamp == its L1 block's) is now encoded in §4.2/§4.3 and
holds either way; it also *pins the `prev_randao` anchor* (closes B6/M1). What remains is which
framing is canonical and therefore what a single batch confirms. **Resolve before fixing §1.2/§4.2.**

### A2 — Spec sufficiency / wire-format depth — DECISION (see Decision 2)
The two implementer reviews independently conclude the byte-exact wire layer is missing (§E). Making
the spec self-sufficient means adding exactly the low-level ABI/encoding/test-vector material that
was deliberately stripped — and "don't reference the contracts" forbids pointing at the source as
the normative artifact. This is a strategic choice, not a local fix.

---

## B. Soundness articulation (devil's advocate — mostly CLARIFY)

The adversarial review's three CRITICALs (unbacked mint, broken atomicity, permissionless
`executeL2TX`) share one root: **the spec proves *internal* consistency (rolling hash, per-entry
ether, pre-state binding) rigorously, then assumes the *external* bindings (real deposit backing,
bundle atomicity, manager honesty) that actually carry safety — without stating them.** Whether the
deployed protocol is sound or not, the *spec* must articulate these bindings, because a careful
reader currently concludes it is broken.

### B1 — ETH backing of the L2 mint is never stated — CLARIFY (was C1)
The mint (`executeIncomingCrossChainCall` "mints exactly `value`") and the L1 `etherDelta = +value`
are presented with the backing ("how `SYSTEM_ADDRESS` is funded so the mint is backed by real
L1-locked value") punted to a "deployment parameter" (§9.3/§11.5). The per-entry ether invariant
(§5.4 H.2) only checks internal bookkeeping; nothing in the spec ties `etherDelta` to ETH actually
locked in `EEZ`. **Fix:** state the locking mechanism (the payable proxy call deposits `msg.value`
into `EEZ`; the invariant `address(EEZ).balance ≥ Σ rollups[*].etherBalance`), so the "cannot
conjure ether" claim (§8.6) is actually supported across the L1↔L2 boundary.

### B2 — Bundle / meta-hook atomicity has no stated mechanism — CLARIFY/GAP (was C2/C3; impl B6/B7)
§7.4 says `[postAndVerifyBatch, trigger]` is all-or-nothing, but the EVM does not roll back tx#1 if
tx#2 reverts. The actual atomicity hinges on §5.5 step 6's **meta hook** — consumption happening
*inside* `postAndVerifyBatch` (so a revert unwinds everything) — but the hook's interface, when it
fires vs. the trigger tx, and the revert semantics are undefined. **Fix:** specify the bundle's
atomicity mechanism and the meta-hook (what calls back, with what ABI, and that a revert reverts the
whole settlement). This simultaneously defuses the "credit before debit" and "permissionless
`executeL2TX` unbacked mint" attacks.

### B3 — "Three independent safety layers" is overstated — GAP (was S2/S3)
§8.6's three layers (N-of-M, on-chain invariants, re-derivation) are not independent: the validator
re-execution and the contract check the **same internal invariants**, and re-derivation reproduces a
*self-consistent* fraudulent state faithfully (it detects operator *equivocation*, not validator-set
fraud). The validator set **is** a trust assumption in v0. **Fix:** state precisely what each layer
guarantees; stop implying re-derivation establishes validity rather than consistency; make the
README "safety does not depend on the operator" claim precise (it holds for parties running a
follower against the *settled* head — see B4).

### B4 — "safety does not depend on the operator" vs the optimistic head — GAP (was M6)
Normal users see the operator's RPC head, which is the *optimistic* (pre-L1-confirmation) head; for
them, safety depends on the operator honoring the rollback obligation (R5). The clean property holds
only for someone running a follower against the L1-confirmed head. **Fix:** qualify the claim.

---

## C. Real design questions to confirm — DESIGN?

### C1 — No domain separation in call hash or signed digest (was S1/B4/N1)
`crossChainCallHash` = `keccak256(targetRollupId,targetAddress,value,data,sourceAddress,
sourceRollupId)` and validators sign the **raw** `publicInputsHash` with no chainId / EEZ-address /
batch-nonce. Two identical-content calls collide; signatures/batches may replay across deployments
or forks. Presented as a *feature* in §3.2 (domain-free proxy salt). **Confirm:** is this an
intentional single-deployment assumption, and what prevents cross-deployment/stale-batch replay (is
`blockHash_r` the sole binding)?

### C2 — `setStateRoot` manager escape + permissionless `registerRollup` + manager trust (was S6/M5)
The per-rollup manager can rewrite the L2 state root arbitrarily (`setStateRoot`, outside the locked
block) and defines the validator set. `registerRollup` is permissionless. Under v0 (centralized,
permissioned) the manager is trusted **by design** — but the spec never lists it as a trust
assumption. **Fix:** add the manager (and `setStateRoot`) to §12.1's trust/limitations; note
permissionless registration + domain-free proxies interact with C1 in the multi-rollup future.

### C3 — Reentrancy guard vs intentionally-reentrant + meta-hook ordering (was M2)
H.7 ("re-entry reverts") vs §5.8 ("intentionally reentrant") vs §5.5 step 6 (arbitrary external call
mid-settlement, *before* step 7 publishes queues). **Fix:** state which paths are guarded vs
allowed, and why the step-6-before-step-7 ordering is safe.

### C4 — STATICCALL-to-proxy is v0-reachable but the lookup path is general-model (was M4)
§3.5 routes a STATICCALL on a proxy to a read-resolution path that §5.3/§5.1 mark general-model and
"empty in v0." **Fix:** state what v0 does on a STATICCALL to a proxy (revert? or the read path *is*
in v0?).

### C5 — Adversarial gas/DA vectors not in the threat model (was S5/M3/S4)
(a) Inbound exec has a fixed ~2M budget + unconditional mint → an attacker-crafted L2 target can OOG
and desync L1/L2 balances; simulation-vs-onchain gas divergence is weaponizable, not just an honest
mistake. (b) Calldata-DA cost falls on the single operator in v0 → spam griefing. (c) Shallow L1
reorg + no batch nonce → trigger re-inclusion / double-or-lost settlement. **Fix:** add these to the
companion threat-model; consider a §10.4 note on shallow-reorg trigger re-inclusion.

---

## D. Referenced-but-undefined (clear fixes) — GAP

- **`crossProofSystemInteractions`** — in the batch struct and the signed `publicInputsHash`, never
  defined. Define it; pin its v0 value (presumably `bytes32(0)`).
- **`transientExecutionEntryCount` / `transientLookupCallCount`** — introduced in §7.3, never
  defined; cross-link to the §5.5 step-5 inline drain and say who sets them / what's validated.
- **"meta hook"** — §5.5 step 6; define interface or describe behaviorally (also B2).
- **`loadExecutionTable`** — appears only in the §5.8 access table; define or drop.
- **`callCount` v0 value** — §5.1 "top-level iterations"; pin the v0 meaning/value.
- **`BridgeReceiver` (0x42…0008)** — declared genesis-mandatory, zero behavior; mark reserved/inert
  in v0 (withdrawal path is out of scope, §10.5).
- **Error/revert table** — reverts are scattered (`RollingHashMismatch`, `UnconsumedCalls`,
  `EtherDeltaMismatch`, `StateRootMismatch`, DELEGATECALL ban, reentry guard, `setStateRoot` lock,
  "not verified this block"); add a consolidated table to Appendix A.

---

## E. Wire-format byte-exactness (implementer headline — feeds Decision 2) — GAP/DEFER

All given as named pseudocode; each is reproduced independently by operator, contract, every
validator, and every follower, so a single-byte disagreement is a fork or attestation failure:

- exact ABI (member order/types, incl. any omitted members) of `ExecutionEntry`, `StateDelta`,
  `L2ToL1Call`, `ExpectedL1ToL2Call`; and the **L1-shape vs L2-shape** entry difference (undefined);
- the rolling-hash encoding (`abi.encodePacked` vs `abi.encode`; widths of `callNumber`/`success`;
  framing of `returnData`);
- the public-inputs fold's exact Solidity (`abi.encode(bytes32[])` head/tail framing inside
  `abi.encodePacked`); `acc_k` / `crossProofSystemInteractions` types;
- the N-of-M attestation byte layout (signature packing, signer ordering/dedup, set storage,
  `vkey[r][k]` = single commitment vs per-signer);
- the type-`0x7E` transaction envelope (fields, RLP/SSZ, tx-hash preimage, nonce/gas/receipt) and
  the exact `executeIncomingCrossChainCall` signature (the elided `…`);
- the DA RLP details (canonical minimal-integer vs fixed-width `blockTxCounts`; whether the Sync
  block contributes a trailing `0` count; block-major flatten order).

**Recommended:** whichever way Decision 2 goes, ship **test vectors** (known inputs → expected
`crossChainCallHash`, `rollingHash`, `publicInputsHash`, one encoded batch, one `0x7E` tx).

---

## F. Client-agnostic residue (editorial) — EDIT

- **§1.3** "`Name.sol:NN` … point at the contract sources at the pinned commit" — no such refs
  remain in the body; the convention sentence contradicts the client-agnostic goal. **Remove.**
- **"OP-aligned" / "`L1FeeVault`-style"** (§11.3/§11.4, A.1) — specific-stack naming; replace with
  neutral descriptions.
- **Storage slots** (`authorizedProxies` slot 0, `rollups` slot 2, the `stateRoot` slot formula) —
  implementation layout, not the normative surface unless a follower reads by `eth_getStorageAt`
  (not stated). Justify or move to companion implementation notes.
- **A.1 "confirm before commit"** — editorial TODO in spec text; remove (it's tracked in §12.2).

---

## G. Deferred deployment parameters (already §12.2; block conformance until pinned) — DEFER

`chainId`; `SYSTEM_ADDRESS` value + genesis balance; EIP-1559 elasticity/denominator + **initial
base fee**; fee-vault recipient addresses + whether base fee is burned or routed (state-affecting);
validator `M`/`N` + signer set; **genesis bytecode/storage + state root + `CrossChainProxy.
creationCode`**; L1-data-fee formula *if* charged to users (v0: operator absorbs — confirm).
`prev_randao` anchor is **now pinned** by the same-timestamp rule (§4.2/§4.3). The genesis bytecode
+ the `0x7E` envelope are the two that are *only* resolvable from the contract/client source today.

---

## H. Editorial consistency — EDIT

- proxy notation `proxy(A,R)` (address-first) vs salt `keccak256(R,A)` (rollupId-first) — note it's
  presentational, or align.
- §9.1 "both taken from proxy identity … never from caller input" over-claims (`value`/`data` come
  from the call); scope to the rollup-ids + source address.
- `L2ToL1Call` used for the v0 **inbound** (L1→L2) call — add a one-line note that it's the
  general-model struct name reused, so it doesn't read as contradicting §9.
- Consolidate the ~6 restatements of "safety does not depend on the operator" to one canonical
  statement (§8.6) + cross-refs.
- `BUILDER_GAS_LIMIT` alias appears once (A.1) and nowhere else — use or drop.
- §8.4 re-summarizes `postAndVerifyBatch` at different granularity than §5.5 — have §8.4 defer to
  §5.5 for the execute-phase substeps.
- `L2ExecutionPerformed` is per-entry but the settlement verdict wants one root — state it compares
  the *final* `newState` for the rollup in that L1 block.
- README names no companion docs for the threat model / related work / blob format — name or link
  them (or state "forthcoming").
