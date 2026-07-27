# 2. Architecture

## 2.1 Roles

### Composer

A composer collects transactions, constructs Rollup0 blocks, simulates cross-network execution,
builds the EEZ batch and Rollup0 DA payload, obtains the required proofs or signatures, and submits
the candidate to Ethereum.

Composition is open. Composer identity is not a validity input and gives no settlement priority.

### Validator/Prover

A validator/prover independently checks a candidate. It MUST sign every candidate it receives that
satisfies the selected EEZ rules and every Rollup0 rule in this specification. It MUST NOT reject a
valid candidate because:

- the composer is unknown;
- it already signed another candidate;
- the candidate is a sibling of another valid candidate; or
- another valid candidate arrived first.

The production validator/prover membership, threshold, proof system, and key-rotation rules are
not yet defined.

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

Rollup0 additionally requires an L2 EEZ predeploy and a deterministic system-transaction mechanism
for inbound execution. Their Rollup0-specific placement and unresolved production parameters are
defined in [Chapter 3](03-evm-proxy-systemtx.md).

Execution clients expose the standard Engine API needed to build, validate, execute, and import
Rollup0 blocks.

---

*Next: [Chapter 3, EVM, Proxy, and System Transactions](03-evm-proxy-systemtx.md).*
