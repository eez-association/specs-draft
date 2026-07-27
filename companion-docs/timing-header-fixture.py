#!/usr/bin/env python3
"""Executable Rollup0 timing/header algorithm and development/example vectors.

The production proof budget and submission slack are unresolved. Timing values
that include those parameters are examples or implementation-development data,
not production profile selections.
"""

from dataclasses import dataclass
from hashlib import sha256


CATCHUP_CAP = 300
U32_MAX = (1 << 32) - 1
U64_MAX = (1 << 64) - 1
EMPTY_OMMERS_ROOT = bytes.fromhex(
    "1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
)
EMPTY_TRIE_ROOT = bytes.fromhex(
    "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
)
EMPTY_REQUESTS_HASH = bytes.fromhex(
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
EXECUTION_HEADER_FIELDS = (
    "parentHash",
    "ommersHash",
    "beneficiary",
    "stateRoot",
    "transactionsRoot",
    "receiptsRoot",
    "logsBloom",
    "difficulty",
    "number",
    "gasLimit",
    "gasUsed",
    "timestamp",
    "extraData",
    "mixHash",
    "nonce",
    "baseFeePerGas",
    "withdrawalsRoot",
    "blobGasUsed",
    "excessBlobGas",
    "parentBeaconBlockRoot",
    "requestsHash",
    "blockAccessListHash",
    "slotNumber",
)


def ceil_div(numerator: int, denominator: int) -> int:
    if numerator < 0 or denominator <= 0:
        raise ValueError("ceil_div expects an unsigned numerator and positive denominator")
    return (numerator + denominator - 1) // denominator


@dataclass(frozen=True)
class Timing:
    d1: int
    d2: int
    proof: int
    slack: int

    def validate(self) -> None:
        assert all(0 <= value <= U32_MAX for value in vars(self).values())
        assert self.d1 > 0 and self.d2 > 0 and self.proof > 0
        assert self.slack >= 0
        assert self.d2 % 1000 == 0
        assert self.d1 % self.d2 == 0
        assert self.k >= 2
        assert self.proof + self.slack < self.d1
        assert self.proof + self.slack <= (self.k - 1) * self.d2

    @property
    def k(self) -> int:
        return self.d1 // self.d2

    @property
    def future(self) -> int:
        return ceil_div(self.proof + self.slack, self.d2) - 1

    @property
    def live(self) -> int:
        return self.k - self.future - 1

    @property
    def trigger_offset(self) -> int:
        return self.d1 - (self.future + 1) * self.d2

    @property
    def deadline_offset(self) -> int:
        return self.d1 - self.slack


def checked_add_u64(left: int, right: int) -> int:
    result = left + right
    if not 0 <= result <= U64_MAX:
        raise OverflowError("uint64 addition")
    return result


def checked_mul_u64(left: int, right: int) -> int:
    result = left * right
    if not 0 <= result <= U64_MAX:
        raise OverflowError("uint64 multiplication")
    return result


def saturating_add_u64(left: int, right: int) -> int:
    return min(checked_nonnegative(left) + checked_nonnegative(right), U64_MAX)


def saturating_mul_u64(left: int, right: int) -> int:
    return min(checked_nonnegative(left) * checked_nonnegative(right), U64_MAX)


def checked_nonnegative(value: int) -> int:
    if value < 0:
        raise ValueError("negative unsigned value")
    return value


def anchor(timing: Timing, genesis_ts: int, l1_number: int, l1_ts: int) -> dict:
    d1_s, d2_s = timing.d1 // 1000, timing.d2 // 1000
    proposed = checked_add_u64(l1_ts, d1_s)
    return {
        "trigger_at": checked_add_u64(l1_ts, timing.trigger_offset // 1000),
        "proposed_sync_time": proposed,
        "target_height": max(proposed - genesis_ts, 0) // d2_s,
        "target_l1_block": checked_add_u64(l1_number, 1),
        "batch_block_number": l1_number,
    }


def composition(timing: Timing, head: int, target: int, cap: int = CATCHUP_CAP):
    if head >= target:
        return ("idle",)
    future = timing.future
    live_end = max(target - (future + 1), 0)
    if head < live_end:
        live_needed = live_end - head
        if live_needed <= timing.live:
            return ("slot", live_needed, future)
        gap = target - head
        steps_back = ceil_div(max(gap - cap, 0), timing.k)
        snap = steps_back * timing.k
        terminal = max(target - snap, 0)
        if snap >= target or terminal <= head:
            return ("idle",)
        return ("catchup", terminal - head - 1)
    in_future = head - live_end
    return ("slot", 0, max(future - in_future, 0))


def header_timestamp(parent_ts: int, proposed_target: int) -> int:
    next_second = checked_add_u64(parent_ts, 1)
    return max(next_second, proposed_target)


def rollup_header_timestamp(parent_ts: int, d2_seconds: int) -> int:
    return checked_add_u64(parent_ts, d2_seconds)


def is_late(now_ms: int, timing: Timing, sync_ts: int) -> bool:
    ready = saturating_add_u64(now_ms, timing.proof)
    sync_ms = saturating_mul_u64(sync_ts, 1000)
    deadline = max(sync_ms - timing.slack, 0)
    return ready > deadline


def next_base_fee(parent_fee: int, parent_gas_used: int, gas_limit: int, elasticity: int, denominator: int) -> int:
    target = gas_limit // elasticity
    if parent_gas_used == target:
        return parent_fee
    if parent_gas_used > target:
        delta = parent_fee * (parent_gas_used - target) // target // denominator
        return parent_fee + max(delta, 1)
    delta = parent_fee * (target - parent_gas_used) // target // denominator
    return parent_fee - delta


def requests_hash(requests: list[bytes]) -> bytes:
    groups = sorted((request for request in requests if len(request) > 1), key=lambda value: value[0])
    return sha256(b"".join(sha256(group).digest() for group in groups)).digest()


def invalid(timing: Timing) -> None:
    try:
        timing.validate()
    except AssertionError:
        return
    raise AssertionError(f"expected invalid timing: {timing}")


def main() -> None:
    # D1 and D2 match the draft production cadence. P and S are illustrative.
    production_cadence_example = Timing(12_000, 2_000, 4_000, 1_500)
    chiado = Timing(5_000, 1_000, 500, 1_300)
    exact_multiple = Timing(12_000, 2_000, 3_500, 500)
    smallest = Timing(4_000, 2_000, 1_500, 100)
    for timing in (production_cadence_example, chiado, exact_multiple, smallest):
        timing.validate()

    assert ceil_div(0, U64_MAX) == 0
    assert ceil_div(U64_MAX, U64_MAX) == 1
    assert ceil_div(U64_MAX, 2) == 1 << 63
    assert ceil_div(U64_MAX, 1) == U64_MAX

    assert (
        production_cadence_example.k,
        production_cadence_example.future,
        production_cadence_example.live,
    ) == (6, 2, 3)
    assert (
        production_cadence_example.trigger_offset,
        production_cadence_example.deadline_offset,
    ) == (6_000, 10_500)
    assert (chiado.k, chiado.future, chiado.live, chiado.trigger_offset) == (5, 1, 3, 3_000)
    assert (exact_multiple.future, exact_multiple.live) == (1, 4)
    assert (smallest.k, smallest.future, smallest.live) == (2, 0, 1)

    invalid(Timing(12_000, 5_000, 2_000, 100))  # non-integral K
    invalid(Timing(5_000, 2_500, 2_000, 100))   # sub-second timestamp cadence
    invalid(Timing(2_000, 2_000, 500, 100))     # K < 2
    invalid(Timing(12_000, 2_000, 10_000, 3_000))
    invalid(Timing(4_000, 2_000, 3_000, 100))
    invalid(Timing(U32_MAX + 1, 1_000, 1, 0))

    assert composition(production_cadence_example, 0, 6) == ("slot", 3, 2)
    assert composition(production_cadence_example, 5, 6) == ("slot", 0, 0)
    assert composition(production_cadence_example, 6, 6) == ("idle",)
    assert composition(production_cadence_example, 0, 318) == ("catchup", 299)
    terminal = 0 + 299 + 1
    assert terminal == 300 and terminal % production_cadence_example.k == 0

    off_grid = anchor(
        production_cadence_example,
        genesis_ts=1000,
        l1_number=40,
        l1_ts=1013,
    )
    assert off_grid == {
        "trigger_at": 1019,
        "proposed_sync_time": 1025,
        "target_height": 12,
        "target_l1_block": 41,
        "batch_block_number": 40,
    }
    assert header_timestamp(1022, 1024) == 1024
    actual_sync = rollup_header_timestamp(
        1022,
        production_cadence_example.d2 // 1000,
    )
    assert actual_sync == 1024
    assert off_grid["proposed_sync_time"] != actual_sync
    assert (off_grid["target_l1_block"], actual_sync) == (41, 1024)
    assert off_grid["batch_block_number"] == 40
    assert off_grid["batch_block_number"] != off_grid["target_l1_block"]

    missed = anchor(
        production_cadence_example,
        genesis_ts=1000,
        l1_number=41,
        l1_ts=1036,
    )
    assert missed["target_height"] == 24
    assert composition(
        production_cadence_example,
        12,
        missed["target_height"],
    ) == ("catchup", 11)

    # A newer observation supersedes, rather than queues behind, an un-fired target.
    pending = anchor(production_cadence_example, 1000, 40, 1013)
    pending = anchor(production_cadence_example, 1000, 41, 1036)
    assert pending == missed

    sync_ms = 1024 * 1000
    deadline_ready = sync_ms - production_cadence_example.slack
    assert not is_late(
        deadline_ready - production_cadence_example.proof,
        production_cadence_example,
        1024,
    )
    assert is_late(
        deadline_ready - production_cadence_example.proof + 1,
        production_cadence_example,
        1024,
    )

    # A later batch may span a missed/deferred nominal slot; K is not a range invariant.
    cursor, endpoint = 12, 24
    assert (
        endpoint - cursor == 12
        and endpoint - cursor != production_cadence_example.k
    )

    try:
        anchor(
            production_cadence_example,
            genesis_ts=0,
            l1_number=0,
            l1_ts=U64_MAX,
        )
    except OverflowError:
        pass
    else:
        raise AssertionError("anchor overflow must fail")

    try:
        rollup_header_timestamp(U64_MAX, 1)
    except OverflowError:
        pass
    else:
        raise AssertionError("header timestamp overflow must fail")

    assert len(EXECUTION_HEADER_FIELDS) == 23
    assert len(set(EXECUTION_HEADER_FIELDS)) == 23
    assert EMPTY_OMMERS_ROOT.hex().startswith("1dcc4de8")
    assert EMPTY_TRIE_ROOT.hex().startswith("56e81f17")
    assert requests_hash([]) == EMPTY_REQUESTS_HASH
    # Request groups are ordered by the one-byte request type before hashing.
    assert requests_hash([b"\x02b", b"\x01a"]) == requests_hash([b"\x01a", b"\x02b"])

    # Historical implementation-development EIP-1559 values, not production selections.
    gas_limit, elasticity, denominator, parent_fee = 30_000_000, 2, 8, 1_000_000_000
    gas_target = gas_limit // elasticity
    assert next_base_fee(parent_fee, gas_target, gas_limit, elasticity, denominator) == parent_fee
    assert next_base_fee(parent_fee, gas_target + 1, gas_limit, elasticity, denominator) == 1_000_000_008
    assert next_base_fee(parent_fee, 0, gas_limit, elasticity, denominator) == 875_000_000

    print("timing/header vectors: OK")


if __name__ == "__main__":
    main()
