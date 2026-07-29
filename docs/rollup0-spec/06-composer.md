# 6. Composer and Candidate Competition

## 6.1 Open Composition

Rollup0 has no composer allowlist and no elected composer. Any party MAY construct a candidate from
the current settled parent and submit it for validation.

A candidate does not gain priority from:

- composer identity;
- arrival time at a validator/prover;
- proof completion time;
- fee offered outside Ethereum; or
- a validator/prover having already signed it.

## 6.2 Candidate Lifecycle

A composer:

1. reads the current settled Rollup0 parent from canonical Ethereum state;
2. collects and orders Rollup0 user transactions;
3. observes an Ethereum-to-Rollup0 intent when the candidate includes one;
4. simulates the complete Ethereum and Rollup0 interaction;
5. builds the Rollup0 blocks and every terminal Sync-block variant;
6. builds the EEZ batch and Rollup0 DA payload;
7. asks the validator/prover set to verify the complete candidate and every possible applied
   synchronous prefix;
8. obtains the required proof or signatures;
9. submits the exact Ethereum prefix-bundle choices; and
10. reconciles its unsafe blocks with canonical Ethereum settlement.

The composer MAY perform these steps with any internal architecture. The resulting candidate MUST
be independently verifiable from its published inputs.

## 6.3 Candidate Validity

A validator/prover checks at least:

- the candidate names the exact parent from which it was built;
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

Each validator/prover provides this work on a best-effort basis. When it completes the checks, it
signs only a candidate that passes them. It MAY sign several valid candidates with the same parent.

## 6.4 Candidate Competition

Candidates are ordered only by canonical Ethereum transaction order. When a candidate settlement
is evaluated:

1. its `fromBlock` and pre-state must equal the current Ethereum-confirmed Rollup0 head;
2. all EEZ and Rollup0 validity checks must pass; and
3. its proof or validator/prover signatures must satisfy the production policy.

The first candidate that meets all three conditions advances Rollup0. A later sibling whose parent
has been superseded is stale and MUST NOT advance, even if it was valid when built or has enough
signatures.

## 6.5 Failure and Retry

A candidate that is invalid, stale, or not included does not advance Rollup0. An included prefix
bundle advances Rollup0 to `B[0]` or a later `B[k]` even when the longest candidate bundle is not
selected. Its composer MAY return eligible transactions from the unselected suffix to its local
pool after checking the canonical result.

A local timeout is not a settlement result. Settlement follows canonical Ethereum evidence.

---

*Next: [Chapter 7, Data Availability, Batches, and Bundles](07-da-batches-bundles.md).*
