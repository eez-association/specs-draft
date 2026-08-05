# Appendix G. Blob Payload Design

This appendix records the design choices behind Rollup0's chain-specific blob payload. It is
informative; Appendix D defines the normative, byte-exact raw, uncompressed, columnar V0 wire
format. If this rationale and Appendix D conflict, Appendix D controls.

The shared EEZ blob format is not a Rollup0 design surface. EEZ defines the physical blob packing,
the logical message stream, message framing, multi-blob continuation, and the `callData` tail.
Rollup0 defines only how its chain-specific data uses fields that EEZ deliberately leaves opaque,
principally `ChainOperation.operations`. Candidate protocol V1 also constrains the decoded value of
`InitiateCrossChainTransaction.tx_data` to be empty; it does not redefine that field's EEZ wire
encoding.

Changing the Rollup0 payload MUST NOT change the interpretation of an EEZ blob-stream version.
The Rollup0 payload has its own format version inside the opaque chain-defined bytes.

!!! success "DECISION: keep the EEZ transport unchanged"
    Rollup0 uses the EEZ blob protocol as specified. It does not replace EEZ field-element packing,
    stream framing, message types, or blob-boundary behavior with OP Stack equivalents.

    The comparison with OP in this appendix is therefore about the organization of Rollup0 block
    data inside the EEZ stream, not about adopting OP's complete batch-submission protocol.

## G.1 Payload Version

The first byte of the decoded `ChainOperation.operations` value selects the Rollup0 payload format:

```text
0x00 || native_block_span_v0
```

`0x00` selects the initial format defined normatively by Appendix D and explained by this appendix.
A decoder consumes this byte before decoding any span field. An empty `operations` value or any
other first byte is invalid under the current rules; a decoder MUST NOT guess a format, fall back
to version `0`, or treat an unknown version as an empty span.

This is a Rollup0-local namespace. It is independent of the EEZ blob-stream version and of the
version inside a type-`0x45` protocol transaction. The complete `operations` value, including this
byte, is already authenticated through the EEZ blob commitment. Supporting another value requires
an explicit Rollup0 protocol activation.

!!! success "DECISION: use one fixed payload-version byte"
    Rollup0 uses one leading `u8` rather than a varint or a magic string. Two hundred and fifty-six
    directly addressable formats provide ample upgrade space, while every payload has a fixed-size,
    canonical dispatch prefix.

    A varint would provide more version numbers but would add continuation and shortest-form rules
    to a field that will normally remain one byte. A magic string could make a raw hex dump easier
    to recognize, but the enclosing EEZ chain operation already determines that the Rollup0 decoder
    applies; repeating that identity would add bytes without strengthening authentication.

    The tradeoff is a finite direct namespace. Exhausting it would require a later protocol to
    introduce an extension mechanism, but it would not change how version `0` is decoded.

## G.2 V0 Compression Policy

Payload format `0x00` does not apply a general-purpose compression layer:

```text
operations = 0x00 || native_block_span_v0
```

Every byte after `0x00` belongs directly to the canonical span encoding. A V0 decoder MUST NOT
inspect the body for a zlib or Brotli signature, attempt decompression, or accept a codec selector.
Bytes that happen to resemble a compression header are interpreted only as V0 span fields and are
invalid if those fields do not decode canonically.

!!! success "DECISION: leave the V0 payload uncompressed"
    V0 has one direct wire representation and needs no compression library, stream-state machine,
    decompressed-size accounting, or zip-bomb defense. Its resource use is bounded directly by the
    authenticated `operations` byte length and the linear decoding checks defined below.

    The tradeoff is lower DA capacity. The columnar layout and maximal runs still remove structural
    repetition, but V0 cannot exploit repetition inside transaction calldata or across transaction
    envelopes. It may therefore require more blobs than a compressed revision for the same block
    range.

    Brotli, using the RFC 7932 format without a custom dictionary, is the preferred option to
    evaluate for a later compressed payload version. Such a revision must use a different
    payload-version byte and define a decompressed-size cap, stream-completion rule, and
    trailing-data rule. Brotli is not a valid or auto-detected encoding of a V0 body.

