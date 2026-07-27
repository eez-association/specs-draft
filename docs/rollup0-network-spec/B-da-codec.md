# Appendix B. DA Codec and Vectors

This appendix is normative for Rollup0 v0 and is outside the reusable EEZ binding.

## B.1 Grammar

```text
payload := 0x00 || rlp([blockTxCounts, transactions, l2_entries])
```

The strict decoding and semantic rules are in §4.1. In summary:

- the body is one canonical three-list RLP item with no trailing bytes;
- `blockTxCounts` is nonempty and uses canonical-minimal `uint16` integers;
- `sum(blockTxCounts) == len(transactions)`;
- transaction and entry items are byte strings consumed completely by their layer-specific
  decoder; and
- the final Sync count can be nonzero and counts user transactions only.

## B.2 Outer-codec vector

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

payload length      = 136 bytes
keccak256(payload)  = 0x2e6652704d2b1093b46c9e5029e0ecbc540c491e87ca4eeb9de5321267dc1504
```

The count list is `c2 02 01`. The second count belongs to the Sync block and proves that a
conforming outer decoder cannot assume a trailing zero.

This vector reproduces the selected codec's outer RLP shape only. Its transaction byte strings are
truncated samples and its entry is an opaque 32-byte word. A complete Rollup0 decoder MUST reject
these items at the transaction and ABI layers. This vector MUST NOT be used as an accepted
derivation payload.

## B.3 Strict decoder vector

The strict vector contains one ordinary signed type-2 user transaction in the Sync-block
partition, followed by one outbound and one populated inbound derivation entry:

```text
blockTxCounts = [0, 1]

user transaction:
  chainId = 1
  nonce   = 0
  sender  = 0x70997970c51812dc3a010c7d01b50e0d17dc79c8
  length  = 109 bytes
  hash    = 0x4a66440cef6634433ea49dc021463f7c8641172f07eef6c7d82656b4855a9ddd

outbound sidecar entry:
  ABI length     = 736 bytes
  ABI hash       = 0x862afd3d25faa565ccffbb6711982614e6d45dd6dfb82a07e94a62aeb5e8ffdf
  proxyEntryHash = 0x0000000000000000000000000000000000000000000000000000000000000000

inbound sidecar entry:
  ABI length     = 736 bytes
  ABI hash       = 0xcfc659cb45a43048b23db1cb0482c9f0461e5817776e063a7f09839056593776
  proxyEntryHash = 0xafe7b73c7bec87333fb3594b35452a9b143619a285117740a95590d6496e55dc

corresponding on-chain entries:
  anchor ABI hash        = 0x81cebf9728ca3e2018685bb550de57dcef4e6f8c461f2f2d4cc98178375bd55e
  outbound ABI hash      = 0x09ebd1a454f8024f1ce6e9620783a6a98be03684dfbf7f3d7644705b9768e74d
  lean inbound ABI hash  = 0x4bbd9222b8a278e1cb15d98ded88aa37d62193ef1d643aa1efc6698df3df877d
  transientExecutionEntryCount = 2

payload length     = 1601 bytes
keccak256(payload) = 0x179bdc0defb0e2a4979efa52123be6cee63c6b86eefb121ea5bddca974e48e5f
```

The executable fixture verifies canonical outer RLP, complete type-2 decoding, canonical
signature recovery, complete L1 `ExecutionEntry` ABI decoding, both §4.1.2 entry
transformations, the state-delta chain and final root, both ether-delta signs, and the
`type(int256).max` value bound. The complete transaction, sidecar-entry, batch-entry, and payload
bytes are in
[`conformance-vectors.json`](fixtures/conformance-vectors.json).

## B.4 Negative vectors

The outer-codec fixture requires rejection of:

1. empty payload;
2. unknown tag;
3. trailing bytes;
4. a non-list body;
5. wrong top-level arity;
6. empty `blockTxCounts`;
7. count-sum mismatch;
8. a count above `uint16`;
9. a noncanonical integer; and
10. a nested RLP item where a transaction byte string is required.

Run from the repository root:

```console
python3 docs/rollup0-network-spec/fixtures/da-rlp-fixture.py
python3 docs/rollup0-network-spec/fixtures/da-strict-fixture.py
```

The outer codec fixture intentionally treats transaction and entry contents as opaque. The
strict fixture requires rejection of the opaque samples, a missing mandatory sidecar, and an
inbound value above `type(int256).max`.
