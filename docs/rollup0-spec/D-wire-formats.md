# Appendix D. Rollup0 Wire Formats and Vectors

[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines EEZ ABI tuples, selectors,
hashes, events, proof inputs, and proxy bytecode. This appendix defines the Rollup0 DA envelope,
inbound protocol transaction, validator ECDSA proof policy, and unsafe-block announcement.

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

The signer signs the raw 32-byte EEZ public-input hash. The Rollup0 manager has already folded the
candidate domain from Section D.2 into that hash. The signer MUST NOT add an EIP-191
`Ethereum Signed Message` prefix or another EIP-712 domain. Verification succeeds only when the
recovered address equals the signer configured for that proof system.

`proofSystems` is strictly increasing by address and contains one proof per element. Rollup0's
proof-system index list is strictly increasing. For active set size `M`, the Rollup0 manager accepts
only configured proof systems and rejects a submitted subset with fewer than
`N = floor(2M / 3) + 1` members.

Candidate protocol V1 MUST set the batch's `crossProofSystemInteractions` field to `bytes32(0)`.
The field remains part of every applicable `publicInputsHash`; therefore any nonzero value produces
a different signed hash but is invalid under the Rollup0 V1 profile.

## D.2 Candidate Domain

The production Rollup0 manager accepts only the EEZ latest-context sentinel:

```text
batch.blockNumber = 2^64 - 1
```

For this value, `getCustomData` returns the exact Solidity ABI encoding below:

```text
candidateDomainTag = keccak256(bytes("EEZ_ROLLUP0_CANDIDATE_V1"))
                   = 0xba3ba53e31274af0c3f0f70c908597cbb1bc9a6a33006333feea258597f384b7

customData = abi.encode(
    bytes32(candidateDomainTag),
    uint256(block.chainid),
    address(EEZ),
    address(Rollup0Manager),
    address(Rollup0SettlementWrapper),
    uint256(rollup0EezRollupId),
    uint256(rollup0ChainId),
    uint256(block.timestamp),
    bytes32(blockhash(block.number - 1))
)
```

`EEZ` is the immutable EEZ address configured in the manager. `Rollup0Manager` is
`address(this)`. `Rollup0SettlementWrapper` is the active wrapper selected by the manager.
`rollup0EezRollupId` is the ID assigned when EEZ registers the manager, and `rollup0ChainId` is the
execution-chain ID fixed by Rollup0 genesis.

The manager MUST revert for every other `blockNumber` value. When EEZ calls `getCustomData`, the
manager MUST also require transaction-scoped authorization from the active settlement wrapper.
The wrapper sets that authorization immediately before calling EEZ and clears it before returning.
A direct call to `EEZ.postAndVerifyBatch` that includes Rollup0 therefore reverts in the manager.

EEZ folds `customData`, keyed by the EEZ rollup ID, into `publicInputsHash`. The ECDSA proof system
continues to verify a signature over that raw hash; it does not add a second signature domain.

The `V1` tag identifies this Rollup0 candidate protocol. A later incompatible protocol uses a new
tag. The blob envelope carries its own format version. Because EEZ authenticates the selected blob
versioned hashes, that format version and the complete encoded payload are covered by the same
proof or signatures.

The leading state delta binds the settled Rollup0 parent block hash, `Hparent`. It does not need to
be repeated in `customData`. Any candidate field that repeats a domain or parent value must match
the value derived above.

!!! success "DECISION: use the Rollup0 manager domain and settlement gate"
    This design uses EEZ's existing `getCustomData` hook. It requires a production Rollup0 manager
    and settlement wrapper, but it does not require an EEZ contract change.

### D.2.1 Initial Settlement Wrapper

Any account or contract can call the active wrapper. For candidate protocol V1, the wrapper:

1. verifies that the batch includes Rollup0;
2. requires `transientExecutionEntryCount = 1` and `transientLookupCallCount = 0`;
3. verifies that entry zero is a call-free Rollup0 anchor: it has destination Rollup0, a zero
   `proxyEntryHash`, exactly one Rollup0 state delta, no ether delta, empty call and nested-action
   arrays, empty return data, `callCount = 0`, and a zero rolling hash;
4. reads the live EEZ commitment, requires it to equal the anchor's `currentState` (`Hparent`), and
   requires the anchor's `newState` (`H[0]`) to differ from it;
5. asks the manager to begin one transaction-scoped settlement session;
6. calls `EEZ.postAndVerifyBatch` with the unchanged batch and blob transaction context;
7. requires the live EEZ commitment to equal `H[0]` after the call;
8. clears the manager's transaction-scoped authorization; and
9. returns only after all checks succeed.

The wrapper MUST prevent reentrancy. The manager MUST accept authorization only from its active
wrapper and MUST reject a second active session. When it begins a session, the manager stores the
current Ethereum block number in a persistent `lastSettlementBlock` field and rejects another
Rollup0 settlement in that block. This latch belongs to the manager so activating another wrapper
cannot bypass it.

Transaction-scoped authorization MUST expire at the end of the transaction and MUST be cleared
before control returns to the relayer. The manager's `getCustomData` getter may read that
authorization but must not try to clear it because EEZ calls the getter with `STATICCALL`. If the
wrapper, manager, cleanup, or EEZ call reverts, the complete settlement transaction reverts,
including the `lastSettlementBlock` write.

The precheck is required. A postcheck alone is insufficient because EEZ catches a stale immediate
anchor, continues, and can still replace the action queues; the old `H[0]` may already equal the live
commitment. This gate makes the unsigned EEZ prefix fields enforceable, makes application of the
leading anchor entry atomic, and prevents same-block queue replacement. It does not make candidate
relay permissioned. It also does not enforce the order or identity of the later Ethereum trigger
transactions. Chapter 7 defines that separate production blocker.

### D.2.2 Rollup0.x Update Path

Initial Rollup0 supports no action originating on Rollup0, so its only immediate execution entry is
the anchor. A later version that enables Rollup0-to-Ethereum actions can activate a new wrapper and
candidate-domain tag. Under the expected outbound design, the execution prefix is the maximal
leading run of entries whose `proxyEntryHash` is zero: one anchor followed by zero or more
top-level outbound entries. Nested calls contained inside one entry do not add another prefix
element.

`transientLookupCallCount` remains zero unless that later version explicitly introduces standalone
lookups that must exist during the posting transaction. A change to either rule requires a new
candidate-domain tag and wrapper policy.

The EEZ team Safe controls this update through the Rollup0 manager. It MUST activate the new domain
tag and wrapper address atomically. The manager then rejects authorization from the old wrapper,
and the changed domain invalidates signatures made under the old policy.

## D.3 Rollup0 Block-Hash Commitment

For a candidate with `s` expected-success actions, each terminal block variant `B[k]`, where
`0 <= k <= s`, has:

```text
H[k] = keccak256(rlp(B[k].header))
R[k] = B[k].header.stateRoot
```

Rollup0 encodes `H[k]` in every EEZ field that carries the network's current state. This includes
the registered `initialState`, `StateDelta.currentState`, `StateDelta.newState`, lookup state pins,
the value stored in `rollups[rollupId].stateRoot`, and the manager escape value. The registered
initial value is the Rollup0 genesis block hash.

The L2 protocol transaction does not contain `H[k]` or an L1 `StateDelta`. The composer constructs
and hashes `B[k]` before placing `H[k]` in the separate L1 EEZ batch. The blob and `callData` do not
carry a second checkpoint table.

## D.4 Blob Format

Rollup0 uses Ethereum blobs for anchored chain data. The first byte of the decoded
`ChainOperation.operations` field is its Rollup0-local payload version:

```text
operations = 0x00 || native_block_span_v0
```

Candidate protocol V1 MUST contain exactly one Rollup0 `ChainOperation` for its anchored range,
and that message's `operations` value MUST contain the complete span. A second Rollup0
`ChainOperation` is invalid; it is not concatenated with the first or interpreted as another span.
The V1 Rollup0-only batch rule independently prohibits a chain operation for another network.

The field MUST contain at least that byte. `0x00` selects the format described below. Every other
first byte is invalid under the current rules and MUST NOT fall back to version `0`. This namespace
is independent of the EEZ blob-stream version and the type-`0x45` transaction-envelope version.
The V0 body is the direct, uncompressed `native_block_span_v0` encoding. A decoder MUST NOT sniff
for or apply zlib, Brotli, or any other decompressor and MUST NOT accept a compression selector.
A later compressed format requires a different payload-version byte.

V0 defines no Rollup0-specific maximum for `len(operations)`. The exact decoded field admitted by
the shared EEZ stream, subject to the blob capacity of its canonical Ethereum settlement
transaction, is the V0 byte bound. A Rollup0 decoder MUST operate only on that length-delimited
slice after the EEZ decoder has assembled it, including through EEZ's own authenticated multi-blob
continuation. It MUST NOT source additional bytes outside that EEZ message stream. Because V0 is
uncompressed, the published and decoded V0 body lengths are identical.

Every field below described as `uvarint32` uses the protobuf unsigned Base128 bit layout and the
shortest encoding of a value from `0` through `2^32 - 1`. The low seven bits are emitted first and
bit 7 indicates that another byte follows. A `uvarint32` occupies one through five bytes. A decoder
MUST reject a truncated continuation, an encoding longer than five bytes, a fifth byte greater than
`0x0f`, or a multi-byte encoding whose final seven-bit group is zero. This canonicality rule applies
inside the opaque Rollup0 `operations` value and does not modify EEZ's enclosing field decoder.

### D.4.1 Linear V0 Grammar

The complete chain-operation payload is the following concatenation, where `||` denotes byte
concatenation and all array elements appear in increasing index order:

```text
operations =
    0x00
    || uvarint32(block_count)
    || concat(uvarint32(pure_transaction_counts[i])
              for i in [0, block_count))
    || concat(uvarint32(beneficiary_run_length[j])
              || beneficiary[j]
              until sum(beneficiary_run_length) = block_count)
    || concat(uvarint32(extra_data_run_length[j])
              || u8(len(extra_data[j]))
              || extra_data[j]
              until sum(extra_data_run_length) = block_count)
    || concat(uvarint32(pure_transaction_lengths[i]) for i in [0, T))
    || concat(pure_transactions[i] for i in [0, T))

T = sum(pure_transaction_counts)
len(beneficiary[j]) = 20
0 <= len(extra_data[j]) <= 32
len(pure_transactions[i]) = pure_transaction_lengths[i]
```

`block_count`, both kinds of run length, and every transaction length are positive. A
`pure_transaction_counts` element may be zero. Both run columns are maximal: adjacent runs in one
column MUST have different values. The final transaction byte ends exactly at the end of
`operations`; no padding or extension byte is permitted.

The version byte is followed by one `uvarint32 block_count` and then exactly `block_count`
`uvarint32 pure_transaction_count` values. `block_count` MUST be nonzero; each transaction count
MAY be zero. The decoder MUST compute `T = sum(pure_transaction_count)` using checked arithmetic.
Exactly `T` transaction lengths and transactions occur in their later columns.

V0 defines no additional `block_count` maximum below `2^32 - 1`. Before allocating storage based
on the declared count, a decoder MUST reject if `block_count` exceeds the number of bytes remaining
in the V0 body: every block requires at least one transaction-count byte. It MUST then validate the
count against the Rollup0 block schedule, parse every count and later column with checked
arithmetic, and consume the V0 body exactly. A truncated column or any trailing byte is invalid.
This early bound is valid because V0 is uncompressed; a later compressed version must define its
own decoded-resource rules.

The complete authenticated candidate consists of this `operations` value together with the
surrounding EEZ logical messages and batch fields. Across those authenticated inputs—not
necessarily as duplicate fields inside `operations`—the candidate must encode or commit to:

1. the first block header inputs from which the exact settled Rollup0 parent is derived;
2. every block boundary in the anchored range;
3. every pure-L2 transaction and every input needed to derive each protocol-derived transaction in
   exact block order;
4. all non-derived header inputs for every block, including its `beneficiary`;
5. the EEZ objects and origin fields for every synchronous effect;
6. the ordered EEZ action brackets from which each manifest index, cross-chain call hash, and
   expected outcome are derived; and
7. every non-derived input needed to reconstruct terminal variants `B[0]` through `B[s]`, where
   `s` is the complete candidate's expected-success action count.

Beneficiaries use maximal run-length encoding. Each run is one positive, shortest-form
protobuf-style unsigned Base128 `u32` run length followed by exactly 20 address bytes. There is no
run-count field: checked summation of the run lengths must reach the block count exactly. No partial
sum may exceed it, and adjacent runs must contain different addresses. Decoding produces one exact
beneficiary per block. The zero address is valid.

`extraData` uses the same maximal-run structure. Each run is one positive, shortest-form
protobuf-style unsigned Base128 `u32` run length, one `u8` byte length from zero through 32, and
exactly that many value bytes. Checked run-length summation must reach the block count exactly
without overshoot, and adjacent runs must contain different byte strings. A zero byte length is the
canonical empty `extraData` value.

Each pure-L2 transaction decodes to its exact canonical EIP-2718 network encoding. Rollup0 does not
decompose a pure transaction into separately encoded signature, nonce, gas, recipient, and payload
columns. Let `T` be the sum of the per-block pure-transaction counts. Exactly `T` shortest-form
protobuf-style unsigned Base128 `u32` varints encode the transaction byte lengths, followed by the
concatenation of the `T` exact transaction byte strings. Every length is nonzero, checked summation
of the lengths must equal the byte-column length, and no byte may remain unassigned.

V0 defines no separate maximum for `T`. After decoding both metadata-run columns and before
allocating storage proportional to `T`, a decoder MUST require
`T <= floor(remaining_body_bytes / 2)`. Each transaction necessarily consumes at least one
length-varint byte and one nonempty transaction byte. The decoder MUST then parse exactly `T`
lengths, validate every transaction slice, and reject any underflow, overflow, or trailing byte.

V0 encodes no candidate-wide gas or execution-work limit. Each reconstructed block MUST satisfy
the Rollup0 block gas limit and all other per-block and per-transaction consensus rules. Splitting
the same valid block sequence across different anchor candidates does not change its execution
validity. Validator admission limits are operational policy, not additional V0 wire validity.

The decoded span MUST begin immediately after the settled Sync-block parent and end at another
Sync position under the active chain configuration. Consequently, production `block_count` is a
positive multiple of `6`; Chiado development `block_count` is a positive multiple of `5`. This
schedule check is candidate validity, even though the integer codec can represent other values.

The action manifest is not a separate Rollup0 byte structure. It is the sequence of top-level EEZ
cross-chain transaction brackets in decoded message order. Candidate protocol V1 requires each
bracket to contain exactly one non-static call from EEZ network `0` to Rollup0, followed directly by
one success or failure return and the transaction finish marker. The bracket ordinal is its
manifest index, and the call hash is derived under the EEZ rules. The initiating `tx_data` field
MUST decode to the empty byte string under the unchanged EEZ encoding. No bracket may follow the
first failed return. The stream does not contain the complete signed bytes or hashes of proposed
Ethereum triggers. A follower obtains the bytes of triggers that actually execute from canonical
Ethereum; omitted proposed triggers have no Rollup0 effect to reconstruct.

The terminal block timestamp and authenticated current Ethereum settlement context determine
whether an anchor is live or catch-up. The format does not need a separate anchor-mode flag. A
catch-up payload has no synchronous effect and an empty action manifest.

Normative Rollup0 conformance vectors start with decoded EEZ logical messages and the exact bytes
of `ChainOperation.operations`. They MUST cover Rollup0 decoding, EEZ-message profile checks, and
derivation outputs, but MUST NOT define a second physical EEZ stream or field-element encoding.
Physical packing, framing, continuation, and `callData` separation remain governed by the EEZ Core
specification and its vectors. A full-blob Rollup0 fixture is an integration artifact rather than an
additional normative wire format.

The presentation of a vector in Markdown, JSON, or a program-specific fixture is not a consensus
choice. The byte strings and expected results printed here are normative; machine-readable mirrors
are non-normative test tooling.

### D.4.2 Initial V0 Codec Vectors

These initial vectors test the Rollup0-owned `operations` codec. They assume a parent context in
which the next six scheduled positions form one complete interval. Full action-manifest and
execution-derivation vectors remain part of the production conformance work.

#### Vector 1: six empty blocks

```text
operations =
0x00060000000000000600000000000000000000000000000000000000000600
```

The 31 bytes decode as:

| Field | Value |
|---|---|
| payload version | `0` |
| `block_count` | `6` |
| `pure_transaction_counts` | `[0, 0, 0, 0, 0, 0]` |
| beneficiary runs | one run of length `6`, value `0x0000000000000000000000000000000000000000` |
| `extraData` runs | one run of length `6`, value `0x` |
| transaction lengths | `[]` |
| transactions | `[]` |

The codec result is valid. Candidate validation separately checks the supplied parent and schedule
context.

#### Vector 2: empty payload

```text
operations = 0x
```

Result: reject because the payload-version byte is absent.

#### Vector 3: unknown payload version

```text
operations = 0x01
```

Result: reject because V0 does not fall back from an unknown version.

#### Vector 4: non-shortest block count

```text
operations = 0x008600
```

Result: reject because `0x86 0x00` is a non-shortest encoding of `6`.

#### Vector 5: impossible block count

```text
operations = 0x0006
```

Result: reject before allocation because six transaction-count bytes are required and none remain.

#### Vector 6: trailing byte

```text
operations =
0x0006000000000000060000000000000000000000000000000000000000060000
```

Result: reject because the final `0x00` remains after the empty transaction-length and transaction
columns have been assigned.

!!! danger "PRODUCTION BLOCKER: complete blob conformance suite"
    The V0 linear codec is defined, but the complete conformance suite is not. In particular,
    action-manifest profile, transaction-bearing, terminal-variant, and end-to-end derivation
    vectors remain required before an independent implementation can claim production conformance.
    EEZ already defines physical packing and multi-blob continuation; Rollup0 adds no competing
    rule.

## D.5 Inbound Protocol Transaction

Rollup0 represents each successful inbound action as an unsigned EIP-2718 transaction in the normal
transaction list. Its typed receipt occupies the matching receipt index. The receipt payload
contains the standard status, cumulative gas used, log bloom, and logs fields. A failed action has
an L1 EEZ failed lookup but no Rollup0 transaction or receipt.

Envelope version `0` is:

```text
0x45 || rlp([
    version,
    chainId,
    sourceHash,
    gasLimit,
    to,
    value,
    input
])
```

The transaction hash is `keccak256` of these complete bytes. Appendix F defines every field and its
canonical RLP encoding.

The transaction is derived rather than signed. Its sender is `SYSTEM_ADDRESS`, its recipient is
`EEZL2`, and its calldata follows the selected `EEZL2` inbound delivery ABI. Its access list,
blob-hash list, and authorization list are empty. Its gas limit is the lower of the block gas
remaining before it starts and the Fusaka per-transaction cap of `16,777,216`.

Type-`0x45` pays no L2 fee. Its EVM gas price is zero, clients bypass ordinary fee-cap and
signed-payer balance checks, and no fee is burned or credited to the block beneficiary. The
transaction and receipt JSON-RPC objects report `gasPrice = 0` and `effectiveGasPrice = 0`,
respectively. Gas consumption still contributes to the receipt and block `gasUsed`.

For JSON-RPC compatibility, a transaction object reports `nonce`, `v`, `r`, `s`, and `yParity` as
`0x0`; reports `accessList`, `blobVersionedHashes`, and `authorizationList` as empty arrays; and
omits `maxFeePerGas`, `maxPriorityFeePerGas`, and `maxFeePerBlobGas`. It additionally reports
`version = 0x0` and the 32-byte `sourceHash`. These zero nonce and signature values are RPC
placeholders, not serialized transaction fields or state transitions. Appendix F defines the
complete transaction and receipt schema.

The calldata carries `sourceAddress` and `sourceRollup`. `sourceAddress` is the source-side
`msg.sender`, while `sourceRollup` is its EEZ network ID. The settlement L1 uses EEZ rollup ID `0`.
Its chain ID is instead bound by the transaction's source identifier. It is fixed by the Rollup0
chain configuration and is not duplicated as an execution field. During execution, the outer frame
has `SYSTEM_ADDRESS` as `msg.sender` and `tx.origin`; the application frame has the deterministic
proxy for `(sourceAddress, sourceRollup)` as `msg.sender`.

`sourceHash` uses the version `0` calculation in Appendix F. Candidate validation recomputes it
from the authenticated settlement context, action-manifest index, and EEZ call hash. The outer
Ethereum transaction hash, nonce, eventual child block hash, transaction index, and log index are
not inputs.

The transaction root commits the exact input and order. The receipt root commits status, gas use,
and logs. The state root commits persistent execution effects. Exact return data is checked against
the EEZ execution data during replay and is not added to the receipt.

For a value-bearing successful transaction, the state checkpoint starts before the temporary
protocol credit and the `EEZL2` call. A failed action opens no checkpoint and creates no L2 value.
Any outer failure in a protocol transaction that was expected to succeed invalidates the candidate.

The matching receipt is:

```text
0x45 || rlp([
    status,
    cumulativeGasUsed,
    logsBloom,
    logs
])
```

A valid inbound transaction has `status = 1`; an outer failure invalidates the candidate. The other
fields use the standard Ethereum receipt encoding. Rollup0 adds no deposit nonce or other consensus
receipt field.

!!! danger "PRODUCTION BLOCKER: transaction conformance"
    Transaction, receipt, execution, RPC, and invalid-input conformance vectors remain to be
    published. The blob format must carry the authenticated manifest, call, and EEZ inputs needed
    to derive the exact serialized transaction bytes. It must not duplicate the resulting
    type-`0x45` envelope.

    [Appendix F](F-system-transaction-design.md) defines the Rollup0 envelope and
    compares it with OP's `0x7e` deposit type.

## D.6 Unsafe-Block Announcement

Before canonical Ethereum settlement, a Rollup0 follower adopts a block into its unsafe view only
when its producer has signed its exact block hash. Envelope version `0` is:

```text
unsafeBlockAnnouncement = rlp([
    version,
    chainId,
    blockHash,
    signature
])
```

The RLP payload is a list of exactly four items with no trailing fields:

| Field | Encoding and rule |
|---|---|
| `version` | canonical non-negative RLP integer; exactly `0` |
| `chainId` | canonical `uint256` RLP integer; equal to the Rollup0 chain ID |
| `blockHash` | exactly 32 bytes; `keccak256(rlp(blockHeader))` |
| `signature` | exactly 65 bytes, `r || s || v` |

The signed message is:

```text
unsafeBlockDomainTag = keccak256(bytes("EEZ_ROLLUP0_UNSAFE_BLOCK_V1"))
                     = 0xdb821d3d941bda3532841751ab0568201783ed2ad81cdc4f5474e73c0552a234

message = keccak256(abi.encode(
    bytes32(unsafeBlockDomainTag),
    uint256(chainId),
    bytes32(blockHash)
))
```

The producer signs this raw 32-byte message without an EIP-191 personal-sign prefix or EIP-712
wrapper. `r` and `s` are 32-byte values, `s` MUST be in the low half of the secp256k1 curve order,
and `v` MUST be `27` or `28`. The recovered address is the producer identity.

Rollup0 has no protocol allowlist for this address. A valid signature from any key makes the
producer identifiable, after which a follower MAY apply its own filtering, prioritization, or
unsafe-fork-choice policy. Such local policy is not Rollup0 validity and cannot veto canonical
Ethereum settlement.

Another network profile may reuse this envelope while defining an authorized signer set. For
example, a permissioned Gnosis sister network can accept only Gnosis-operated sequencer keys. That
profile is not Rollup0: its signer authorization and rotation rules belong in the sister network's
specification and configuration.

The announcement authenticates a block, not the peer carrying it. Any peer MAY relay the same
envelope and block. Before adopting it as unsafe, a follower MUST also retrieve the complete block,
verify that its header hashes to `blockHash`, execute and validate the block normally, and verify
that it extends the follower's selected parent. A valid signature does not authorize an invalid
block.

This envelope is not included in the block header, block hash, candidate, DA payload, validator
proof input, or Ethereum settlement transaction. It gives no candidate priority and does not make
the block safe. If canonical Ethereum settles another valid range—including one that was never
announced into the unsafe view—the follower MUST adopt that settled range as its safe view under
Chapter 10.

!!! danger "PRODUCTION BLOCKER: unsafe announcement interoperability"
    Production still requires canonical and invalid-signature vectors and a P2P capability/message
    mapping that carries the envelope alongside or ahead of the block identified by `blockHash`.

---

*Next: [Appendix E, Current Implementation Differences](E-implementation-divergences.md).*