Rollup0 considered enabling Brotli immediately, but selected raw V0 to minimize the first
consensus decoder and establish conformance vectors for the native span before adding another
parsing layer. A per-payload compression flag was also rejected: format-version dispatch already
provides a clean upgrade boundary and avoids two representations within V0.

!!! success "DECISION: use the enclosing DA capacity as V0's byte limit"
    V0 adds no Rollup0-specific maximum for `len(operations)`. The unchanged EEZ stream determines
    the exact length-delimited field, and a candidate must fit the blob capacity permitted to its
    canonical Ethereum settlement transaction. Because the V0 body is uncompressed, its decoded
    byte length is exactly its published byte length.

    A second byte cap would either repeat the enclosing limit or intentionally strand capacity that
    Ethereum and EEZ make available. Omitting it also lets Rollup0 benefit automatically if a later
    Ethereum fork increases the blob allowance.

    The tradeoff is that V0's maximum per-candidate parsing workload follows that external
    allowance instead of a Rollup0 constant. This is acceptable for a linear raw decoder. It does
    not justify an unbounded compressed revision: that revision must select an explicit
    decompressed-size cap before enabling Brotli.

## G.3 Selected Block Organization

One Rollup0 anchor covers a consecutive, non-empty span of blocks. Candidate protocol V1 carries
that complete span in exactly one Rollup0 `ChainOperation`; another Rollup0 `ChainOperation` is
invalid rather than concatenated. Its chain-operation payload uses a **columnar span**. At the
structural level, before selecting the byte encoding of each element, it contains:

```text
NativeBlockSpan {
    block_count                                      // uvarint32, greater than zero
    pure_transaction_counts[block_count]             // uvarint32 values, zero permitted
    beneficiary_runs
    extra_data_runs
    pure_transaction_lengths[sum(pure_transaction_counts)]
    pure_transaction_bytes[sum(pure_transaction_lengths)]
}
```

`uvarint32` uses the protobuf unsigned Base128 bit layout and always uses the shortest encoding.
The encoder emits the low seven bits in each byte, sets bit 7 when another byte follows, and emits
at most five bytes. A decoder rejects a truncated continuation, more than five bytes, a fifth byte
greater than `0x0f`, or a multi-byte encoding whose final seven-bit group is zero. These are
Rollup0-local rules inside `operations`; they do not alter the shared EEZ decoder's varint rules.

Immediately after the version byte, one `uvarint32` encodes `block_count`, followed by exactly
`block_count` `uvarint32` pure-transaction counts. `block_count` MUST be positive. A transaction
count MAY be zero and is how the format retains an empty block. The decoder accumulates
`T = sum(pure_transaction_counts)` with checked arithmetic; `T` determines the exact number of
transaction-length values later in the payload.

All per-block vectors use the same zero-based block index. Element `0` describes the first block
after the settled parent, and element `block_count - 1` describes the terminal Sync block. The
flattened transaction sequence is in block order and transaction order. For each block, its count
selects the next consecutive transactions from that sequence. A zero count encodes an empty pure-L2
block and does not omit the block position.

Decoding `beneficiary_runs` produces the exact 20-byte `beneficiary` used by every block. Decoding
`extra_data_runs` produces each block's exact zero-to-32-byte `extraData`. These values are included
because Rollup0 permits the composer to select them independently for every block. Block numbers
and timestamps are omitted from this conceptual structure because they follow from the settled
parent and Rollup0's fixed two-second cadence.

`pure_transaction_bytes` contains only the pure-L2 prefix. Existing Rollup0 execution rules place
the successful protocol-derived transactions after that prefix in the terminal Sync block. The
surrounding EEZ action brackets and batch entries supply the authenticated inputs needed to
construct each permitted terminal variant. Appendix D defines that boundary; V0 does not duplicate
those inputs inside `operations`.

!!! success "DECISION: columnar native-block span"
    Rollup0 groups block counts, beneficiaries, extra data, and the flattened pure-transaction
    sequence by field rather than encoding a complete record for one block before starting the
    next.

    The transaction-count vector defines every block boundary, including empty blocks. Keeping
    values of the same kind adjacent also makes repeated beneficiaries, short extra data, and
    transaction fields more amenable to compression if a later payload version introduces it.

    The cost is that a decoder must validate the complete vector lengths and count sum before it can
    finish partitioning the span. This is acceptable because an anchor candidate is authenticated
    and validated as one object.

