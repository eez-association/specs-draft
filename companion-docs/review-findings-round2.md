# Rollup0 Spec — Review Findings, Round 2

> **Historical, informative review snapshot.** Findings describe a pre-correction draft and do
> not state the active protocol. Current normative behavior is under `docs/`. A1, B1, B3, B5,
> B6, B8, B10, B12, B13, the Sync-count/order minors, and the old wire-corpus conclusions are
> superseded. Rollup0 v0 selects signed legacy system transactions, prefunded transfers, a
> cursor-derived non-empty range, variable-cardinality ordered bundles, strict tag-`0x00`
> calldata DA with empty `blobIndices`, canonical partial-settlement derivation, standard
> EIP-1559 parameters, and a zero beneficiary. Type `0x7E` is future design material only.

Synthesis of a six-lens review (two second-client core devs — node and L1-contracts —, an
adversarial consistency checker, a security critic, a byte-level wire-format reviewer, and a
spec editor), 91 raw findings de-duplicated to 41, each surviving finding adversarially verified
against the docs (agent-verified where marked; the remainder hand-verified or spot-checked
by grep/computation as noted). Bar applied: **"a core dev team could read this and implement a
second client without any other context."**

**Headline.** The previous round's demand — byte-exact wire formats — has genuinely landed:
multiple reviewers independently recomputed every Appendix D conformance vector (call hash,
CREATE2 with the embedded creation code, rolling hash, public-inputs folds, DA RLP, selector)
and everything reproduces. The L1 settlement/hashing layer is implementable from the spec alone.
What still forks two clients is the **node half**: the 0x7E system transaction, the slot function
under real L1 conditions, genesis, and the flat-processor / entry-shape semantics. Fix the five
blockers and the spec is close to its bar.

---

## A. Blockers (two independent clients fork; no route-around)

### A1 — Type-0x7E system transaction is deferred to a spec that does not exist
*D.8, §3.4, §11.5, A.1 — reported by all six lenses; agent-verified.*
D.8: the envelope "MUST be pinned by the execution-layer specification" — no such document exists
in the doc set, contradicting the README's "self-contained" claim, and the gap is untracked in
§12.2/App C. A second client cannot serialize the system tx (RLP field list, tx-hash preimage),
compute the Sync block's `transactionsRoot`/`receiptsRoot`/`gasUsed`, or the post-block state:
does the system tx pay base fee, and to whom; does `SYSTEM_ADDRESS`'s nonce increment; is its gas
counted against the 30M limit; what is the receipt shape? Related unresolved ambiguity: §3.4
"mints exactly `value`" vs §11.5 "`SYSTEM_ADDRESS` … is the mint source" — supply-increase vs
balance-debit changes the state root. A.1 gives the inbound gas budget as "≈ 2_000_000" — an
approximate value for a consensus constant.
**Fix:** a normative EL section pinning envelope bytes, hash preimage, exact gas constant,
base-fee/nonce/receipt/balance semantics, plus one encoded-0x7E conformance vector.

### A2 — The slot/timestamp function is undefined the moment L1 misbehaves
*§4.1/§4.2/§4.3/§4.4, §12.2, §7.2 — agent-verified.*
§4.1 pins `timestamp = parent + 2 s`; §4.2 pins the Sync block's timestamp to its anchoring L1
block's. Jointly satisfiable only if an L1 block exists at every 12 s grid point — Ethereum skips
slots routinely. On a missed slot the anchor (and hence `prev_randao` for all K blocks, and every
subsequent block hash) is undefined; nothing covers cadence deviation, bundle inclusion slipping a
block, or the rollback scope when a bundle misses (§4.4 "roll the Sync block back" vs the batch
confirming all 6 blocks — may the next batch cover 11 blocks? must a deriver enforce
`toBlock − fromBlock == K`?). §12.2 still lists the `prev_randao` anchor as *unpinned*, directly
contradicting §4.3's claim that the shared-timestamp rule pins it.
**Fix:** define the slot schedule as a total function of (genesis timestamp, L1 chain): anchor
selection on missed slots, missed-bundle rollback scope, next-batch range, follower's range-length
acceptance rule; reconcile §12.2 with §4.3.

