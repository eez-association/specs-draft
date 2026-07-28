# 11. Gas, Limits, and Economics

## 11.1 Rollup0 Execution Gas

Rollup0 blocks use a gas limit of `30,000,000`. Transaction gas follows the selected EVM fork.
The base fee follows EIP-1559 and is derived from the parent header.

Ordinary and protocol-derived transactions share this limit. An inbound protocol transaction
encodes the gas remaining when it starts. It has no separate allowance and no smaller
per-transaction cap. Rollup0 charges the active fork's standard non-creation transaction intrinsic
gas over its calldata. Intrinsic and EVM execution gas contribute to its typed receipt and the
block's `gasUsed`.

!!! note "TO BE DEFINED"
    The production EIP-1559 parameters, genesis base fee, fee recipient, and treatment of base and
    priority fees are not yet selected.

Rollup0 has not yet selected whether ordinary transaction fees use the Ethereum base-fee burn and
priority-fee recipient rules or route some fees to deployment-selected vaults.

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

## 11.5 Inbound Transaction Gas and Value

Chapter 3 defines the common gas pool and the protocol credit used for inbound value. Every
composer, validator or prover, and follower must reproduce the same gas use and value movement.

!!! note "TO BE DEFINED"
    Rollup0 must select one of the protocol-transaction fee approaches discussed in Chapter 3. The
    choice must define who pays, which asset is charged, how the amount is calculated, where it
    goes, how refunds work, what `GASPRICE` and `effectiveGasPrice` return, and how inbound value is
    backed by value held on Ethereum.

---

*Next: [Chapter 12, Limitations and Open Issues](12-open-issues.md).*