!!! success "DECISION: use canonical uvarint32 block and transaction counts"
    `block_count` and every `pure_transaction_counts` element use the same shortest-form
    `uvarint32` already selected for run lengths and transaction lengths. Common per-block counts
    occupy one byte, while the representation still has ample range for catch-up spans.

    Fixed-width `u32` values would simplify indexing but would spend four bytes on every count,
    including zero counts for empty blocks. A fixed `u16` would save only two bytes per count while
    introducing a substantially lower hard ceiling. The selected representation instead costs a
    small variable-length decoding step and requires explicit overflow and minimality checks.

!!! success "DECISION: do not add a separate V0 block-count cap"
    V0 imposes no `block_count` maximum below the `u32` representation bound. Because the body is
    uncompressed and contains exactly one transaction-count varint per block, every declared block
    requires at least one additional authenticated payload byte. The decoder can therefore require
    `block_count <= remaining_body_bytes` immediately after reading the count, before allocating a
    count-sized vector. The later column checks make the actual bound stricter.

    An explicit lower cap would duplicate the natural DA bound and could prevent a well-funded
    catch-up candidate from using blob capacity that Ethereum and EEZ already permit. It would also
    make the Rollup0 limit sensitive to an arbitrary operational estimate rather than to the bytes
    actually published.

    The tradeoff is that the largest possible span grows if Ethereum later permits more blob data
    in one settlement transaction. V0 parsing and empty-block reconstruction still grow only
    linearly with that authenticated input. If execution or proving needs a separate workload cap,
    it should constrain the relevant aggregate resource directly rather than use block count as a
    proxy. A compressed later version must reconsider output and element limits because this
    one-byte-per-block argument would no longer apply.

`beneficiary_runs` is a sequence of:

```text
BeneficiaryRun {
    run_length   // shortest-form protobuf-style u32 varint
    beneficiary  // exactly 20 bytes
}
```

There is no separate run count or byte length. The decoder stops after the checked sum of
`run_length` values reaches `block_count`. Every run length MUST be positive, no partial sum may
exceed `block_count`, and adjacent runs MUST have different beneficiaries. The zero address is a
valid beneficiary.

!!! success "DECISION: run-length-encode beneficiaries"
    Rollup0 encodes one beneficiary per maximal consecutive run instead of one address per block.
    A repeated address across a long catch-up range therefore costs one address and one run length.

    Requiring maximal runs gives every decoded beneficiary vector one canonical run encoding. In
    the worst case where every block changes beneficiary, the format adds normally one length byte
    per block compared with a flat 20-byte array.

`extra_data_runs` is a sequence of:

```text
ExtraDataRun {
    run_length         // shortest-form protobuf-style u32 varint
    extra_data_length  // u8, 0 through 32
    extra_data         // exactly extra_data_length bytes
}
```

As with beneficiaries, there is no separate run count or byte length. Checked summation of the
positive run lengths determines the end of the column and MUST reach `block_count` exactly without
overshoot. Adjacent runs MUST contain different `extra_data` byte strings. Length zero represents
empty `extraData` and is valid.

!!! success "DECISION: run-length-encode extraData"
    Rollup0 encodes one `extraData` value per maximal consecutive run. Empty or repeated values
    therefore add only one run length, one value-length byte, and one copy of the value for the
    complete run.

    If every block has different `extraData`, the format adds normally one run-length byte per
    block compared with a flat one-byte length column. The 32-byte protocol limit makes a fixed
    `u8` value length sufficient and avoids another varint.

### Candidate-wide execution work

Every reconstructed block remains subject to Rollup0's `30,000,000` block gas limit and all
per-transaction execution rules. V0 does not add a sum-of-gas, execution-step, or other workload
field for the complete span.

