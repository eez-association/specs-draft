# 11. Gas, Limits, and Economics

## 11.1 Rollup0 Execution Gas

Rollup0 blocks use a gas limit of `30,000,000`. Transaction gas follows the selected EVM fork.
The base fee follows EIP-1559 and is derived from the parent header.

!!! note "TO BE DEFINED"
    The production EIP-1559 parameters, genesis base fee, fee recipient, and treatment of base and
    priority fees are not yet selected.

The draft budgets approximately `2,000,000` Rollup0 gas for an inbound system call.

Rollup0 routes fees to deployment-selected fee-vault recipients rather than requiring the
Ethereum-style base-fee burn. The exact vaults remain deployment parameters.

## 11.2 Composer Costs

A composer can pay for:

- Rollup0 execution;
- validation or proving;
- blob publication;
- the Ethereum settlement transaction;
- the trigger transaction or bundle inclusion; and
- retries for a candidate that loses or is not included.

Rollup0 does not currently guarantee reimbursement. Open composition therefore does not imply that
candidate production is profitable.

## 11.3 Data Availability Cost

Rollup0 publishes anchored chain data in Ethereum blobs. Cost follows Ethereum blob-gas pricing and
the number of blobs used by a candidate.

The production design must select:

- a maximum payload size;
- a maximum user-transaction count;
- a maximum candidate range;
- who pays the DA cost; and
- whether Rollup0 charges users an explicit Ethereum-data fee.

!!! note "TO BE DEFINED"
    The exact blob capacity and fee-allocation rules are not yet selected.

## 11.4 Settlement and Bundle Limits

The settlement transaction, trigger, and all other transactions in their Ethereum block must fit
within the Ethereum block gas limit. The candidate must also fit the limits of its selected proof
system and inclusion mechanism.

The draft budgets `4,000,000` Ethereum gas for `postAndVerifyBatch`. The maximum bundle capacity
still depends on the final batch shape, proof threshold, trigger, and Ethereum block gas headroom.

## 11.5 System-Call Gas and Value

The Sync system call requires an exact gas limit, fee rule, authorization rule, and value
source. These values must be deterministic and available to every composer and follower.

!!! note "TO BE DEFINED"
    Rollup0 must define separate gas accounting and receipt or log behavior for its EIP-4788-style
    system calls. It must also define how value supplied by a system call on Rollup0 is backed by
    value held on Ethereum.

---

*Next: [Chapter 12, Limitations and Open Issues](12-open-issues.md).*
