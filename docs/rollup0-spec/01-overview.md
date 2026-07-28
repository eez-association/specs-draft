# 1. Overview and Scope

Rollup0 uses EEZ to settle synchronous cross-network execution on Ethereum. The
[EEZ specification](../eez-protocol-spec/index.md) defines behavior shared by EEZ networks. This
specification defines the choices made by Rollup0.

## 1.1 Rollup0 Choices

Rollup0 selects:

- Ethereum as its settlement network;
- a strict 2-second L2 block interval;
- six L2 block positions for every Ethereum slot, including a missed slot;
- open block production and composition with no composer allowlist;
- open block syncing, distribution, and RPC service with no sequencer allowlist;
- a permissioned validator set that operates on a best-effort basis;
- signing of valid sibling candidates without slashing or an equivocation penalty;
- canonical Ethereum transaction order as the candidate-selection rule;
- unsigned protocol-derived transactions for accepted inbound actions;
- blob data availability; and
- reconstruction from archived blobs, or from peer-to-peer data checked against Ethereum.

The fixed 2-second cadence continues when an Ethereum slot is missed. The corresponding six L2
positions still exist, but no synchronous transaction can settle in the missed Ethereum slot.

Every Rollup0 block can contain pure-L2 transactions. The block at the sixth position is a Sync
block, whether or not synchronous execution occurs. A Sync block places all pure-L2 transactions
before its zero or more synchronous actions. Each accepted action is represented by an unsigned
transaction derived from its Ethereum trigger.

Every anchor contains every L2 block since the previous anchor, including empty blocks. A composer
must anchor when a synchronous transaction occurs. It should also anchor after the operational
maximum interval without a synchronous transaction.

!!! note "TO BE DEFINED"
    The maximum time between anchors is not yet selected. It is an operational target, not a
    condition that can make an otherwise valid anchor invalid after it lands on Ethereum.

## 1.2 Sequencers, Composers, and L2 Views

The current working distinction is:

- a **composer** creates pure L2 and Sync blocks and prepares anchor candidates;
- a **sequencer** syncs blocks, makes them available over peer-to-peer protocols, and provides RPC
  services; and
- one party can perform both roles.

Neither role has an allowlist. A composer can extend pure L2 blocks received from another composer
or sequencer. Different composers can build different valid L2 views, and sequencers can serve
different views. A user can follow any sequencer, knowing that its view might never become
canonical.

An anchor candidate extends the Rollup0 safe head associated with the state root currently stored
in EEZ. The candidate's first block must name that safe head as its parent and use the next block
number. The candidate contains the complete chain from that parent through its terminal Sync
position.

When the candidate has `n` synchronous actions, it defines terminal block variants `B[0]` through
`B[n]`. `B[i]` contains the fixed pure-L2 prefix followed by the first `i` synchronous actions. The
Ethereum outcome selects one of these variants as the candidate's exact endpoint.

Validators and followers check the parent block hash and number from the published block data. The
proof system must enforce the same rule before accepting the candidate. The EEZ contract checks the
starting state root separately; it does not store or check the Rollup0 parent block hash or number.

!!! note "TO BE DEFINED"
    The proof system will check the exact parent block hash and number. The team still needs to
    decide how the blob format carries them.

    - An explicit parent record makes the anchor easy to inspect, but repeats data available from
      the first block header.
    - Deriving them from the first block header and the safe cursor uses less data, but puts more
      responsibility on the decoder.

A candidate is applicable when it:

1. extends the current Ethereum-confirmed Rollup0 safe head;
2. follows the EEZ and Rollup0 rules;
3. has the required validator signatures; and
4. can establish `R0` and defines every possible synchronous prefix correctly.

The first applicable candidate in canonical Ethereum transaction order advances Rollup0. Ethereum
block builders therefore control the ordering between valid candidates. This is intentional.
Sibling candidates for the old parent then become stale.

!!! note "TO BE DEFINED"
    The protocol used to share candidates with validators is not yet selected.

## 1.3 Validation

