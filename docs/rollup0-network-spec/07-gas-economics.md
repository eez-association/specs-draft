# 7. Gas, Limits, and Economics

## 7.1 L2 block gas

`rollup0-v0` fixes the block gas limit at `30_000_000`. Every user and system transaction consumes
that same block budget. The active EVM fork schedule, transaction validity rules, intrinsic gas,
refunds, receipts, and cumulative gas are ordinary Ethereum execution rules unless this profile
overrides them explicitly.

The development genesis in Appendix D activates forks through Osaka from genesis. That
development artifact is reproducible, but it does not activate a production network.

## 7.2 Base fee and fee recipient

Every block contains `baseFeePerGas`, derived from its parent by the integer operation order in
§2.6. Rollup0 v0 fixes:

```text
elasticity multiplier       = 2
base-fee change denominator = 8
genesis base fee            = 1_000_000_000 wei
```

These are protocol values, not client defaults or unresolved production parameters. A different
value requires a new activated profile.

Every v0 header fixes the beneficiary to the zero address. The base-fee portion is burned.
Priority fees are credited to the zero beneficiary and are economically inaccessible. No fee
vault, fee oracle, L1-data surcharge, or L1-cost debit is part of the v0 state transition.
Changing the beneficiary or fee mechanism is consensus-affecting and requires a new activated
protocol version.

## 7.3 System-transaction gas

Every outbound-load and inbound-delivery transaction in Appendix C is a legacy transaction with:

```
gasLimit = 2_000_000
gasPrice = 1_000_000_000 wei
```

It is admissible only when the fixed gas price covers the block base fee and the full gas limit
fits the block's remaining gas. Before admission, `SYSTEM_ADDRESS` MUST cover:

```
maximum_upfront_cost = value + gasLimit * gasPrice
```

Unused gas is refunded. A successful transaction using `g` gas decreases the sender balance by
`value + g * gasPrice`; an outbound load has `value = 0`. For a status-`0` execution, call value
and call-state effects revert, but the nonce increment and gas charge remain. System receipts and
gas contribute normally to `receiptsRoot`, `logsBloom`, and header `gasUsed`.

The fixed gas price means a sufficiently high base fee can halt cross-chain delivery even when the
account is funded. Changing either system gas constant changes the signed envelope and requires a
protocol activation.

## 7.4 Host settlement and DA cost

The operator pays Chiado gas for `postAndVerifyBatch` and at most three appended source
transactions. It also pays for the tag-`0x00` calldata payload. Rollup0 v0 defines neither a
reimbursement transfer nor an L2 data-fee vault. Capacity is bounded by Chiado block gas, relay
constraints, proof verification, and the fixed L2 block gas limit. Appendix A records measured
cost inputs; they are operational observations, not consensus constants.

## 7.5 Reserve and backing blocker

The system account is prefunded; no system transaction mints L2 value. Production MUST pin the
initial reserve, custody/backing relationship, allowed top-up procedure, and monitoring threshold.
The operator's Chiado funding policy and economic sustainability also remain deployment
requirements. These unresolved funding and custody choices do not make the fee-market constants
above variable. The development allocation and public test key do not satisfy the production
requirement.

---

*Next: [§8 Open Issues and Limitations](08-limitations.md).*
