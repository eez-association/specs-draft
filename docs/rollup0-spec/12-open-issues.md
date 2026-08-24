# 12. Limitations and Open Issues

## 12.1 Protocol Limitations

- **Permissioned validity:** candidate production and relay are open, but settlement depends on a
  permissioned prover set.
- **No force inclusion:** the protocol does not guarantee that a valid candidate reaches or is
  included by Ethereum.
- **No trustless exit:** a follower can detect invalid history but cannot reverse Ethereum
  settlement or force a withdrawal.
- **One cross-network direction:** only one top-level Ethereum-to-Rollup0 state-changing call is
  selected.
- **Unfinished blob format:** the required blob contents are known, but their byte-exact encoding is
  not yet defined.
- **Unfinished catch-up limits:** historical catch-up anchors are defined, but the DA limits,
  minimum recovery rate, lag thresholds, and backpressure policy are not.
- **Unsafe siblings:** local unsafe state can be replaced when another valid sibling settles first.
- **Builder dependency:** composers request one of several ordered prefixes through
  `eth_sendBundle`. The API does not prevent a builder from repackaging the signed transactions.
  The builder trust assumption or a contract-enforced alternative is still under discussion.
- **Private trigger trust:** provers, relayers, and builders receive signed Ethereum trigger
  transactions before inclusion. Initial Rollup0 trusts them not to leak or submit those
  transactions outside an approved bundle.
- **Duplicate call identity:** the rule for identical top-level cross-chain call hashes is not yet
  selected.
- **Trusted manager:** the Rollup0 manager selects the proof policy and retains the EEZ
  `setStateRoot` escape power assigned by the generic protocol.
- **Permissioned recovery:** exceptional recovery requires an authority that is not yet defined.
- **No secure in-block randomness:** anchor-derived `prevRandao` is predictable after the anchor
  seed is known. Deriving a different value for each block adds no entropy; copying the seed
  unchanged, as the OP Stack does within an L1-origin epoch, makes the same limitation explicit.
- **Simulation parity:** a composer and every prover must simulate the exact selected EVM
  fork and protocol-transaction semantics. A mismatch makes an apparently valid candidate fail on
  Ethereum or derive a different Rollup0 block.
- **Unsigned EEZ dispatch counts:** the fixed EEZ proof digest does not bind the transient
  execution-entry or lookup counts. Rollup0 requires exact values, but a relayer can change them
  without invalidating prover signatures. The mitigation is not yet selected.

## 12.2 Undefined Production Choices

The following need exact definitions before production:

- Rollup0 chain ID, EEZ rollup ID, native asset, genesis, and initial RANDAO seed;
- whether `prevRandao` uses the current per-block derivation or copies the live-anchor seed
  unchanged;
- the selected EEZ version;
- production contract addresses, predeploy bytecode, and upgrade rules;
- the genesis base fee;
- the post-Fusaka EVM fork-activation schedule;
- prover membership, proof systems, keys, threshold, and rotation;
- proof context and domain separation;
- the protocol-transaction type, byte-exact payload, source identifier, transaction-hash vectors,
  receipt encoding, and RPC fields;
- protocol-transaction fee handling, including `GASPRICE` and receipt `effectiveGasPrice`;
- deterministic failed-lookup construction and validation for caught Rollup0 failures;
- whether to keep one protocol transaction per successful Ethereum trigger;
- whether every protocol-level transaction failure invalidates the complete candidate;
- whether `EEZL2` keeps the selected per-transaction balance-neutrality rule;
- deterministic lowering from EEZ entries and Ethereum origin data to the protocol transaction;
- the Ethereum builder and strict prefix-bundle submission mechanism;
- whether a later version permits actions after a caught failure by trusting exact builder ordering
  or by adding a unified on-chain action cursor;
- enforcement that the leading anchor-root transition either applies or reverts;
- enforcement of the fixed Rollup0 transient dispatch counts without changing EEZ;
- the duplicate top-level cross-chain call rule;
- enforcement of one EEZ batch that contains Rollup0 per Ethereum block, or equivalent queue
  integrity;
- maximum payload size, transaction count, and gas;
- catch-up range limits, recovery-rate requirements, lag thresholds, and transaction-intake
  backpressure;
- the later dedicated-vault design, including liquidity, yield, losses, and withdrawals;
- fee recipients, DA charging, and composer reimbursement;
- deployment start block and historical upgrade boundaries; and
- reorganization history bounds and emergency authority.

These are unresolved protocol inputs. A client MUST NOT select production values by convention.

## 12.3 Possible Rollup0.x L2 Contract Changes

The initial Rollup0 network uses the `eez-core-protocol` `EEZL2` implementation without changing
it. This keeps the initial L2 contract surface aligned with the reference implementation and avoids
introducing a second contract design before genesis.

A later Rollup0.x hardfork may consider:

- enabling synchronous actions originating on Rollup0, routing them from sequencers to composers,
  and then extending the profile to full nested composability in both directions;
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
