# 2. Architecture

Rollup0 consists of **three roles** and **two contracts**, connected by standard interfaces.

## 2.1 Roles

- **Operator** — the single, permissioned actor. It sequences L2 transactions, produces L2
  blocks, observes cross-chain intents, simulates each interaction across both chains, builds the
  batch, commits the Sync block on L2, and posts the batch together with the triggering L1
  transaction to L1 as one atomic bundle. The operator MUST produce blocks that any follower can
  re-derive byte-identically (§10). (How the operator is decomposed into sub-components is an
  implementation matter.)
- **Validator set** — a permissioned set of *M* signers. Each independently verifies a batch and
  signs its public-inputs hash; the L1 contract advances L2 state only when an **N-of-M** threshold
  of signatures verifies (§8). A validator MUST sign only a batch it has verified to be a correct
  state transition.
- **Follower / Deriver** — any party that reconstructs the L2 chain from L1 data alone, without
  trusting the operator (§10). It derives the L2 **safe** and **finalized** views from L1 and
  rejects any operator-published head that does not descend from them.

## 2.2 Contracts

- **EEZ** (L1) — the registry and execution manager. It holds, per registered rollup, a **state
  root** and an **ether balance**; verifies batches (`postAndVerifyBatch`, §8); and replays
  cross-chain calls against cross-chain proxies (§5). Per-rollup policy — the validator set and
  threshold — lives in a per-rollup **manager** contract the registry consults; the registry
  itself holds no policy.
- **EEZL2** (L2) — the L2-side execution manager, a genesis predeploy at
  `0x4200000000000000000000000000000000000007`. It has no proofs and no registry: a trusted
  `SYSTEM_ADDRESS` drives inbound cross-chain delivery (§3.4) and the L2 mirrors EEZ's execution
  model (§5).

Both contracts share the cross-chain **proxy** machinery, the **rolling-hash** accumulator, the
`authorizedProxies` registry, and the cross-chain **call hash** (§3, §5).

## 2.3 Interfaces

- **Engine API** — between the operator (and a follower) and its L2 execution client. Standard;
  clients implement it.
- **EEZ contract ABI** — the L1 settlement surface (`registerRollup`, `postAndVerifyBatch`,
  `executeCrossChainCall`, `executeL2TX`, `setStateRoot`; §8).

---

*Next: [§3 EVM, Cross-Chain Proxy & System Transaction](03-evm-proxy-systemtx.md).*