### A3 — No genesis specification
*§12.2, §3.1, App C preamble — agent-verified.*
EEZL2/BridgeReceiver predeploy runtime bytecode + storage, `SYSTEM_ADDRESS` balance, allocations,
genesis header, and the resulting genesis hash are specified nowhere (D.3 pins only
`CrossChainProxy` *creation* code). App C's preamble claims "genesis bytecode … tracked in §12.2"
— §12.2 has no such item (only timestamp-grid alignment). Derivation (§10.1) starts at genesis;
two clients fork at block 0. (Partial refutations applied: chainId, M/N, initial base fee, fee
vaults *are* registered in §12.2; the fork schedule is effectively pinned by §3.1's Cancun
statement.)
**Fix:** a genesis appendix (per-address code/storage/balance, genesis header rule, genesis hash)
or at minimum a correct §12.2 entry.

### A4 — The flat call processor and the L1-shape / L2-shape entry split are unspecified
*§5.3/§5.4, §5.1, §7.1/D.7 (`l2_entries`) — agent-verified.*
What consuming an `L2ToL1Call` on L1 concretely does — dispatch via the source proxy's
`executeOnBehalf` (a function appearing in zero docs, only in the opaque D.3 bytecode), the
`msg.sender` the target observes, CREATE2 auto-deploy of missing source proxies, the `etherOut`
accrual rule, and where CALL_END's consensus-critical `(success, returnData)` come from — cannot
be determined from the spec. Worse, §5.1's "(v0: the inbound call)" annotation misstates the
reference design (the v0 **L1-shape** entry carries an *empty* `L2ToL1Calls` array with
precomputed `returnData`; the call travels only in the **L2-shape** entry), and "L2-shape" is used
in §7.1/§9.3/§10.1/D.7 but *defined nowhere* — flagged in round 1 (§E) and still open. That both
reviewers and the review's own first-pass fix mis-reconstructed the mechanism is direct evidence a
second client cannot get this right from the spec.
**Fix:** define both entry shapes field-by-field with a v0 worked example on each chain, and
specify the processor algorithm per side (execution context, fold inputs, `etherIn`/`etherOut`
rules, proxy auto-deploy).

### A5 — Resolved: network identity and settlement target were split
*Former README/overview contradiction — hand-verified.*
Rollup0 now pins `gnosis-chain-eez-chiado@0.1-draft` (`chainId = 10200`, nominal 5-second slots),
while the Gnosis Chain EEZ Network Specification is a separate host profile. Production
deployment values remain explicit release blockers.

---

## B. Majors (likely divergence or a security hole; verified unless noted)

- **B1 — §7.2's block-range claim is false as written** *(agent-verified)*: `fromBlock`/`toBlock`
  are *not* in the §8.3/D.5 public-inputs fold, no on-chain record or event stores an L2 height,
  and the actual mechanism (deriver-local cursor from genesis; `toBlock = fromBlock +
  blockTxCounts.length`; position pinned transitively by the `StateDelta.currentState` pre-state
  chain) appears only in the non-normative threat model. Rewrite §7.2 truthfully; fix §10.1 step 3.
