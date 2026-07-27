# Appendix C. Signed System Transactions

This appendix is normative for `rollup0-v0`. The reusable EEZ EVM call semantics and proxy
machinery are specified by the EEZ framework. This appendix fixes the Rollup0 execution-network
choice that EEZ deliberately leaves to a network profile: transaction construction,
authorization, ordering, fees, value accounting, receipts, failures, and reconstruction.

The rules were checked against
`eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c` and its
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` gitlink. The exact
compatibility ABI is in [Appendix E](E-compatibility-binding.md).

## C.1 Transaction roles

The rules in this appendix and
[Appendix E §E.8](E-compatibility-binding.md#e8-system-entry-points-and-signed-legacy-transactions)
are **normative for v0**. Rollup0 uses ordinary EIP-155-signed legacy transactions for both L2
system operations:

- `loadExecutionTable` stages one outbound L2→L1 entry immediately before the L2 user transaction
  that consumes it; and
- `executeIncomingCrossChainCall` loads and executes one inbound call in a self-contained
  transaction.

The transaction's RPC type is `0x0`. Its EIP-2718/network encoding is the signed legacy RLP list
itself, with no `0x00` type byte. It has no access list, EIP-1559 fee fields, blob fields, or
authorization list.

## C.2 Signer, chain ID, and prefunded account

Each deployment MUST pin its L2 `chainId`, the `EEZL2` address, a valid secp256k1 private key
`k_system`, and the corresponding account:

```
SYSTEM_ADDRESS =
    last20(keccak256(uncompressed_public_key(k_system)[1:]))
```

The `SYSTEM_ADDRESS` in genesis, the immutable in `EEZL2`, the address derived from the configured
key, and the signer recovered from every system transaction MUST be identical. At genesis this
account MUST have nonce `0`, empty code and storage, and a pinned non-zero balance. It remains an
ordinary EOA: protocol operation does not mint into it or bypass its nonce or balance. A deployment
MUST also define how its reserve may be topped up and how that reserve is backed (§5.3).

The transaction's `chainId` is the active L2 chain specification's `chainId`, not the source
rollup ID, L1 chain ID, or Rollup0 registry ID. A signer configured with its own chain ID MUST
either leave that setting unset or set it to the same L2 value; a mismatch is a construction
failure. Unprotected legacy signatures (`v = 27` or `28`) are not system transactions. The operator
and every cross-chain-capable follower need the same private key because v0 requires
byte-identical deterministic signatures. A node without it cannot derive a cross-chain Sync block.

For the development profile only, the exact public test identity is:

```text
k_system      = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
SYSTEM_ADDRESS = 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266
```

Clients MUST verify the address derivation before use. This key is intentionally public and MUST
NOT be used by a production profile. The independent Appendix C.8 envelope vector uses private
key `0x00...01` and address `0x7e5f...5bdf`; those fixture-only values test signing and decoding
and MUST NOT replace the development profile identity.

## C.3 Derivation entries and calldata

The DA sidecar carries derivation entries in the L1 `ExecutionEntry` ABI, not transaction bytes.
It excludes the call-empty state-root anchor and has the exact one-to-one relation to the remaining
on-chain entries in §4.1.2. It is mandatory whenever any producing entry exists. A follower MUST
NOT substitute `batch.entries`: the lean on-chain inbound entry does not contain the call needed
for L2 delivery.

The first `transientExecutionEntryCount - 1` sidecar items are outbound and the remainder are
inbound. Validate their zero/nonzero `proxyEntryHash` values; do not partition or reorder the list.
Settlement applies a prefix of that order. Limit reconstruction to the actually applied
non-anchor count, consuming the outbound prefix before the inbound suffix, and preserve order
within each direction. Every sidecar item has exactly one flat call and `callCount = 1`.
`outer.value` MUST NOT exceed `type(int256).max`, and one outbound user transaction MUST NOT
produce more than one entry.

For an outbound entry and its consuming raw L2 user transaction, let `outer` be
`entry.l2ToL1Calls[0]`. Construct one lean L2 entry:

```
proxyEntryHash = keccak256(abi.encode(
    MAINNET_ROLLUP_ID, outer.targetAddress, outer.value, outer.data,
    outer.sourceAddress, thisRollupId))
incomingCalls         = []
expectedOutgoingCalls = []
expectedLookups       = []
callCount             = 0
returnData            = entry.returnData
rollingHash           = bytes32(0)
```

The system calldata is `abi.encodeCall(EEZL2.loadExecutionTable,
([leanEntry], []))`. Loading replaces any previous table and resets its cursor, so the paired user
transaction MUST execute immediately after this load and before another load.

For an inbound entry addressed to this rollup, let `outer = entry.l2ToL1Calls[0]` and construct:

```
proxyEntryHash = keccak256(abi.encode(
    thisRollupId, outer.targetAddress, outer.value, outer.data,
    outer.sourceAddress, outer.sourceRollupId))
