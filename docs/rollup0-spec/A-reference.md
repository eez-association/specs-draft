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
| EVM fork | Cancun |
| Settlement transaction gas budget | `4,000,000` |
| Inbound system-transaction gas budget | approximately `2,000,000` |
| DA tag | `0x00` |
| DA channel | Ethereum calldata |
| Candidate production | open |
| Candidate relay | permissionless |
| Candidate selection | first applicable candidate in canonical Ethereum transaction order |

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
| L2 EEZ manager | `0x4200000000000000000000000000000000000007` |
| Bridge receiver | `0x4200000000000000000000000000000000000008` |
| Inbound system-transaction type | `0x7e` |

The production genesis must bind exact bytecode and exact system-transaction behavior.

## A.4 Provisional Deployment Values

The restored draft uses these development defaults. Production must either confirm or replace them:

| Item | Development default |
|---|---|
| EIP-1559 elasticity multiplier | `6` |
| EIP-1559 base-fee-change denominator | `250` |
| Maximum validator/prover set size | `M <= 20` |
| Example threshold | `ceil(2M / 3) + 1` |

The Rollup0 chain ID, genesis base fee, `SYSTEM_ADDRESS`, fee-vault addresses, validator/prover
keys, and actual threshold are not fixed.

## A.5 DA Grammar

```text
payload = 0x00 || rlp([blockTxCounts, transactions, l2Entries])
```

`blockTxCounts` contains canonical minimal RLP integers with values in `[0, 65535]`.
Its last value is zero for the Sync block. See [Appendix D](D-wire-formats.md).

## A.6 Terms

- **Candidate:** one proposed Rollup0 range, EEZ batch, DA payload, proof context, proof or
  signatures, and intended Ethereum bundle.
- **Composer:** any party that constructs a candidate.
- **Validator/prover:** a member of the permissioned validity set that independently checks and
  signs or proves candidates.
- **Relayer:** any party that submits a completed candidate to Ethereum.
- **Follower:** a client that derives Rollup0 from canonical Ethereum.
- **Live block:** an ordinary Rollup0 block in a nominal interval.
- **Sync block:** the final Rollup0 position in an interval and the only block that carries an
  inbound system transaction.
- **Settled cursor:** the exact Rollup0 parent identity established by canonical Ethereum history.
- **Sibling:** one of several candidates built from the same settled parent.
- **Applicable:** valid and based on the current settled cursor when evaluated on Ethereum.
- **Stale:** based on a cursor that an earlier applicable candidate has superseded.

---

*Next: [Appendix B, Gas and Cost Model](B-gas-cost-analysis.md).*
