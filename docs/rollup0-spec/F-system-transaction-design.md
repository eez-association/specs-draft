# Appendix F. Inbound Transaction Design

This appendix explains why Rollup0 records inbound EEZ execution as protocol-derived
transactions. Section F.3 normatively defines the exact type-`0x45` envelope, RPC representation,
and `sourceHash` calculation referenced by Appendix D. The remaining sections explain the design
and restate execution behavior selected in Chapters 3 through 5; those chapters take precedence
if the explanatory text conflicts with them.

The representation needed an explicit protocol decision because it affects:

- which data the block header commits;
- how independent clients reconstruct and execute a block;
- how gas and transaction order are recorded;
- whether application logs have normal transaction hashes and indexes;
- whether receipts, traces, explorers, and indexers use standard Ethereum data; and
- how the block is transported, stored, removed after a reorganization, and replayed.

These rules cannot be left to each client. Two clients that represent the same successful inbound
action in different ways calculate different block hashes.

## F.1 Selected Design

Each Ethereum trigger whose Rollup0 action succeeds produces one unsigned, protocol-derived
[EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) transaction in the Rollup0 Sync block. The
transaction appears after the pure-L2 prefix and after any earlier protocol transaction. A failed
action produces an L1 EEZ failed lookup but no Rollup0 transaction.

Derivation authorizes the transaction. A user does not sign it, it has no nonce, and a node does
not accept it through the public transaction pool. Once derived, it occupies an ordinary position
in the block's transaction list and has a matching typed receipt.

The composer derives the bytes from the accepted EEZ action. Validators sign the complete
candidate, not this individual transaction. No service signs as `SYSTEM_ADDRESS` and there is no
system private key.

EIP-2718 defines only the typed envelope and its inclusion in the transaction and receipt tries.
It does not require a signature, nonce, fee payment, or account update. The Rollup0 transaction
type defines those rules. Its first EVM frame uses `SYSTEM_ADDRESS` as both `tx.origin` and
`msg.sender`, but it does not increment that account's nonce or charge it an L2 fee.

This gives every successful inbound action:

- a transaction hash and transaction index;
- a receipt status and cumulative gas value;
- normal receipt logs and log indexes;
- a normal trace position;
- inclusion in the transaction and receipt roots; and
- the ordinary Rollup0 reorganization and history behavior.

Ordinary signed user transactions do not change. Wallets do not construct or submit the new
transaction type.

## F.2 Alternatives Considered

Rollup0 considered two block representations:

| Question | Out-of-band protocol call | Protocol-derived transaction |
|---|---|---|
| Block input commitment | separate record and header commitment | normal transaction root |
| Result commitment | separate result format | normal receipt and state roots |
| Application logs | custom log identity and APIs | normal receipt logs |
| Gas accounting | separate record and receipt relationship | normal cumulative receipt gas |
| Tracing | custom call identifier | transaction hash and index |
| Block transport | custom sidecar or body extension | normal transaction list |
| Client support | second execution and RPC path | custom transaction type across the client |

