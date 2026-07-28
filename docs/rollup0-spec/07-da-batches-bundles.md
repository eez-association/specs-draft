# 7. Data Availability, Batches, and Ethereum Bundles

## 7.1 Rollup0 DA Payload

Rollup0 publishes its anchored chain data in Ethereum blobs. The EEZ batch identifies the blobs
that belong to the candidate.

The published data must let an independent follower recover:

- the exact settled parent named by the candidate;
- every Rollup0 block and block boundary in the anchored range;
- every signed pure-L2 transaction in block order, including those at the start of the Sync block;
- the exact serialized bytes of every protocol-derived transaction in block order;
- every non-derived header input;
- the EEZ objects and Ethereum origin data for every synchronous action;
- the exact ordered manifest of intended Ethereum trigger transactions; and
- the format version.

The manifest binds each trigger by its Ethereum transaction hash and position. Validators receive
the complete signed transactions and verify that they reproduce the manifest and the proposed
`eth_sendBundle` payload. A transaction-hash commitment in the manifest does not make that hash
available to the EEZ contract during execution.

!!! note "TO BE DEFINED"
    The byte-exact blob format, its versioning rule, capacity limits, and conformance vectors are
    not yet defined. Appendix D lists the required fields but does not yet define an encoding.

## 7.2 Range Correspondence

Let `fromBlock` be the candidate's named settled parent and `toNumber` its terminal block number.
The payload covers exactly:

```text
(fromBlock.number, toNumber]
```

The published data binds `fromBlock` and defines terminal variants `B[0]` through `B[n]`. Every
variant has block number `toNumber`, the same timestamp, the same pure-L2 prefix, and exactly its
first `i` synchronous actions. Candidate validation checks every variant against the current
Ethereum-confirmed Rollup0 head.

`R[0]` means `R0`, the state root of `B[0]`.

The following must agree:

- the number of encoded block boundaries equals `toNumber - fromBlock.number`;
- the first encoded block is `fromBlock.number + 1`;
- the last encoded block has number `toNumber`;
- every `B[i].timestamp` equals the intended Ethereum settlement timestamp;
- every user transaction appears once in its selected block;
- every required L2 entry corresponds to the exact accepted EEZ action; and
- replay from `fromBlock` produces every `B[i]` and `R[i]`.

!!! note "TO BE DEFINED"
    The maximum anchor range and blob payload size are not yet selected.

## 7.3 EEZ Batch

The settlement transaction carries the batch object defined by
[EEZ Proving and Settlement](../eez-protocol-spec/04-proving-and-settlement.md).
Rollup0 requires:

- the selected blobs to be referenced by the batch;
- no duplicate or unrelated blob index;
- proof context bound to the intended Ethereum settlement domain;
- Rollup0 state deltas derived from `R0` and every exact synchronous prefix;
- enough L2 entries and origin data to reconstruct every protocol transaction; and
- the proof or signatures required by Chapter 8.

Rollup0 does not redefine the EEZ batch tuple or public-input hash.

## 7.4 Ethereum Bundle

Every settlement choice uses this order:

```text
bundle[k] = [postAndVerifyBatch, trigger1, ..., triggerK]
```

`postAndVerifyBatch` publishes and verifies the candidate and establishes `R0`. Each `trigger`
is an exact Ethereum transaction whose cross-chain proxy call can consume the next prepared EEZ
action.

The intended settlement is the exact atomic inclusion of one submitted `bundle[k]`. Every included
outer trigger transaction must succeed. Deterministic replay must show that each one made its exact
expected proxy call and received the committed success or revert result. If `bundle[k]` is included
without modification, the canonical endpoint is `B[k]` with state root `R[k]`.

For a successful Rollup0 result, the follower checks the retained EEZ consumption and state-update
logs. For a Rollup0 revert caught by the Ethereum caller, the failed EEZ frame leaves no retained
log. The follower must replay the exact Ethereum transaction to verify that the expected proxy call
occurred and returned the committed revert data. A successful Ethereum receipt alone is not enough.

`eth_sendBundle` is a builder API, not an Ethereum consensus rule. A public-mempool submission is
not a valid replacement for the required same-block ordering.