incomingCalls = [{
    targetAddress:  outer.targetAddress,
    value:          outer.value,
    data:           outer.data,
    sourceAddress:  outer.sourceAddress,
    sourceRollupId: outer.sourceRollupId,
    revertSpan:     0
}]
expectedOutgoingCalls = []
expectedLookups       = []
callCount             = 1
returnData            = entry.returnData
rollingHash           = CALL_END(CALL_BEGIN(bytes32(0), 1), 1, true, returnData)
```

The calldata is `abi.encodeCall(EEZL2.executeIncomingCrossChainCall,
(outer.targetAddress, outer.value, outer.data, outer.sourceAddress,
outer.sourceRollupId, [leanEntry], []))`. `EEZL2` requires a non-empty entry array, requires
`msg.value == value`, recomputes `proxyEntryHash`, replaces the table, executes entry `0`, checks
the rolling hash and cursors, and sets `executionIndex = 1`. Appendix E §E.8 pins both function
signatures, tuple layouts, selectors, and executable vectors.

## C.4 Legacy envelope and signature

Let `N` be the `SYSTEM_ADDRESS` nonce in the post-state of the immediate parent of the Sync block.
Do not use a pending-pool nonce. Number all system transactions in canonical Sync-block order with
`j = 0, 1, …`; transaction `j` uses `N + j`. Addition outside the `uint64` nonce range is a
construction failure.

| Legacy field | `loadExecutionTable` | `executeIncomingCrossChainCall` |
|---|---|---|
| `nonce` | `N + j` | `N + j` |
| `gasPrice` | `1_000_000_000` wei | `1_000_000_000` wei |
| `gasLimit` | `2_000_000` | `2_000_000` |
| `to` | `EEZL2`, `0x4200000000000000000000000000000000000007` | same |
| `value` | `0` | exactly `outer.value` |
| `input` | `loadExecutionTable` calldata above | `executeIncomingCrossChainCall` calldata above |
| `chainId` | deployment L2 `chainId` | same |

RLP scalars use canonical minimal big-endian encoding; integer zero is the empty byte string. For
the selected row, compute:

```
signingPayload = rlp([
    nonce, gasPrice, gasLimit, to, value, input, chainId, 0, 0
])
signingHash = keccak256(signingPayload)
```

Sign the 32-byte hash directly—without an EIP-191 prefix or EIP-712 wrapper—using secp256k1 ECDSA,
RFC 6979 deterministic nonce generation with SHA-256, and low-`s` normalization. With
`yParity ∈ {0, 1}` after normalization:

```
v = 35 + 2 * chainId + yParity
rawTransaction = rlp([
    nonce, gasPrice, gasLimit, to, value, input, v, r, s
])
transactionHash = keccak256(rawTransaction)
```

Require `1 ≤ r < secp256k1n`, `1 ≤ s ≤ secp256k1n / 2`, recover
`encodedChainId = (v - 35) // 2` and `yParity = (v - 35) mod 2`, and require
`encodedChainId == chainId`. Recovery from `(signingHash, yParity, r, s)` MUST yield
`SYSTEM_ADDRESS`. There is no leading type byte.

## C.5 Sync-block ordering

Let `O` be the number of settled outbound entries, `I` the number of settled inbound entries, and
let `user_k` be the raw L2 transaction paired with outbound entry `k`. These symbols are unrelated
to the nominal timing width `K` in §2. The full order is:

```
load_0(N), user_0,
load_1(N+1), user_1,
…,
load_{O-1}(N+O-1), user_{O-1},
deliver_0(N+O), …, deliver_{I-1}(N+O+I-1),
remaining Sync-block user transactions
```

Outbound pairs come first; inbound deliveries retain their sidecar order and come second. Only
system transactions consume this displayed `SYSTEM_ADDRESS` nonce sequence. A purported user
transaction from `SYSTEM_ADDRESS` is not a supported v0 input because it would interfere with the
reserved sequence.

System transactions are reconstructed and are not transported in the DA `transactions` list.
Every user transaction is transported and counted, including each `user_k`; therefore the Sync
block's `blockTxCounts` value is `O + remainingUserCount`, not necessarily zero (§4.1). Each
transaction executes in list order and its gas contributes to the `30_000_000` block gas limit.

## C.6 Admission, fees, and value accounting

Normal legacy-transaction validation under the active pinned fork schedule applies. In particular:

- the recovered sender, EIP-155 chain ID, and exact nonce must be valid;
- `gasPrice >= block.baseFeePerGas`;
- intrinsic gas under the active Osaka v0 fork rules must not exceed `2_000_000`;
- `2_000_000` must not exceed the gas remaining in the block; and
- immediately before the transaction, `SYSTEM_ADDRESS` must cover
  `value + 2_000_000 × 1_000_000_000` wei.

