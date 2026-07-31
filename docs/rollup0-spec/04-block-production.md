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
sentinel. For that value, the Rollup0 manager contributes
`abi.encode(block.timestamp, blockhash(block.number - 1))` to the authenticated proof input.
`block.timestamp` is the containing Ethereum block's timestamp. `blockhash(block.number - 1)` is
its known parent hash. Zero or an explicit historical block number does not provide this complete
context and is invalid for Rollup0 settlement.

If the target Ethereum slot is missed, or if the named Ethereum parent changes, the candidate and
its signatures expire. For a live candidate, the composer can retain its pure-L2 `B[0]` as an
unsafe block, but it discards the unaccepted synchronous variants. If the settled Rollup0 parent
is still current, the composer can propose that exact pure-L2 range as a catch-up candidate for a
later Ethereum slot. It cannot reuse the synchronous variants or triggers. For an expired
catch-up candidate, the same historical range can also be proposed again. In both cases, the
candidate needs a new settlement context and new signatures. Any encoded bytes that commit the
expired context must be rebuilt. Only a canonical anchor makes the retained range safe.

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
| `beneficiary` | TO BE DEFINED and carried in the authenticated blob payload |
| `prevRandao` | anchor-scoped derivation defined below |
| `baseFeePerGas` | EIP-1559 value derived from the parent with elasticity `2` and denominator `50` |
| `withdrawals` | present and empty when required by the selected EVM fork |
| `parentBeaconBlockRoot` | 32 zero bytes |
| `requestsHash` | SHA-256 of the empty byte string |
| transaction, receipt, state, and blob fields | exact execution-derived or parent-derived values required by the selected EVM fork |

!!! note "TO BE DEFINED: block beneficiary"
    The blob format must carry the exact `beneficiary` whenever it is not fixed by the protocol.
    Rollup0 still needs to choose between a composer-selected address, one deployment-wide fee
    recipient, and the zero address. The choice affects the `COINBASE` opcode, the block hash, and
    any priority-fee routing.

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

The EIP-2935 parent-block-hash update defined in Chapter 3 is independent of a beacon chain and
executes before the block's transactions.

The composer-selected `extraData` is part of the block hash and must be available in the published
block data so followers reconstruct the same header.

### Live-Anchor-Scoped `prevRandao`

Rollup0 refreshes its RANDAO seed only after a successful canonical live anchor. A catch-up anchor
and a scheduled Sync position that is not anchored do not refresh the seed. An Ethereum
reorganization that leaves the latest Rollup0 live anchor in the canonical chain does not require
block rebuilding solely because of a RANDAO seed change. Normal anchor selection can still change
safe Rollup0 history.

For block `b`, define:

```text
DOMAIN = keccak256(UTF8("ROLLUP0_PREVRANDAO_V1"))

prevRandao(b) = keccak256(
    DOMAIN
    || uint256_be(rollup0ChainId)
    || currentSeed
    || uint256_be(b.number)
)
```

`uint256_be(x)` is the 32-byte, unsigned, big-endian encoding of `x`. `currentSeed` is 32 bytes.
The initial `currentSeed` is selected in the production genesis.

When a live anchor becomes canonical on Ethereum, its next seed is the current-epoch RANDAO mix in
the Ethereum beacon state after processing the beacon block that contains the accepted anchor. The
next seed becomes `currentSeed` for the first Rollup0 block after the anchored endpoint. The
anchored terminal block itself uses the previous seed because the next seed is not available until
its Ethereum block is published.

A catch-up anchor retains `currentSeed` for the first block after its endpoint. Existing unsafe
descendants can therefore remain valid while several historical ranges become safe. When a later
live anchor catches up to the current Ethereum timestamp, that live anchor refreshes the seed for
its descendants.

Every Live and Sync block uses the same formula. Blocks between two anchors have different
`prevRandao` values because their block numbers differ, but they share one source of entropy.
Rollup0 does not repeatedly hash the preceding Rollup0 block's `prevRandao`.

If an Ethereum reorganization removes the latest live anchor, Rollup0 restores the seed from the
last surviving live anchor and rebuilds the affected descendants. Removing a catch-up anchor
retreats the settled cursor but does not change the seed. Neither case adds a new reorganization
condition: removing an anchor already requires Rollup0 to retreat to the preceding settled cursor.

Applications MUST NOT use `prevRandao` as secure same-block randomness. Once `currentSeed` is
known, every derived value until the next live anchor is predictable. The hash gives each block a
separate value but does not add entropy. Secure application randomness requires a delayed
commitment to a future live-anchor seed.

