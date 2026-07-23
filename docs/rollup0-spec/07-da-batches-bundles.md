# 7. Data Availability, Batches & L1 Bundles

This chapter defines the on-the-wire batch, its data-availability payload, and the L1 bundle. The
settlement *rule* (when a posted batch counts as settled) is in [§8](08-proving-settlement.md);
L1-reorg handling is in [§10](10-derivation-following.md).

## 7.1 Data-availability payload

The DA payload is a tagged, RLP-encoded structure:

```
payload := tagByte ‖ rlp([ blockTxCounts, transactions, l2_entries ])
tagByte  = 0x00          // calldata format (the v0 format)
```

| Field | Type | Meaning |
|---|---|---|
| `blockTxCounts` | `list<uint16>` | one entry per L2 block in the batch range; `blockTxCounts[i]` = number of user transactions in block `fromBlock + 1 + i`; length `== toBlock − fromBlock` |
| `transactions` | `list<bytes>` | flat, block-major list of EIP-2718 signed user transactions |
| `l2_entries` | `list<bytes>` | ABI-encoded L2-shape `ExecutionEntry`s, for followers to rebuild the inbound system transaction; empty for non-value batches |

Decode invariants: leading byte `== 0x00` (else reject); `sum(blockTxCounts) == transactions.len()`;
each count fits `uint16`. `blockTxCounts` integers use **canonical minimal-length RLP** (the RLP
default, not a fixed 2-byte width). The Sync block is the last block in the range, so `blockTxCounts`
carries a **trailing `0`** for it: its user-transaction list is **empty** in the payload — the Sync
block's system transactions are reconstructed deterministically from the batch's entries (§3.4), not
transported. Per-transaction field validity is checked by re-execution, not the codec. Byte-exact
grammar in [Appendix D](D-wire-formats.md).

> **Blob DA.** EIP-4844 blobs are the intended default DA channel, with calldata used when
> cheaper. The blob packing format is specified separately and is out of scope here; **v0 uses the
> calldata format above.** Full data availability is a Rollup0/GC choice, not an EEZ requirement.

## 7.2 Block range as public input

A batch covers the full L2-block range it produced: `fromBlock = cursor` (the L1-confirmed L2 head;
not itself a produced block), and the first produced block is `fromBlock + 1`; `toBlock` is the
Sync block. `fromBlock`/`toBlock` are **not** in the payload — they are public inputs bound by the
proof, recovered from on-chain state (the highest L2 block any landed batch confirmed; §8, §10). A
batch therefore cannot misrepresent which L2 blocks it covers.

## 7.3 The batch

`postAndVerifyBatch` takes a single `ProofSystemBatchPerVerificationEntries`:

```solidity
struct ProofSystemBatchPerVerificationEntries {
    ExecutionEntry[]           entries;                       // §5
    LookupCall[]               l1ToL2lookupCalls;             // proven STATICCALL reads (v0); reverting-call lookups general-model (§13)
    uint256                    transientExecutionEntryCount;  // count of leading entries loaded as transient (≤ entries.length); §5.5
    uint256                    transientLookupCallCount;       // count of leading lookup calls loaded as transient (≤ l1ToL2lookupCalls.length)
    address[]                  proofSystems;                  // §8
    RollupIdWithProofSystems[] rollupIdsWithProofSystems;     // per-rollup proof-system subset (§8)
    bytes32                    crossProofSystemInteractions;  // opaque domain separator (App. C.1)
    uint256[]                  blobIndices;                   // empty in v0 (calldata DA)
    bytes                      callData;                      // the §7.1 payload
    bytes[]                    proofs;                         // one per proofSystems entry; ECDSA PS = 65-byte r‖s‖v (§8, App. D)
    uint64                     blockNumber;                   // L1-block context bound by the proof
}
```

`callData` carries the payload; the contract treats it as opaque, hashing it into the public
inputs (§8). In v0 the operator posts one batch per L1 block, covering the slot's blocks.

## 7.4 The L1 bundle

A batch settles as a single all-or-nothing bundle, in order:

```
bundle = [ postAndVerifyBatch_tx, trigger_L1_tx ]
```

— the `postAndVerifyBatch` transaction followed by the L1 transaction that triggered the
cross-chain interaction. The bundle MUST be included **whole and in order in one L1 block, or not
at all**. A relay/builder that cannot guarantee all-or-nothing inclusion provides no atomicity, and
is not a conforming v0 deployment.

**Where atomicity comes from.** The two transactions play distinct roles. `postAndVerifyBatch`
(first) verifies the attestation, advances the L2 state root, and **seeds the L1 execution tables**
with the proven cross-chain results — for each proxy call the batch covers, it records the value
that call MUST return given the current state. The triggering user transaction (second) then runs
the real interaction: when the L1 contract calls a proxy, `EEZ` returns the seeded value, and the
transaction **validates the transition** — if L1 execution disagrees with what was seeded (and hence
with the attested L2 effect), it reverts (§5.4). The EVM does not roll the first transaction back if
the second reverts; atomicity is instead the **all-or-nothing bundle** above — the builder includes
both transactions or neither, so a reverting trigger drops the whole bundle and the L2-root advance
never lands. (The §5.5 meta hook is the in-frame variant used when the settlement caller is itself a
contract; the v0 user-trigger path is the two-transaction bundle described here.)

If the bundle does not land, the optimistically-committed Sync block is rolled back (§4.4, §6).

---

*Next: [§8 Proving & Settlement](08-proving-settlement.md).*
