# 10. Future Design

This chapter is informative. It does not change `rollup0-v0`; reusable EEZ behavior belongs in the
[EEZ Framework specification](../eez-protocol-spec/index.md), not here.

## 10.1 Candidate protocol changes

Future Rollup0 versions can select additional EEZ capabilities, including:

- multiple, nested, or reentrant cross-chain calls;
- cross-rollup routing beyond the Gnosis host and one L2;
- open or based sequencing with force inclusion and a permissionless exit;
- validity proofs in place of the current permissioned ECDSA policy;
- a key-free typed system envelope;
- blob DA and an explicit data-fee mechanism;
- a nonzero fee recipient or fee vault; and
- an authenticated Gnosis-derived `prev_randao`.

Each selection needs an explicit binding version, activation boundary, state-transition rule,
derivation rule, conformance vectors, and rollback/reorg behavior. Contract fields that happen to
exist in the historical implementation do not activate a capability.

## 10.2 Rollup1 direction

“Rollup1” denotes the intended permissionless, based, validity-proven successor. It would replace
the centralized operator, trusted proof policy, shared system key, and missing exit path. Open
posting also introduces requirements that v0 avoids, such as deterministic ordering among
independent posters and state-root chaining between multiple batches in one host block.

The type-`0x7E` system transaction discussed in Appendix C is only a candidate for that direction.
No v0 client may emit or accept it as a Rollup0 system envelope.

---

*End of the normative body. Appendices A-E provide analysis, codec, system-transaction, genesis,
and compatibility material.*
