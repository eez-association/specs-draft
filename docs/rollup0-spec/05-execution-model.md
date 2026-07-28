# 5. Execution Profile

EEZ defines execution entries, lookups, state deltas, rolling hashes, value accounting, proxy
calls, and settlement consumption. Rollup0 uses those rules without changing their wire formats.
See [EEZ Execution Model](../eez-protocol-spec/03-execution-model.md).

## 5.1 Selected EEZ Subset

Rollup0 selects this subset:

- one top-level state-changing Ethereum-to-Rollup0 call per Ethereum transaction;
- one return value;
- no cross-network lookup unless the `STATICCALL` extension in Chapter 1 is selected;
- no direct execution-network-to-execution-network action;
- no cross-network reentrancy;
- no nested cross-network action; and
- no synchronous action originating on Rollup0.

Ordinary nested calls that remain on one network are allowed.

## 5.2 Rollup0 State Transition

For each candidate, the composer and every validator/prover independently:

1. execute every block after the named Rollup0 parent;
2. execute the terminal block's pure-L2 transactions and record `R0`;
3. execute each synchronous action in its intended Ethereum trigger order;
4. construct `B[i]` and record `R[i]` after each action `i`;
5. represent a successful Ethereum-side result with its EEZ execution entry and a reverting result
   with its failed lookup;
6. derive the state deltas, return data, and value changes for every prefix; and
7. require the EEZ state sequence to be `R0, R[1], ..., R[n]`.

`R0` is the Sync-block root when no synchronous action is processed. For a successful action
`i`, its EEZ entry requires `R[i - 1]` and produces `R[i]`. For a reverting action, the Rollup0
`EEZL2` contract verifies the application failure and then reverts its outer call with the
dedicated verified-failure error. The protocol transaction receives status `0` and leaves no
persistent Rollup0 state or value change. Therefore `R[i]` MUST equal `R[i - 1]`. `B[i]` remains
distinct because its transaction root includes the transaction and its receipt root includes the
failed receipt. The pure-L2 transactions are identical in every possible block variant.

The transaction root commits the exact protocol transaction and its position. The receipt root
commits its status, cumulative gas use, bloom, and logs. Exact return or revert data remains
committed by the EEZ execution data and is checked by deterministic replay; Ethereum-style
receipts do not contain return data.

The proof or signatures cover the EEZ public-input hash, including commitments to the execution
entries, lookups, and Rollup0 DA payload. A supplied root or return value is not trusted without
re-execution. Fields outside that EEZ digest still require the checks selected by this
specification; their domain binding is an open question in Appendix C.

## 5.3 Required Invariants

A valid candidate preserves all EEZ invariants, including:

- the current state in each state delta equals the state committed before the effect;
- state deltas form one continuous state transition;
- `R0` contains the complete pure-L2 prefix and no synchronous effect;
- every `B[i]` contains exactly the first `i` synchronous actions;
- the rolling hash matches the exact call order, results, and return data;
- every expected successful call is consumed in replay;
- every expected failed lookup returns its exact committed revert data in replay;
- value is conserved under the EEZ accounting rules; and
- the accepted `B[i]` header and state equal independent Rollup0 execution.

A candidate that fails an EEZ invariant is invalid regardless of how many parties signed it.

## 5.4 Failed Calls

An ordinary Rollup0 call failure is a possible precomputed result. This includes `REVERT` and an
exceptional halt such as an out-of-gas inside the target call. `EEZL2` verifies the target result
and its exact data before returning the dedicated verified-failure error. Rollup0 recognizes that
error as a completed failed protocol transaction with receipt status `0` and rolls back its
complete EVM frame. EEZ returns the committed failure data on Ethereum through a failed lookup. If
the outer Ethereum transaction catches that failure and succeeds, the synchronous action is
processed and the next trigger can execute. The failed protocol transaction leaves no persistent
state, value movement, or log.

When the outer Ethereum trigger transaction reverts, any EEZ consumption and state update in that
transaction also reverts. Under the intended atomic-bundle rule, a bundle containing that trigger is
ineligible and a selected shorter bundle contains no later trigger. Chapter 7 describes the current
builder trust assumption and the unresolved enforcement design.

The candidate remains valid only when every composer-supplied result, `B[i]`, and prefix root
exactly matches independent execution.

---

*Next: [Chapter 6, Composer and Candidate Competition](06-composer.md).*
