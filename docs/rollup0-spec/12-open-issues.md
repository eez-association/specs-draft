# 12. Limitations and Open Issues

## 12.1 Protocol Limitations

- **Permissioned validity:** candidate production and relay are open, but settlement depends on a
  permissioned validator/prover set.
- **No force inclusion:** the protocol does not guarantee that a valid candidate reaches or is
  included by Ethereum.
- **No trustless exit:** a follower can detect invalid history but cannot reverse Ethereum
  settlement or force a withdrawal.
- **One cross-network direction:** only one top-level Ethereum-to-Rollup0 state-changing call is
  selected.
- **Calldata-only DA:** no blob encoding or fallback DA channel is defined.
- **Unsafe siblings:** local unsafe state can be replaced when another valid sibling settles first.
- **Builder dependency:** synchronous execution depends on ordered, all-or-none inclusion of the
  settlement and trigger transactions.
- **Trusted manager:** the Rollup0 manager selects the proof policy and retains the EEZ
  `setStateRoot` escape power assigned by the generic protocol.
- **Permissioned recovery:** exceptional recovery requires an authority that is not yet defined.
- **No secure in-block randomness:** the interval's Ethereum-derived `prevRandao` is predictable to
  block builders and proposer-biasable.
- **Simulation parity:** a composer and every validator/prover must simulate the exact Cancun gas
  and execution semantics. A mismatch makes an apparently valid candidate fail on Ethereum or
  derive a different Rollup0 block.

## 12.2 Undefined Production Choices

The following need exact definitions before production:

- Rollup0 chain ID, EEZ rollup ID, native asset, and genesis;
- the selected EEZ version;
- production contract addresses, predeploy bytecode, and upgrade rules;
- production fee-market parameters and the genesis base fee;
- validator/prover membership, proof systems, keys, threshold, and rotation;
- proof context and domain separation;
- the `0x7e` system-transaction envelope, authorization, nonce, gas, and value source;
- deterministic lowering from EEZ entries to the system transaction;
- the Ethereum bundle builder or inclusion mechanism;
- maximum payload size, transaction count, and gas;
- value custody and backing;
- fee recipients, DA charging, and composer reimbursement;
- genesis-timestamp alignment to the 2-second block grid;
- deployment start block and historical upgrade boundaries; and
- reorganization history bounds and emergency authority.

These are unresolved protocol inputs. A client MUST NOT select production values by convention.

## 12.3 Interoperability Boundary

The fixed parts of this draft define the Rollup0 network model, normal cadence, open candidate
rules, calldata codec, and deterministic derivation requirements.

The undefined choices above prevent a byte-identical production genesis, Sync system transaction,
proof policy, and settlement path. Independent production implementations are not interoperable
until those choices are specified and accompanied by conformance vectors.

Detailed questions are listed in [Appendix C](C-open-questions.md).

---

*Next: [Appendix A, Reference](A-reference.md).*