!!! note "TO BE DISCUSSED: per-block `prevRandao` mapping"
    The seed-refresh rule and the mapping from one seed to L2 header values are independent
    decisions. Holding the refresh rule fixed, Rollup0 can use either of the following mappings:

    - **Per-block derivation (current draft).** The formula above gives every block a distinct,
      chain- and height-separated value. This avoids exact repeats for applications that use
      `prevRandao` as a per-block salt. It is a Rollup0-specific consensus rule, however, and a
      changing value can be mistaken for fresh randomness. Once `currentSeed` is public, a
      composer, user, or contract can calculate every value until the next refresh. A composer can
      therefore delay a transaction to a favorable known block when an application incorrectly
      makes its result depend on the derived value.

    - **Direct copy (OP Stack style).** Set `prevRandao(b) = currentSeed` for every block until the
      seed refreshes. The OP Stack similarly copies the L1 origin's `prev_randao` into each L2
      block, so the value repeats for all L2 blocks with that origin and changes when the origin
      advances. This rule is simpler, matches a deployed L2 convention, makes the lack of fresh
      entropy visible, and offers no menu of different `prevRandao` values within one seed
      interval. Its cost is exact repetition: an application that uses only `prevRandao` receives
      the same result in consecutive blocks, and multiple chains can expose the same raw L1 value.
      Applications that need a unique per-block salt can include `block.number`, `block.chainid`,
      and application-specific context themselves.

    Neither mapping adds entropy, repairs bias in the L1 seed, changes when the seed becomes
    predictable, or changes which Ethereum reorganizations require rebuilding Rollup0 history.
    Those properties are controlled by the seed source and refresh cadence. The choice is therefore
    between explicit repetition and deterministic diversification, not between weak and strong
    randomness.

!!! note "TO BE DISCUSSED: RANDAO refresh cadence"
    The anchor-scoped design may be suboptimal. It avoids making every Ethereum reorganization an
    L2 reorganization, but the seed can remain known and unchanged for the complete period between
    live anchors, including a long catch-up period.

    Before production, the team should compare this rule with more frequent Ethereum-derived
    refreshes and a separate delayed-randomness mechanism. The comparison must cover freshness,
    manipulation and censorship, Ethereum reorganization behavior, consensus-layer data
    requirements, and the maximum time between anchors.

!!! note "TO BE DEFINED: genesis RANDAO seed"
    The production genesis must select the initial 32-byte `currentSeed`.

## 4.3 Sync Blocks and Candidate Ranges

An anchor range:

- starts immediately after its named settled Rollup0 parent;
- contains every Rollup0 block since that parent, including empty blocks;
- can span more than one nominal Ethereum interval;
- ends at a scheduled Sync position;
- does not end after the target Ethereum block timestamp; and
- publishes enough boundary data to reconstruct every block in the range.

The range begins at the last Ethereum-confirmed Rollup0 head. Its first block is
`fromBlock.number + 1`. Its terminal position contains the variants `B[0]` through `B[n]` described
in Chapter 7.

For a live anchor, the terminal timestamp equals the target Ethereum timestamp and `n` can be zero
or greater. For a catch-up anchor, the terminal timestamp is earlier than the target Ethereum
timestamp, `n = 0`, and the complete range contains no inbound protocol transaction or failed
lookup. Consecutive catch-up anchors can advance through old ranges over several Ethereum blocks.

!!! note "TO BE DEFINED"
    One proof or signature set covers all synchronous prefixes. The published data must be enough
    to reconstruct every terminal variant, but the blob format still needs to choose between
    carrying an explicit ordered vector of terminal block hashes and deriving that vector entirely
    from the authenticated block inputs. Any carried hash is checked against replay.

    The candidate must also commit the action count and ordered trigger manifest. A block hash
    alone cannot distinguish two prefix lengths when a failed action adds no Rollup0 transaction
    and leaves the terminal block unchanged.

## 4.4 Unsafe Blocks

A composer MAY publish an unsafe candidate before Ethereum selects it. Several composers can
publish different valid unsafe siblings.

Only canonical Ethereum settlement advances the safe Rollup0 chain. A composer whose candidate
loses or is not included MUST stop extending its conflicting unsafe branch and build from the new
canonical settled parent. It MAY retain the old branch as noncanonical data in case an Ethereum
reorganization makes it relevant again.

---

*Next: [Chapter 5, Execution Profile](05-execution-model.md).*
