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

A Live block contains ordinary Rollup0 transactions. A Sync block terminates the interval and
carries the system transaction described in [Chapter 3](03-evm-proxy-systemtx.md) when an inbound
action is accepted.

This draft has no proof window. All five non-Sync positions are Live positions.

Each Sync block shares the timestamp of the Ethereum block that carries its candidate. The six
Rollup0 blocks in that interval use the same Ethereum anchor.

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
| `extraData` | empty |
| `difficulty` | zero |
| `nonce` | eight zero bytes |
| `beneficiary` | deployment fee recipient |
| `baseFeePerGas` | EIP-1559 value derived from the parent |
| `withdrawals` | present and empty when required by the selected EVM fork |
| `parentBeaconBlockRoot` | zero when required by the selected EVM fork |
| transaction, receipt, state, request, and blob fields | exact execution-derived or parent-derived values required by the selected EVM fork |

The `prevRandao` value is the RANDAO of the Ethereum block to which the interval is anchored. All
six Rollup0 blocks in that interval use the same value. The shared Sync/Ethereum timestamp identifies
that block. Applications MUST NOT use this value as secure randomness: it is visible to builders
and can be biased by the Ethereum proposer.

## 4.3 Sync Blocks and Candidate Ranges

A normal candidate range:

- starts immediately after its named settled Rollup0 parent;
- contains the six Rollup0 blocks for one nominal interval;
- ends at a Sync block; and
- publishes one transaction count for every block in the range.

The range begins at the last Ethereum-confirmed Rollup0 head. Its first block is
`fromBlock + 1`, and its Sync block is `toBlock`.

## 4.4 Unsafe Blocks

A composer MAY publish an unsafe candidate before Ethereum selects it. Several composers can
publish different valid unsafe siblings.

Only canonical Ethereum settlement advances the safe Rollup0 chain. A composer whose candidate
loses or is not included MUST discard the conflicting unsafe blocks before building on the
canonical settled parent.

---

*Next: [Chapter 5, Execution Profile](05-execution-model.md).*
