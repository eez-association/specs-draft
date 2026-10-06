#!/usr/bin/env python3
"""Check published EEZ vectors 4–6 using Python and Foundry cast; no RPC required.

These vectors cover the bundled EEZ digest, not the unpinned production Core version.
Run: python3 companion-docs/check-wire-vectors.py
"""

from pathlib import Path
import re
import subprocess


def cast(*args):
    return subprocess.check_output(["cast", *args], text=True).strip().lower()


def word(value):
    return "0x" + value.to_bytes(32, "big").hex()


def result(section, label):
    return re.search(re.escape(label) + r"\s*=\s*(0x[0-9a-f]+)", section)[1]


def main():
    root = Path(__file__).resolve().parents[1]
    doc = (root / "docs/eez-protocol-spec/05-wire-formats.md").read_text()
    vectors = re.split(r"### Vector \d+:", doc)
    section = vectors[4]
    printed = re.search(r"abi.encode\(entry\) =\s*0x([0-9a-f\s]+)\n\nentryHash", section)[1]
    printed = "0x" + "".join(printed.split())
    call_hash = result(vectors[1], "crossChainCallHash")
    rolling_hash = result(vectors[3], "after CALL_END(1,true,0x01)")
    entry_type = (
        "((uint256,bytes32,bytes32,int256)[],bytes32,uint256,"
        "(address,uint256,bytes,address,uint256,uint256)[],"
        "(bytes32,uint256,bytes)[],uint256,bytes,bytes32)"
    )
    entry = (
        f"([(1,{word(0xaa)},{word(0xbb)},0)],{call_hash},1,"
        "[(0x00000000000000000000000000000000deadbeef,0,0xdeadbeef,"
        "0x0000000000000000000000000000000000c0ffee,0,0)],"
        f"[],1,0x,{rolling_hash})"
    )
    encoded = cast("abi-encode", f"f({entry_type})", entry)
    assert printed == encoded, "Vector 4 entry bytes differ from its ABI tuple"
    entry_hash = cast("keccak", printed)
    assert entry_hash == result(section, "entryHash"), "Vector 4 entry hash mismatch"

    empty = cast("abi-encode", "f(bytes32[])", "[]")
    assert empty == "0x" + word(32)[2:] + word(0)[2:]
    arrays = cast("abi-encode", "f(bytes32[])", f"[{entry_hash}]") + empty[2:] * 2
    shared = cast("keccak", arrays + cast("keccak", "0x")[2:] + word(0)[2:])
    assert shared == result(vectors[5], "sharedPublicInput"), "Vector 5 shared hash mismatch"
    assert shared == result(vectors[6], "sharedPublicInput"), "Vector 6 shared hash mismatch"

    for number, proof_index, members in (
        (5, 0, [(1, 0x100)]),
        (6, 0, [(1, 0x100)]),
        (6, 1, [(1, 0x101), (2, 0x201)]),
    ):
        accumulator = word(0)
        for rollup, key in members:
            accumulator = cast("keccak", cast(
                "abi-encode", "f(bytes32,uint256,bytes32,bytes32,uint256)",
                accumulator, str(rollup), word(key), word(0), "0",
            ))
        label = "acc" if number == 5 else f"acc(PS{proof_index})"
        assert accumulator == result(vectors[number], label), f"Vector {number} fold mismatch"
        digest = cast("keccak", shared + accumulator[2:])
        assert digest == result(vectors[number], f"publicInputsHash[{proof_index}]")
    print("PASS: EEZ vectors 4–6 (entry ABI, entry hash, shared input, proof-system folds)")


if __name__ == "__main__":
    main()
