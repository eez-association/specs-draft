# 7. Gas, Limits, and Economics

## 7.1 L2 Execution Fees

Rollup0 uses ordinary EVM transaction admission, execution, refunds, receipts, and EIP-1559
accounting under its activated fork schedule.

The draft fixes a `30_000_000` block gas limit and a zero fee recipient. The active production fork
schedule, genesis base fee, native asset, funding policy, and complete fee-market activation are
release blockers. Values in the current development genesis are not production selections.

No L1-data surcharge, fee oracle, fee vault, or sequencer reimbursement is defined in
`rollup0@0.2-draft`.

## 7.2 System Transaction Fees

System transactions consume the same block gas budget and obey the same base-fee validity rule as
user transactions. Their nonce, gas limit, gas price or fee caps, sender authorization, value
source, and signing or protocol envelope MUST be fixed by the activated profile.

The current implementation-development mode uses signed legacy transactions with:

```text
gasLimit = 2_000_000
gasPrice = 1_000_000_000 wei
```

Those constants and the public development key are not production rules. Production system
authorization and gas policy are release blockers.

After admission, a reverting system call remains a valid failed transaction: it consumes its
nonce and gas, and its call effects and value transfer revert.

## 7.3 Limits

The following limits are fixed in this draft unless an activated revision replaces them:

| Item | Limit |
|---|---:|
| L2 block gas | `30_000_000` |
| Production L2 interval | `2_000 ms` |
| Production blocks per nominal Ethereum interval | `6` |

The maximum user transactions per settlement bundle, proof budget, submission slack, system
transaction gas policy, calldata capacity, and relay-specific limits are unresolved production
parameters.

A client MUST fail when checked arithmetic overflows or when a block, transaction, DA payload, or
settlement bundle exceeds an activated limit. It MUST NOT silently truncate, split, or defer a
consensus object.

## 7.4 Settlement Cost

Candidate submitters pay Ethereum gas for `postAndVerifyBatch`, proof verification, calldata, and
any companion transactions required by the selected settlement construction. Rollup0 does not
define reimbursement or guaranteed profitability.

Open candidate admission does not make settlement submission free. Any account
or contract may relay an already validated candidate. A production deployment
MUST still specify how fees are paid, how front-running and replay are
prevented, and what atomic-inclusion mechanism is used. Those choices are
release blockers.

Appendix A gives planning formulas only. Gas schedules, calldata prices, proof-system membership,
and builder terms are deployment inputs, not consensus constants.

---

*Next: [§8 Limitations and Release Blockers](08-limitations.md).*
