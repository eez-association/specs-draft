# Appendix F. Inbound Transaction Design

This appendix explains why Rollup0 records inbound EEZ execution as protocol-derived
transactions. Section F.3 normatively defines the exact type-`0x45` envelope, RPC representation,
and `sourceHash` calculation referenced by Appendix D. The remaining sections explain the design
and restate execution behavior selected in Chapters 3 through 5; those chapters take precedence
if the explanatory text conflicts with them.

The envelope and source formula match the shared native format in Rollup0 PR #235 and RollupX.
This alignment does not select their deployment addresses, broader action profiles, or balance
policies. The [Implementations comparison](../implementations/A-rollup0-differences.md#a61-native-format-alignment)
records those remaining differences against pinned implementation revisions.

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

The canonical, versionless envelope is:

```text
0x45 || rlp([
    chainId,
    sourceHash,
    gasLimit,
    to,
    value,
    input
])
```

The RLP payload is a list of exactly six items with no trailing fields:

| Field | Encoding and rule |
|---|---|
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
no version, signature, nonce, access list, blob-hash list, or authorization list. Extra fields
and trailing bytes are invalid.

The envelope has no gas-price, fee-cap, priority-fee, or payer field and charges no L2 fee. Adding
a fee payer or fee fields requires a separately specified protocol change and Rollup0 hardfork.

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
| `version` | omitted |
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
    type requires an explicit new encoding and activation rule; this envelope has no version field.

The `gasLimit` field must not exceed `16,777,216`. Derivation sets it to the lower of that value
and the gas remaining in the block before the protocol transaction starts. Although this value was
selected from Fusaka EIP-7825, it is fixed for this native transaction format. A later Ethereum
fork that changes the ordinary transaction cap does not change these bytes; changing the inbound
cap requires an explicitly specified Rollup0 hardfork.

### F.3.2 Source Identity

The source identifier names a complete native execution group's position without relying on a
system-account nonce. It uses the same construction as Rollup0 PR #235 and RollupX:

```text
sourceHash = keccak256(abi.encode(
    string("SOURCE_ENTRY_V1"),
    uint256(l2ChainId),
    bytes32(intendedL1ParentHash),
    uint64(groupIndex)
))
```

Use Ethereum Keccak-256 and standard Solidity ABI encoding. The tag is a literal dynamic string,
not a prehashed or padded `bytes32`, packed bytes, RLP, or a null-terminated string. There is no
separate `sourceDomain` hash and no envelope version. `sourceHash` is exactly 32 bytes.

`l2ChainId` is the target Rollup0 EVM chain ID, equal to the envelope's `chainId`; it is not the
EEZ registry's rollup ID. The formula ABI-encodes it as `uint256`. The compared implementations
support configured `uint64` EVM chain IDs. `intendedL1ParentHash` is the nonzero hash of the known
Ethereum parent for the intended settlement, not the eventual child block hash, a log's block hash,
or an L2 state or block commitment. The target L2 chain ID must be nonzero.

`groupIndex` is a zero-based `uint64` ordinal in the complete original Sync-block native execution
sequence. Derive it before selecting an applied prefix or an unconsumed suffix; partial settlement
and resumption must retain the original indexes. Do not reset it for a later posting of that same
Sync candidate. Ordinary transactions, anchors and lookups that create no native transaction do
not consume an index. Reject an index that cannot be represented as `uint64`.

Under Rollup0's initial inbound-only profile, each successful action produces one native delivery
and consumes one index. Since the only permitted failed action is terminal and emits no native
transaction, `groupIndex = manifestIndex` for every emitted transaction. The failed action has no
native source identity.

The same encoding also identifies the broader execution groups described in the Implementations
chapter. An outbound table load and its immediately following signed user transaction count once;
each applying inbound delivery counts once. Nested callbacks do not create separate groups,
and failed or static inbound lookups without a native transaction do not advance the index. Those
implementations order outbound groups before inbound deliveries. These counting rules explain the
shared format; Chapters 3 and 5 still define which actions Rollup0 permits.

`sourceHash` and action authorization have different jobs. A source hash identifies an execution
position, not the call contents, its result, or a globally unique occurrence. Competing candidates
with the same L2 chain ID, intended L1 parent and group index can have the same `sourceHash` while
containing different calls and transaction hashes. Retransmitting a candidate also preserves it.
There is no global source-hash deduplication rule or system-account nonce replay guard.

The formula deliberately omits the settlement chain ID, EEZ deployment and rollup ID, settlement
timestamp, call hash, manager and wrapper addresses. It also omits the outer Ethereum transaction
hash and nonce, eventual child block hash, transaction index, and log index. A different L2 chain
ID, parent hash or group index changes `sourceHash`; changing a call or timestamp alone does not.
Changing encoded calldata, value, gas, or another envelope field changes the transaction hash.

These omissions do not remove candidate authorization. Validators and followers MUST independently
authenticate the candidate context and original execution order, reconstruct every native field,
and compare the exact transaction bytes. The EEZ call hash, execution results, authorized value,
accepted commitment transitions and candidate domain remain separately checked. Chapters 7 and 8
and Appendix D define the action and settlement-signature domains, including their timestamp and
deployment bindings. A candidate that misses its slot must still be rebuilt and signed again.
An equal source hash is neither permission to execute another candidate nor evidence that two
deployments or settlement contexts are interchangeable.

!!! note "UPGRADE: envelope and source rules"
    The six-field envelope has no version selector. The `V1` suffix in `SOURCE_ENTRY_V1` is part
    of the fixed literal tag, not a separately encoded version. Changes to the envelope, source
    formula, or execution semantics require an explicitly specified Rollup0 hardfork and new
    conformance vectors. A decoder MUST NOT guess the format from extra fields or accept the
    earlier seven-field draft envelope as this format.

    Replacing a manager or wrapper does not itself change this formula. Candidate authorization
    must still bind the active settlement path. Any change to that authorization domain must be
    specified independently of the native transaction identity.

### F.3.3 Encoding Vectors

These vectors check the shared source formula and envelope serialization. They do not validate an
EEZ action, execution, or settlement. In particular, the envelope vector uses empty calldata and
the existing PR #235 predeploy address as codec inputs; it is not an executable Rollup0 candidate
under Chapter 3. The complete production conformance suite remains required.

```text
l2ChainId = 1
intendedL1ParentHash = 0x9999999999999999999999999999999999999999999999999999999999999999
groupIndex = 7
sourceHash = 0x67fb5da1784078579c726c542563b4577c50fb90652c54566d49b9f170784d37

chainId = 1
gasLimit = 16777216
to = 0x4200000000000000000000000000000000000007
value = 0
input = 0x
transaction = 0x45f83e01a067fb5da1784078579c726c542563b4577c50fb90652c54566d49b9f170784d3784010000009442000000000000000000000000000000000000078080
transactionHash = 0x1cac881a63a11d3ccd475da54a7c289f55579afb3e025ae84bbef9ed6858ebb0
```

Run `python3 companion-docs/check-wire-vectors.py` from the repository root to check these values
using Foundry `cast`, alongside the existing EEZ vectors.

## F.4 Difference from an OP Deposit

Both designs use an unsigned EIP-2718 transaction authorized by derivation, but their execution
models are different. The OP column below describes a user-deposited transaction under the current
[OP deposit specification](https://specs.optimism.io/protocol/deposits.html):

| Property | OP user deposit `0x7e` | Rollup0 inbound transaction |
|---|---|---|
| Purpose | Execute an L1 deposit directly on L2 | Execute a precomputed EEZ action through `EEZL2` |
| Sender | Explicit `from`; EVM `msg.sender` and `tx.origin` start as `from` | Implicit `SYSTEM_ADDRESS`; destination `msg.sender` is an EEZ cross-chain proxy |
| Recipient | Arbitrary address or contract creation | Fixed `EEZL2` predeploy; application destination is inside the ABI input |
| Source identity | Actual L1 block hash and deposit-log index | L2 chain ID, intended L1 parent hash, and complete native execution-group index |
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
