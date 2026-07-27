#!/usr/bin/env python3
"""Check the Rollup0 tag-0x00 DA conformance vector."""


def encode_length(length: int, offset: int) -> bytes:
    if length < 56:
        return bytes([offset + length])
    encoded = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([offset + 55 + len(encoded)]) + encoded


def encode_bytes(value: bytes) -> bytes:
    if len(value) == 1 and value[0] < 0x80:
        return value
    return encode_length(len(value), 0x80) + value


def encode_list(items: list[bytes]) -> bytes:
    value = b"".join(items)
    return encode_length(len(value), 0xC0) + value


def encode_uint(value: int) -> bytes:
    if value == 0:
        return encode_bytes(b"")
    return encode_bytes(value.to_bytes((value.bit_length() + 7) // 8, "big"))


def decode_item(data: bytes):
    if not data:
        raise ValueError("empty RLP")

    first = data[0]
    if first < 0x80:
        return data[:1], data[1:]
    if first < 0xB8:
        length = first - 0x80
        return data[1:1 + length], data[1 + length:]
    if first < 0xC0:
        length_of_length = first - 0xB7
        length = int.from_bytes(data[1:1 + length_of_length], "big")
        start = 1 + length_of_length
        return data[start:start + length], data[start + length:]
    if first < 0xF8:
        length = first - 0xC0
        return decode_list(data[1:1 + length]), data[1 + length:]

    length_of_length = first - 0xF7
    length = int.from_bytes(data[1:1 + length_of_length], "big")
    start = 1 + length_of_length
    return decode_list(data[start:start + length]), data[start + length:]


def decode_list(data: bytes) -> list:
    items = []
    while data:
        item, data = decode_item(data)
        items.append(item)
    return items


def decode(data: bytes):
    item, rest = decode_item(data)
    if rest:
        raise ValueError("trailing RLP bytes")
    return item


def main() -> None:
    counts = [2, 0]
    transactions = [
        bytes.fromhex("02f8650180808094000000000000000000000000000000000000dead80c0"),
        bytes.fromhex("02f8650180018094000000000000000000000000000000000000beef80c0"),
    ]
    entries = [
        bytes.fromhex(
            "00000000000000000000000000000000000000000000000000000000deadbeef"
        ),
    ]

    inner = encode_list([
        encode_list([encode_uint(value) for value in counts]),
        encode_list([encode_bytes(value) for value in transactions]),
        encode_list([encode_bytes(value) for value in entries]),
    ])
    payload = b"\x00" + inner

    expected = bytes.fromhex(
        "00f865c20280f83e9e02f865018080809400000000000000000000000000000000"
        "0000dead80c09e02f8650180018094000000000000000000000000000000000000"
        "beef80c0e1a000000000000000000000000000000000000000000000000000000"
        "000deadbeef"
    )
    assert payload == expected
    assert len(payload) == 104

    decoded = decode(payload[1:])
    assert len(decoded) == 3
    decoded_counts = [int.from_bytes(value, "big") if value else 0 for value in decoded[0]]
    assert decoded_counts == counts
    assert decoded[1] == transactions
    assert decoded[2] == entries
    assert sum(decoded_counts) == len(transactions)
    assert decoded_counts[-1] == 0

    print("Rollup0 DA vector: OK")
    print("payload: 0x" + payload.hex())


if __name__ == "__main__":
    main()
