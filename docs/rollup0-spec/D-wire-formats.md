# Appendix D. Rollup0 Wire Format and Vector

[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines EEZ ABI tuples, selectors,
hashes, events, proof inputs, and proxy bytecode. This appendix defines only the Rollup0 DA
envelope and the Rollup0 ECDSA proof policy.

## D.1 ECDSA Attestation

Rollup0 realizes an `N`-of-`M` attestation with one independent single-signer ECDSA proof system
per validator/prover.

For proof system `k`:

```text
proofs[k] = r || s || v
message   = publicInputsHash[k]
signer    = ecrecover(message, v, r, s)
```

The proof is exactly 65 bytes:

```text
r: bytes32
s: bytes32, low-s
v: uint8, either 27 or 28
```

The signer signs the raw 32-byte EEZ public-input hash. The signer MUST NOT add an EIP-191
`Ethereum Signed Message` prefix or an EIP-712 domain. Verification succeeds only when the
recovered address equals the signer configured for that proof system.

`proofSystems` is strictly increasing by address and contains one proof per element. Rollup0's
proof-system index list is strictly increasing. The Rollup0 manager accepts only configured proof
systems and rejects a submitted subset with fewer than the selected threshold `N`.

## D.2 DA Grammar

```text
payload = 0x00 || rlp([blockTxCounts, transactions, l2Entries])
```

The top-level RLP item is exactly a three-element list.

| Element | RLP shape | Rule |
|---|---|---|
| `blockTxCounts` | list of byte strings interpreted as unsigned integers | one count per Rollup0 block |
| `transactions` | list of byte strings | complete signed EIP-2718 user transactions in block-major order |
| `l2Entries` | list of byte strings | complete EEZ L2 execution-object encodings |

A decoder MUST enforce:

1. The payload starts with `0x00`.
2. The remaining bytes contain exactly one canonical RLP item and no trailing bytes.
3. The top-level item contains exactly three lists.
4. `blockTxCounts` is nonempty.
5. Each count is a canonical minimal unsigned RLP integer in `[0, 65535]`.
6. The checked sum of all counts equals `len(transactions)`.
7. The last count is zero.
8. Every transaction and L2-entry element is an RLP byte string.

Integer zero is encoded as the RLP empty byte string, `0x80`.

Candidate validation, rather than the outer RLP decoder, MUST then require each transaction byte
string to contain one complete supported signed EIP-2718 envelope. It MUST require each L2-entry
byte string to contain one complete EEZ L2 object, and require the entries to match the candidate's
system transactions in count and order.

## D.3 DA Conformance Vector

The range contains two Rollup0 blocks. The first has two user transactions. The second is the Sync
block and has no user transaction.

```text
blockTxCounts = [2, 0]

transactions = [
  0x02f8650180808094000000000000000000000000000000000000dead80c0,
  0x02f8650180018094000000000000000000000000000000000000beef80c0
]

l2Entries = [
  0x00000000000000000000000000000000000000000000000000000000deadbeef
]
```

Canonical RLP:

```text
0xf865c20280f83e9e02f8650180808094000000000000000000000000000000000000dead80c09e02f8650180018094000000000000000000000000000000000000beef80c0e1a000000000000000000000000000000000000000000000000000000000deadbeef
```

Complete payload:

```text
0x00f865c20280f83e9e02f8650180808094000000000000000000000000000000000000dead80c09e02f8650180018094000000000000000000000000000000000000beef80c0e1a000000000000000000000000000000000000000000000000000000000deadbeef
```

The payload length is 104 bytes. The `c20280` segment encodes the count list `[2, 0]`.

The executable fixture is [`fixtures/da-rlp-fixture.py`](fixtures/da-rlp-fixture.py).

## D.4 Undefined System Envelope

Transaction type `0x7e` is reserved for Rollup0 inbound system transactions. This draft does not
define its byte encoding. No conformance vector exists for that envelope. The encoding is an
explicit production blocker, not an implementation choice.
