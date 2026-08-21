# Appendix B. Gas and Cost Model

This appendix explains the gas rules in Chapter 11 and the reasoning behind them.

## B.1 Base-Fee Parameters

Rollup0 uses a `30,000,000` gas limit, an EIP-1559 elasticity multiplier of `2`, and a
base-fee-change denominator of `50`.

This gives Rollup0:

| Measure | Value |
|---|---:|
| Target gas per 2-second block | `15,000,000` |
| Maximum gas per 2-second block | `30,000,000` |
| Target gas per 12 seconds | `90,000,000` |
| Maximum gas per 12 seconds | `180,000,000` |
| Full-block base-fee increase | approximately `2%` per block |
| Empty-block base-fee decrease | `2%` per block, before integer rounding |

The elasticity multiplier controls burst capacity. A value of `2` lets one block use twice the
sustained target. It avoids treating a much larger burst allowance as normal capacity.

The denominator controls how quickly the base fee changes. Ethereum uses elasticity `2` and
denominator `8`, which changes the base fee by up to `12.5%` once per 12-second block. Applying
those parameters to Rollup0's 2-second blocks would allow six such changes in the same time. Six
consecutive full Rollup0 blocks would raise the fee by about `102.7%`.

For parent base fee `f`, a full or empty Rollup0 block applies the EIP-1559 integer rules:

```text
full:  f_next = f + max(floor(f / 50), 1)
empty: f_next = f - floor(f / 50)
```

Ignoring integer rounding, a full block therefore raises the fee by `2%`. Six consecutive full
blocks raise it by about `12.6%`, close to Ethereum's `12.5%` change over one full 12-second block.
Six empty Rollup0 blocks lower it by about `11.4%`. The percentages and chart are explanatory
real-number approximations; block validation uses the active fork's exact integer calculation.

The earlier `6/250` proposal also raises the fee by `2%` when a `30,000,000` gas block is full.
However, it sets the target to only `5,000,000` gas per block and lowers the fee by only `0.4%`
after an empty block. It therefore combines a six-times burst allowance with much slower fee
decay. Rollup0 instead uses `2/50` to keep the same full-block response while setting a
`15,000,000` gas target and a two-times burst allowance.

[![Comparison of Rollup0 EIP-1559 parameter choices](../assets/rollup0-base-fee-comparison.svg)](../assets/rollup0-base-fee-comparison.svg)

The left chart shows the next-block base-fee change at different gas use. The right chart shows
the cumulative increase during twelve seconds of full blocks. The `6/250` curve is omitted from
the right chart because it exactly overlaps `2/50`: both increase by `2%` at the `30,000,000` gas
ceiling. The left chart shows their different targets and behavior below that ceiling.

These parameters do not prove that `90,000,000` target gas per 12 seconds is operationally safe.
The deployment still needs load, execution, proving, and data-availability tests. The fixed
`30,000,000` per-block limit bounds a single two-second burst while those measurements are made.

## B.2 Candidate Participant Costs

A candidate can create the following costs across different participants:

```text
composer             = construction + Rollup0 execution + expected retry cost
validators/provers   = validation + signing or proving
blob sender          = Ethereum blob gas + settlement-transaction execution
trigger senders      = their Ethereum transaction execution
private participants = any builder, relayer, or bundle-inclusion payments
```

Open composition exposes candidate participants to losing-sibling risk. Composers can lose their
construction and retry costs, validators or provers can spend resources on an unselected sibling,
and a relayer can incur submission costs even when another valid candidate settles first. Rollup0
does not reimburse these costs at protocol level and does not assign every cost to one party.
Private arrangements may redistribute them.

A planned permissioned Gnosis sister network, separate from Rollup0, may fund its
sequencer/composer and require that operator to use a Gnosis-designated block beneficiary.
Ordinary priority-fee revenue from its blocks can offset that funding, but Rollup0 neither encodes
this arrangement nor guarantees that the revenue covers the costs. On Rollup0 itself, an
independent composer remains free to choose its block beneficiary.

## B.3 Data Availability

For a candidate using `b` blobs, the DA fee paid by the blob-transaction sender is determined by
the containing Ethereum fork's blob gas per blob and that block's blob base fee:

```text
DA_fee = b * blob_gas_per_blob * blob_base_fee
```

Settlement-transaction execution fees and private inclusion payments are additional publication
costs; they are not part of `DA_fee`.

## B.4 Settlement and Bundle Scaling

The settlement transaction's gas use grows with:

- encoded EEZ batch size;
- number of execution entries and lookups;
- validator/prover threshold and proof-system verification cost;
- state reads and writes; and
- settlement-wrapper and manager checks.

The complete bundle's Ethereum block footprint additionally includes each selected trigger's gas
and transaction bytes. Private builder or relayer payments affect monetary inclusion cost but do
not themselves add a Rollup0 consensus gas budget.

Production capacity limits require measurements against the final contracts, proof policy, and
protocol-transaction format. This draft does not provide measured limits. Rollup0 imposes no
smaller settlement-transaction budget: the active Ethereum per-transaction cap and the gas
remaining in the block are the validity limits.

---

*Next: [Appendix C, Open Questions](C-open-questions.md).*