!!! caution "TO BE DEFINED: prefix bundle submission"
    Rollup0 requires one strict successful trigger prefix, but the exact builder submission method
    is not yet selected.

    1. **Submit one atomic bundle for every prefix and trust the builder.** The composer submits
       `[post]`,
       `[post, trigger1]`, `[post, trigger1, trigger2]`, and so on, without
       `revertingTxHashes`. The shared settlement transaction prevents two submitted bundles from
       being included as submitted, and any submitted bundle containing a reverted outer trigger is
       invalid. This uses standard `eth_sendBundle` semantics, but sends `n + 1` overlapping bundles.
       It also trusts the builder not to extract the signed trigger transactions and assemble a
       sequence that the composer did not submit.
    2. **Add a contract-enforced progress mechanism.** A single bundle could allow trigger reverts
       if the protocol could persistently close the suffix after failure. The current EEZ contract
       cannot do this with a simple flag because all writes made by a reverted outer transaction
       also revert. A workable design would need a larger execution or finalization change.
    3. **Use one bundle with every trigger in `revertingTxHashes`.** This is one request, but it does
       not enforce the required prefix with the current contracts. Failed lookups and
       no-state-change outcomes can leave no progress marker, so a later trigger can still run. This
       option is not valid unless option 2 supplies the missing enforcement.

    An `eth_sendBundle` request is not visible to the EVM. Even with option 1, a builder that has the
    signed transactions can omit one trigger or add another transaction outside the submitted
    bundle. A skipped successful execution entry remains at the EEZ queue head and blocks a later
    trigger with a different call hash, even if that entry would not change the state root. A failed
    lookup is not part of that queue and leaves no persistent cursor. Omitting its trigger can
    therefore allow a later successful entry to execute. Duplicate call hashes can also let a later
    trigger consume an earlier occurrence.

    The team must either accept compatible builders as a Rollup0 trust assumption or design option
    2. The selected builders, fee policy, and exact rule are production blockers. Candidate relay
    remains permissionless.

    `postAndVerifyBatch` must be submitted as an EIP-4844 blob transaction with its blob sidecar.
    The selected relay and builder APIs must accept and simulate that sidecar together with every
    prefix bundle. Support and size limits for this path are also production blockers.

## 7.5 Identical Cross-Chain Calls

The EEZ call hash identifies the target network, target address, value, calldata, source address,
and source network. It does not identify the Ethereum transaction that made the call. Two
occurrences with the same fields therefore have the same hash.

When two prepared actions have the same hash, EEZ cannot always select the intended occurrence. For
example, if one occurrence has a failed lookup and another has a successful execution entry, the
execution queue can match the successful entry before the failed lookup. A trigger can then receive
a result prepared for the other occurrence. Under a single-bundle design that permits outer
trigger reverts, a later identical trigger can also consume an earlier rolled-back entry.

!!! caution "TO BE DEFINED: duplicate call identity"
    Rollup0 must select one of these rules before production:

    1. **Bind an entry to the Ethereum transaction hash.** This preserves normal application calls
       and gives every occurrence an exact identity. Standard Ethereum execution does not expose
       the current transaction hash or account nonce to contracts. A hash in the blob or proof
       cannot make the EEZ queue compare against it. This option would require new Ethereum
       execution context and is not currently available. It would solve occurrence identity, but
       would not create the missing cursor for a skipped failed lookup.
    2. **Reject duplicate top-level call hashes in one candidate.** The uniqueness check covers
       both successful execution entries and failed lookups; zero-hash immediate entries are not
       call identities. This works with standard Ethereum transactions and the current proxy
       interface. Rollup0 validators and proofs can reject such a candidate while leaving EEZ
       flexible for other networks. Alternatively, EEZ can reject duplicates while posting the
       batch, which gives an on-chain check but adds gas and applies the restriction to every
       affected EEZ network unless it is configurable. Identical calls remain valid in different
       candidates.
    Treating identical calls as interchangeable is not an option. Two occurrences can have
    different results because they execute against different Rollup0 states. A later Ethereum
    transaction could otherwise receive an earlier occurrence's result and continue with L1
    behavior that was not validated for that transaction.

    Until the team selects a rule, candidates with duplicate top-level call hashes do not have a
    complete Rollup0 settlement definition.

## 7.6 Canonical Evidence

A follower uses canonical Ethereum transaction and receipt order. It verifies:

- the exact settlement transaction and ordered trigger manifest;
- successful settlement execution;
- logs from the selected EEZ deployment only;
- the Rollup0 ID;
- every processed action, `B[k]`, `R[k]`, and the resulting safe cursor; and
- the candidate's position relative to competing candidates.

An event name or matching state-root value by itself is not settlement evidence.

---

*Next: [Chapter 8, Proving and Settlement](08-proving-settlement.md).*
