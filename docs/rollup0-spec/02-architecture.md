# 2. Architecture

## 2.1 Roles

### Composer

A composer receives synchronous Ethereum transactions through a private pool, constructs Sync
blocks and anchor candidates, simulates cross-network execution, builds the EEZ batch and Rollup0
DA payload, obtains the required proofs or signatures, and submits the candidate to Ethereum. A
composer can also build or adopt pure-L2 blocks.

Composition is open. Composer identity is not a validity input and gives no settlement priority.

### Sequencer

A sequencer builds and signs unsafe Rollup0 blocks and may distribute them over peer-to-peer
protocols and provide RPC services. It can delegate Sync-block composition to a composer and can
also perform the composer role itself. Other peers may relay a signed unsafe block unchanged and
may serve canonically settled blocks and state.

When pure-L2 transaction simulation reaches a cross-network proxy, an initial Rollup0 sequencer
should reject the transaction instead of adding it to a pure-L2 block. Rejection does not consume
the sender's nonce or charge an on-chain fee. Sequencers may rate limit or ban clients that waste
simulation resources. Forwarding these transactions to a composer for outbound synchronous
execution belongs to Rollup0.x.

Sequencing is open. Rollup0 has no sequencer signer allowlist. A follower MUST require the Appendix
D producer signature before adopting an announced block into its unsafe view, but any key may
produce that signature. The signature authenticates producer identity so peers can apply local
filtering and fork-choice policy; it does not grant protocol authority. A valid block selected by
canonical Ethereum settlement becomes safe regardless of who produced or previously announced it.

### Validator/Prover

A validator/prover provides candidate checking and signing as a best-effort service. It tries to
check each candidate that it accepts for processing, but gives no availability or response-time
guarantee. It can reject work before full validation, rate limit senders, and ban abusive senders.

When it completes validation, it signs a candidate only if the candidate satisfies the selected
EEZ rules and every Rollup0 rule in this specification. It does not treat any of these facts as a
validity failure:

- the composer is unknown;
- it already signed another candidate;
- the candidate is a sibling of another valid candidate; or
- another valid candidate arrived first.

Initial Rollup0 also trusts every validator/prover that receives a signed Ethereum trigger to keep
it private and not submit it outside an approved candidate bundle. Chapter 6 describes this
confidentiality assumption.

!!! success "DECISION: dynamic strict-two-thirds validator set"
    Let `M` be the number of active validator/prover proof systems when a settlement transaction
    executes. The required threshold is `N = floor(2M / 3) + 1`. Membership is not fixed at
    genesis. The EEZ team Safe can add, remove, or rotate members.

    A change to `M` and the corresponding change to `N` must execute atomically in one Ethereum
    transaction. Membership changes take effect in canonical Ethereum transaction order. Chapter 8
    defines the exact policy and its trust assumption.

### Relayer

Any account or contract MAY relay a completed candidate through the active Rollup0 settlement
wrapper. The wrapper does not grant composer privileges. A relayer cannot change the candidate
bytes covered by its proof or signatures or the V1 transient-prefix values enforced by the wrapper.
A relayer that receives private signed trigger transactions is trusted not to disclose or submit
them outside an approved candidate bundle.

### Follower

A follower obtains the settled Rollup0 block hash from canonical Ethereum data. It can derive
recent anchors from their blobs or use normal Rollup0 execution-layer block and state
synchronization from that exact checkpoint. It maintains unsafe, safe, and finalized Rollup0 views
as described in [Chapter 10](10-derivation-following.md).

## 2.2 Contracts and Interfaces

Rollup0 uses the settlement contracts and EVM binding defined by
[EEZ Architecture](../eez-protocol-spec/01-architecture.md). The EEZ specification owns:

- registration and settlement operations;
- batch and proof interfaces;
- cross-chain proxies;
- execution and lookup tables;
- state-delta and value accounting;
- proof-input construction; and
- generic events and ABI encodings.

Rollup0 additionally requires an L2 EEZ predeploy and a deterministic protocol-transaction
mechanism for inbound execution. Their Rollup0-specific placement and unresolved production
parameters are defined in [Chapter 3](03-evm-proxy-systemtx.md).

## 2.3 Engine API Profile

Execution clients use the Engine API to validate, execute, and import Rollup0 payloads. Under the
[Osaka Engine API](https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md), the
standard method profile is:

| Operation | Method and Rollup0 values |
|---|---|
| update fork choice / start a standard build | `engine_forkchoiceUpdatedV3`; exact Rollup0 timestamp and `prevRandao`, composer-selected `suggestedFeeRecipient`, empty withdrawals, and zero `parentBeaconBlockRoot` |
| obtain an Osaka payload | `engine_getPayloadV5`; empty blob bundle and empty `executionRequests` for a valid Rollup0 block |
| validate or import a payload | `engine_newPayloadV4`; empty `expectedBlobVersionedHashes`, zero `parentBeaconBlockRoot`, and empty `executionRequests` |

Rollup0 adopts the corresponding standard method profile when it activates a later Ethereum
execution fork. A client MUST NOT infer nonempty consensus-layer withdrawals, blobs, beacon roots,
or execution requests merely because the standard method schema contains those fields.

Standard payload attributes carry the selected `beneficiary` as `suggestedFeeRecipient` and the
Rollup0 seed as `prevRandao`, but they do not carry composer-selected `extraData` or provide a
general method for an external composer to inject a deterministic non-pool type-`0x45`
transaction after the Sync block's pure-L2 prefix. Construction MUST therefore happen in process
or through a versioned Rollup0-specific extension that supplies those values. That extension is an
interoperability and deployment interface, not a new consensus input: every constructed payload
remains subject to the same block-validation rules and can be imported through the profile above.

---

*Next: [Chapter 3, EVM, Proxy, and Inbound Transactions](03-evm-proxy-systemtx.md).*