Validators provide a best-effort service. They can reject malformed or oversized messages before
full validation. They can rate limit or ban parties that waste resources.

After fully checking a candidate, a validator signs it when it is valid. A validator can sign
several valid siblings and can finish signing a candidate after another sibling arrives. This is
not equivocation and carries no slashing risk.

Each signature is for one intended Ethereum settlement block. The first applicable candidate that
lands on Ethereum wins. Signatures for candidates that still name the old parent can no longer
advance Rollup0.

!!! note "TO BE DEFINED"
    The exact Ethereum slot, block, or parent fields that bind a signature to one settlement block
    are not yet selected.

Rollup0 has no force-inclusion path. A valid empty candidate can win while excluding pending
transactions. Force inclusion and TEE-backed validators are possible features for Rollup0.x, not
this version.

## 1.4 Cross-Network Scope

Each Ethereum transaction can make at most one cross-chain call into Rollup0. A candidate can
contain several Ethereum transactions that each make one such call.

For synchronous transactions, the composer submits this ordered Ethereum bundle through
`eth_sendBundle`:

```text
[postAndVerifyBatch, trigger1, trigger2, ...]
```

`postAndVerifyBatch` publishes and verifies the possible results of all Rollup0 calls before the
trigger transactions execute. Each following trigger transaction can then call its proxy and
receive its precomputed result.

The settlement mechanism must include `postAndVerifyBatch` and a strict prefix of the ordered
trigger transactions in one Ethereum block. Every included outer trigger transaction must succeed
and execute its expected proxy call. Chapter 7 discusses how the composer can submit these prefix
choices through atomic bundles.

`eth_sendBundle` requests this behavior from a builder; Ethereum does not enforce bundle membership.
Chapter 7 marks the choice between trusting compatible builders and adding protocol enforcement as
**To be defined**.

Let `R0` be the state root after the fixed pure-L2 prefix and before any synchronous action. Let
`R[i]` be the root after the first `i` synchronous actions. A synchronous action that returns a
caught revert leaves `R[i]` equal to `R[i - 1]`.

`postAndVerifyBatch` establishes `R0`. The canonical endpoint is `B[k]`, where `k` is the number of
included trigger transactions. A trigger outside the selected prefix does not remove the pure-L2
transactions or the earlier actions. Chapter 7 defines this processing and the unresolved rule for
identical cross-chain call hashes.

This is the synchronous property: each trigger transaction receives the Rollup0 result while it
executes, after the result has been prepared earlier in the same Ethereum block.

The call returns arbitrary bytes. A revert is also a result and includes its revert data. The
Ethereum transaction can make ordinary local calls and reads before and after its cross-chain call.
The Rollup0 target can make ordinary local Rollup0 calls and reads.

Cross-chain reads are not part of the current Rollup0 rules. A limited exception for cross-chain
`STATICCALL` may be added later.

!!! note "TO BE DEFINED"
    Whether Rollup0 supports cross-chain `STATICCALL`, and under which rules, is not yet selected.

Synchronous calls originating on Rollup0 and direct calls between execution networks are outside
this version. A candidate can contain ordinary Rollup0 transactions without any cross-chain call.

## 1.5 Data and Reconstruction

Rollup0 publishes anchored chain data in Ethereum blobs.

!!! note "TO BE DEFINED"
    The exact blob format, versioning rules, capacity limits, and archive expectations are not yet
    selected.

A follower with the genesis, fixed network settings, and all historical blobs can reconstruct the
complete Rollup0 chain without help from a sequencer.

Ethereum does not retain blob data forever. When old blobs are no longer available, a follower can
fetch the missing history from peers. It must check the data against the commitments on Ethereum
and reproduce the accepted block hash and state root.

!!! note "TO BE DEFINED"
    The peer-to-peer history sync protocol is not yet selected.

## 1.6 Conventions

The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY mark protocol requirements.

Terms defined by EEZ keep their EEZ meaning. Rollup0 terms are listed in
[Appendix A](A-reference.md). Missing decisions are marked **To be defined**.

---

*Next: [Chapter 2, Architecture](02-architecture.md).*
