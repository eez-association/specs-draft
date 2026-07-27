# Appendix B. Rollup0 DA Codec

This appendix is normative for `rollup0@0.2-draft`. It specifies the Rollup0 outer DA envelope.
It does not duplicate the EEZ ABI. Items inside `l2_entries` MUST use the tuple family selected by
[EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md).

## B.1 Grammar

```text
payload := 0x00 || rlp([blockTxCounts, transactions, l2_entries])
```

- The body is exactly one canonical RLP list with three child lists and no trailing bytes.
- `blockTxCounts` contains one canonical-minimal unsigned integer per L2 block.
- The count list is nonempty.
- Each count is at most `65535`.
- `sum(blockTxCounts) == len(transactions)`.
- Every `transactions` item is one complete supported signed EIP-2718 envelope.
- Every `l2_entries` item is one complete ABI object required for derivation.
- Counts cover transported user transactions only. Reconstructed system transactions are not
  counted.
- The last count belongs to the Sync block and MAY be nonzero.

Tag `0x00` is the only selected channel. `blobIndices` MUST be empty. Unknown tags and nonempty
blob references are invalid.

## B.2 Outer-codec vector

This vector tests the outer RLP grammar only:

```text
blockTxCounts = [2, 1]
transactions  = [
  0x02f8650180808094000000000000000000000000000000000000dead80c0,
  0x02f8650180018094000000000000000000000000000000000000beef80c0,
  0x02f865018002809400000000000000000000000000000000000000cafe80c0
]
l2_entries = [
  0x00000000000000000000000000000000000000000000000000000000deadbeef
]

payload =
0x00f885c20201f85e9e02f8650180808094000000000000000000000000000000000000dead80c09e02f8650180018094000000000000000000000000000000000000beef80c09f02f865018002809400000000000000000000000000000000000000cafe80c0e1a000000000000000000000000000000000000000000000000000000000deadbeef

payload length     = 136 bytes
keccak256(payload) = 0x2e6652704d2b1093b46c9e5029e0ecbc540c491e87ca4eeb9de5321267dc1504
```

The sample transaction and entry bytes are intentionally opaque and incomplete at their inner
layers. A full derivation decoder MUST reject them after the outer-codec test. They are not an
accepted Rollup0 block vector.

## B.3 Rejection cases

A decoder MUST reject:

1. an empty payload;
2. an unknown tag;
3. a missing or trailing body byte;
4. a non-list body or wrong top-level arity;
5. an empty count list;
6. a noncanonical or overflowing count;
7. a count-sum mismatch;
8. a nested RLP value where a byte string is required;
9. a transaction envelope with unconsumed bytes; and
10. an ABI item with unconsumed bytes or the wrong EEZ binding tuple.

Run the independent outer-codec fixture from the repository root:

```console
python3 docs/rollup0-network-spec/fixtures/da-rlp-fixture.py
```

An accepted end-to-end `eez-evm@0.2-draft` Rollup0 payload vector has not yet been published. It is
a release blocker for production client interoperability.
