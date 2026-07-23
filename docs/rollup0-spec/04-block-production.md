# 4. Block Production & Header Fields

The operator and any follower build L2 blocks by the **same** rules from the same inputs, so the
blocks are byte-identical; a field not derivable identically by both would fork the chain. Header
fields are therefore pinned to protocol constants wherever a choice exists.

## 4.1 Header fields

| Field | Value / derivation |
|---|---|
| `parentHash` | the parent block's hash |
| `number` | `parent.number + 1` |
| `timestamp` | `parent.timestamp + L2_BLOCK_TIME` (2 s), strictly increasing |
| `prev_randao` (`mixHash`) | the RANDAO of the L1 block the L2 block is anchored to (§4.3) |
| `suggested_fee_recipient` | the deployment fee recipient (§11) |
| `gasLimit` | `30_000_000` (protocol constant) |
| `baseFeePerGas` | EIP-1559 from the parent header (parameters in [Appendix A](A-reference.md)) |
| `extraData` | empty |
| `withdrawalsRoot` / `withdrawals` | `Some(empty)` when Shanghai-active; Rollup0 has no L1-style withdrawals |
| `parentBeaconBlockRoot` | `Some(0x0)` when Cancun-active; the L2 has no beacon chain |
| `difficulty`, `nonce` | `0` (post-Merge) |
| `blobGasUsed`, `excessBlobGas` | per Cancun; L2 blocks carry no blobs |
| roots / bloom / `gasUsed` | computed by execution over the block's transactions |

## 4.2 Slot model (v0)

L2 production is organized into **sync slots**, one per L1 block. v0 fixes **K = 6** L2 blocks per
slot: **5 Live blocks followed by 1 Sync block** (the last block of the slot). There is **no
proof-window** — every non-Sync block is an ordinary Live block. (A proof-window is only needed by
a future sequencer+ZK variant; see [§12](12-open-issues.md).)

- **Live block** — ordinary cadence; user transactions only.
- **Sync block** — the last block of the slot. It carries the cross-chain **system transactions**
  at its head (§3.4) and is aligned to the L1 block that carries the slot's batch (§7). When a
  slot has no cross-chain work, the Sync block is empty.

L2 block time MUST be a whole number of seconds, and the L1 block time MUST be an integer multiple
of it (so `K` is integral). Each Sync block shares the **timestamp of the L1 block it anchors to** —
the two are co-produced for the same instant — which fixes the slot's L1 anchor (and therefore
`prev_randao`, §4.3).

## 4.3 `prev_randao`

`prev_randao` is the **RANDAO of the L1 block the slot is anchored to** — the L1 block whose
timestamp the Sync block shares (§4.2) and that carries the slot's batch (§7, §8). All `K` L2 blocks
of the slot use this one value. The shared timestamp pins *which* L1 block supplies it, so the value
is identical across operator and follower — deterministic and re-derivable — and known to the
builder at build time.

> `prev_randao` on Rollup0 is **predictable to the operator and L1-proposer-biasable** — like L1's
> own RANDAO, the value is an input to the block and is therefore known to whoever builds it. It
> MUST NOT be used as a source of adversary-resistant randomness; applications needing secure
> randomness must use a VRF or commit-reveal. (Unpredictable in-block randomness is impossible
> under synchronous deterministic execution — the value must be fixed before the block runs.)

## 4.4 Optimistic commit and rollback

The operator commits the Sync block to L2 **immediately**, then posts the batch and the triggering
L1 transaction to L1 as one atomic bundle (§7). **L1 is the source of truth:** if the bundle does
not land, the operator MUST roll the Sync block back so the L2 keeps only what L1 confirmed. A
follower never adopts an operator head that L1 has not confirmed (§10).

---

*Next: [§5 Execution Model](05-execution-model.md).*
