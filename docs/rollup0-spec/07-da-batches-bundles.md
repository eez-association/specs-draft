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

Execution-derived fields do not need separate encodings. A follower derives each transaction root,
receipt, receipt root, logs bloom, gas-used value, state root, header, and block hash from the
published inputs. Any redundant claimed value must equal the replayed value.

The manifest binds each trigger by its Ethereum transaction hash and position. Provers receive
the complete signed transactions and verify that they reproduce the manifest and the proposed
`eth_sendBundle` payload. A transaction-hash commitment in the manifest does not make that hash
available to the EEZ contract during execution.

!!! note "TO BE DEFINED"
    The byte-exact blob format, its versioning rule, capacity limits, and conformance vectors are
    not yet defined. It must also define the exact candidate-domain fields and how they are divided
    between the blob, EEZ batch, and manager `customData`. Appendix D lists the required fields but
    does not yet define an encoding.

## 7.2 Range Correspondence

Let `fromBlock` be the candidate's named settled parent and `toNumber` its terminal block number.
The payload covers exactly:

```text
(fromBlock.number, toNumber]
```

The published data binds `fromBlock` and defines terminal variants `B[0]` through `B[n]`. Every
variant has block number `toNumber`, the same timestamp, the same pure-L2 prefix, and exactly its
protocol transactions for successful actions among the first `i` Ethereum triggers. A failed
action adds no Rollup0 transaction, so adjacent variants can be identical. Candidate validation
checks every variant against the current Ethereum-confirmed Rollup0 head. A failed action must be
the final action in the manifest.

`R[0]` means `R0`, the state root of `B[0]`.

A live candidate has a terminal timestamp equal to its intended Ethereum settlement timestamp. A
catch-up candidate has an older terminal timestamp, only the `B[0]` variant, and an empty trigger
manifest. It contains no inbound protocol transaction or failed lookup. A terminal timestamp later
than the intended Ethereum settlement timestamp is invalid. The relationship between the two
timestamps determines the anchor form; the blob does not need a separate mode flag.

The following must agree:

- the number of encoded block boundaries equals `toNumber - fromBlock.number`;
- the first encoded block is `fromBlock.number + 1`;
- the last encoded block has number `toNumber`;
- the terminal timestamp follows the live or catch-up rule above;
- every user transaction appears once in its selected block;
- every required L2 entry corresponds to one exact successful EEZ action;
- every failed action corresponds to one exact failed EEZ lookup and no L2 transaction; and
- replay from `fromBlock` produces every `B[i]` and `R[i]`.

!!! caution "TO BE DISCUSSED: catch-up capacity and backpressure"
    Historical catch-up works only when each published range fits the Ethereum blob limits and the
    backlog drains faster than new Rollup0 data is created. At minimum, the data for one complete
    six-position interval must always fit in one valid catch-up candidate. Otherwise no catch-up
    anchor can advance the cursor.

    The byte-exact blob format must set per-block, per-interval, and per-candidate data limits. It
    must also leave enough publication capacity during recovery for old data to be published
    faster than composers create new unsafe data. These limits are not yet defined.

    If one interval cannot be guaranteed to fit, the team must either lower Rollup0's data limits
    or permit smaller historical ranges that do not end at a Sync position. The second option
    would change the anchor rule in Chapter 4 and is not part of the current design.

    If the available rate is too low, block positions and timestamps still advance. Until an
    objective validity limit is selected, a composer that wants its unsafe view to remain
    anchorable SHOULD reduce or stop pure-L2 transaction intake until the lag shrinks. It cannot
    force other open composers to do the same. Synchronous actions cannot settle through a
    catch-up anchor. The team must decide the lag thresholds, how clients report them, and which
    backpressure rules are protocol validity rules rather than operational policy.

!!! caution "TO BE DISCUSSED: historical production evidence"
    The current rules prove that a catch-up range forms a valid chain with the scheduled
    timestamps. They do not prove that its blocks were produced or gossiped at those times. An
    open composer can build a competing historical range later and include transactions that it
    received after the claimed block timestamps. If Ethereum selects that candidate, applications
    observe those scheduled historical timestamps through the EVM.

    A local first-seen rule cannot solve this because different nodes can see different blocks.
    The direct options are to accept that a Rollup0 timestamp is a scheduled chain position rather
    than proof of publication time, require timely attestations that are retained through an
    outage, or precommit block data to Ethereum or another agreed timestamping system. Timely
    attestations add a new availability and trust requirement. Precommitment adds cost and may be
    unavailable during the same outage. Initial Rollup0 has not selected an option.

## 7.3 EEZ Batch

