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
- blob data availability; and
- reconstruction from archived blobs, or from peer-to-peer data checked against Ethereum.

The fixed 2-second cadence continues when an Ethereum slot is missed. The corresponding six L2
positions still exist, but no synchronous transaction can settle in the missed Ethereum slot.

An L2 block is a Sync block when it contains synchronous transactions. Otherwise, it is a pure L2
block. The sixth position can therefore contain a pure L2 block when no synchronous transaction
occurs.

Every anchor contains every L2 block since the previous anchor, including empty blocks. A composer
must anchor when a synchronous transaction occurs. It must also anchor after a maximum interval
without a synchronous transaction.

> **To be defined:** The maximum time between anchors.

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

An anchor candidate names its exact parent block hash and block number. Its state root is checked
separately. The candidate contains the complete chain from that parent to its proposed endpoint.

A candidate is applicable when it:

1. names the current Ethereum-confirmed Rollup0 parent;
2. follows the EEZ and Rollup0 rules;
3. has the required validator signatures; and
4. can complete its intended Ethereum settlement and synchronous transactions.

The first applicable candidate in canonical Ethereum transaction order advances Rollup0. Ethereum
block builders therefore control the ordering between valid candidates. This is intentional.
Sibling candidates for the old parent then become stale.

> **To be defined:** The protocol used to share candidates with validators.

## 1.3 Validation

Validators provide a best-effort service. They can reject malformed or oversized messages before
full validation. They can rate limit or ban parties that waste resources.

After fully checking a candidate, a validator signs it when it is valid. A validator can sign
several valid siblings and can finish signing a candidate after another sibling arrives. This is
not equivocation and carries no slashing risk.

Each signature is for one intended Ethereum settlement block. The first applicable candidate that
lands on Ethereum wins. Signatures for candidates that still name the old parent can no longer
advance Rollup0.

> **To be defined:** The exact Ethereum slot, block, or parent fields that bind a signature to one
> settlement block.

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

`postAndVerifyBatch` publishes and verifies the results of all Rollup0 calls before the trigger
transactions execute. Each following trigger transaction can then call its proxy and receive the
precomputed result. The complete bundle must land in one Ethereum block, in this order. Either the
whole bundle is included or none of it is included.

This is the synchronous property: each trigger transaction receives the Rollup0 result while it
executes, after the result has been prepared earlier in the same Ethereum block.

The call returns arbitrary bytes. A revert is also a result and includes its revert data. The
Ethereum transaction can make ordinary local calls and reads before and after its cross-chain call.
The Rollup0 target can make ordinary local Rollup0 calls and reads.

Cross-chain reads are not part of the current Rollup0 rules. A limited exception for cross-chain
`STATICCALL` may be added later.

> **To be defined:** Whether Rollup0 supports cross-chain `STATICCALL`, and under which rules.

Synchronous calls originating on Rollup0 and direct calls between execution networks are outside
this version. A candidate can contain ordinary Rollup0 transactions without any cross-chain call.

## 1.5 Data and Reconstruction

Rollup0 publishes anchored chain data in Ethereum blobs.

> **To be defined:** The exact blob format, versioning rules, capacity limits, and archive
> expectations.

A follower with the genesis, fixed network settings, and all historical blobs can reconstruct the
complete Rollup0 chain without help from a sequencer.

Ethereum does not retain blob data forever. When old blobs are no longer available, a follower can
fetch the missing history from peers. It must check the data against the commitments on Ethereum
and reproduce the accepted block hash and state root.

> **To be defined:** The peer-to-peer history sync protocol.

## 1.6 Conventions

The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY mark protocol requirements.

Terms defined by EEZ keep their EEZ meaning. Rollup0 terms are listed in
[Appendix A](A-reference.md). Missing decisions are marked **To be defined**.

---

*Next: [Chapter 2, Architecture](02-architecture.md).*