The sender prepays the gas limit and its nonce increments. After execution, unused gas is refunded
at `gasPrice`, so the net gas charge is `gasUsed × gasPrice`. The
`gasUsed × block.baseFeePerGas` portion is removed from supply; the remainder,
`gasUsed × (gasPrice - block.baseFeePerGas)`, is credited to the header beneficiary (the zero
address in v0). This is ordinary Ethereum fee accounting.

A load transaction has zero value. A successful inbound transaction debits `outer.value` from the
prefunded sender and passes it into `EEZL2`; the current v0 entry expects the inner destination
call to succeed and transfer that value through the source proxy. The corresponding L1 settlement
locks the incoming value and applies `StateDelta.etherDelta = +outer.value`. If the outer system
transaction fails, its L2 value transfer rolls back to `SYSTEM_ADDRESS`.

Conversely, a successful value-bearing outbound user call transfers its L2 `msg.value` from the
caller to `SYSTEM_ADDRESS`; the preceding load transaction itself moves no value. Its L1 immediate
entry pays the L1 target and applies `StateDelta.etherDelta = −outer.value`, subject to available
rollup escrow. If the user transaction fails, that L2 transfer rolls back. These are balance
transfers, not mint or burn operations. Apart from the base-fee burn, neither direction changes
total L2 supply. The L1 deltas record backing and do not fund an L2 transaction
([EEZ Framework §4.4](../eez-protocol-spec/04-execution-model.md) and
[Rollup0 §5.3](05-l1-to-l2.md#53-value-accounting)).

## C.7 Receipts and failures

Each system transaction produces the standard post-Byzantium legacy receipt:

```
receipt = rlp([status, cumulativeGasUsed, logsBloom, logs])
```

There is no receipt type prefix. `status` is `1` for successful outer execution and `0` for a
failed outer execution; `cumulativeGasUsed` includes every earlier system and user transaction in
the block. RPC fields report `type = 0x0`, `from = SYSTEM_ADDRESS`, `to = EEZL2`,
`effectiveGasPrice = 1_000_000_000`, the actual `gasUsed`, and the signed
`transactionHash`. Contract return data is not a receipt field. Logs and state from a failed outer
execution are absent because they roll back.

A malformed entry, signing failure, or nonce overflow is a construction failure: the operator
MUST NOT publish the rich candidate and a deriver MUST halt rather than guess. A transaction
validation failure—bad signature/chain ID, wrong nonce, insufficient balance, intrinsic gas above
the limit, gas price below base fee, or insufficient remaining block gas—makes the candidate block
invalid.

An EVM `REVERT`, exceptional halt, or out-of-gas after admission is different: it is a valid
transaction with receipt status `0`. Its nonce and gas charge remain; its call state, logs, and
value effects roll back; later list entries still execute. Failure of a load does not suppress its
paired user transaction, and failure of that user transaction does not roll back the earlier load;
the next load replaces the table. If no later load replaces it, the table cannot be consumed in a
later block because `EEZL2` binds consumption to `lastLoadBlock`. There is no implicit retry,
synthetic deposit, or cross-transaction rollback.

## C.8 Conformance vectors

[`fixtures/system-tx-fixture.py`](fixtures/system-tx-fixture.py) independently constructs an
outbound load at nonce 7 and an inbound delivery at nonce 8. It asserts calldata selectors and
hashes, signing hashes, low-`s` EIP-155 signatures, raw transaction lengths and hashes, decoding,
embedded chain IDs, and recovered senders.

[`fixtures/system-tx-vector.rs`](fixtures/system-tx-vector.rs) exercises the selected Rust
`build_inbound_system_txs` implementation directly. The fixture private keys are public test
values and MUST NOT be used by a deployment.

The canonical selectors are:

| Operation | Selector |
|---|---|
| `loadExecutionTable(...)` | `0x59683c8b` |
| `executeIncomingCrossChainCall(...)` | `0xeb494246` |

Full signature strings and tuple layouts are in
[Appendix E](E-compatibility-binding.md#e9-abi-selector-fingerprint).

## C.9 Future type `0x7E` (informative)

An unsigned typed envelope that removes private-key distribution is a possible future design. No
authoritative field list, encoding, signing exception, hash rule, receipt rule, or state-transition
rule exists for it in Rollup0 v0. Type `0x7E` is therefore **non-normative** and MUST NOT be emitted
or accepted as a v0 system transaction. In particular, implementations MUST NOT infer Optimism's
deposit format merely because it uses the same type number. A future protocol revision must
specify, activate, and vectorize a typed transaction before use.

---

*Return to [§1 Network Profile](01-profile.md), or continue with
[§2 Timing, Slot Production & Header Rules](02-block-production.md).*
