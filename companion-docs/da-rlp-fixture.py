#!/usr/bin/env python3
"""
DA tag-0x00 payload RLP round-trip fixture for Appendix D of the Rollup0 spec.

CODEC-AUTHORED (not contract-authored): the DA payload codec is an off-chain /
execution-layer artifact. The `sync-rollups-protocol` contracts at commit fe7bf66
do NOT implement this RLP grammar, so these bytes have no on-chain provenance —
they are produced here by a self-contained canonical-minimal RLP encoder as a
reference fixture for the grammar specified in D.7.

Grammar:  payload := 0x00 || rlp([ blockTxCounts, transactions, l2_entries ])
  - blockTxCounts : list of canonical-minimal RLP integers (one per L2 block in
                    (fromBlock, toBlock]); uint16-valued.
  - transactions  : list of byte strings (flat, block-major, EIP-2718 user txs).
  - l2_entries    : list of byte strings (ABI-encoded L2 ExecutionEntry blobs).
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
    assert rest == b"", "trailing bytes after RLP item"
    return item


def _rlp_decode_item(data: bytes):
    if len(data) == 0:
        raise ValueError("empty")
    b0 = data[0]
    if b0 < 0x80:
        return data[0:1], data[1:]
    if b0 < 0xB8:
        l = b0 - 0x80
        return data[1:1 + l], data[1 + l:]
    if b0 < 0xC0:
        ll = b0 - 0xB7
        l = int.from_bytes(data[1:1 + ll], "big")
        s = 1 + ll
        return data[s:s + l], data[s + l:]
    if b0 < 0xF8:
        l = b0 - 0xC0
        return _rlp_decode_list(data[1:1 + l]), data[1 + l:]
    ll = b0 - 0xF7
    l = int.from_bytes(data[1:1 + ll], "big")
    s = 1 + ll
    return _rlp_decode_list(data[s:s + l]), data[s + l:]


def _rlp_decode_list(data: bytes):
    items = []
    while data:
        item, data = _rlp_decode_item(data)
        items.append(item)
    return items


def main():
    # --- Sample batch: (fromBlock, toBlock] spans 2 L2 blocks ---
    # block fromBlock+1 : 2 user txs
    # block fromBlock+2 (the Sync block, toBlock) : 0 user txs (trailing 0)
    block_tx_counts = [2, 0]

    # flat, block-major list of EIP-2718 signed user txs (sample raw bytes)
    transactions = [
        bytes.fromhex("02f8650180808094000000000000000000000000000000000000dead80c0"),
        bytes.fromhex("02f8650180018094000000000000000000000000000000000000beef80c0"),
    ]

    # one ABI-encoded L2-shape ExecutionEntry blob (sample raw bytes)
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

    print("block_tx_counts      =", block_tx_counts, "(2 blocks; Sync block trailing 0)")
    print("transactions (count) =", len(transactions))
    print("l2_entries  (count)  =", len(l2_entries))
    print("rlp([...]) inner     = 0x" + inner.hex())
    print("payload (0x00||rlp)  = 0x" + payload.hex())
    print("payload length       =", len(payload), "bytes")

    # --- Round-trip: decode and re-check invariants ---
    assert payload[0] == 0x00, "tag byte not 0x00"
    decoded = rlp_decode(payload[1:])
    assert len(decoded) == 3, "top list must be [counts, txs, entries]"
    d_counts = [int.from_bytes(c, "big") if c else 0 for c in decoded[0]]
    d_txs = decoded[1]
    d_entries = decoded[2]
    assert d_counts == block_tx_counts, (d_counts, block_tx_counts)
    assert d_txs == transactions
    assert d_entries == l2_entries
    assert sum(d_counts) == len(d_txs)
    print("round-trip decode    = OK (counts/txs/entries match, sum(counts)==txcount)")


if __name__ == "__main__":
    main()