!!! success "DECISION: do not add a candidate-wide execution-work cap"
    The validity of a block sequence does not depend on where a composer divides it into anchors.
    Two candidates covering adjacent portions and one candidate covering their combined range are
    subject to the same per-block consensus rules.

    An aggregate cap would give validators and proof systems a predictable upper bound per request,
    but it would make anchor partitioning consensus-visible and could force otherwise unnecessary
    catch-up submissions. Validators may reject or defer work operationally, and composers may split
    ranges, without making the underlying blocks invalid.

    If even the first complete unsettled interval of an unsafe branch cannot fit a valid candidate,
    that branch cannot become safe because V1 anchors end at Sync positions. Another composer can
    rebuild a smaller sibling from the settled cursor by omitting or reordering pure-L2
    transactions. The oversized unsafe branch may be replaced, but it does not permanently block
    canonical progress.

    Any future proof system that cannot cover the full valid V0 domain must be activated with an
    explicit protocol rule or a new candidate version. An implementation-specific proving limit
    MUST NOT silently become an additional V0 validity rule.

## G.4 Pure-L2 Transaction Representation

Every transaction slice in `pure_transaction_bytes` is the exact canonical EIP-2718 network
encoding of one signed pure-L2 transaction. For a legacy transaction this is its canonical RLP
list. For a typed transaction it is the transaction-type byte followed by its exact opaque
transaction payload.

Decoding the Rollup0 payload produces these bytes without field reconstruction or reserialization.
The bytes determine the transaction hash and the value inserted into the block's transaction trie.
The transaction must also be canonical and valid under the EVM fork and transaction-type rules
active for its block. Transaction types prohibited by the Rollup0 profile remain invalid even when
their byte encoding is otherwise well formed.

Let `T = sum(pure_transaction_counts)`. The length column contains exactly `T` unsigned Base128
varints using the protobuf varint bit layout. Each value is the byte length of the corresponding
transaction and MUST use its shortest representation. A length is at most `2^32 - 1`, so its
encoding occupies one to five bytes. The decoder uses checked arithmetic and requires:

```text
len(pure_transaction_lengths) = T
sum(pure_transaction_lengths) = len(pure_transaction_bytes)
```

Each length MUST be nonzero. After slicing, each byte string must decode as one canonical
transaction valid for its block. No byte may remain unassigned.

After the beneficiary and `extraData` columns have ended, the body contains only the `T` length
varints and their transaction bytes. Before allocating storage proportional to `T`, the decoder
MUST require:

```text
T <= floor(remaining_body_bytes / 2)
```

This follows because each transaction needs at least one length-varint byte and, because zero
length is invalid, at least one transaction byte. Subsequent decoding enforces the stronger exact
length sum and transaction-validity rules.

!!! success "DECISION: carry exact pure-L2 transaction bytes"
    Rollup0 carries each signed pure-L2 transaction as its exact EIP-2718 byte string. It does not
    split signatures, recipients, nonces, gas fields, and payload fields into OP-style columns.

    Exact bytes keep the DA decoder independent of individual transaction schemas, preserve the
    transaction hash and trie value directly, and allow a later EIP-2718 transaction type without
    redesigning the Rollup0 span codec merely to add its fields.

    The tradeoff is lower format-specific compression. Generic compression can still exploit
    repetition across adjacent transaction bytes if Rollup0 later selects it, but it will not gain
    all of the savings from OP's field-aware decomposition.

!!! success "DECISION: canonical transaction-length column"
    Rollup0 encodes one shortest-form protobuf-style `u32` varint per pure transaction, followed by
    the concatenation of the exact transaction byte strings. It does not locate boundaries by
    parsing the transaction payloads themselves.

    The explicit lengths add normally one to three bytes per transaction, but keep the span codec
    independent of transaction-type schemas, including a future EIP-2718 type whose opaque payload
    is not RLP. A fixed-width length would be simpler but would spend four bytes on every
    transaction; an outer RLP list would add another framing convention and usually more overhead.

!!! success "DECISION: do not add a separate V0 transaction-count cap"
    V0 imposes no maximum on `T` below the bound created by the uncompressed bytes that must encode
    its length and transaction columns. The `remaining_body_bytes / 2` check rejects an impossible
    count before allocation, and exact column exhaustion keeps valid parsing work linear in the
    authenticated payload size.

    A fixed cap would make resource estimates simpler, but it could leave usable DA capacity idle
    and would duplicate the physical bound. As with `block_count`, a future compressed revision
    must define decoded-resource limits before this conclusion can be carried forward.

