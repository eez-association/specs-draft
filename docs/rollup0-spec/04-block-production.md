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

A Live block contains ordinary Rollup0 transactions. The final position is the Sync position. Its
block can contain ordinary pure-L2 transactions. When an inbound action is applied, the block also
carries the protocol-derived transaction described in
[Chapter 3](03-evm-proxy-systemtx.md), after all of its pure-L2 transactions.

This draft has no proof window. All five non-Sync positions are Live positions.

Each Sync block has the scheduled timestamp of its corresponding Ethereum slot. The Sync block
still exists when that Ethereum slot is missed. Only the terminal Sync block of an included
candidate necessarily shares a timestamp with the Ethereum block that carries the candidate.

Chiado is a development settlement network only. Its nominal 5-second interval contains five
1-second Rollup0 positions: four Live positions followed by one Sync position. Chiado values are
not production values.

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
| `beneficiary` | deployment fee recipient |
| `baseFeePerGas` | EIP-1559 value derived from the parent |
| `withdrawals` | present and empty when required by the selected EVM fork |
| `parentBeaconBlockRoot` | 32 zero bytes |
| transaction, receipt, state, request, and blob fields | exact execution-derived or parent-derived values required by the selected EVM fork |

Rollup0 has no beacon chain. It retains the Cancun header field without changing the header
encoding, but fixes `parentBeaconBlockRoot` to 32 zero bytes in every block. Protocol transactions
are already committed by the transaction root. Their status, cumulative gas use, and logs are
committed by the receipt root, and their state changes are committed by the state root.

!!! note "No EIP-4788 beacon-roots update"
    Rollup0 does not execute the EIP-4788 beacon-roots contract call. It also does not expose the
    zero placeholder as a usable beacon root.

The composer-selected `extraData` is part of the block hash and must be available in the published
block data so followers reconstruct the same header.

Applications MUST NOT use `prevRandao` as secure randomness. Its source is visible to builders and
can be biased by the Ethereum proposer.

!!! note "TO BE DEFINED"
    The exact `prevRandao` source for live, unanchored, and missed-slot Rollup0 blocks is not yet
    selected.

    - Using the latest observed Ethereum RANDAO permits live block production before the matching
      Ethereum slot completes, but several Rollup0 intervals can reuse one value.
    - Using the RANDAO from the Ethereum block at the matching Sync timestamp gives direct slot
      alignment, but requires waiting for that block and needs a separate missed-slot rule.

## 4.3 Sync Blocks and Candidate Ranges

An anchor range:

- starts immediately after its named settled Rollup0 parent;
- contains every Rollup0 block since that parent, including empty blocks;
- can span more than one nominal Ethereum interval;
- ends at the Rollup0 position whose timestamp equals the target Ethereum block timestamp; and
- publishes enough boundary data to reconstruct every block in the range.

The range begins at the last Ethereum-confirmed Rollup0 head. Its first block is
`fromBlock.number + 1`. Its terminal position contains the variants `B[0]` through `B[n]` described
in Chapter 7.

!!! note "TO BE DEFINED"
    The exact block commitment for every possible synchronous prefix is not yet selected. The
    published data must be enough to reconstruct each prefix block, but the team still needs to
    decide whether validators sign every possible block hash or derive the selected hash from the
    number of processed actions. The commitment must distinguish different prefix lengths even
    when their state roots are equal.

## 4.4 Unsafe Blocks

A composer MAY publish an unsafe candidate before Ethereum selects it. Several composers can
publish different valid unsafe siblings.

Only canonical Ethereum settlement advances the safe Rollup0 chain. A composer whose candidate
loses or is not included MUST discard the conflicting unsafe blocks before building on the
canonical settled parent.

---

*Next: [Chapter 5, Execution Profile](05-execution-model.md).*
