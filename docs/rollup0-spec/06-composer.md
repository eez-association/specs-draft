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
5. builds the Rollup0 blocks and terminal Sync block;
6. builds the EEZ batch and Rollup0 DA payload;
7. asks the validator/prover set to verify the complete candidate;
8. obtains the required proof or signatures;
9. submits the exact Ethereum bundle; and
10. reconciles its unsafe blocks with canonical Ethereum settlement.

The composer MAY perform these steps with any internal architecture. The resulting candidate MUST
be independently verifiable from its published inputs.

## 6.3 Candidate Validity

A validator/prover checks at least:

- the candidate names the exact parent from which it was built;
- the block range and terminal Sync position follow Chapter 4;
- every block and header is valid;
- every transaction executes from the claimed parent state;
- the EEZ batch is the exact result of that execution;
- the DA payload reconstructs the complete range;
- the system transaction is byte-identical to the deterministic Rollup0 construction;
- the proposed Ethereum bundle matches the simulated interaction.

Each validator/prover MUST sign every candidate it receives that passes these checks. It MAY sign
several valid candidates with the same parent.

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

A candidate that is invalid, stale, not included, or whose bundle cannot execute does not advance
Rollup0. Its composer MAY return eligible user transactions to its local pool after checking the
canonical winning candidate.

A local timeout is not a settlement result. Settlement follows canonical Ethereum evidence.

---

*Next: [Chapter 7, Data Availability, Batches, and Bundles](07-da-batches-bundles.md).*
