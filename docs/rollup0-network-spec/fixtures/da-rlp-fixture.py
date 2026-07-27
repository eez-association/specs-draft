#!/usr/bin/env python3
"""
DA tag-0x00 outer-RLP round-trip fixture for Rollup0 Appendix B.

The DA payload codec is a Rollup0 execution-network rule, not an EEZ contract
ABI. These bytes are produced by a self-contained canonical-minimal RLP encoder
as a cross-language fixture for the outer codec only.

Grammar:  payload := 0x00 || rlp([ blockTxCounts, transactions, l2_entries ])
  - blockTxCounts : list of canonical-minimal RLP integers (one per L2 block in
                    the non-empty cursor-derived inclusive range); uint16-valued.
  - transactions  : list of byte strings (flat, block-major, EIP-2718 user txs).
  - l2_entries    : list of byte strings (ABI-encoded derivation-entry blobs).

This fixture owns the RLP layer only. It checks strict/canonical RLP, shape,
integer range, and count cardinality. Transaction-envelope and ABI-entry
validity are execution/derivation-layer checks.
"""


def rlp_encode_length(length, offset):
    if length < 56:
        return bytes([offset + length])
    else:
        len_bytes = length.to_bytes((length.bit_length() + 7) // 8, "big")
        return bytes([offset + 55 + len(len_bytes)]) + len_bytes


def rlp_encode_bytes(b: bytes) -> bytes:
    # Single byte in [0x00, 0x7f] encodes as itself.
    if len(b) == 1 and b[0] < 0x80:
        return b
    return rlp_encode_length(len(b), 0x80) + b


def rlp_encode_list(items) -> bytes:
    out = b"".join(items)
    return rlp_encode_length(len(out), 0xC0) + out


def rlp_encode_uint(n: int) -> bytes:
    # Canonical minimal big-endian integer; 0 encodes as the empty string (0x80).
    if n == 0:
        return rlp_encode_bytes(b"")
    return rlp_encode_bytes(n.to_bytes((n.bit_length() + 7) // 8, "big"))


def rlp_decode(data: bytes):
    item, rest = _rlp_decode_item(data)
    if rest:
        raise ValueError("trailing bytes after RLP item")
    return item


def _rlp_decode_item(data: bytes):
    if not data:
        raise ValueError("truncated RLP item")

    b0 = data[0]
    if b0 < 0x80:
        return data[0:1], data[1:]

    if b0 < 0xB8:
        length = b0 - 0x80
        end = 1 + length
        if len(data) < end:
            raise ValueError("truncated short RLP string")
        value = data[1:end]
        if length == 1 and value[0] < 0x80:
            raise ValueError("non-canonical single-byte RLP string")
        return value, data[end:]

    if b0 < 0xC0:
        length, start = _rlp_decode_long_length(data, b0 - 0xB7, "string")
        end = start + length
        if len(data) < end:
            raise ValueError("truncated long RLP string")
        return data[start:end], data[end:]

    if b0 < 0xF8:
        length = b0 - 0xC0
        end = 1 + length
        if len(data) < end:
            raise ValueError("truncated short RLP list")
        return _rlp_decode_list(data[1:end]), data[end:]

    length, start = _rlp_decode_long_length(data, b0 - 0xF7, "list")
    end = start + length
    if len(data) < end:
        raise ValueError("truncated long RLP list")
    return _rlp_decode_list(data[start:end]), data[end:]


def _rlp_decode_long_length(data: bytes, length_of_length: int, kind: str):
    start = 1 + length_of_length
    if len(data) < start:
        raise ValueError(f"truncated RLP {kind} length")
    length_bytes = data[1:start]
    if length_bytes[0] == 0:
        raise ValueError(f"non-canonical RLP {kind} length")
    length = int.from_bytes(length_bytes, "big")
    if length < 56:
        raise ValueError(f"non-canonical long RLP {kind}")
    return length, start


def _rlp_decode_list(data: bytes):
    items = []
    while data:
        item, data = _rlp_decode_item(data)
        items.append(item)
    return items


def rlp_decode_uint16(raw) -> int:
    if not isinstance(raw, bytes):
        raise ValueError("block count must be an RLP byte string")
    if raw == b"":
        return 0
    if raw[0] == 0:
        raise ValueError("non-canonical RLP integer")
    value = int.from_bytes(raw, "big")
    if value > 0xFFFF:
        raise ValueError("block count exceeds uint16")
    return value


def decode_payload(payload: bytes):
    if not payload:
        raise ValueError("empty payload")
    if payload[0] != 0x00:
        raise ValueError("unsupported payload tag")

    decoded = rlp_decode(payload[1:])
    if not isinstance(decoded, list) or len(decoded) != 3:
        raise ValueError("body must be a three-element RLP list")
    counts_raw, transactions, l2_entries = decoded
    if not all(isinstance(field, list) for field in decoded):
        raise ValueError("all three body fields must be RLP lists")
    if not counts_raw:
        raise ValueError("blockTxCounts must be non-empty")
    if not all(isinstance(tx, bytes) for tx in transactions):
        raise ValueError("transactions must contain byte strings")
    if not all(isinstance(entry, bytes) for entry in l2_entries):
        raise ValueError("l2_entries must contain byte strings")

    counts = [rlp_decode_uint16(raw) for raw in counts_raw]
    if sum(counts) != len(transactions):
        raise ValueError("sum(blockTxCounts) does not equal transactions length")
    return counts, transactions, l2_entries


def expect_rejected(name: str, payload: bytes):
    try:
        decode_payload(payload)
    except ValueError:
        return
    raise AssertionError(f"malformed fixture accepted: {name}")


def main():
    assert rlp_encode_uint(0) == b"\x80", "canonical RLP integer zero drift"

    # --- Sample batch spans 2 cursor-derived L2 blocks ---
    # first block: 2 user txs
    # second block (the Sync block): 1 user tx
    block_tx_counts = [2, 1]

    # Flat, block-major opaque transaction bytes. This fixture validates the
    # payload codec only; execution-layer transaction validity is checked later.
    transactions = [
        bytes.fromhex("02f8650180808094000000000000000000000000000000000000dead80c0"),
        bytes.fromhex("02f8650180018094000000000000000000000000000000000000beef80c0"),
        bytes.fromhex("02f865018002809400000000000000000000000000000000000000cafe80c0"),
    ]

    # One opaque derivation-entry byte string. It is deliberately not an ABI
    # conformance vector; decode_payload only owns the outer RLP grammar.
    l2_entries = [
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000deadbeef"),
    ]

    # Decode invariants (MUST):
    assert sum(block_tx_counts) == len(transactions), "sum(counts) != tx count"
    assert all(0 <= c <= 0xFFFF for c in block_tx_counts), "count not uint16"

    inner = rlp_encode_list([
        rlp_encode_list([rlp_encode_uint(c) for c in block_tx_counts]),
        rlp_encode_list([rlp_encode_bytes(tx) for tx in transactions]),
        rlp_encode_list([rlp_encode_bytes(e) for e in l2_entries]),
    ])
    payload = bytes([0x00]) + inner

    expected_payload_hex = (
        "00f885c20201f85e"
        "9e02f8650180808094000000000000000000000000000000000000dead80c0"
        "9e02f8650180018094000000000000000000000000000000000000beef80c0"
        "9f02f865018002809400000000000000000000000000000000000000cafe80c0"
        "e1a000000000000000000000000000000000000000000000000000000000deadbeef"
    )
    assert payload.hex() == expected_payload_hex, "Rollup0 DA vector drift"
    assert len(payload) == 136, "Rollup0 DA vector length drift"

    print("block_tx_counts      =", block_tx_counts, "(2 blocks; Sync block has 1 user tx)")
    print("transactions (count) =", len(transactions))
    print("l2_entries  (count)  =", len(l2_entries))
    print("rlp([...]) inner     = 0x" + inner.hex())
    print("payload (0x00||rlp)  = 0x" + payload.hex())
    print("payload length       =", len(payload), "bytes")

    # --- Round-trip: strict decode and re-check invariants ---
    d_counts, d_txs, d_entries = decode_payload(payload)
    assert d_counts == block_tx_counts, (d_counts, block_tx_counts)
    assert d_txs == transactions
    assert d_entries == l2_entries
    assert sum(d_counts) == len(d_txs)
    print("outer round-trip     = OK (inner transaction/entry bytes remain opaque)")

    # --- Negative conformance cases ---
    empty_lists = bytes.fromhex("00c3c0c0c0")
    mismatch = bytes([0x00]) + rlp_encode_list([
        rlp_encode_list([rlp_encode_uint(1)]),
        rlp_encode_list([]),
        rlp_encode_list([]),
    ])
    overflow = bytes([0x00]) + rlp_encode_list([
        rlp_encode_list([rlp_encode_uint(0x10000)]),
        rlp_encode_list([]),
        rlp_encode_list([]),
    ])
    noncanonical_integer = bytes([0x00]) + rlp_encode_list([
        rlp_encode_list([b"\x00"]),
        rlp_encode_list([]),
        rlp_encode_list([]),
    ])
    nested_transaction = bytes([0x00]) + rlp_encode_list([
        rlp_encode_list([rlp_encode_uint(1)]),
        rlp_encode_list([rlp_encode_list([])]),
        rlp_encode_list([]),
    ])
    malformed = {
        "empty payload": b"",
        "unknown tag": bytes([0x01]) + inner,
        "trailing bytes": payload + b"\x80",
        "body is not a list": bytes.fromhex("0080"),
        "wrong top-level arity": bytes.fromhex("00c2c0c0"),
        "empty blockTxCounts": empty_lists,
        "count-sum mismatch": mismatch,
        "uint16 overflow": overflow,
        "non-canonical integer": noncanonical_integer,
        "nested transaction item": nested_transaction,
    }
    for name, bad_payload in malformed.items():
        expect_rejected(name, bad_payload)
    print("malformed rejection  =", len(malformed), "negative cases OK")


if __name__ == "__main__":
    main()
