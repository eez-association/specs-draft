# 5. Execution Profile

EEZ defines execution entries, lookups, state deltas, rolling hashes, value accounting, proxy
calls, and settlement consumption. Rollup0 uses those rules without changing their wire formats.
See [EEZ Execution Model](../eez-protocol-spec/03-execution-model.md).

## 5.1 Selected EEZ Subset

Rollup0 selects this subset:

- one top-level state-changing Ethereum-to-Rollup0 call per interaction;
- one return value;
- read-only EEZ lookups;
- no direct execution-network-to-execution-network action;
- no cross-network reentrancy;
- no nested cross-network action; and
- no synchronous action originating on Rollup0.

Ordinary nested calls that remain on one network are allowed.

## 5.2 Rollup0 State Transition

For each candidate, the composer and every validator/prover independently:

1. execute the ordered user transactions from the named Rollup0 parent;
2. construct the terminal Sync block;
3. insert the deterministic inbound system transaction when required;
4. execute the complete range;
5. derive the EEZ entries, lookups, state deltas, return data, and value changes from that
   execution; and
6. require the final EEZ state commitment to equal the Sync block state root.

The proof or signatures cover the EEZ public-input hash, including commitments to the execution
entries, lookups, and Rollup0 DA payload. A supplied root or return value is not trusted without
re-execution. Fields outside that EEZ digest still require the checks selected by this
specification; their domain binding is an open question in Appendix C.

## 5.3 Required Invariants

A valid candidate preserves all EEZ invariants, including:

- the current state in each state delta equals the state committed before the effect;
- state deltas form one continuous state transition;
- the rolling hash matches the exact call order, results, and return data;
- every expected call and lookup is consumed exactly once;
- value is conserved under the EEZ accounting rules; and
- the accepted Rollup0 endpoint equals independently executed Rollup0 state.

A candidate that fails an EEZ invariant is invalid regardless of how many parties signed it.

## 5.4 Failed Calls

An ordinary EVM revert is part of execution. Its receipt, gas use, state rollback, and return data
are handled by the selected EVM and EEZ rules.

The candidate remains valid only when every composer-supplied result exactly matches independent
execution. This specification does not add a retry or cross-transaction rollback rule.

---

*Next: [Chapter 6, Composer and Candidate Competition](06-composer.md).*