The settlement transaction carries the batch object defined by
[EEZ Proving and Settlement](../eez-protocol-spec/04-proving-and-settlement.md).
An initial Rollup0 batch SHOULD contain only Rollup0. This keeps candidate validation and failure
handling independent from other EEZ networks.

A batch MAY also contain another EEZ network when all of these conditions hold:

- `transientExecutionEntryCount` remains exactly `1`, and the one transient entry is Rollup0's
  leading `A -> R0` entry;
- `transientLookupCallCount` remains exactly `0`;
- every entry, lookup, state delta, and queue item that names, pins, routes to, or changes Rollup0
  is part of the Rollup0 candidate and follows this specification;
- data for another network cannot change the Rollup0 block range, action order, state sequence, or
  selected endpoint;
- every included network accepts the shared `blockNumber = 2^64 - 1` current context; and
- every proof required by the shared EEZ batch succeeds.

These rules allow cost sharing but do not enable execution-network-to-execution-network calls in
initial Rollup0. A network that needs another transient layout cannot share this batch.

Every Rollup0 batch also requires:

- `blockNumber = 2^64 - 1` to select the authenticated current Ethereum settlement context;
- no other EEZ batch that contains Rollup0 in the same Ethereum block;
- the selected blobs to be referenced by the batch;
- no duplicate or unrelated blob index;
- proof context bound to the intended Ethereum settlement domain;
- Rollup0 state deltas derived from `R0` and every successful synchronous action;
- enough L2 entries and origin data to reconstruct every protocol transaction; and
- the prover signatures required by Chapter 8.

Rollup0 does not redefine the EEZ batch tuple or public-input hash.

## 7.4 Ethereum Bundle

Every settlement choice uses this order:

```text
bundle[k] = [postAndVerifyBatch, trigger1, ..., triggerK]
```

`postAndVerifyBatch` publishes and verifies the candidate and establishes `R0`. Each `trigger`
is an exact Ethereum transaction whose cross-chain proxy call can consume the next prepared EEZ
action.

A Rollup0-only catch-up candidate has `n = 0`, so its only bundle is
`[postAndVerifyBatch]`. A Rollup0-only live candidate without a synchronous action uses the same
one-transaction bundle. In a permitted shared batch, Rollup0 contributes no trigger transaction
in either case. Transactions required by another network follow that network's specification and
must not affect Rollup0.

The intended settlement is the exact atomic inclusion of one submitted `bundle[k]`. Every included
outer trigger transaction must succeed. Deterministic replay must show that each one made its exact
expected proxy call and received the committed success or revert result. If `bundle[k]` is included
without modification, the canonical endpoint is `B[k]` with state root `R[k]`. When trigger `k`
contains a caught Rollup0 failure, it must also be trigger `n`, the final action in the candidate.

For a successful Rollup0 result, the follower checks the retained EEZ consumption and state-update
logs. For a Rollup0 revert caught by the Ethereum caller, the failed EEZ frame leaves no retained
log. The follower must replay the exact Ethereum transaction to verify that the expected proxy call
occurred and returned the committed revert data. A successful Ethereum receipt alone is not enough.

`eth_sendBundle` is a builder API, not an Ethereum consensus rule. A public-mempool submission is
not a valid replacement for the required same-block ordering.

The exact signed trigger transactions remain private before inclusion. Provers, relayers, and
builders that receive them are trusted not to leak or submit them separately. Chapter 6 states the
consequences and scope of this trust assumption.

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
       not enforce the required prefix with the current contracts. It permits an Ethereum trigger
       outcome that differs from the signed manifest without making settlement revert. This option
       is not valid unless option 2 supplies the missing enforcement.

    An `eth_sendBundle` request is not visible to the EVM. Even with option 1, a builder that has the
    signed transactions can omit one trigger or add another transaction outside the submitted
    bundle. A skipped successful execution entry remains at the EEZ queue head and blocks a later
    trigger with a different call hash, even if that entry would not change the state root. A failed
    lookup is not part of that queue and leaves no persistent cursor. Initial Rollup0 therefore
    requires it to be the final prepared action. Duplicate call hashes can still let another
    transaction receive a result prepared for the intended occurrence.

    A unified cursor would enforce prefixes without requiring all combinations of triggers or state
    roots. It does not work by itself for caught failures: the proxy reports failure with `REVERT`,
    which rolls back the cursor update. A compatible acknowledgement mechanism has not been
    designed.

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
example, a valid candidate can contain a successful action followed by a terminal failed action
with the same hash. If a builder omits the first trigger, the terminal trigger can match the
successful execution entry before the failed lookup and receive the wrong result. Under a
single-bundle design that permits outer trigger reverts, a later identical trigger can also consume
an earlier rolled-back entry.

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
       interface. Rollup0 provers can reject such a candidate while leaving EEZ
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