## G.5 Protocol-Derived Transaction Reconstruction

The Rollup0 payload does not carry a second byte-string copy of a successful type-`0x45`
transaction. It carries the authenticated, non-derived action inputs from which Appendix F's
envelope is constructed.

For successful manifest action `i`, derivation first executes the pure-L2 prefix and every preceding
successful protocol transaction. It then computes the gas remaining before action `i` and
constructs the exact envelope from:

- envelope version `0` and the configured Rollup0 chain ID;
- the `sourceHash` derived from the authenticated settlement context, manifest index, and call hash;
- the lower of the remaining block gas and the protocol-transaction gas cap;
- the fixed `EEZL2` recipient;
- the action value; and
- the exact `executeIncomingCrossChainCall` ABI input derived from the authenticated EEZ action.

The resulting bytes determine the transaction hash and transaction-trie value. They MUST decode as
the Appendix F envelope and produce the terminal variant hash committed by the corresponding EEZ
state delta. A failed action produces no type-`0x45` transaction and therefore no envelope bytes.

!!! success "DECISION: derive type-0x45 transaction bytes"
    Rollup0 reconstructs every type-`0x45` transaction from authenticated action data and consensus
    context. The blob does not duplicate the resulting serialized envelope.

    This keeps the non-derived action data as the single source of truth and avoids publishing the
    usually large ABI input twice. Supplying an envelope copy would not remove the derivation logic:
    validators would still have to reconstruct it and reject any mismatch.

    The tradeoff is sequential reconstruction. The transaction's gas limit is not known until the
    preceding prefix has executed. Validators and followers already execute that prefix to validate
    the candidate, so this does not add another consensus dependency.

## G.6 Action Manifest from EEZ Brackets

Rollup0 does not encode a second action-manifest array inside `ChainOperation.operations`. The
manifest is the semantic view of the top-level EEZ cross-chain transaction brackets that follow the
native Rollup0 span in decoded message order. The transport-only `CloseBlobStream` marker, if it
separates blob data from the `callData` tail, does not affect that order.

Candidate protocol V1 permits zero or more brackets with exactly this shape:

```text
InitiateCrossChainTransaction(chain_id = 0, tx_data = "")
Call(to_chain = rollup0_eez_id, from_address, to_address, value, gas, data)
ReturnSuccess(return_data) | ReturnFail(return_data)
FinishCrossChainTransaction
```

`chain_id = 0` is the settlement L1's EEZ network ID. The bracket contains exactly one top-level,
non-static `Call` to Rollup0. It contains no additional call, nested call, snapshot, revert, or
chain operation. `tx_data` is the empty byte string.

If the brackets are indexed from zero in decoded message order, bracket `i` has
`manifestIndex = i`. The EEZ call-hash algorithm derives its `crossChainCallHash` from the target
rollup ID, target address, value, data, source address, and source rollup ID; neither the hash nor
the manifest index is encoded again. The bracket's `gas` remains an authenticated simulation input
but is not one of EEZ's call-hash identity fields and is not the derived type-`0x45` gas limit.
`ReturnSuccess` selects one successful action and supplies its exact return data. `ReturnFail`
selects the optional terminal failed action and supplies its exact revert data.

All successful brackets MUST precede the optional failed bracket. No action bracket may follow a
bracket containing `ReturnFail`. A catch-up candidate contains no action bracket. The corresponding
L1 EEZ batch must contain one matching execution entry per successful bracket and at most one
matching failed lookup for the terminal failed bracket.

!!! success "DECISION: use EEZ action brackets as the manifest"
    The ordered EEZ brackets are the candidate's action manifest. Their positions, call fields, and
    return-message types uniquely determine the manifest indexes, call hashes, and expected
    outcomes used by Rollup0 derivation.

    This avoids duplicating those values in a Rollup0-specific manifest and eliminates mismatch
    rules between two authenticated representations. The cost is a strict Rollup0 profile over the
    otherwise more general EEZ grammar: validators and followers must scan the brackets and reject
    unsupported nesting or additional messages.

