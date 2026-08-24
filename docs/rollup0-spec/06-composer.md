# 6. Composer and Candidate Competition

## 6.1 Open Composition

Rollup0 has no composer allowlist and no elected composer. Any party MAY construct a candidate from
the current Ethereum-confirmed Rollup0 cursor and submit it for validation.

A candidate does not gain Rollup0 protocol priority from:

- composer identity;
- arrival time at a prover;
- proof completion time;
- a fee or side payment; or
- a prover having already signed it.

Fees and side payments can affect whether an Ethereum builder includes a candidate and where the
builder places it. They do not change candidate validity. Canonical Ethereum transaction order
still determines which applicable candidate wins.

Rollup0 does not require a composer signature on a settlement candidate. A producer signature in
an unsafe block-gossip envelope can help peers filter or prioritize blocks, but it is not part of
settled validity. A completed candidate has no protocol owner and may be relayed unchanged by any
party.

## 6.2 Candidate Lifecycle

A composer:

1. derives the current Ethereum-confirmed Rollup0 block number, block hash, and state root from
   canonical Ethereum settlement evidence and local replay;
2. builds or adopts a valid pure-L2 chain from that cursor and collects and orders additional
   Rollup0 user transactions;
3. observes an Ethereum-to-Rollup0 intent when the candidate includes one;
4. simulates the complete Ethereum and Rollup0 interaction;
5. builds the Rollup0 blocks and every terminal Sync-block variant;
6. builds the EEZ batch and Rollup0 DA payload;
7. asks the prover set to verify the complete candidate and every possible applied
   synchronous prefix;
8. obtains one required set of prover signatures for the complete candidate;
9. submits the exact Ethereum prefix-bundle choices or gives them to a relayer; and
10. reconciles its unsafe blocks with canonical Ethereum settlement.

Composers may build and provers may pre-validate speculative descendants before their parent is
confirmed. A candidate submitted for final validation must nevertheless contain the complete range
from the current Ethereum-confirmed cursor. A prover must not sign a candidate whose
named parent is only an unsafe or proposed Rollup0 block.

A composer may include, exclude, and order valid pure-L2 transactions and synchronous intents. It
does not have to use arrival order, fee order, or any other fairness rule. Different valid
candidates may select and order the same pending transactions differently.

The selected order must still satisfy every Rollup0 validity rule. In particular, ordinary
pure-L2 transactions precede protocol transactions in the Sync block, sender nonces and gas limits
remain valid, and the ordered trigger manifest must match the exact Ethereum bundle choices. A
composer cannot alter a signed user transaction.

A candidate is valid for exactly one intended Ethereum child slot. Its authenticated settlement
context contains that slot's timestamp and known parent Ethereum block hash. The future child block
hash is not known and is not part of the candidate. A live candidate ends at that timestamp. A
catch-up candidate can end at an older Sync timestamp but is still bound to the current child slot.

If the target slot is missed or the Ethereum parent changes, the candidate expires. A live
candidate cannot reuse its synchronous variants. If its settled Rollup0 parent is still current,
its exact pure-L2 `B[0]` range may instead become a catch-up candidate. A catch-up composer may
also propose the same historical range again. In either case, it must bind the candidate to the
new settlement context and obtain a new set of prover signatures. Transactions reused in a newly
built live endpoint must remain valid.

The composer MAY perform these steps with any internal architecture. The resulting candidate MUST
be independently verifiable from its published inputs.

## 6.3 Candidate Validity

A prover checks at least:

- the candidate's parent block number, block hash, and state root equal the current
  Ethereum-confirmed Rollup0 cursor in the candidate's bound Ethereum settlement context;
- the target timestamp and parent Ethereum block hash name the intended child slot;
- a live endpoint equals the target timestamp, or a catch-up endpoint is older and contains no
  synchronous action;
- the block range and terminal Sync position follow Chapter 4;
- replay reproduces every complete block and its exact block hash;
- every transaction executes from the claimed parent state;
- the transaction root, receipts, receipt root, logs bloom, gas used, state root, and all header
  fields match replay;
