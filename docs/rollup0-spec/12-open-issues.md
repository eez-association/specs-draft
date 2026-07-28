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
- **Unfinished blob format:** the required blob contents are known, but their byte-exact encoding is
  not yet defined.
- **Unsafe siblings:** local unsafe state can be replaced when another valid sibling settles first.
- **Builder dependency:** composers request one of several ordered prefixes through
  `eth_sendBundle`. The API does not prevent a builder from repackaging the signed transactions.
  The builder trust assumption or a contract-enforced alternative is still under discussion.
- **Duplicate call identity:** the rule for identical top-level cross-chain call hashes is not yet
  selected.
- **Trusted manager:** the Rollup0 manager selects the proof policy and retains the EEZ
  `setStateRoot` escape power assigned by the generic protocol.
- **Permissioned recovery:** exceptional recovery requires an authority that is not yet defined.
- **No secure in-block randomness:** the interval's Ethereum-derived `prevRandao` is predictable to
  block builders and proposer-biasable.
- **Simulation parity:** a composer and every validator/prover must simulate the exact selected EVM
  fork and protocol-transaction semantics. A mismatch makes an apparently valid candidate fail on
  Ethereum or derive a different Rollup0 block.

## 12.2 Undefined Production Choices

The following need exact definitions before production:

- Rollup0 chain ID, EEZ rollup ID, native asset, and genesis;
- the selected EEZ version;
- production contract addresses, predeploy bytecode, and upgrade rules;
- production fee-market parameters and the genesis base fee;
- the initial EVM fork and later fork-activation schedule;
- validator/prover membership, proof systems, keys, threshold, and rotation;
- proof context and domain separation;
- the protocol-transaction type, byte-exact payload, source identifier, transaction-hash vectors,
  receipt encoding, and RPC fields;
- protocol-transaction fee handling, including `GASPRICE` and receipt `effectiveGasPrice`;
- the failure-capable `EEZL2` artifact and verified-failure error ABI;
- whether to keep one protocol transaction per Ethereum trigger transaction;
- whether every protocol-level transaction failure invalidates the complete candidate;
- whether `EEZL2` keeps the selected per-transaction balance-neutrality rule;
- deterministic lowering from EEZ entries and Ethereum origin data to the protocol transaction;
- the Ethereum builder and strict prefix-bundle submission mechanism;
- the duplicate top-level cross-chain call rule;
- enforcement of one Rollup0 settlement per Ethereum block;
- maximum payload size, transaction count, and gas;
- value custody and backing;
- fee recipients, DA charging, and composer reimbursement;
- genesis-timestamp alignment to the 2-second block grid;
- deployment start block and historical upgrade boundaries; and
- reorganization history bounds and emergency authority.

These are unresolved protocol inputs. A client MUST NOT select production values by convention.

## 12.3 Possible Rollup0.x L2 Contract Changes

The initial Rollup0 network uses the `eez-core-protocol` `EEZL2` implementation without changing
it. This keeps the initial L2 contract surface aligned with the reference implementation and avoids
introducing a second contract design before genesis.

A later Rollup0.x hardfork may consider:

- clearing an inbound execution table immediately after its action completes, which removes
  inactive table data but adds storage writes;
- moving action-scoped execution data to EIP-1153 transient storage, which gives it a natural
  transaction lifetime but requires a different storage implementation; and
- replacing the array-based inbound entrypoint with one action per call, which makes the Rollup0
  protocol-transaction calldata smaller but changes the `eez-core-protocol` ABI.

These changes affect predeploy bytecode, state roots, protocol-transaction encoding, and client
conformance. They are not part of the initial Rollup0 protocol.

## 12.4 Interoperability Boundary

The fixed parts of this draft define the Rollup0 network model, normal cadence, open candidate
rules, and deterministic derivation requirements.

The undefined choices above prevent a byte-identical production genesis, inbound protocol
transaction, proof policy, and settlement path. Independent production implementations are not
interoperable until those choices are specified and accompanied by conformance vectors.

Detailed questions are listed in [Appendix C](C-open-questions.md).

---

*Next: [Appendix A, Reference](A-reference.md).*
