#!/usr/bin/env python3
"""Construct and verify a historical Rollup0 development genesis header.

The default input is an implementation-development fixture copied from the
reviewed repository. It is neither normative nor a production profile. The
implementation is dependency-free: it includes
canonical RLP, Keccak-256, and the secure hexary Merkle-Patricia trie used for
Ethereum state and storage roots.

For another network profile, pass its genesis JSON path. The script constructs
the semantic genesis state/header, but only the bundled development profile has
published expected outputs and therefore receives the additional fixture
assertions.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


MASK64 = (1 << 64) - 1
KECCAK_RATE = 136
KECCAK_ROUNDS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)
KECCAK_ROTATION = (
    0,
    1,
    62,
    28,
    27,
    36,
    44,
    6,
    55,
    20,
    3,
    10,
    43,
    25,
    39,
    41,
    45,
    15,
    21,
    8,
    18,
    2,
    61,
    56,
    14,
)

EMPTY_REQUESTS_HASH = hashlib.sha256(b"").digest()
INITIAL_BASE_FEE = 1_000_000_000
EEZL2_ADDRESS = "0x4200000000000000000000000000000000000007"
BRIDGE_RECEIVER_ADDRESS = "0x4200000000000000000000000000000000000008"
HISTORY_STORAGE_ADDRESS = "0x0000f90827f1c53a10cb7a02335b175320002935"
DEV_SYSTEM_ADDRESS = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
DEV_BURN_ADDRESS = "0xdeaddeaddeaddeaddeaddeaddeaddeaddeaddead"

EXPECTED_DEV_FILE_SHA256 = (
    "fb1ca15108f3fa320471d344ac24c55925bd88d2ce57cdbfd2d069ced2e94ef6"
)
EXPECTED_DEV_STATE_ROOT = (
    "d381d828f650845aa890778c74ad2de245f5b3f2a24763f243e19a6bafb4fec5"
)
EXPECTED_DEV_GENESIS_HASH = (
    "cc2334a5f46d86829de4f761b295ee171731bdde1dcb20be6e2ccb6d504a0b56"
)
EXPECTED_DEV_EMPTY_CHILD_STATE_ROOT = (
    "fd75dc8a45e5f8ed14c051b2477fc288c4978a4ac204bf0799da22413ffba3c3"
)
EXPECTED_DEV_EMPTY_CHILD_HASH = (
    "f3dc1444419145cfbf018cccdb7e85fc92db53194e1d20c79420d85683126653"
)
EXPECTED_DEV_HISTORY_STORAGE_ROOT = (
    "c999055097d38a22d00765ecaa6f33abc21adaa90a51bfcc54fccb56ee3c1335"
)
EXPECTED_DEV_CODE = {
    EEZL2_ADDRESS: (
        13_406,
        "b443cc3f745ada484c302b9ba255b44e85bf04b1c14ba486e2498640934fcdb6",
    ),
    BRIDGE_RECEIVER_ADDRESS: (
        64,
        "2867570fb0a81631762d16010f1afeb0dc2aace809800dd110b78c0ad460639a",
    ),
    HISTORY_STORAGE_ADDRESS: (
        83,
        "6e49e66782037c0555897870e29fa5e552daf4719552131a0abce779daec0a5d",
    ),
}
EXPECTED_DEV_EOAS = {
    "0x14dc79964da2c08b23698b3d3cc7ca32193d9955",
    "0x15d34aaf54267db7d7c367839aaf71a00a2c6a65",
    "0x1cbd3b2770909d4e10f157cabc84c7264073c9ec",
    "0x23618e81e3f5cdf7f54c3d65f7fbc0abf5b21e8f",
    "0x2546bcd3c84621e976d8185a91a922ae77ecec30",
    "0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc",
    "0x70997970c51812dc3a010c7d01b50e0d17dc79c8",
    "0x71be63f3384f5fb98995898a86b02fb2426c5788",
    "0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199",
    "0x90f79bf6eb2c4f870365e785982e1f101e93b906",
    "0x976ea74026e726554db657fa54763abd0c3a0aa9",
    "0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc",
    "0xa0ee7a142d267c1f36714e4a8f75612f20a79720",
    "0xbcd4042de499d14e55001ccbb24a551f3b954096",
    "0xbda5747bfd65f08deb54cb465eb87d40e51b197e",
    "0xcd3b766ccdd6ae721141f452c550ca635964ce71",
    "0xdd2fd4581271e230360230f9337d5c0430bf44c0",
    "0xdf3e18d64bc6a983f673ab319ccae4f1a57c7097",
    DEV_SYSTEM_ADDRESS,
    "0xfabb0ac9d68b0b445fb7357272ff202c5651694a",
}
EXPECTED_DEV_CONFIG = {
    "chainId": 1,
    "daoForkSupport": False,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "mergeNetsplitBlock": 0,
    "shanghaiTime": 0,
    "cancunTime": 0,
    "pragueTime": 0,
    "osakaTime": 0,
    "terminalTotalDifficulty": 0,
    "terminalTotalDifficultyPassed": True,
}

DEPLOYMENT_FORK_OVERRIDES = {
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "muirGlacierBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "arrowGlacierBlock": 0,
    "grayGlacierBlock": 0,
    "mergeNetsplitBlock": 0,
    "shanghaiTime": 0,
    "cancunTime": 0,
    "pragueTime": 0,
    "osakaTime": 0,
    "terminalTotalDifficulty": 0,
    "terminalTotalDifficultyPassed": True,
}

EIP1559_ELASTICITY = 2
EIP1559_BASE_FEE_CHANGE_DENOMINATOR = 8
HISTORY_SERVE_WINDOW = 8191


def rotate_left(value: int, count: int) -> int:
    if count == 0:
        return value
    return ((value << count) | (value >> (64 - count))) & MASK64


def keccak_f1600(state: list[int]) -> None:
    for round_constant in KECCAK_ROUNDS:
        columns = [
            state[x]
            ^ state[x + 5]
            ^ state[x + 10]
            ^ state[x + 15]
            ^ state[x + 20]
            for x in range(5)
        ]
        deltas = [
            columns[(x - 1) % 5] ^ rotate_left(columns[(x + 1) % 5], 1)
            for x in range(5)
        ]
        for y in range(5):
            for x in range(5):
                state[x + 5 * y] ^= deltas[x]

        lanes = [0] * 25
        for y in range(5):
            for x in range(5):
                lanes[y + 5 * ((2 * x + 3 * y) % 5)] = rotate_left(
                    state[x + 5 * y], KECCAK_ROTATION[x + 5 * y]
                )

        for y in range(5):
            for x in range(5):
                state[x + 5 * y] = lanes[x + 5 * y] ^ (
                    (~lanes[(x + 1) % 5 + 5 * y])
                    & lanes[(x + 2) % 5 + 5 * y]
                )
                state[x + 5 * y] &= MASK64
        state[0] ^= round_constant


def keccak256(data: bytes) -> bytes:
    """Legacy Keccak-256 (Ethereum), not NIST SHA3-256."""

    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(b"\x00" * ((KECCAK_RATE - len(padded) % KECCAK_RATE) % KECCAK_RATE))
    padded[-1] ^= 0x80

    state = [0] * 25
    for offset in range(0, len(padded), KECCAK_RATE):
        block = padded[offset : offset + KECCAK_RATE]
        for lane in range(KECCAK_RATE // 8):
            state[lane] ^= int.from_bytes(block[lane * 8 : lane * 8 + 8], "little")
        keccak_f1600(state)
    return b"".join(lane.to_bytes(8, "little") for lane in state)[:32]


def rlp_length(length: int, offset: int) -> bytes:
    if length < 56:
        return bytes([offset + length])
    encoded_length = int_bytes(length)
    return bytes([offset + 55 + len(encoded_length)]) + encoded_length


def rlp(value: bytes | list[object]) -> bytes:
    if isinstance(value, bytes):
        if len(value) == 1 and value[0] < 0x80:
            return value
        return rlp_length(len(value), 0x80) + value
    payload = b"".join(rlp(item) for item in value)
    return rlp_length(len(payload), 0xC0) + payload


def int_bytes(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative integer")
    if value == 0:
        return b""
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def quantity(value: str | int | None, default: int | None = None) -> int:
    if value is None:
        if default is None:
            raise ValueError("missing required quantity")
        return default
    if isinstance(value, int):
        return value
    return int(value, 0)


def hex_bytes(value: str, size: int | None = None) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"not a 0x-prefixed byte string: {value!r}")
    raw = bytes.fromhex(value[2:])
    if size is not None and len(raw) != size:
        raise ValueError(f"expected {size} bytes, got {len(raw)}")
    return raw


def nibbles(raw: bytes) -> tuple[int, ...]:
    return tuple(nibble for byte in raw for nibble in (byte >> 4, byte & 0x0F))


def hex_prefix(path: tuple[int, ...], leaf: bool) -> bytes:
    odd = len(path) % 2
    flag = 2 * int(leaf) + odd
    encoded = (flag,) + path if odd else (flag, 0) + path
    return bytes(
        (encoded[index] << 4) | encoded[index + 1]
        for index in range(0, len(encoded), 2)
    )


def common_prefix(items: list[tuple[tuple[int, ...], bytes]]) -> int:
    limit = min(len(path) for path, _ in items)
    first = items[0][0]
    for index in range(limit):
        if any(path[index] != first[index] for path, _ in items[1:]):
            return index
    return limit


def trie_node(items: list[tuple[tuple[int, ...], bytes]]) -> bytes:
    if len(items) == 1:
        path, value = items[0]
        return rlp([hex_prefix(path, True), value])

    prefix_length = common_prefix(items)
    if prefix_length:
        child = trie_node(
            [(path[prefix_length:], value) for path, value in items]
        )
        child_reference = child if len(child) < 32 else keccak256(child)
        return rlp([hex_prefix(items[0][0][:prefix_length], False), child_reference])

    branch: list[object] = []
    for nibble in range(16):
        children = [
            (path[1:], value)
            for path, value in items
            if path and path[0] == nibble
        ]
        if not children:
            branch.append(b"")
            continue
        child = trie_node(children)
        branch.append(child if len(child) < 32 else keccak256(child))
    exact = [value for path, value in items if not path]
    branch.append(exact[0] if exact else b"")
    return rlp(branch)


def secure_trie_root(items: list[tuple[bytes, bytes]]) -> bytes:
    if not items:
        return keccak256(rlp(b""))
    paths = sorted(
        ((nibbles(keccak256(key)), value) for key, value in items),
        key=lambda item: item[0],
    )
    return keccak256(trie_node(paths))


def account_value(account: dict[str, object]) -> bytes:
    storage_items = []
    for key, value in account.get("storage", {}).items():
        storage_value = quantity(value)
        if storage_value == 0:
            continue
        storage_items.append(
            (
                quantity(key).to_bytes(32, "big"),
                rlp(int_bytes(storage_value)),
            )
        )
    storage_root = secure_trie_root(storage_items)
    code = hex_bytes(account.get("code", "0x"))
    return rlp(
        [
            int_bytes(quantity(account.get("nonce"), 0)),
            int_bytes(quantity(account.get("balance"), 0)),
            storage_root,
            keccak256(code),
        ]
    )


def is_active(config: dict[str, object], key: str, genesis_value: int) -> bool:
    activation = config.get(key)
    return activation is not None and quantity(activation) <= genesis_value


def construct_genesis(genesis: dict[str, object]) -> tuple[bytes, bytes, bytes]:
    config = genesis["config"]
    number = quantity(genesis.get("number"), 0)
    timestamp = quantity(genesis["timestamp"])

    london = is_active(config, "londonBlock", number)
    shanghai = is_active(config, "shanghaiTime", timestamp)
    cancun = is_active(config, "cancunTime", timestamp)
    prague = is_active(config, "pragueTime", timestamp)
    if shanghai and not london:
        raise ValueError("Shanghai cannot precede London")
    if cancun and not shanghai:
        raise ValueError("Cancun cannot precede Shanghai")
    if prague and not cancun:
        raise ValueError("Prague cannot precede Cancun")
    if is_active(config, "amsterdamTime", timestamp):
        raise ValueError("Amsterdam header construction is not supported by this fixture")

    accounts = [
        (hex_bytes(address, 20), account_value(account))
        for address, account in genesis["alloc"].items()
    ]
    state_root = secure_trie_root(accounts)
    empty_trie_root = secure_trie_root([])

    header: list[object] = [
        hex_bytes(genesis.get("parentHash", "0x" + "00" * 32), 32),
        keccak256(rlp([])),
        hex_bytes(genesis["coinbase"], 20),
        state_root,
        empty_trie_root,
        empty_trie_root,
        bytes(256),
        int_bytes(quantity(genesis["difficulty"])),
        int_bytes(number),
        int_bytes(quantity(genesis["gasLimit"])),
        b"",  # gasUsed
        int_bytes(timestamp),
        hex_bytes(genesis["extraData"]),
        hex_bytes(genesis["mixHash"], 32),
        quantity(genesis["nonce"]).to_bytes(8, "big"),
    ]
    if london:
        header.append(
            int_bytes(quantity(genesis.get("baseFeePerGas"), INITIAL_BASE_FEE))
        )
    if shanghai:
        header.append(empty_trie_root)
    if cancun:
        header.extend(
            [
                int_bytes(quantity(genesis.get("blobGasUsed"), 0)),
                int_bytes(quantity(genesis.get("excessBlobGas"), 0)),
                bytes(32),
            ]
        )
    if prague:
        header.append(EMPTY_REQUESTS_HASH)

    header_rlp = rlp(header)
    return state_root, header_rlp, keccak256(header_rlp)


def canonical_development_derivative(
    template: dict[str, object],
    timestamp: int,
    chain_id_override: int | None = None,
) -> tuple[dict[str, object], bytes]:
    """Apply the implementation's deployment-time genesis transformation.

    The implementation retains chainId 1. An optional chain-ID override exists
    only to demonstrate that chainId is not part of the genesis header. Both
    forms retain public development keys and are not production genesis files.
    """

    if chain_id_override is not None and chain_id_override <= 0:
        raise ValueError("chain id must be positive")
    if timestamp < 0:
        raise ValueError("timestamp must be non-negative")

    genesis = copy.deepcopy(template)
    if chain_id_override is not None:
        genesis["config"]["chainId"] = chain_id_override
    genesis["config"].update(DEPLOYMENT_FORK_OVERRIDES)
    genesis["timestamp"] = hex(timestamp)
    # This matches scripts/deploy.sh: UTF-8 JSON, indent=2, no terminal LF.
    raw = json.dumps(genesis, indent=2).encode()
    return genesis, raw


def next_base_fee(
    parent_base_fee: int,
    parent_gas_used: int,
    parent_gas_limit: int,
) -> int:
    target = parent_gas_limit // EIP1559_ELASTICITY
    if parent_gas_used == target:
        return parent_base_fee
    if parent_gas_used > target:
        delta = parent_gas_used - target
        change = max(
            parent_base_fee
            * delta
            // target
            // EIP1559_BASE_FEE_CHANGE_DENOMINATOR,
            1,
        )
        return parent_base_fee + change
    delta = target - parent_gas_used
    change = (
        parent_base_fee
        * delta
        // target
        // EIP1559_BASE_FEE_CHANGE_DENOMINATOR
    )
    return parent_base_fee - change


def construct_empty_child(
    genesis: dict[str, object],
    genesis_hash: bytes,
    block_time: int,
) -> tuple[bytes, bytes, bytes, bytes]:
    """Construct the first empty post-genesis block.

    Prague is active in the bundled profile, so EIP-2935 stores the parent
    block hash before transaction execution. This is the only state change in
    the empty-child vector.
    """

    if block_time <= 0:
        raise ValueError("block time must be positive")

    parent_number = quantity(genesis.get("number"), 0)
    parent_timestamp = quantity(genesis["timestamp"])
    child_number = parent_number + 1
    child_timestamp = parent_timestamp + block_time
    config = genesis["config"]

    child_alloc = copy.deepcopy(genesis["alloc"])
    history_storage_root = secure_trie_root([])
    if is_active(config, "pragueTime", child_timestamp):
        history_index = parent_number % HISTORY_SERVE_WINDOW
        history_account = child_alloc[HISTORY_STORAGE_ADDRESS]
        history_account["storage"] = {
            hex(history_index): "0x" + genesis_hash.hex(),
        }
        history_storage_root = secure_trie_root(
            [
                (
                    history_index.to_bytes(32, "big"),
                    rlp(int_bytes(int.from_bytes(genesis_hash, "big"))),
                )
            ]
        )

    accounts = [
        (hex_bytes(address, 20), account_value(account))
        for address, account in child_alloc.items()
    ]
    state_root = secure_trie_root(accounts)
    empty_trie_root = secure_trie_root([])
    parent_gas_limit = quantity(genesis["gasLimit"])
    parent_base_fee = quantity(
        genesis.get("baseFeePerGas"),
        INITIAL_BASE_FEE,
    )

    header: list[object] = [
        genesis_hash,
        keccak256(rlp([])),
        bytes(20),
        state_root,
        empty_trie_root,
        empty_trie_root,
        bytes(256),
        b"",
        int_bytes(child_number),
        int_bytes(parent_gas_limit),
        b"",
        int_bytes(child_timestamp),
        b"",
        bytes(32),
        bytes(8),
    ]
    if is_active(config, "londonBlock", child_number):
        header.append(
            int_bytes(next_base_fee(parent_base_fee, 0, parent_gas_limit))
        )
    if is_active(config, "shanghaiTime", child_timestamp):
        header.append(empty_trie_root)
    if is_active(config, "cancunTime", child_timestamp):
        header.extend([b"", b"", bytes(32)])
    if is_active(config, "pragueTime", child_timestamp):
        header.append(EMPTY_REQUESTS_HASH)

    header_rlp = rlp(header)
    return (
        history_storage_root,
        state_root,
        header_rlp,
        keccak256(header_rlp),
    )


def validate_derivation_vector(
    repository_root: Path,
    template: dict[str, object],
) -> None:
    vector_path = (
        repository_root
        / "docs/rollup0-network-spec/fixtures/genesis-validation-vector.json"
    )
    vector = json.loads(vector_path.read_bytes())
    inputs = vector["deploymentDerivation"]["inputs"]
    derived, raw = canonical_development_derivative(
        template,
        quantity(inputs["timestamp"]),
    )
    state_root, header_rlp, genesis_hash = construct_genesis(derived)
    expected = vector["deploymentDerivation"]["expected"]
    assert hashlib.sha256(raw).hexdigest() == expected["artifactSha256"][2:]
    assert len(raw) == expected["artifactBytes"]
    assert quantity(derived["config"]["chainId"]) == quantity(expected["chainId"])
    assert state_root.hex() == expected["stateRoot"][2:]
    assert genesis_hash.hex() == expected["genesisHash"][2:]
    assert len(header_rlp) == expected["headerRlpLength"]

    override = vector["chainIdOverrideDemonstration"]
    inputs = override["inputs"]
    derived, raw = canonical_development_derivative(
        template,
        quantity(inputs["timestamp"]),
        quantity(inputs["chainId"]),
    )
    state_root, header_rlp, genesis_hash = construct_genesis(derived)
    expected = override["expected"]
    assert hashlib.sha256(raw).hexdigest() == expected["artifactSha256"][2:]
    assert len(raw) == expected["artifactBytes"]
    assert quantity(derived["config"]["chainId"]) == quantity(expected["chainId"])
    assert state_root.hex() == expected["stateRoot"][2:]
    assert genesis_hash.hex() == expected["genesisHash"][2:]
    assert len(header_rlp) == expected["headerRlpLength"]


def validate_development_fixture(
    repository_root: Path,
    path: Path,
    raw: bytes,
    genesis: dict[str, object],
    state_root: bytes,
    genesis_hash: bytes,
) -> None:
    vector = json.loads(
        (
            repository_root
            / "docs/rollup0-network-spec/fixtures/genesis-validation-vector.json"
        ).read_bytes()
    )
    expected_genesis = vector["developmentGenesis"]
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_DEV_FILE_SHA256
    assert expected_genesis["artifactSha256"][2:] == EXPECTED_DEV_FILE_SHA256
    assert len(raw) == expected_genesis["artifactBytes"]
    assert len(genesis["alloc"]) == 24
    assert len(genesis["alloc"]) == expected_genesis["allocationAccounts"]
    assert state_root.hex() == EXPECTED_DEV_STATE_ROOT
    assert expected_genesis["stateRoot"][2:] == EXPECTED_DEV_STATE_ROOT
    assert genesis_hash.hex() == EXPECTED_DEV_GENESIS_HASH
    assert expected_genesis["genesisHash"][2:] == EXPECTED_DEV_GENESIS_HASH
    assert quantity(genesis["config"]["chainId"]) == 1
    assert quantity(expected_genesis["chainId"]) == 1
    assert genesis["config"] == EXPECTED_DEV_CONFIG
    assert quantity(genesis["config"]["pragueTime"]) == 0
    assert quantity(genesis["config"]["osakaTime"]) == 0
    assert set(genesis) == {
        "config",
        "nonce",
        "timestamp",
        "extraData",
        "gasLimit",
        "difficulty",
        "mixHash",
        "coinbase",
        "alloc",
        "number",
        "parentHash",
    }
    assert quantity(genesis["nonce"]) == 0
    assert quantity(genesis["timestamp"]) == 0x6490FDD2
    assert genesis["extraData"] == "0x"
    assert quantity(genesis["gasLimit"]) == 30_000_000
    assert quantity(genesis["difficulty"]) == 0
    assert genesis["mixHash"] == "0x" + "00" * 32
    assert genesis["coinbase"] == "0x" + "00" * 20
    assert quantity(genesis["number"]) == 0
    assert genesis["parentHash"] == "0x" + "00" * 32
    assert "baseFeePerGas" not in genesis

    alloc = {address.lower(): account for address, account in genesis["alloc"].items()}
    assert set(alloc) == EXPECTED_DEV_EOAS | {DEV_BURN_ADDRESS} | set(EXPECTED_DEV_CODE)
    for address in EXPECTED_DEV_EOAS:
        account = alloc[address]
        assert quantity(account["balance"]) == 10**24
        assert quantity(account.get("nonce"), 0) == 0
        assert account.get("code", "0x") == "0x"
        assert not account.get("storage")
    burn_account = alloc[DEV_BURN_ADDRESS]
    assert quantity(burn_account["balance"]) == 10**31
    assert quantity(burn_account.get("nonce"), 0) == 0
    assert burn_account.get("code", "0x") == "0x"
    assert not burn_account.get("storage")
    assert sum(
        quantity(account.get("balance"), 0) for account in alloc.values()
    ) == 10_000_020_000_000 * 10**18

    for address, (expected_length, expected_hash) in EXPECTED_DEV_CODE.items():
        expected_predeploy = expected_genesis["predeploys"][address]
        code = hex_bytes(alloc[address]["code"])
        assert len(code) == expected_length
        assert len(code) == expected_predeploy["codeLength"]
        assert keccak256(code).hex() == expected_hash
        assert expected_predeploy["codeHash"][2:] == expected_hash
        assert quantity(alloc[address].get("nonce"), 0) == quantity(
            expected_predeploy["nonce"]
        )
        assert quantity(alloc[address].get("balance"), 0) == quantity(
            expected_predeploy["balance"]
        )
        assert not alloc[address].get("storage")

    system_account = alloc[DEV_SYSTEM_ADDRESS]
    assert quantity(system_account["balance"]) == 10**24
    eezl2_code = hex_bytes(alloc[EEZL2_ADDRESS]["code"])
    assert eezl2_code.count((1).to_bytes(32, "big")) == 4
    assert eezl2_code.count(bytes(12) + hex_bytes(DEV_SYSTEM_ADDRESS, 20)) == 4
    assert quantity(alloc[HISTORY_STORAGE_ADDRESS]["nonce"]) == 1
    assert all(not account.get("storage") for account in alloc.values())
    assert path.name == "genesis-dev.json"
    assert expected_genesis["headerRlpLength"] == 610

    (
        history_storage_root,
        child_state_root,
        child_header_rlp,
        child_hash,
    ) = construct_empty_child(genesis, genesis_hash, block_time=1)
    assert history_storage_root.hex() == EXPECTED_DEV_HISTORY_STORAGE_ROOT
    assert child_state_root.hex() == EXPECTED_DEV_EMPTY_CHILD_STATE_ROOT
    assert child_hash.hex() == EXPECTED_DEV_EMPTY_CHILD_HASH
    assert len(child_header_rlp) == 610

    empty_child = vector["emptyChild"]
    assert quantity(empty_child["blockTime"]) == 1
    assert quantity(empty_child["number"]) == 1
    assert quantity(empty_child["timestamp"]) == quantity(genesis["timestamp"]) + 1
    assert quantity(empty_child["baseFeePerGas"]) == next_base_fee(
        INITIAL_BASE_FEE,
        0,
        quantity(genesis["gasLimit"]),
    )
    assert empty_child["historyStorage"]["address"] == HISTORY_STORAGE_ADDRESS
    assert empty_child["historyStorage"]["slot"] == "0x0"
    assert empty_child["historyStorage"]["value"][2:] == genesis_hash.hex()
    assert (
        empty_child["historyStorage"]["storageRoot"][2:]
        == history_storage_root.hex()
    )
    assert empty_child["stateRoot"][2:] == child_state_root.hex()
    assert empty_child["blockHash"][2:] == child_hash.hex()
    assert empty_child["headerRlpLength"] == len(child_header_rlp)

    validate_derivation_vector(repository_root, genesis)


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    default_fixture = (
        repository_root / "docs/rollup0-network-spec/fixtures/genesis-dev.json"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("genesis", nargs="?", type=Path, default=default_fixture)
    parser.add_argument(
        "--check-dev",
        action="store_true",
        help="require all published development-fixture values",
    )
    parser.add_argument(
        "--dump-header-rlp",
        action="store_true",
        help="print the complete RLP-encoded genesis header",
    )
    parser.add_argument(
        "--derive-chain-id",
        type=lambda value: int(value, 0),
        help=(
            "synthetically override the EIP-155 chain id while deriving; "
            "requires --derive-timestamp"
        ),
    )
    parser.add_argument(
        "--derive-timestamp",
        type=lambda value: int(value, 0),
        help=(
            "apply the implementation-development deployment transformation "
            "with this genesis timestamp"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the derived canonical JSON bytes to this path",
    )
    args = parser.parse_args()

    deriving = args.derive_timestamp is not None
    if args.derive_chain_id is not None and not deriving:
        parser.error("--derive-chain-id requires --derive-timestamp")
    if args.output is not None and not deriving:
        parser.error("--output requires derivation inputs")
    if deriving and args.check_dev:
        parser.error("--check-dev cannot be combined with derivation")

    source_raw = args.genesis.read_bytes()
    source_genesis = json.loads(source_raw)
    if deriving:
        genesis, raw = canonical_development_derivative(
            source_genesis,
            args.derive_timestamp,
            args.derive_chain_id,
        )
        if args.output is not None:
            args.output.write_bytes(raw)
    else:
        raw = source_raw
        genesis = source_genesis

    state_root, header_rlp, genesis_hash = construct_genesis(genesis)
    check_development = not deriving and (
        args.check_dev
        or args.genesis.resolve() == default_fixture.resolve()
    )
    if check_development:
        validate_development_fixture(
            repository_root,
            args.genesis,
            raw,
            genesis,
            state_root,
            genesis_hash,
        )

    print(f"artifact_sha256 = 0x{hashlib.sha256(raw).hexdigest()}")
    print(f"chain_id        = {quantity(genesis['config']['chainId'])}")
    print(f"alloc_accounts  = {len(genesis['alloc'])}")
    print(f"state_root      = 0x{state_root.hex()}")
    # RLP itself carries the field count only structurally; report it from fork activation.
    field_count = 15
    config = genesis["config"]
    number = quantity(genesis.get("number"), 0)
    timestamp = quantity(genesis["timestamp"])
    field_count += int(is_active(config, "londonBlock", number))
    field_count += int(is_active(config, "shanghaiTime", timestamp))
    field_count += 3 * int(is_active(config, "cancunTime", timestamp))
    field_count += int(is_active(config, "pragueTime", timestamp))
    print(f"header_fields   = {field_count}")
    print(f"header_rlp_len  = {len(header_rlp)}")
    print(f"genesis_hash    = 0x{genesis_hash.hex()}")
    if args.dump_header_rlp:
        print(f"header_rlp      = 0x{header_rlp.hex()}")
    if check_development:
        _, child_state_root, _, child_hash = construct_empty_child(
            genesis,
            genesis_hash,
            block_time=1,
        )
        print(f"empty_child_root = 0x{child_state_root.hex()}")
        print(f"empty_child_hash = 0x{child_hash.hex()}")
        print("development fixture: OK")
    if args.output is not None:
        print(f"wrote             = {args.output}")


if __name__ == "__main__":
    main()
