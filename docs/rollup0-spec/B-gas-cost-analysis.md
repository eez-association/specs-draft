# Appendix B. Gas and Cost Model

This appendix is informative. It defines no gas constant beyond the Rollup0 block gas limit in
Chapter 11.

## B.1 Candidate Cost

A candidate's direct cost is approximately:

```text
Rollup0 execution
+ proof or validation
+ Ethereum blobs
+ Ethereum settlement execution
+ ordered bundle inclusion
+ expected retry cost
```

Open composition exposes each composer to losing-sibling risk. A composer can pay validation and
submission costs even when another valid candidate settles first.

## B.2 Data Availability

For a candidate using `n` blobs, the DA cost is determined by the Ethereum blob base fee and the
blob gas charged per blob:

```text
DA_cost = n * blob_gas_per_blob * blob_base_fee
```

The exact monetary cost also depends on settlement execution gas and any inclusion payment.

## B.3 Settlement Scaling

Settlement cost grows with:

- encoded EEZ batch size;
- number of execution entries and lookups;
- validator/prover threshold and proof-system verification cost;
- state reads and writes;
- trigger execution; and
- bundle inclusion overhead.

Production capacity limits require measurements against the final contracts, proof policy, and
protocol-transaction format. This draft does not provide measured limits.

---

*Next: [Appendix C, Open Questions](C-open-questions.md).*
