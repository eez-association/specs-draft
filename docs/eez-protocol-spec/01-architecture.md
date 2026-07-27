# 1. Architecture

EEZ consists of two contracts connected through standard interfaces.

## 1.1 Contracts

- **EEZ** (settlement layer) — the registry and execution manager. It holds, per registered
  rollup, a **state root** and an **ether balance**; verifies batches; and replays cross-chain calls
  against cross-chain proxies. Per-rollup proof policy lives in a per-rollup **manager** contract
  the registry consults; the registry itself holds no policy.
- **EEZL2** (execution layer) — the execution-side manager. It has no proofs and no registry: a
  trusted `SYSTEM_ADDRESS` drives inbound cross-chain delivery and the L2 mirrors EEZ's execution
  model.

Both contracts share the cross-chain **proxy** machinery, the **rolling-hash** accumulator, the
`authorizedProxies` registry, and the cross-chain **call hash**.

## 1.2 Interfaces

- **EEZ contract ABI** — the settlement surface: `registerRollup`, `postAndVerifyBatch`,
  `executeCrossChainCall`, `executeL2TX`, and `setStateRoot`.
- **Rollup manager** — supplies the proof systems, verification keys, and block context accepted
  for one registered rollup.
- **Proof system** — implements `verify(proof, publicInputsHash) → bool`.

EEZ defines these interfaces, but does not select the manager, proof system, or proof threshold for
a network.

---

*Next: [EVM and Cross-Chain Proxies](02-evm-and-proxies.md).*

