# 12. Limitations and Open Issues

## 12.1 Accepted Protocol Limitations

- **Permissioned validity and Ethereum custody:** candidate production and relay are open, but
  settlement depends on a permissioned validator/prover set. A conforming follower independently
  executes an accepted candidate and halts if its claimed result is invalid, so the threshold
  cannot silently fabricate the follower's Rollup0 history. It can nevertheless authorize
  unjustified Ethereum-side EEZ results, corrupt dependent applications, and drain assets they
  control. Threshold compromise is catastrophic and follower detection cannot reverse those L1
  effects.
- **Validator liveness authority:** no candidate can settle without `N` timely attestations. The
  service is best effort and has no force-inclusion or fallback proof path. In particular,
  `M <= 3` requires unanimity, so one unavailable member halts anchoring, synchronous execution,
  safe-head progress, and any withdrawal path that depends on new finalized anchors.
- **No force inclusion:** the protocol does not guarantee that a valid candidate reaches or is
  included by Ethereum.
- **One cross-network direction:** V1 supports top-level state-changing actions from Ethereum to
  Rollup0 only. A candidate may contain an ordered sequence of these actions, with exactly one
  top-level Rollup0 action in each trigger. Top-level Rollup0-to-Ethereum actions are not supported.
- **No L2 blob transactions:** Rollup0 uses Ethereum blobs for L1 data availability but does not
  provide a beacon sidecar network for blob transactions inside Rollup0 blocks.
- **Historical data availability:** standard P2P block and state synchronization does not require
  blob archives, but ordinary pruning can make old bodies, receipts, and historical states
  unavailable. Historical RPC requires normal Rollup0 archive nodes.
- **Scheduled catch-up timestamps:** a catch-up block's timestamp identifies its scheduled
  Rollup0 position, not when the block was first produced or gossiped. Ethereum settlement
  determines when the position becomes safe and finalized.
- **No candidate-cost reimbursement:** ordinary priority fees are the only protocol-level producer
  revenue currently defined. Rollup0 does not guarantee reimbursement for construction,
  validation, proving, DA, settlement, retries, or losing siblings.
- **Unanchorable unsafe branches:** an unsafe range that cannot fit a valid blob-backed candidate
  never becomes safe. A composer can rebuild a smaller sibling from the settled cursor, but nodes
  following the oversized branch experience an unsafe reorganization.
- **Unsafe siblings:** local unsafe state can be replaced when another valid sibling settles first.
- **Private trigger trust:** validators, relayers, and builders receive signed Ethereum trigger
  transactions before inclusion. They are trusted not to leak them. Ordered-call identity keeps a
  substituted matching call consistent with Rollup0, but it cannot prevent a leaked transaction
  from being included on Ethereum and producing ordinary L1 effects.
- **No blob triggers:** an Ethereum trigger cannot be an EIP-4844 blob transaction or otherwise
  require a blob sidecar. `submitCandidate` is the candidate's blob transaction.
- **Trusted manager:** the Rollup0 manager selects the proof policy and retains the EEZ
  `setStateRoot` escape power assigned by the generic protocol. Despite its legacy name, this
  function sets Rollup0's block-hash commitment. An out-of-protocol use changes Ethereum-side EEZ
  state but is not automatically accepted by Rollup0 followers.
- **Community hardfork recovery:** ordinary non-finalized reorganizations return to the latest
  finalized Ethereum checkpoint and have no separate Rollup0 depth limit. A conflict with
  finalized Rollup0 history has no privileged in-protocol recovery authority; followers halt until
  a community-coordinated hardfork defines a new authenticated checkpoint.
- **No secure in-block randomness:** each interval copies `prevRandao` from an earlier Ethereum
  block whose value is already known before the interval starts. All six positions repeat it, so
  applications must not treat it as fresh or unpredictable entropy.
- **Simulation parity:** a composer and every validator/prover must simulate the exact selected EVM
  fork and protocol-transaction semantics. A mismatch makes an apparently valid candidate fail on
  Ethereum or derive a different Rollup0 block.
- **Settlement-wrapper dependency:** the fixed EEZ proof digest does not bind the transient-prefix
  lengths, and EEZ does not revert when the leading anchor entry is skipped. Rollup0 therefore
  requires its manager-gated settlement wrapper. Direct EEZ submission is invalid.
- **Pooled EEZ custody:** permissionless sibling-rollup registration shares the EEZ contract's
  physical ETH balance. Safety relies on Rollup0's proof authorization and manager-gated batch
  scope, together with EEZ's per-entry ether conservation and per-rollup balance-underflow checks.
  The arithmetic checks alone do not prevent a transfer of backing between rollup ledgers.
  A dedicated vault could provide clearer physical isolation but is not part of V1.
- **Legacy EEZ terminology:** the current contracts call Rollup0's opaque block-hash commitment a
  state root. The encoding is unambiguous and does not block production, but a later EEZ revision
  should use commitment-oriented names.

## 12.2 Production Blockers and Launch Parameters

The following are not accepted V1 limitations. They need exact definitions or implementations
before production:

- Rollup0 chain ID, EEZ rollup ID, `FEE_COLLECTOR` address, genesis, and finalized Ethereum
  RANDAO reference block;
- the unsafe-block announcement P2P mapping and conformance vectors;
- the selected and pinned EEZ Core version, including the exact `getCustomData` public-input fold
  and complete physical blob-message stream;
- an end-to-end `publicInputsHash` vector and full-blob vectors for that EEZ version;
- the initial validator/prover membership, proof-system keys, and manager configuration;
- production contract addresses, predeploy bytecode, and upgrade rules;
- comprehensive conformance vectors for the normative byte-exact blob payload format;
- protocol-transaction, receipt, execution, RPC, and invalid-input conformance vectors;
- deterministic failed-lookup construction and validation for caught Rollup0 failures;
- deterministic lowering from the settlement context, action manifest, and EEZ entries to the
  protocol transaction;
- the asynchronous ETH withdrawal authorization, confirmation, payout, and replay rules;
- the Ethereum builder API and operational prefix-bundle submission policy;
- the composer-to-execution-client construction interface when composition is not in process;
- the transaction-scoped L1 EEZ guard and its conformance vectors;
- catch-up recovery-rate and intake-backpressure reporting;
- deployment start block and historical upgrade boundaries.

Consensus and wire-format values require normative specification and conformance vectors.
Deployment-specific addresses, builder integrations, and operational policies require published
network configuration. A client MUST NOT invent missing consensus values by convention.

## 12.3 Possible Rollup0.x L2 Contract Changes

The initial Rollup0 network uses the `eez-core-protocol` `EEZL2` implementation without changing
it. This keeps the initial L2 contract surface aligned with the reference implementation and avoids
introducing a second contract design before genesis.

A later Rollup0.x hardfork may consider:

- enabling synchronous actions originating on Rollup0, routing them from sequencers to composers,
  and then extending the profile to full nested composability in both directions;
- adding an Ethereum-initiated synchronous withdrawal claim against ETH previously locked in a
  Rollup0 withdrawal escrow;
- activating a new settlement wrapper and candidate-domain tag whose transient execution prefix
  includes the anchor followed by all leading top-level outbound entries;
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
