# 4. Block Production and Header Fields

## 4.1 Production Cadence

Rollup0 production uses:

```text
nominal Ethereum interval = 12 seconds
Rollup0 block interval     = 2 seconds
positions per interval     = 6
```

The six positions are five Live positions followed by one Sync position:

```text
Live, Live, Live, Live, Live, Sync
```

Production genesis is block `0`. Its timestamp MUST be an Ethereum slot timestamp, and genesis is a
Sync position. For block number `n`:

```text
n mod 6 = 0  -> Sync
otherwise    -> Live
```

For example, let production genesis have number `0` and timestamp `T`, where `T` is an Ethereum
slot timestamp. The first complete interval after genesis is `(T, T + 12]`:

| Rollup0 block | Timestamp | Position |
|---:|---:|---|
| `0` | `T` | preceding Sync / genesis |
| `1` | `T + 2` | Live |
| `2` | `T + 4` | Live |
| `3` | `T + 6` | Live |
| `4` | `T + 8` | Live |
| `5` | `T + 10` | Live |
| `6` | `T + 12` | Sync for the next Ethereum slot |

Thus “five Live positions followed by one Sync position” describes the six new positions after a
settled Sync parent; it does not classify genesis as Live. Chiado uses the analogous interval
`(T, T + 5]`, with four one-second Live positions followed by the Sync position at `T + 5`.

A Live block contains ordinary Rollup0 transactions. The final position is the Sync position. Its
block can contain ordinary pure-L2 transactions. When an inbound action succeeds, the block also
carries the protocol-derived transaction described in
[Chapter 3](03-evm-proxy-systemtx.md), after all of its pure-L2 transactions.

Live and Sync classify positions in the Rollup0 chain. They do not specify when a composer seals or
pre-builds a block. Rollup0 has no protocol-level Future position or proof window. A composer can
close transaction intake early when it needs more time to validate and submit a candidate.

Each Sync block has the scheduled timestamp of its corresponding Ethereum slot. The Sync block
still exists when that Ethereum slot is missed. A missed-slot Sync block can contain pure-L2
transactions, but cannot contain an applied inbound action. In a live candidate that spans several
Ethereum intervals, only the terminal Sync block can contain inbound protocol calls.

A **live anchor** ends at the Sync block whose timestamp equals the Ethereum block that includes the
candidate. A **catch-up anchor** ends at a Sync block with an older timestamp. A catch-up anchor
contains no inbound protocol call anywhere in its range. Its purpose is to advance the settled
cursor through pure-L2 history that accumulated while anchoring was unavailable.

Every candidate uses the EEZ current-settlement context. This context commits the containing
Ethereum child slot's timestamp and known parent Ethereum block hash to the signed input. It
identifies the intended settlement slot even when a catch-up anchor has an older Rollup0 endpoint.
The child block hash cannot be known before submission. A terminal Rollup0 timestamp later than
the intended Ethereum timestamp is invalid.

Every Rollup0 batch MUST set its EEZ `blockNumber` field to `2^64 - 1`, the latest-context
sentinel. For that value, the production Rollup0 manager contributes the complete candidate-domain
value defined in Appendix D to the authenticated proof input. This value includes
`block.timestamp`, the containing Ethereum block's timestamp, and
`blockhash(block.number - 1)`, its known parent hash. The manager rejects zero or an explicit
historical block number for Rollup0 settlement.

If the target Ethereum slot is missed, or if the named Ethereum parent changes, the candidate and
its signatures expire. For a live candidate, the composer can retain its pure-L2 `B[0]` as an
unsafe block after a producer signs its block hash under Appendix D; it discards the unaccepted
synchronous variants. If the settled Rollup0 parent is still current, the composer can propose that
exact pure-L2 range as a catch-up candidate for a later Ethereum slot. It cannot reuse the
synchronous variants or triggers. For an expired catch-up candidate, the same historical range can
also be proposed again. In both cases, the candidate needs a new settlement context and new
validator signatures. Any encoded bytes that commit the expired context must be rebuilt. Only a
canonical anchor makes the retained range safe.

Chiado is a development settlement network only. Its nominal 5-second interval contains five
1-second Rollup0 positions: four Live positions followed by one Sync position. Chiado values are
not production values. Chiado genesis is also a Sync position, and block `n` is Sync when
`n mod 5 = 0`.

The block interval is a whole number of seconds, and the nominal settlement interval is an integer
multiple of it.

## 4.2 Block Construction

Every block is derived from its parent:

```text
number    = parent.number + 1
timestamp = parent.timestamp + block_interval
```