### Empty source-transaction data

EEZ deliberately leaves `InitiateCrossChainTransaction.tx_data` opaque so each source network can
define what identifies or reconstructs its originating transaction. Rollup0 candidate protocol V1
requires the decoded field to have length zero. The enclosing field continues to use the shared EEZ
encoding exactly as specified by EEZ; Rollup0 adds no bytes or alternate framing inside it.

The action is identified instead by:

```text
(authenticated settlement context, manifestIndex, crossChainCallHash)
```

The settlement context comes from the Rollup0 manager, `manifestIndex` is the bracket ordinal, and
the call hash is derived from the bracket's `Call`. Together they bind the source and target EEZ
networks, source address, destination, value, calldata, candidate slot, and ordered occurrence.

The signed Ethereum transaction proposed for delivery is not part of that identity. The composer
constructs a candidate before Ethereum inclusion, and canonical execution may use a different
transaction that produces the same next ordered call. Standard EVM execution exposes neither the
current transaction hash nor its sender nonce to the EEZ contract, so placing either value in
`tx_data` would not let the on-chain queue enforce it.

Full proposed trigger bytes would also publish signatures, nonces, fee settings, and any unrelated
Ethereum behavior for transactions that may never be included. That can leak a private bundle
suffix and make an unused signed transaction available for replay. A hash avoids the byte cost but
still creates an unenforceable carrier identity and conflicts with the selected substitution rule.

Validators receive proposed signed triggers out of band and simulate each intended prefix before
attesting. Relayers and builders receive the same delivery data. This verifies that a usable
delivery path exists, but the proposed trigger bytes do not affect candidate identity or canonical
Rollup0 derivation. Followers obtain transactions that actually execute from canonical Ethereum.

!!! success "DECISION: empty InitiateCrossChainTransaction.tx_data"
    Candidate protocol V1 requires every action bracket's `tx_data` to be empty. Any non-empty value
    makes the Rollup0 candidate invalid even though the shared EEZ grammar can carry it for another
    network.

    Empty `tx_data` does not authorize an arbitrary Ethereum transaction. The next-call hash and
    ordered EEZ queue constrain the action semantics, while the L1 transaction-scoped guard requires
    one Rollup0 action per outer transaction and rejects blob-carrying trigger transactions.

    The cost is intentional: the candidate cannot reconstruct or audit a proposed transaction that
    was never included. Such a transaction has no canonical Rollup0 effect to reconstruct.

Rollup0 considered these alternatives:

| `tx_data` choice | Benefit | Reason not selected |
|---|---|---|
| Complete signed Ethereum transaction | Self-contained proposal and direct bundle simulation input | Publishes private or unused transactions, adds substantial data, and binds a carrier that canonical execution may validly replace |
| Signed transaction hash | Small commitment to an out-of-band proposal | The EEZ contract cannot observe and enforce the current transaction hash, and the value is not Rollup0 action identity |
| Source nonce or custom intent identifier | Can distinguish proposed source operations | Not available to the EEZ call path without changing the application interface; duplicates the ordered call identity |
| Empty byte string | No carrier-specific value or carrier dependency | Selected; proposed delivery data remains out of band |

## G.7 Relationship to an OP Span Batch

