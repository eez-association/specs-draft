# Appendix C. Protocol Open Questions

This informative appendix records unresolved EEZ-wide design questions. It does not fill a
network-profile selection.

## C.1 Enforced deployment domain

The action hash contains no Ethereum settlement chain ID, manager address, binding version, or
per-call nonce. The
proxy salt contains no chain or deployment term. The batch has no explicit monotonic nonce.

The current binding folds each participating manager's opaque
`getCustomData(batch.blockNumber)` result into proof inputs. A manager can use those bytes to bind a
settlement chain, `EEZ` address, profile version, and batch position, but EEZ does not require one
encoding. The binding therefore does not provide a universal deployment domain.

Open protocol questions are:

- Should a future binding require a canonical commitment to the settlement chain ID, `EEZ` address,
  rollup ID, binding version, and monotonic batch nonce?
- Which nonce or state must the contract persist to reject stale resubmission?
- How should a binding distinguish deployments that share pre-fork settlement history?
- Should action hashes also carry an explicit deployment or per-action domain?

Until a future binding answers these questions, every profile MUST define its manager custom data
and residual replay assumptions. It MUST NOT describe opaque custom data as domain separation
unless its construction and enforcement are normative.

## C.2 Proof-bound execution routing

In `eez-evm@0.2-draft`, the two transient prefix counts and `msg.sender` are absent from proof
public inputs. The contract is permissionless and uses those unbound values to select immediate,
meta-hook, discarded, and persistent routing. The current production constraint is therefore an
external, versioned mitigation selected by the network profile.

A future binding should decide whether to:

- commit both counts and an authorized submitter or submitter-policy identifier in proof inputs;
- enforce a contract allowlist or nonce;
- remove submitter-dependent meta-hook selection; or
- replace the partition with a routing rule derived entirely from proved batch content.

Any correction changes authorization or proof inputs and therefore requires a new binding edition
and activation rule.

## C.3 Cross-side construction

The current binding specifies exact local L1 and L2 state machines but does not derive one side's
objects from the other. A profile must define the relationship between:

- an observed action and the distinct L1 and L2 entries, calls, expected calls, and lookups;
- explicit inbound delivery parameters and `entries[0].incomingCalls[0]`;
- L1 state-root endpoints and network blocks;
- L1 physical custody/book accounting and L2 supply or burn; and
- partial L1 consumption and the L2 representation that remains valid.

Should a future EEZ binding make any of this mapping reusable protocol behavior, or should it
remain entirely profile-owned? If it becomes reusable, it requires cross-side vectors and an
activation rule because it can change proof inputs and execution outcomes.

## C.4 Aggregate custody

The current L1 binding enforces an entry-local accounting equation and individual book-balance
underflow checks. It does not enforce aggregate `address(EEZ).balance >= sum(etherBalance)`, does
not segregate custody, and defines no withdrawal.

Open questions are whether a future binding should:

- enforce aggregate solvency directly;
- segregate value by rollup;
- define a canonical deposit and withdrawal surface; or
- continue delegating all economic backing to network profiles.

Execution-network-specific DA, transaction-envelope, gas, candidate-admission, finality, and reorg
questions belong to the relevant network specification.
