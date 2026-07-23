# Appendix A. Constants, Formulae & Glossary

A consolidated lookup surface for protocol constants, addresses, formulae, and terms. This appendix
**defines nothing of its own**: each entry is gathered from the chapter that defines it normatively,
cited inline as `(§…)`. Where this index and a chapter ever disagree, the **chapter is
authoritative**.

## A.1 Constants

| Name | Value | Meaning |
|---|---|---|
| `gasLimit` | `30_000_000` | L2 header gas limit; a protocol constant so all build paths agree (§4.1) |
| `L2_BLOCK_TIME` | `2 s` | L2 block interval; whole seconds (§4.2) |
| `L1_BLOCK_TIME` | `12 s` | L1 (Ethereum) block interval; an integer multiple of `L2_BLOCK_TIME` (§4.2) |
| `K` | `6` | L2 blocks per sync slot: 5 Live + 1 Sync (Sync last); `= L1_BLOCK_TIME / L2_BLOCK_TIME` (§4.2) |
| `MAINNET_ROLLUP_ID` | `0` | reserved id for L1; registered rollups start at 1 |
| `CALL_BEGIN / CALL_END` | `1 / 2` | rolling-hash tags for a call (§5.2) |
| `NESTED_BEGIN / NESTED_END` | `3 / 4` | rolling-hash tags for a reentrant frame (general-model, §13) |
| `POST_BATCH_GAS_LIMIT` | `4_000_000` | gas budget for the `postAndVerifyBatch` transaction (§11.3) |
| inbound-execution gas budget | `≈ 2_000_000` | per inbound system transaction (§11.5) |
| `TAG_CALLDATA` | `0x00` | the v0 DA payload tag (§7.1) |

**Deployment defaults (provisional; to pin per §12.2):** EIP-1559 elasticity `6`,
base-fee-change denominator `250`; validator set `M ≤ 20`,
threshold `N` (e.g. `⌈2M/3⌉+1`).

## A.2 Addresses & identifiers

| Item | Value | Meaning |
|---|---|---|
| `EEZL2` predeploy | `0x4200000000000000000000000000000000000007` | L2 manager + proxy factory; carries `SYSTEM_ADDRESS` (§3.1) |
| `BridgeReceiver` predeploy | `0x4200000000000000000000000000000000000008` | L2 bridge receiver (§3.1) |
| `authorizedProxies` slot | `0` | proxy registry mapping, on both managers (§3.2) |
| `rollups` mapping slot (`EEZ`) | `2` | per-rollup config `{ rollupContract, stateRoot, etherBalance }` |
| `postAndVerifyBatch` selector | `0x51dd0af6` | L1 settlement entry point (§8.4) |
| `BatchPosted` topic0 | `keccak256("BatchPosted(uint256)")` | settlement event (§8) |
| `L2ExecutionPerformed` topic0 | `keccak256("L2ExecutionPerformed(uint256,bytes32)")` | per-entry settlement verdict; `(rollupId, newState)` (§8.5) |

`SYSTEM_ADDRESS` is a deployment parameter (§12.2).

## A.3 Formulae

**Cross-chain call hash** (§3.3):
```
keccak256(abi.encode(targetRollupId, targetAddress, value, data, sourceAddress, sourceRollupId))
```

**Cross-chain proxy address (CREATE2)** (§3.2):
```
salt          = keccak256(abi.encodePacked(originalRollupId, originalAddress))
bytecodeHash  = keccak256(CrossChainProxy.creationCode ‖ abi.encode(manager, originalAddress, originalRollupId))
address       = keccak256(0xff ‖ manager ‖ salt ‖ bytecodeHash)[12:]
```

**`rollups[id].stateRoot` storage slot:** `keccak256(abi.encode(id, uint256(2))) + 1`.

**Public-inputs hash:** the two-stage `sharedPublicInput` + per-proof-system fold (§8.3).

**Rolling hash** (§5.2): `CALL_BEGIN = keccak256(h, 1, callNumber)`;
`CALL_END = keccak256(h, 2, callNumber, success, returnData)`; `NESTED_*` add tags `3`/`4`.

**Slot heights** (§4.2): `K = L1_BLOCK_TIME / L2_BLOCK_TIME`; one Sync block per L1 block, as the
last block of the slot.

**Per-entry ether invariant** (§5.4): `Σ StateDelta.etherDelta == etherIn − etherOut`.

