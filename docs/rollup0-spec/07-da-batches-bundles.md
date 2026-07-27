# 7. Data Availability, Batches, and Ethereum Bundles

## 7.1 Rollup0 DA Payload

Rollup0 publishes one calldata payload:

```text
payload = 0x00 || rlp([blockTxCounts, transactions, l2Entries])
```

| Field | Meaning |
|---|---|
| `blockTxCounts` | one canonical unsigned `uint16` count per Rollup0 block |
| `transactions` | complete signed EIP-2718 user transactions in block-major order |
| `l2Entries` | complete EEZ L2 execution objects needed to reconstruct system transactions |

`blockTxCounts` partitions `transactions`. Its checked sum MUST equal
`len(transactions)`. The final count belongs to the Sync block and MUST be zero. System
transactions are reconstructed and are not included in `transactions`.

`l2Entries` is empty when the candidate needs no L2 execution object.

The byte-exact grammar and conformance vector are in [Appendix D](D-wire-formats.md). The inner EEZ
objects use the ABI defined by [EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md).

This draft selects calldata only. Any EEZ batch field that selects blobs MUST be empty.

## 7.2 Range Correspondence

Let `fromBlock` be the candidate's named settled parent and `toBlock` its terminal Sync block.
The payload covers exactly:

```text
(fromBlock, toBlock]
```

The payload does not encode `fromBlock` or `toBlock`. They are bound by candidate validation
against the current Ethereum-confirmed Rollup0 head and the executed Sync endpoint.

The following must agree:

- `len(blockTxCounts) = toBlock.number - fromBlock.number`;
- the first count belongs to `fromBlock.number + 1`;
- the last count belongs to `toBlock.number`;
- `toBlock` is a Sync block;
- every user transaction appears once in its selected block;
- every required L2 entry corresponds to the exact accepted EEZ action; and
- replay from `fromBlock` produces `toBlock`.

The maximum range and payload size remain open production parameters.

## 7.3 EEZ Batch

The settlement transaction carries the batch object defined by
[EEZ Proving and Settlement](../eez-protocol-spec/04-proving-and-settlement.md).
Rollup0 requires:

- the tag-`0x00` payload in the batch calldata field;
- no blob indices;
- proof context bound to the intended Ethereum settlement domain;
- Rollup0 state deltas derived from the exact executed range;
- enough L2 entries to reconstruct every system transaction; and
- the proof or signatures required by Chapter 8.

Rollup0 does not redefine the EEZ batch tuple or public-input hash.

## 7.4 Ethereum Bundle

An interaction candidate uses this exact order:

```text
bundle = [postAndVerifyBatch, trigger]
```

`postAndVerifyBatch` publishes and verifies the candidate. `trigger` is the exact Ethereum
transaction whose cross-chain proxy call consumes the prepared EEZ action.

Both transactions MUST be included in this order in one Ethereum block, or neither transaction may
be included. `trigger` MUST immediately follow `postAndVerifyBatch` in Ethereum transaction order.
Public-mempool submission alone does not guarantee this property.

The builder or inclusion mechanism that provides this guarantee, its fee policy, and its failure
behavior are not yet selected. Candidate relay remains permissionless.

## 7.5 Canonical Evidence

A follower uses canonical Ethereum transaction and receipt order. It verifies:

- the exact settlement transaction and trigger;
- successful settlement execution;
- logs from the selected EEZ deployment only;
- the Rollup0 ID;
- the accepted EEZ effect and endpoint; and
- the candidate's position relative to competing candidates.

An event name or matching state-root value by itself is not settlement evidence.

---

*Next: [Chapter 8, Proving and Settlement](08-proving-settlement.md).*
