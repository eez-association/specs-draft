# Appendix C. Open Questions to Answer

Design questions surfaced by review that still need a protocol **decision** before they can be
specified normatively. Answered questions are folded into the body and removed from this list.
(Deployment parameters still to be pinned — `chainId`, `SYSTEM_ADDRESS`, fee vaults, validator
`M`/`N`, genesis bytecode, etc. — are tracked in [§12.2](12-open-issues.md), not here.)

## C.1 Domain separation / replay

The cross-chain call hash (§3.3) and the digest validators sign (the **raw** `publicInputsHash`, §8)
carry no chainId, no settlement-contract address, and no batch nonce; §3.2 deliberately makes the
proxy salt domain-free **of any chain/deployment term** (it *does* include `rollupId`). The same
`(rollupId, address)` therefore maps to the same proxy across **separate EEZ deployments** that
share a deployer + bytecode, and an attestation may be replayable against another deployment or
fork.

- Is the domain-free design an intentional **single-deployment** assumption?
- What binds a signature/batch to *this* deployment and *this* position in the chain — is
  `blockHash_r` (§8.3) the sole anti-replay binding, and is it sufficient?
- What prevents re-submission of a stale-but-valid batch?

## C.2 Adversarial gas / DA

- Inbound execution has a fixed (~2M) gas budget and an **unconditional mint**; an attacker-crafted
  L2 target that runs out of gas could desync the L1 accounting from the L2 effect. Is there a v0
  mitigation, or is it accepted (with the composer's simulation, §6 R2, responsible for parity)?
- Calldata-DA cost falls on the lone operator in v0 (§11.4); large-calldata spam griefs the
  operator. Accepted, or bounded (per-batch size cap, fee floor)?
- A **shallow L1 reorg** can un-mine the trigger while the batch remains re-submittable; with no
  batch nonce (C.1), is trigger re-inclusion safe (§10.4)?

---

**Resolved (now in the body):** *manager trust* — the per-rollup manager is a fully-trusted
component for Rollup0/GC, recorded in [§12.1](12-open-issues.md) (replaceable / burnable under
Rollup1). *STATICCALL reads* — part of v0, recorded as proven lookup-table entries (§3.5, §5.3).

*See also [§12 Open Issues & Limitations](12-open-issues.md) and [Appendix D](D-wire-formats.md).*
