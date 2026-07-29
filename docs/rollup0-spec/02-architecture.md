# 2. Architecture

## 2.1 Roles

### Composer

A composer receives synchronous Ethereum transactions through a private pool, constructs Sync
blocks and anchor candidates, simulates cross-network execution, builds the EEZ batch and Rollup0
DA payload, obtains the required proofs or signatures, and submits the candidate to Ethereum. A
composer can also build or adopt pure-L2 blocks.

Composition is open. Composer identity is not a validity input and gives no settlement priority.

### Sequencer

A sequencer syncs and distributes Rollup0 blocks over peer-to-peer protocols and can provide RPC
services. It can build pure-L2 blocks and delegate Sync-block composition to a composer. A sequencer
can also perform the composer role itself.

When pure-L2 transaction simulation reaches a cross-network proxy, an initial Rollup0 sequencer
should reject the transaction instead of adding it to a pure-L2 block. Rejection does not consume
the sender's nonce or charge an on-chain fee. Sequencers may rate limit or ban clients that waste
simulation resources. Forwarding these transactions to a composer for outbound synchronous
execution belongs to Rollup0.x.

Sequencing is open. Rollup0 has no sequencer allowlist.

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

!!! note "TO BE DEFINED"
    The production validator/prover membership, threshold, keys, and key-rotation rules are not yet
    selected. Chapter 8 defines the ECDSA attestation mechanism.

### Relayer

Any account or contract MAY relay a completed candidate. A relayer cannot change the candidate
bytes covered by its proof or signatures.

### Follower

A follower reconstructs Rollup0 from canonical Ethereum data. It maintains unsafe, safe, and
finalized Rollup0 views as described in [Chapter 10](10-derivation-following.md).

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

Execution clients expose the standard Engine API needed to build, validate, execute, and import
Rollup0 blocks.

---

*Next: [Chapter 3, EVM, Proxy, and Inbound Transactions](03-evm-proxy-systemtx.md).*
