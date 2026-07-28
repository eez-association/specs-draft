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
| EVM fork | TO BE DEFINED; no earlier than Cancun |
| Settlement transaction gas budget | `4,000,000` |
| Inbound system-call gas budget | approximately `2,000,000` |
| DA channel | Ethereum blobs |
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

The production genesis must bind exact bytecode and exact system-call behavior.

## A.4 Provisional Deployment Values

The restored draft uses these development defaults. Production must either confirm or replace them:

| Item | Development default |
|---|---|
| EIP-1559 elasticity multiplier | `6` |
| EIP-1559 base-fee-change denominator | `250` |
| Maximum validator/prover set size | `M <= 20` |
| Example threshold | `ceil(2M / 3) + 1` |

!!! note "TO BE DEFINED"
    The Rollup0 chain ID, initial EVM fork, genesis base fee, system caller, fee-vault addresses,
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
  contains a pure-L2 transaction prefix followed by zero or more synchronous actions.
- **Settled cursor:** the exact Rollup0 parent identity established by canonical Ethereum history.
- **Sibling:** one of several candidates built from the same settled parent.
- **Applicable:** valid and based on the current settled cursor when evaluated on Ethereum.
- **Stale:** based on a cursor that an earlier applicable candidate has superseded.

---

*Next: [Appendix B, Gas and Cost Model](B-gas-cost-analysis.md).*
