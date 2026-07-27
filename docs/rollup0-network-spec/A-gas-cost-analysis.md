# Appendix A. Settlement Cost Model

This appendix is informative. It gives a planning model and selects no production parameters.

For one Rollup0 candidate, let:

```text
G_total =
    G_intrinsic
  + G_calldata
  + G_EEZ
  + G_proofs
  + G_companions
```

`G_calldata` depends on the exact tag-`0x00` payload bytes and Ethereum calldata pricing.
`G_EEZ` depends on entry and lookup counts, storage state, immediate versus queued processing, and
logs. `G_proofs` depends on the activated proof systems and threshold. `G_companions` depends on
the activated atomic-inclusion design.

For independent ECDSA attestations, verification cost grows approximately linearly with the
required signer count. Aggregate signatures can trade a larger fixed verification cost for a
smaller marginal cost. This qualitative comparison does not select a signature scheme, validator
count, threshold, or gas budget.

A production capacity study MUST measure the exact selected contracts and calldata on the target
Ethereum fork. It MUST include worst-case entry shapes, reverted effects, cold storage access,
proof verification, builder constraints, and fee volatility. Measurements from Chiado or the
historical `5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` binding are not
production constants for `eez-evm@0.2-draft`.

---

*See also [§7 Gas, Limits, and Economics](07-gas-economics.md).*