**Partition invariant** (general-model, §13): `callCount + Σ expectedL1ToL2Calls[i].callCount ==
L2ToL1Calls.length`.

## A.4 DA payload grammar (§7.1)

```
payload := 0x00 ‖ rlp([ blockTxCounts: uint16[], transactions: bytes[], l2_entries: bytes[] ])
```
Invariants: `sum(blockTxCounts) == transactions.len()`; each count fits `uint16`; `blockTxCounts`
uses canonical minimal-length RLP integers; the Sync block contributes a trailing `0`. Byte-exact:
[Appendix D](D-wire-formats.md).

## A.5 Glossary

- **EEZ** — the general cross-chain protocol (contracts + execution/settlement model).
- **Rollup0 / GC** — the first chain on EEZ (Gnosis Chain).
- **Operator** — the single permissioned actor: sequences, simulates, builds, posts (§2.1).
- **Validator set** — the permissioned N-of-M signers attesting batches (§8).
- **Follower / Deriver** — a party reconstructing the L2 from L1 (§10).
- **Sync block** — the last L2 block of a slot; carries the inbound system transactions (§4.2).
- **Live block** — an ordinary L2 block; user transactions only (§4.2).
- **Sync slot** — the `K` L2 blocks per L1 block (§4.2).
- **Cross-chain proxy** — local CREATE2 stand-in for a remote contract (§3.2).
- **System transaction** — the unsigned type-`0x7E` inbound delivery from `SYSTEM_ADDRESS` (§3.4).
- **Execution entry (`ExecutionEntry`)** — the unit of cross-chain execution (§5.1).
- **Lookup (`LookupCall`)** — a proven cross-chain **read** (`STATICCALL`; v0, §3.5/§5.3); the
  *reverting*-call lookup is general-model (§13).
- **Rolling hash** — the per-entry accumulator binding replay to the attested execution (§5.2).
- **`revertSpan`** — forced rollback of successful calls (general-model, §13).
- **State delta (`StateDelta`)** — one rollup's pre→post state transition + ether change (§5.1).
- **Public-inputs hash** — the digest validators sign and the contract recomputes (§8.3).
- **Bundle** — the all-or-nothing `[postAndVerifyBatch, trigger]` L1 transaction pair (§7.4).
- **Batch** — `ProofSystemBatchPerVerificationEntries`, the `postAndVerifyBatch` argument (§7.3).

## A.6 Errors (reverts)

| Error | Condition | Ref |
|---|---|---|
| `StateRootMismatch` | an entry's `currentState` ≠ the rollup's live state root | H.1, §5.4 |
| `EtherDeltaMismatch` | per-entry ether not conserved (`totalEtherDelta ≠ etherIn − etherOut`) | H.2, §5.4 |
| `RollingHashMismatch` | end-of-entry accumulator ≠ `entry.rollingHash` | H.4, §5.4 |
| `UnconsumedCalls` | an entry's `L2ToL1Calls` were not all consumed | §5.4 |
| `UnconsumedNestedActions` | reentrant frames not fully consumed (general-model) | §13 |
| `PostBatchReentry` | `postAndVerifyBatch` re-entered | H.7 |
| `ValueMismatch` | inbound `msg.value ≠ value` | §3.4 |
| `EmptyEntries` | inbound delivery carries no entries | §3.4 |
| `EntryHashMismatch` | delivered call hash ≠ `entries[0].proxyEntryHash` | §3.4 |
| `ThresholdNotMet` | fewer accepted proof systems attested than the rollup's threshold | §8.1 |
| `ProofSystemNotAllowed` | a listed proof system has no stored vkey for the rollup | §8.1 |
| `InvalidProof` | a proof system's `verify` returned false | §8.5 |
| `InvalidProofSystemConfig` | out-of-order / duplicate rollups or proof systems | §8.3 |
| `BlockHashUnavailable` | the requested L1 blockhash is unavailable (0) | §8.3 |

Non-named reverts: `DELEGATECALL`/`CALLCODE` to a proxy (§3.5); consuming an entry on a rollup not
verified in the current L1 block (§5.3, H.6); `setStateRoot` while locked for the L1 block a batch
already touched the rollup (§5.8).

---

*See also [Appendix B](B-gas-cost-analysis.md) and [Appendix D](D-wire-formats.md).*