The columnar idea is inspired by
[OP span batches](https://specs.optimism.io/protocol/delta/span-batches.html#span-batch-format), but
the resulting Rollup0 object is not an OP span batch. Both formats describe consecutive L2 blocks,
carry a block-count vector, use per-block transaction counts to recover boundaries, flatten
transactions in block order, and group similar data to improve compression.

The surrounding protocol and several consensus inputs differ:

| Topic | OP span batch | Rollup0 native-block span |
|---|---|---|
| Enclosing transport | Compressed channel split into numbered frames, potentially across multiple L1 transactions | Uncompressed opaque V0 payload inside the existing EEZ message stream; EEZ defines blob continuation and closure |
| Parent check | First 20 bytes of the starting parent hash | No truncated parent check in the native span; the EEZ state transition binds the full settled parent block hash |
| L1 relationship | Last L1-origin number and hash check plus one origin-change bit per L2 block | No OP-style per-block L1 origin; the authenticated Rollup0 settlement context and Sync schedule define the anchor relationship |
| Time | Starting timestamp relative to L2 genesis | Every timestamp is derived from the settled parent with the fixed two-second interval |
| Block boundaries | `block_count` plus `block_tx_counts` | `block_count` plus `pure_transaction_counts` |
| Transactions derived elsewhere | Deposits and the L1-attributes transaction are excluded from the batch and derived from L1 | Successful EEZ actions deterministically produce Rollup0 type-`0x45` transactions; a terminal failed action creates no L2 transaction |
| Transaction representation | Signed sequencer transactions are split into columnar signature, recipient, data, nonce, gas, and flag fields | Pure-L2 transactions remain exact EIP-2718 byte strings with a separate canonical length column |
| Fee recipient | Active span-batch version 1 does not encode it; payload derivation uses the Sequencer Fee Vault. An experimental version 2 proposes an indexed recipient set | One composer-selected `beneficiary` is mandatory for every block and encoded in maximal runs |
| `extraData` | Not a span-batch field | Exact zero-to-32-byte value is required for every block and encoded in maximal runs |
| Synchronous outcomes | L1-derived deposits lead to one derived block sequence | One candidate defines terminal variants according to the successful prefix of its ordered EEZ action manifest |

The OP-specific prefix fields are useful because OP derives blocks through sequencing windows and
L1 origins. Copying them into Rollup0 would add a second, partially redundant settlement model.
Conversely, copying OP span version 1 unchanged would omit Rollup0's per-block beneficiary and
`extraData`, its EEZ action data, and its terminal-variant rules.

OP's transaction decomposition is separable from its block-level columnar layout. Rollup0 can use
the latter without adopting the former.

## G.8 Execution Outputs and Block Storage

The Rollup0 DA payload carries the inputs required to execute the span. It does not carry receipts,
logs, state-trie data, full block headers, execution-derived roots, or a separate vector of block
hashes.

Those outputs remain part of ordinary Rollup0 blocks:

- the block body contains the exact transaction sequence;
- the receipt sequence contains every receipt and log;
- the header contains `transactionsRoot`, `receiptsRoot`, `logsBloom`, `gasUsed`, and `stateRoot`;
  and
- the block hash commits the complete header.

The separate L1 EEZ batch provides the authenticated output commitment. Its leading state delta
contains `H[0]`, the hash of the terminal block with the pure-L2 prefix and no successful
synchronous action. Each successful action state delta contains the next terminal-variant hash
`H[k]`. These values are part of the EEZ public inputs and are authenticated by the candidate proof
or signatures. Canonical Ethereum execution leaves exactly the selected `H[k]` in EEZ storage.

`H[0]` transitively commits every earlier block in the span: its header contains its parent's hash,
that parent header contains the preceding hash, and so on through `Hparent`. Each committed header
in turn contains its transaction, receipt, and state roots. Each sibling terminal hash `H[k]`
commits the same preceding span and the exact terminal header for that action prefix.

Validators and provers MUST execute the complete candidate and compare every computed `H[k]` with
the corresponding EEZ state delta before attesting. A follower MUST execute the canonically selected
action prefix and compare its computed terminal block hash with the commitment actually retained by
EEZ. A mismatch is invalid canonical data and the follower must halt.

!!! success "DECISION: authenticate outputs through terminal block hashes"
    Rollup0 does not duplicate execution-derived header fields in its DA payload. The authenticated
    EEZ `H[k]` values are the candidate's execution-output commitments. A matching `H[k]` proves,
    subject to the collision resistance of the block hash, that the locally reconstructed terminal
    header and every ancestor header agree, including their transaction, receipt, and state roots.

    Publishing roots separately would not strengthen this commitment. It would consume DA, create
    a second representation that requires equality rules, and still require execution to establish
    validity. Separate intermediate hashes or roots may be supplied as non-consensus debugging or
    proving data, but they do not affect candidate validity.

    The tradeoff is diagnostic granularity: one terminal mismatch does not by itself identify the
    first divergent block or header field. An implementation can retain locally computed
    checkpoints or compare the reconstructed header chain to peer data without adding them to the
    consensus payload.

This differs from omitting roots from Rollup0 blocks. Rollup0 uses normal Ethereum-style block
headers containing those roots. The DA payload is a derivation input, not an archival serialization
of the complete block. Recent followers reconstruct the headers by executing the published inputs;
late followers fetch headers, bodies, receipts, and state through the standard execution-layer
peer-to-peer protocols and authenticate the fetched terminal header directly against EEZ `H[k]`.

## G.9 Alternatives Considered

| Property | Sequential block records | Selected columnar span | OP span batch unchanged |
|---|---|---|---|
| Block boundary | Local list length in each block record | Shared transaction-count vector | Shared transaction-count vector |
| Empty blocks | Explicit empty record | Zero in the count vector, with matching metadata entries | Zero in the count vector |
| Streaming | A block can be decoded as soon as its record ends | Metadata vectors are decoded before the flattened transactions are partitioned | Requires OP prefix, transaction reconstruction, and channel processing |
| Compression locality | Repeated field kinds are interleaved with transactions | Like fields are adjacent | Like fields are adjacent and transactions are decomposed |
| Rollup0 header inputs | Natural to add per block | Dedicated beneficiary and `extraData` vectors | Missing from the active OP format |
| EEZ integration | Requires a Rollup0 subcodec | Requires a Rollup0 subcodec | Also requires OP frames, channels, origins, and derivation semantics that EEZ does not provide |

Sequential records are easier to inspect and incrementally decode, but scatter repeated per-block
metadata throughout transaction data. Rollup0 selected the columnar organization because block
counts already give exact boundaries and because anchor candidates are consumed as complete,
authenticated objects.

Using the complete OP format would provide more existing code, but that code implements a different
derivation protocol. Removing its origin fields and adding Rollup0 fields would no longer be an
as-is adoption and would leave Rollup0 coupled to unrelated OP semantics.

## G.10 Conformance Boundary

Normative Rollup0 vectors begin after the shared EEZ decoder has produced its logical message
values. They contain:

- the exact bytes of each Rollup0 `ChainOperation.operations` value and the expected decoded
  `NativeBlockSpan` or rejection;
- the decoded EEZ action-bracket messages and the expected Rollup0 action manifest or rejection;
  and
- for derivation vectors, the required settlement and parent context plus the expected transaction,
  header, and terminal-commitment outputs.

They do not redefine how EEZ serializes those messages into its stream, packs the stream into field
elements, continues it across blobs, or separates the `callData` tail. Implementations must conform
to the EEZ Core vectors for that layer independently.

!!! success "DECISION: keep Rollup0 vectors above the EEZ physical codec"
    The normative Rollup0 fixtures use exact opaque payload bytes and decoded EEZ message values.
    This tests every Rollup0-owned byte and profile rule without copying the physical EEZ blob
    specification into this repository.

    The cost is that these vectors alone cannot detect a bug at the seam between an EEZ blob decoder
    and the Rollup0 decoder. A non-normative end-to-end integration fixture may pack one Rollup0
    vector with a pinned conforming EEZ implementation, but those physical bytes remain governed by
    EEZ and do not create an additional Rollup0 encoding rule.

## G.11 Conformance Presentation

The specification publishes normative known-answer examples directly in Appendix D. Each example
shows its exact input bytes or decoded EEZ values, its expected decoded or derived result, and, for
an invalid case, the rule that requires rejection.

!!! success "DECISION: do not standardize a vector-container format"
    JSON, YAML, and binary fixture files are test-distribution formats, not blob formats. Requiring
    one would add no consensus property as long as the examples in Appendix D remain byte-exact and
    unambiguous.

    Implementations may mirror the normative examples into JSON or another machine-readable form
    for automated tests. Such a mirror is useful tooling, but its file layout, number syntax, and
    metadata schema are non-consensus and may evolve without a Rollup0 protocol version.

The V0 payload-design decisions are now complete. Appendix D consolidates them into the normative
linear grammar and owns the conformance examples.

---

*This is the final appendix.*