Both additions MUST be checked. A composer MUST NOT replace the parent-derived timestamp with its
wall clock.

The fixed header choices are:

| Field | Rollup0 rule |
|---|---|
| `parentHash` | exact parent hash |
| `number` | checked parent number plus one |
| `timestamp` | checked parent timestamp plus 2 seconds |
| `gasLimit` | `30,000,000` |
| `extraData` | zero to 32 bytes selected by the composer |
| `difficulty` | zero |
| `nonce` | eight zero bytes |
| `beneficiary` | composer-selected address carried in the authenticated blob payload |
| `prevRandao` | anchor-scoped derivation defined below |
| `baseFeePerGas` | EIP-1559 value derived from the parent with elasticity `2` and denominator `50` |
| `withdrawals` | present and empty when required by the selected EVM fork |
| `parentBeaconBlockRoot` | 32 zero bytes |
| `requestsHash` | SHA-256 of the empty byte string |
| `blobGasUsed` | zero |
| `excessBlobGas` | standard parent-derived value with zero blob use; zero from genesis |
| transaction, receipt, and state fields | exact execution-derived values required by the selected EVM fork |

The Rollup0 genesis block uses `baseFeePerGas = 1,000,000,000` wei. Every later block derives its
base fee from its parent with the `2/50` rule above.

!!! success "DECISION: composer-selected block beneficiary"
    The composer selects one 20-byte `beneficiary` for each block, including the zero address if it
    chooses. The authenticated blob data must carry the exact address for every anchored block so
    all clients reconstruct the same header.

    This is a per-block value, not one value for the complete anchor batch. A catch-up batch can
    contain historical blocks from different composers. The Rollup0 blob payload uses the canonical
    run-length encoding defined in Appendix D, and decoding produces one exact `beneficiary` for
    every block.

    All terminal Sync-block variants for one block position use the same `beneficiary`; only their
    transaction-derived header values differ.

    `COINBASE` returns this address. Ordinary signed transactions use Ethereum's fee routing: the
    base fee is burned and the priority fee is credited to `beneficiary`. Type-`0x45` protocol
    transactions consume gas but pay no fee and do not credit `beneficiary`.

Rollup0 has no beacon chain. It retains the post-Cancun header field without changing the header
encoding, but fixes `parentBeaconBlockRoot` to 32 zero bytes in every block. Protocol transactions
are already committed by the transaction root. Their status, cumulative gas use, and logs are
committed by the receipt root, and their state changes are committed by the state root.

!!! note "No EIP-4788 beacon-roots update"
    Rollup0 does not execute the EIP-4788 beacon-roots contract call. It also does not expose the
    zero placeholder as a usable beacon root.

Rollup0 does not produce EIP-7685 requests for a consensus layer. Every block therefore commits
the standard empty requests hash:

```text
requestsHash = sha256("") =
0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Rollup0 does not extract EIP-6110 deposit requests and does not execute the EIP-7002 withdrawal or
EIP-7251 consolidation request system calls. These operations exist to pass requests to an
Ethereum consensus layer, which Rollup0 does not have. The corresponding request contracts are not
Rollup0 protocol predeploys.

The EIP-2935 parent-block-hash update defined in Chapter 3 is independent of a beacon chain and
executes before the block's transactions.

The composer-selected `beneficiary` and `extraData` are part of the block hash and must be available
in the published block data so followers reconstruct the same header.

### Live-Anchor-Scoped `prevRandao`

Rollup0 refreshes its RANDAO seed only after a successful canonical live anchor. A catch-up anchor
and a scheduled Sync position that is not anchored do not refresh the seed. An Ethereum
reorganization that leaves the latest Rollup0 live anchor in the canonical chain does not require
block rebuilding solely because of a RANDAO seed change. Normal anchor selection can still change
safe Rollup0 history.

For every Rollup0 block `b` before the next seed refresh:

```text
prevRandao(b) = currentSeed
```

`currentSeed` is 32 bytes. Its initial value is the `prevRandao` in the header of the finalized
Ethereum reference block selected by the Rollup0 genesis configuration.

When a live anchor becomes canonical on Ethereum, its next seed is the `prevRandao` field in the
authenticated header of the Ethereum execution block that contains the accepted anchor. That value
becomes `currentSeed` for the first Rollup0 block after the anchored endpoint. The anchored terminal
block itself uses the previous Rollup0 seed; the refresh applies only after Ethereum selects the
anchor. The containing Ethereum block's `prevRandao` may be known before inclusion, so this rule
does not claim fresh or unpredictable entropy from the anchor block's later beacon-chain reveal.

A catch-up anchor retains `currentSeed` for the first block after its endpoint. Existing unsafe
descendants can therefore remain valid while several historical ranges become safe. When a later
live anchor catches up to the current Ethereum timestamp, that live anchor refreshes the seed for
its descendants.

Every Live and Sync block copies the same value until the seed refreshes. Rollup0 does not hash the
seed with the block number and does not repeatedly hash the preceding block's `prevRandao`.

If an Ethereum reorganization removes the latest live anchor, Rollup0 restores the seed from the
last surviving live anchor and rebuilds the affected descendants. Removing a catch-up anchor
retreats the settled cursor but does not change the seed. Neither case adds a new reorganization
condition: removing an anchor already requires Rollup0 to retreat to the preceding settled cursor.

Applications MUST NOT use `prevRandao` as secure same-block randomness. Once `currentSeed` is
known, every block exposes that same value until the next live anchor. Secure application randomness
requires a delayed commitment to a future live-anchor seed.

!!! success "DECISION: direct-copy `prevRandao` mapping"
    Rollup0 copies `currentSeed` directly into every block until the next successful canonical live
    anchor refreshes it. Exact repetition makes the absence of fresh entropy visible and does not
    offer a menu of different derived values within one seed interval.

    Hashing the seed with the chain ID and block number would give each block a distinct value but no
    additional entropy. Rollup0 does not use that mapping. Applications that need a unique per-block
    salt can combine `prevRandao` with `block.number`, `block.chainid`, and application-specific
    context. That still does not turn a known seed into secure randomness.

!!! warning "Review before production: RANDAO refresh cadence"
    Live-anchor-only refreshes are the selected Rollup0 rule and are not a production blocker. They
    avoid rebuilding L2 history for Ethereum reorganizations that do not remove a Rollup0 anchor,
    but the seed can remain known and unchanged for the complete period between live anchors,
    including a long catch-up period.

    The team may revisit more frequent Ethereum-derived refreshes or a separate delayed-randomness
    mechanism before genesis. If it does not, the live-anchor-only rule remains in force. Changing
    the rule after genesis requires a Rollup0 hardfork.

!!! success "DECISION: copy the genesis reference block's RANDAO"
    Rollup0 copies the `prevRandao` of its designated finalized Ethereum reference block directly
    into the genesis `currentSeed`. This avoids an arbitrary constant and uses the same direct-copy
    rule as later live-anchor refreshes.

    The reference block number and hash are genesis parameters. The final Rollup0 genesis block
    cannot be calculated until that Ethereum block is finalized.

## 4.3 Sync Blocks and Candidate Ranges

An anchor range:

- starts immediately after its named settled Rollup0 parent;
- contains every Rollup0 block since that parent, including empty blocks;
- can span more than one nominal Ethereum interval;
- ends at a scheduled Sync position;
- does not end after the target Ethereum block timestamp; and
- publishes enough boundary data to reconstruct every block in the range.

The range begins at the last Ethereum-confirmed Rollup0 head. Its first block is
`fromBlock.number + 1`. Its terminal position contains the variants `B[0]` through `B[s]` described
in Chapter 7.

For a live anchor, the terminal timestamp equals the target Ethereum timestamp and `n` can be zero
or greater. For a catch-up anchor, the terminal timestamp is earlier than the target Ethereum
timestamp, `n = 0`, and the complete range contains no inbound protocol transaction or failed
lookup. Consecutive catch-up anchors can advance through old ranges over several Ethereum blocks.

!!! success "DECISION: terminal block hashes are EEZ commitments"
    One proof or signature set covers all synchronous prefixes. Rollup0 derives every terminal
    block hash from the authenticated block inputs. `H[0]` and each successful `H[k]` appear in the
    Rollup0 state deltas of the EEZ batch, so the blob does not carry a second hash vector.

    The candidate also commits the action count and ordered action manifest. A failed terminal
    action adds no Rollup0 transaction or block variant, so the block hash alone cannot distinguish
    a caught terminal failure from an omitted proposed trigger. Rollup0 derivation need not
    distinguish them; the endpoint depends only on the successful-action count `k`.

## 4.4 Unsafe Blocks

A composer MAY publish an unsafe candidate before Ethereum selects it. Several composers can
publish different valid unsafe siblings.

Only canonical Ethereum settlement advances the safe Rollup0 chain. A composer whose candidate
loses or is not included MUST stop extending its conflicting unsafe branch and build from the new
canonical settled parent. It MAY retain the old branch as noncanonical data in case an Ethereum
reorganization makes it relevant again.

---

*Next: [Chapter 5, Execution Profile](05-execution-model.md).*