- **B2 — Deposit flow (§9.3)** *(agent-verified)*: the "deposit shape" entry is named, never
  defined; the custody either/or ("held by the proxy, or routed to a bridge") is incompatible with
  both the §9.2 diagram and D.3's pinned proxy bytecode (CALLVALUE is forwarded into `EEZ`), so
  custody is *not* a deployment choice; payability of the entry points and `etherIn` for
  system-driven entries unstated; round-1's B1 invariant (`address(EEZ).balance ≥
  Σ rollups[*].etherBalance`) still absent.
- **B3 — Bundle cardinality contradiction** *(agent-verified)*: §7.4/A pin exactly
  `[postAndVerifyBatch, trigger]` while §11.3/§12.2/B.2 define a per-bundle *user-transaction
  bound* (and the reference builds `[batch, user_tx…]`, `MAX_USER_TXS_PER_BUNDLE = 3`); B.2
  mislabels the riders "L2 user transactions." Multi-intent slots, trigger ordering vs the entry
  queue: unspecified.
- **B4 — Meta hook has no interface** *(agent-verified)*: §5.5 step 6 / §7.4 rely on it for
  in-frame atomicity; no name/selector/args/revert semantics anywhere (deployed:
  `IMetaCrossChainReceiver.executeMetaCrossChainTransactions()`; the deployed invocation condition
  also differs from the spec's "if msg.sender has code"). Round-1 §D flagged this; half-fixed.
- **B5 — Partial consumption** *(agent-verified)*: no operator obligation and no follower rule for
  which system txs to include when a batch settles only a prefix of its entries — two followers
  build different Sync blocks against the same settled endpoint. State one rule.
- **B6 — Settlement events underspecified** *(agent-verified)*: `BatchPosted(uint256)`'s parameter
  undefined (deployed: rollupCount, indexed); `L2ExecutionPerformed` indexing unstated though §8.5
  mandates topic filters; with multiple entries per batch, "the last event's `newState` for that
  rollup" is never stated as the root-match rule.
- **B7 — D.5 prose mis-describes `abi.encode(bytes32[])`** *(computationally verified)*: "length
  word + elements" omits the leading `0x20` offset word; the prose reading yields a *different*
  `sharedPublicInput` (checked numerically; the with-offset reading reproduces Vector 5). One
  sentence, consensus-critical.
- **B8 — Resolved: blob DA is outside this profile** *(hand-verified)*:
  `rollup0-chiado@0.1-draft` fixes the tag-`0x00` calldata codec and empty `blobIndices`;
  `blob-da-spec.md` is explicitly informative. Selecting blobs requires a later profile version.
- **B9 — The EEZ/manager ABI surface is incomplete** *(hand-verified)*: D.9 pins only
  `postAndVerifyBatch`; `executeCrossChainCall`, `executeL2TX`, `staticCallLookup`,
  `registerRollup`, and the manager functions the registry calls at settlement
  (`checkProofSystemsAndGetVkeys`, `getTimestampAndBlockHash`) are named without exact
  signatures/selectors — yet the pinned D.3 proxy bytecode *hardcodes* manager selectors, so the
  ABI is consensus-adjacent and currently recoverable only by reversing that bytecode.
- **B10 — Base-fee routing vs EVM equivalence** *(hand-verified)*: §11.2 routes the base fee to a
  vault "rather than burning" — on an "Ethereum-equivalent EVM" (§3.1) the base fee is burned;
  the redirect is a consensus-level deviation with no specified mechanism or timing.
- **B11 — `StateDelta.rollupId` is not bound to the attested set** *(hand-verified)*: no stated
  check that every delta's rollup appears in `rollupIdsWithProofSystems`; as written a batch could
  carry deltas for rollups whose validators never attested. State the check (or the argument why
  the pre-state binding suffices).
- **B12 — `batch.blockNumber` mode rule missing** *(hand-verified; partially tracked in C.1)*:
  D.5 documents three modes (0 ⇒ zero binding; `uint64.max`; explicit) but no normative rule for
  which the operator MUST use and which validators/the contract MUST accept — `0` yields zero
  anti-replay binding. Also: the explicit-`blockNumber` branch never states what timestamp is
  folded.
- **B13 — Degraded-input derivation rules** *(agent-verified as real, downgraded from blocker)*:
  no MUST for a follower hitting an invalid user tx in a settled payload (bad signature, stale
  nonce, type-3 blob tx) or an undecodable payload the contract accepted opaquely — skip, include,
  reject, halt? One rule each.
- **B14 — Immediate-entry failure semantics** *(unverified — reviewer-reported)*: whether a
  failing inline-executed (`proxyEntryHash == 0`) entry reverts the whole settlement or is
  skipped; the reviewer claims the spec's wording implies the opposite of deployed behaviour.
  Confirm against source.

---

## C. Minors / editorial

- `sourceAddress` derivation for L1-originated calls never pinned (= the proxy's caller) — D.2 *(agent-verified)*.
- `loadExecutionTable` still dangling in §5.8's table (round-1 said "define or drop") *(agent-verified)*.
- `BridgeReceiver` still has zero specified behaviour/bytecode (round-1 asked "mark reserved/inert") *(agent-verified)*.
- D.10 Vector 4's printed encoding is truncated — 24 words shown, correct is 26 (832 B); the two
  missing trailing zero words are the empty `expectedL1ToL2Calls` and `returnData` lengths. The
  quoted `entryHash` is correct (independently recomputed) *(computationally verified)*.
- `da-rlp-fixture.py` / Vector 8 sample "signed EIP-2718 user transactions" are malformed RLP
  (`0x02f865…` declares 101 bytes, 27 present) — opaque to the codec but misleading in a
  conformance fixture; use real signed txs *(computationally verified)*.
- §3.4 "system transactions … before any user transactions" contradicts §7.1/D.7's "Sync block's
  user-transaction list is **empty**" — may a Sync block carry user txs or not? *(hand-verified)*.
- §5.1 "a reverting top-level result is expressed as a lookup (§13)" reads as contradicting §9.4's
  v0 revert-via-`CALL_END` handling; clarify entry-level vs call-level failure *(hand-verified)*.
- D.3's immutable-placeholder note names "manager / signer / threshold" — `CrossChainProxy`'s
  immutables are `(eez, originalAddress, originalRollupId)`; signer/threshold belongs to
  `ECDSAProofSystem` *(hand-verified)*.
- Low-`s` signature constraint is stated nowhere (OZ `ECDSA.recover` rejects high-`s`; D.6 pins
  only `v ∈ {27,28}`) *(hand-verified)*.
- A.2's `authorizedProxies` slot is pinned but the `ProxyInfo` value packing is not — unusable for
  `eth_getStorageAt` *(hand-verified)*.
- All three prose companion docs cross-reference a stale chapter layout (§14/§16 etc. do not
  exist) *(hand-verified for related-work.md)*.
- A.6's error table vs source completeness *(unverified — reviewer counted ~a dozen missing and
  some wrong argument lists; re-check against `IEEZ.sol`)*.
- JSON-RPC surface: Engine API is declared standard (§2.3) but the user-facing RPC surface is
  neither specified nor declared out of scope — one sentence *(hand-verified)*.

**Refuted in verification:** "constant provenance is circular" (`POST_BATCH_GAS_LIMIT` is properly
defined in A with B cross-referencing it); the §5.4-vs-§9.2 `etherDelta` "contradiction" (dissolves
once the empty-calls L1-shape entry is understood — but see A4: the spec doesn't say that).

## D. Verbosity (the "precise but not overly verbose" axis)

The spec is *not* bloated; duplication is confined and specific:
- the DA grammar + invariants are stated three times (§7.1, A.4, D.7) with wording drift — state
  once in D.7, summarize elsewhere;
- the "safety does not depend on the operator / only liveness" refrain and the former combined-profile
  not an EEZ requirement" disclaimer each appear ~5–6 times — one canonical statement + cross-refs
  (round-1 §H asked the same);
- §8.4 re-narrates the §5.5 lifecycle at a different granularity — have it defer.

## E. Suggested fix order

1. A1 + A5 (EL chapter + one settlement-target sentence) — unblocks the node team.
2. A2 + A3 (slot function, genesis appendix) — unblocks derivation end-to-end.
3. A4 + B1/B2 (entry shapes, processor, truthful §7.2, deposit shape) — unblocks the contracts team.
4. B3–B12 in one reconciliation pass against `sync-rollups-protocol@fe7bf66` (most have one-paragraph fixes).
5. Minors + verbosity consolidation last.