An out-of-band call resembles the fixed protocol operation used by
[EIP-4788](https://eips.ethereum.org/EIPS/eip-4788). That approach is suitable for a small,
fixed state update that does not need application receipts or event indexing.

Successful inbound Rollup0 execution can run arbitrary application code, transfer value, consume
substantial gas, and emit logs. An out-of-band design would therefore need its own record, receipt,
log-index, trace, storage, and RPC rules. If its logs were omitted from `eth_getLogs`, applications
would miss them. If Rollup0 added synthetic transaction hashes to those logs, a later transaction
lookup would refer to an item that was not in the transaction root.

The protocol-derived transaction requires more than a decoder. Execution clients must support the
type in their block and receipt structures, encoding, storage, validation, block-building
interface, RPC conversion, tracing, and block propagation. It still avoids a separate execution
and receipt model. Rollup0 selected this option because inbound EEZ execution behaves like
application execution rather than fixed block maintenance.

## F.3 Exact Envelope

!!! success "DECISION: Rollup0-specific EIP-2718 type"
    Rollup0 uses transaction type `0x45`, the ASCII byte for `E`. It does not reuse OP's `0x7e`
    type with different execution rules. Sharing the byte while changing its meaning would cause
    OP-aware software to decode or execute a Rollup0 transaction incorrectly.

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

The RLP payload is a list of exactly seven items with no trailing fields:

| Field | Encoding and rule |
|---|---|
| `version` | canonical non-negative RLP integer; exactly `0` |
| `chainId` | canonical `uint256` RLP integer; equal to the Rollup0 chain ID |
| `sourceHash` | exactly 32 bytes; calculated below |
| `gasLimit` | canonical `uint64` RLP integer; at most `16,777,216` |
| `to` | exactly 20 bytes; equal to the `EEZL2` predeploy |
| `value` | canonical `uint256` RLP integer; equal to the accepted EEZ action value |
| `input` | byte string; exact `executeIncomingCrossChainCall` ABI calldata |

Canonical RLP integers use the shortest big-endian byte representation. Zero is the empty byte
string. The transaction hash is:

```text
transactionHash = keccak256(0x45 || rlp(payload))
```

`chainId` is the target Rollup0 EVM chain ID. `to` must equal the `EEZL2` predeploy. `input` is the
complete ABI encoding of `executeIncomingCrossChainCall`, including `sourceAddress`, `sourceRollup`,
the execution entry, and the lookup array. `value` must equal the inbound action value and the
function's `value` argument. The sender is implicitly `SYSTEM_ADDRESS`; it is not encoded. There is
no signature, nonce, access list, blob-hash list, or authorization list.

Version `0` has no gas-price, fee-cap, priority-fee, or payer field and charges no L2 fee. Charging
an L2 account through transaction fee fields would require a later envelope version.

The source caller is not duplicated as an envelope-level `from` field. The source-side
`msg.sender` and EEZ network ID are already committed as `sourceAddress` and `sourceRollup` inside
`input`. The source-side `tx.origin` is not propagated. On Rollup0, the outer `EEZL2` frame sees
`SYSTEM_ADDRESS`, then the destination sees the deterministic proxy for
`(sourceAddress, sourceRollup)` as `msg.sender`.

### F.3.1 JSON-RPC Transaction Representation

`eth_getTransactionByHash`, block transaction objects, and equivalent standard JSON-RPC methods
MUST represent a type-`0x45` transaction as follows. Quantity values shown as zero use the JSON
quantity `0x0`; fields marked omitted MUST be absent rather than `null`:

| JSON-RPC field | Required value |
|---|---|
| `type` | `0x45` |
| `hash` | `keccak256` of the complete typed envelope |
| `chainId` | the target Rollup0 chain ID |
| `from` | `SYSTEM_ADDRESS` |
| `to` | `EEZL2` |
| `gas` | envelope `gasLimit` |
| `input` | envelope `input`, the complete inbound ABI call |
| `value` | envelope `value` |
| `nonce` | `0x0`, as an RPC compatibility placeholder |
| `gasPrice` | `0x0` |
| `v`, `r`, `s`, `yParity` | `0x0`, as unsigned-transaction compatibility placeholders |
| `accessList` | `[]` |
| `blobVersionedHashes` | `[]` |
| `authorizationList` | `[]` |
| `maxFeePerGas`, `maxPriorityFeePerGas`, `maxFeePerBlobGas` | omitted |
| `version` | `0x0` |
| `sourceHash` | the envelope's 32-byte value |

The standard inclusion fields `blockHash`, `blockNumber`, and `transactionIndex` identify the
canonical Rollup0 block position in the ordinary way. The zero nonce and signature values exist
only to make the derived transaction legible to generic RPC consumers. They are not envelope
fields, do not participate in the transaction hash, do not read or increment an account nonce,
and do not imply a signature by `SYSTEM_ADDRESS`.

Clients MUST NOT place the source-side `sourceAddress` in the standard `from` field. An RPC
extension MAY additionally expose decoded `sourceAddress` and `sourceRollup` values for explorers
and indexers, but those extension fields are not part of this schema or consensus.

The type has no signing hash. A node must reject type `0x45` through its transaction pool, signing
APIs, raw-transaction RPC, and public transaction gossip. Block validation accepts it only at the
exact position derived for a Sync block and only when every field matches the authenticated
candidate.

The matching receipt is:

```text
0x45 || rlp([status, cumulativeGasUsed, logsBloom, logs])
```

These are the four standard Ethereum receipt fields with no extension. A valid type-`0x45`
transaction has `status = 1`; otherwise the candidate is invalid. Its JSON-RPC receipt reports
`type = 0x45`, `from = SYSTEM_ADDRESS`, `to = EEZL2`, `status = 0x1`, and
`effectiveGasPrice = 0x0`. Its transaction/block identifiers, gas fields, logs, and bloom have
their ordinary receipt values; `contractAddress` is `null`. The pre-Byzantium `root` field and the
blob-only `blobGasUsed` and `blobGasPrice` fields are omitted.

!!! warning "Local type-byte reservation"
    [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) does not define a global assignment process.
    [EIP-7808](https://eips.ethereum.org/EIPS/eip-7808) proposes `0x40` through `0x7f` for rollup
    transaction types, but it is currently Stagnant and does not itself assign individual bytes.
    Rollup0 reserves `0x45` locally and SHOULD coordinate an assignment through the applicable RIP
    process before production.

    If an Ethereum fork later assigns incompatible meaning to `0x45`, Rollup0 cannot adopt that
    transaction type unchanged. A Rollup0 hardfork must resolve the conflict. Moving the inbound
    type also requires incrementing the envelope version so that `sourceDomain` changes.

The `gasLimit` field must not exceed `16,777,216`. Derivation sets it to the lower of that value
and the gas remaining in the block before the protocol transaction starts. Although this value was
selected from Fusaka EIP-7825, it is an envelope-version-`0` constant. A later Ethereum fork that
changes the ordinary transaction cap does not change these bytes; changing the inbound cap needs a
new envelope version and Rollup0 hardfork.

The source identifier must distinguish otherwise identical actions without relying on a system
account nonce. It also needs enough domain information so that the same origin produces a different
L2 transaction identity on another settlement chain, EEZ deployment, Rollup0 instance, or protocol
version.

Rollup0 envelope version `0` uses this construction:

```text
sourceDomain = keccak256(abi.encode(
    bytes32(keccak256(bytes("EEZ_ROLLUP0_INBOUND_SOURCE"))),
    uint256(version),
    uint256(settlementChainId),
    address(settlementEezAddress),
    uint256(eezRollupId),
    uint256(rollup0ChainId)
))

sourceHash = keccak256(abi.encode(
    bytes32(sourceDomain),
    uint256(settlementTimestamp),
    bytes32(settlementParentHash),
    uint256(manifestIndex),
    bytes32(crossChainCallHash)
))
```

The inner source-domain tag is:

```text
keccak256(bytes("EEZ_ROLLUP0_INBOUND_SOURCE")) =
0xa5463ebc06077538d400f54b653944302edcce2ec4d9c2675a764c6b403c567f
```

For the initial version, `version = 0`. The ASCII domain string has no terminator. Both hashes use
Solidity ABI encoding, not packed encoding. `sourceHash` is a 32-byte envelope field.

The envelope `version` is also the version used in `sourceDomain`; there is no second derivation
version. The transaction type byte selects the Rollup0 transaction family, while `version` selects
the exact rules within that family. Changing either requires a Rollup0 hardfork, and changing the
type byte requires incrementing `version`.

`settlementChainId` is the Ethereum chain ID in production and the configured L1 chain ID in a
development deployment. `settlementEezAddress` is the canonical EEZ contract on that L1, not the
L2 `EEZL2` predeploy. `eezRollupId` identifies Rollup0 in that EEZ deployment. `rollup0ChainId` is
the target EVM chain ID. `settlementTimestamp` and `settlementParentHash` are the intended Ethereum
child-slot timestamp and known parent block hash from the authenticated candidate domain.
`manifestIndex` is the zero-based ordinal of the action's top-level EEZ transaction bracket in
decoded message order. It is not encoded separately and is not an index inside an outer Ethereum
transaction. The `crossChainCallHash` is likewise derived rather than duplicated: it commits the
target EEZ rollup ID, source EEZ network ID, source address, destination, value, and application
calldata through EEZ's existing hash.

The settlement chain ID is therefore required, but it is bound inside `sourceHash` rather than
copied into another top-level envelope field. The source EEZ network ID remains in the call data
because it selects the proxy identity during execution.

`sourceHash` and `crossChainCallHash` have different jobs. `sourceHash` identifies one ordered
action in one authenticated settlement context. Rollup0 candidate validation recomputes it and
rejects a protocol transaction from the wrong context or manifest position. `crossChainCallHash`
identifies only the EEZ call contents and is used by EEZ execution. It can be equal at two manifest
positions; `manifestIndex` distinguishes their protocol transactions.

This does not replace the domain separation of the EEZ settlement signature. The ECDSA validator
signs the EEZ `publicInputsHash`, whose manager-bound candidate domain is defined in Chapter 8 and
Appendix D.

!!! note "UPGRADE: manager and wrapper identity"
    `sourceDomain` intentionally omits the Rollup0 manager and settlement-wrapper addresses. The
    candidate domain still binds the exact manager and active wrapper, so replacing either contract
    invalidates signatures made for the old settlement path without unnecessarily changing the
    identity of an otherwise identical inbound action.

    A replacement that preserves the version-`0` envelope, derivation, and execution semantics MAY
    retain envelope version `0`. If an upgrade changes the meaning or authenticated inputs of an
    inbound transaction, it MUST increment the envelope version and define a new `sourceDomain`;
    it MUST NOT reinterpret version `0` or retroactively add the new contract addresses to its
    hash formula. A change confined to L1 authorization or settlement gating needs a new candidate
    domain when applicable, but not automatically a new inbound envelope version.

!!! success "DECISION: ordered-call source identity"
    The formula above is final for envelope version `0`. The source identifier is part of the
    derived transaction bytes and transaction root. The signed candidate authenticates every input
    to the formula rather than carrying a second serialized transaction copy. Every validator and
    follower must recompute it from the authenticated settlement context and action manifest.

    It intentionally omits the outer Ethereum transaction hash, sender nonce, eventual child block
    hash, transaction index, and log index. Those inclusion values are unavailable before the
    builder constructs the block and are not Rollup0 action identity. The intended timestamp and
    known parent hash are available before signing and bind the source to the same settlement
    context as the candidate. A candidate that misses its slot must be rebuilt and signed again.

    A different outer Ethereum transaction can perform the same action when it produces the
    expected call hash at the expected manifest position. A different call, position, timestamp, or
    settlement parent changes `sourceHash`. A different execution result for the same ordered call
    changes the full protocol transaction and its transaction hash, but not `sourceHash`.

    This aligns protocol-transaction identity with information enforceable by the current call path.
    EEZ observes the call hash and assigns a successful match to the next queue position. The
    production manager supplies the settlement context. Rollup0 does not claim to authenticate the
    surrounding Ethereum transaction or its unrelated L1 effects.

## F.4 Difference from an OP Deposit

Both designs use an unsigned EIP-2718 transaction authorized by derivation, but their execution
models are different. The OP column below describes a user-deposited transaction under the current
[OP deposit specification](https://specs.optimism.io/protocol/deposits.html):

| Property | OP user deposit `0x7e` | Rollup0 inbound transaction |
|---|---|---|
| Purpose | Execute an L1 deposit directly on L2 | Execute a precomputed EEZ action through `EEZL2` |
| Sender | Explicit `from`; EVM `msg.sender` and `tx.origin` start as `from` | Implicit `SYSTEM_ADDRESS`; destination `msg.sender` is an EEZ cross-chain proxy |
| Recipient | Arbitrary address or contract creation | Fixed `EEZL2` predeploy; application destination is inside the ABI input |
| Source identity | Actual L1 block hash and deposit-log index | Authenticated settlement context, manifest index, and EEZ call hash |
| Source caller | Explicit envelope `from`, with OP address aliasing for L1 contracts | `sourceAddress` plus `sourceRollup` in EEZ calldata; no source `tx.origin` |
| Value | Separate `mint` and call `value`; mint survives execution failure | Temporary protocol credit for the exact EEZ value; an expected-success failure invalidates the candidate |
| Failure | The deposit remains in the block with a failed receipt | A failed EEZ action has no Rollup0 transaction; it is represented by the verified L1 lookup |
| Nonce | No encoded nonce, but OP increments the `from` account nonce | No encoded nonce and no `SYSTEM_ADDRESS` nonce change |
| Gas and fees | Gas is bought on L1; modern deposits use the normal L2 gas pool and charge no L2 fee | Uses the common Rollup0 block gas pool and charges no L2 fee |
| Receipt | Standard fields plus OP deposit nonce extensions | Matching typed receipt with standard Ethereum receipt fields |

OP can use the actual L1 block hash and log index because its deposits are derived after L1
inclusion. Rollup0's candidate is constructed and signed before its bundle lands on Ethereum, so
those inclusion values do not exist yet. This is why Rollup0 needs a source identity that does not
depend on the candidate's eventual L1 placement.

Rollup0 calls its transaction a system or protocol transaction because derivation creates it and
its outer sender is `SYSTEM_ADDRESS`. This does not mean that it bypasses the block gas pool. OP's
historical `isSystemTx` field controlled that separate question and is required to be `false` for
modern OP deposits. Rollup0 does not need that field because Chapter 3 already requires a shared
block gas pool.

## F.5 Value and Failure

An inbound action can carry value even though the system caller has no prefunded balance. For a
successful action, Rollup0 opens a state checkpoint before crediting the exact value and executing
the `EEZL2` call. The value moves according to the verified EEZ action and the checkpoint is
committed.

This differs from the OP deposit execution rule, where the `mint` operation occurs before EVM
execution. Reusing the OP wire format would not make that behavior suitable for Rollup0.

A failed action creates no Rollup0 protocol transaction, receipt, gas use, or temporary value
credit. The L1 EEZ failed lookup contains its exact revert data and is pinned to the Rollup0
pre-action block-hash commitment. The action manifest and proof or validator signatures bind the
lookup to its ordered call position. Validators reproduce the proposed failure before signing. A
Rollup0 follower need not determine whether that terminal failure is reached because it has no
Rollup0 effect. An L1 application or indexer may replay the actual canonical trigger to report it.

If the Ethereum caller catches the verified proxy revert, the Ethereum transaction can settle and
is the candidate's final trigger. If the outer Ethereum transaction reverts, that trigger is not
part of the accepted prefix. A later Rollup0.x version can add an L2 failure receipt if the network
decides that mirrored failure history is worth a new execution rule.

!!! success "DECISION: V1 has no protocol-transaction fee"
    Type-`0x45` consumes and reports gas but has no payer, deduction, refund, burn, fee-collector
    credit, or beneficiary credit. Clients bypass ordinary EIP-1559 fee-cap and signed-payer balance checks for this type.
    `GASPRICE`, JSON-RPC `gasPrice`, and receipt `effectiveGasPrice` are zero. A failed inbound
    action creates no Rollup0 transaction or fee, and Rollup0 does not reimburse its simulation or
    validation.

## F.6 Header and Identity Consequences

A separate `systemCallsHash` is not needed. The transaction root commits each protocol
transaction's exact bytes and position. The receipt root commits status, cumulative gas, bloom, and
logs. The state root commits persistent execution effects. Rollup0 therefore fixes
`parentBeaconBlockRoot` to zero and does not create a duplicate commitment.

After constructing a terminal block variant, Rollup0 uses its block hash as the state commitment
stored by EEZ. That block hash includes the transaction, receipt, and state roots above. It is not
included in the protocol transaction that it commits.

The Rollup0 protocol-transaction hash intentionally does not identify the Ethereum transaction
currently calling the EEZ proxy. Chapter 7 defines an occurrence by authenticated settlement
context, ordered manifest position, and call hash. A different outer transaction that produces the
next expected call is the same Rollup0 action; its nonce, fees, and unrelated Ethereum effects are
not represented by the protocol transaction.

---

*Next: [Appendix G, Blob Payload Design](G-blob-payload-design.md).*