- the EEZ batch is the exact result of that execution;
- the DA payload reconstructs the complete range;
- every protocol transaction has the required position and is byte-identical to the deterministic
  Rollup0 construction;
- every protocol transaction and typed receipt is included in the correct transaction and receipt
  root;
- every failed action has one correctly pinned L1 EEZ failed lookup, exact revert data, and no
  Rollup0 transaction;
- a failed action, when present, is the candidate's final trigger;
- `R0` and every later prefix root match independent execution; and
- every proposed Ethereum prefix bundle and the ordered trigger manifest match the simulated
  interaction.

Each prover provides this work on a best-effort basis. When it completes the checks, it signs only
a candidate that passes them. It MAY sign several valid candidates with the same parent.

One set of prover signatures covers the complete candidate, including the ordered trigger manifest
and every deterministic terminal variant `B[0]` through `B[n]`. It is not split into a separate
set of prover signatures for each prefix. The candidate data authenticated by the EEZ public-input
hash must contain everything needed to reconstruct and check every variant. Ethereum execution
then selects one of those already checked endpoints.

!!! warning "TRUST ASSUMPTION: private Ethereum triggers"
    Every prover must receive the exact signed Ethereum trigger transactions to
    reproduce the intended L1 execution and bundle. Relayers and Ethereum builders also receive
    those transactions when they handle the bundle.

    Initial Rollup0 trusts each recipient to keep the transactions private and to submit them only
    in an approved bundle whose first transaction is the matching `postAndVerifyBatch`. This is not
    enforced cryptographically.

    A recipient can leak or submit a trigger by itself. A reverting standalone transaction still
    consumes the sender's nonce and gas. If its outer call catches the missing Rollup0 result, it
    can also succeed and change Ethereum state. Users must treat this as part of Rollup0's
    permissioned-prover and private-order-flow trust model.

    Encrypted transaction delivery, threshold release, and intent-based execution are possible
    Rollup0.x designs. They are not part of the initial protocol.

!!! warning "FIXED EEZ LIMITATION: incomplete batch authentication"
    The set of prover signatures does not authenticate the batch's two transient dispatch counts.
    Chapter 5 explains how changing those unsigned fields can alter Rollup0 settlement. Until
    Rollup0 selects a mitigation, a valid signature set does not by itself authenticate every
    settlement-affecting batch field.

## 6.4 Candidate Competition

Candidates are ordered only by canonical Ethereum transaction order. When a candidate settlement
is evaluated:

1. its named parent block number, block hash, and state root must equal the current
   Ethereum-confirmed Rollup0 cursor;
2. all EEZ and Rollup0 validity checks must pass; and
3. its prover signatures must satisfy the production policy.

The first candidate that meets all three conditions advances Rollup0. A later sibling whose parent
has been superseded is stale and MUST NOT advance, even if it was valid when built or has enough
signatures.

## 6.5 Failure and Retry

A candidate that is invalid, stale, expired, or not included does not advance Rollup0. An included
prefix bundle advances Rollup0 to `B[0]` or a later `B[k]` even when the longest candidate bundle
is not selected.

A transaction that landed on canonical Ethereum or in canonical `B[k]` must not be retried. This
includes an Ethereum trigger that landed and caught a Rollup0 failure. An omitted synchronous
transaction or a transaction from a losing unsafe branch may return to a private or pure-L2 pool
only after the node revalidates it against the new canonical L1 and L2 state. Revalidation includes
its nonce, balance, gas, expiry conditions, and any state-dependent call result.

An expired or stale candidate's proof and signatures cannot be reused. A node may retain its
losing branch as noncanonical data for a possible Ethereum reorganization, but it must not keep
extending that branch as its current Rollup0 view.

A local timeout is not a settlement result. Settlement follows canonical Ethereum evidence.

---

*Next: [Chapter 7, Data Availability, Batches, and Bundles](07-da-batches-bundles.md).*
