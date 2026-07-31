# Appendix A. Reference

This appendix summarizes values defined in the main chapters. The chapter text takes precedence.

## A.1 Fixed Production Values

| Name | Value |
|---|---|
| Settlement network | Ethereum |
| Nominal Ethereum interval | `12 seconds` |
| Rollup0 block interval | `2 seconds` |
| Positions per nominal interval | `6` |
| Position order | `5 Live, 1 Sync` |
| Block gas limit | `30,000,000` |
| EIP-1559 gas target | `15,000,000` |
| EIP-1559 elasticity multiplier | `2` |
| EIP-1559 base-fee-change denominator | `50` |
| Initial EVM fork | Fusaka, using the Osaka execution-layer rules |
| Settlement transaction gas budget | `4,000,000` |
| Inbound transaction type | TO BE DEFINED; unsigned EIP-2718 transaction |
| Maximum transaction gas limit | `16,777,216` (`2^24`) |
| Inbound transaction gas limit | `min(remaining block gas, 16,777,216)` |
| Inbound transaction gas charging | standard non-creation intrinsic gas and EIP-7623 calldata floor |
| Inbound transaction fee | TO BE DISCUSSED |
| System caller | `0xfffffffffffffffffffffffffffffffffffffffe` |
| Inbound transaction access list | empty |
| Inbound transaction blob hashes | empty |
| EIP-2935 history update | enabled from genesis |
| `parentBeaconBlockRoot` | 32 zero bytes |
| EIP-4788 beacon-roots update | disabled |
| `requestsHash` | `sha256("")` |
| `prevRandao` refresh | after each successful canonical live anchor |
| Refreshed RANDAO source | post-block Ethereum beacon-state RANDAO mix |
| Refreshed seed activation | first Rollup0 block after the anchored endpoint |
| `prevRandao` mapping | per-block derivation in the current draft; direct copy under discussion |
| `extraData` | zero to 32 composer-selected bytes |
| DA channel | Ethereum blobs |
| Candidate production | open |
| Candidate relay | permissionless |
| Candidate selection | first applicable candidate in canonical Ethereum transaction order |
| Candidate lifetime | one intended Ethereum child slot |
| Rollup0 batch limit | one EEZ batch that contains Rollup0 per Ethereum block |
| EEZ batch `blockNumber` | `2^64 - 1` (current settlement context) |
| Live-anchor endpoint | Sync timestamp equal to containing Ethereum block timestamp |
| Catch-up-anchor endpoint | older Sync timestamp; no synchronous action |
| Catch-up RANDAO behavior | retain the seed from the latest live anchor |
| EEZ batch scope | Rollup0-only SHOULD; restricted shared batches allowed |
| Failed application call | Final candidate action; L1 EEZ failed lookup; no Rollup0 transaction or receipt; block and state root unchanged |
| `EEZL2` genesis balance | `0` |
| `EEZL2` inbound transaction balance rule | post-call balance equals pre-call balance |
| Ordinary genesis native balances | none |
| L1 native-value custody | pooled in EEZ and accounted through Rollup0's per-rollup `etherBalance` |

## A.2 Development Cadence

Chiado development uses:

```text
nominal interval       = 5 seconds
Rollup0 block interval = 1 second
positions              = 5
order                  = 4 Live, 1 Sync
```

These are not production values.

## A.3 Reserved Rollup0 Addresses and Types

| Item | Draft value |
|---|---|
| `EEZL2` predeploy | `0xee50000000000000000000000000000000000000` |
| `EEZL2` implementation | Latest `eez-core-protocol` version selected for genesis |

The production genesis must bind exact bytecode and exact protocol-transaction behavior.

## A.4 Provisional Deployment Values

The restored draft uses these development defaults. Production must either confirm or replace them:

| Item | Development default |
|---|---|
| Maximum validator/prover set size | `M <= 20` |
| Example threshold | `ceil(2M / 3) + 1` |

!!! note "TO BE DEFINED"
    The Rollup0 chain ID, genesis base fee, genesis RANDAO seed, fee-vault addresses,
    validator/prover keys, and actual threshold are not fixed.

## A.5 DA Format

!!! note "TO BE DEFINED"
    Rollup0 publishes anchored chain data in Ethereum blobs. The byte-exact format is not yet
    defined. See [Appendix D](D-wire-formats.md).

## A.6 Terms

- **Candidate:** one proposed Rollup0 range, EEZ batch, DA payload, proof context, proof or
  signatures, and set of intended Ethereum prefix bundles.
- **Composer:** any party that constructs a candidate.
- **Validator/prover:** a member of the permissioned validity set that independently checks and
  signs or proves candidates.
- **Relayer:** any party that submits a completed candidate to Ethereum.
- **Follower:** a client that derives Rollup0 from canonical Ethereum.
- **Live block:** an ordinary Rollup0 block in a nominal interval.
- **Sync block:** the block at the scheduled final Rollup0 position for an Ethereum slot. It
  contains a pure-L2 transaction prefix followed by zero or more successful synchronous actions.
- **Live anchor:** an anchor whose terminal Sync timestamp equals the containing Ethereum block
  timestamp. It can contain synchronous actions and refreshes the RANDAO seed after inclusion.
- **Catch-up anchor:** an anchor whose terminal Sync timestamp is older than the containing
  Ethereum block timestamp. It contains only pure-L2 execution and does not refresh the RANDAO
  seed.
- **Protocol transaction:** an unsigned EIP-2718 transaction derived from a successful
  Ethereum-to-Rollup0 action and included after the Sync block's pure-L2 prefix.
- **Ethereum-confirmed cursor (settled cursor):** the exact Rollup0 parent identity established by
  canonical Ethereum history. It is safe but not necessarily finalized and can retreat after an
  Ethereum reorganization.
- **Sibling:** one of several candidates built from the same settled parent.
- **Applicable:** valid and based on the current settled cursor when evaluated on Ethereum.
- **Stale:** based on a cursor that an earlier applicable candidate has superseded.

---

*Next: [Appendix B, Gas and Cost Model](B-gas-cost-analysis.md).*
