# 10. Future Design

This chapter is informative. None of these items is active in `rollup0@0.2-draft`.

Potential revisions include:

- a permissionless proof market with protocol-defined service and aggregation rules;
- a contract-level candidate auction or inclusion mechanism that preserves the first-applicable
  Ethereum ordering rule;
- proof inputs that bind transient counts, caller, complete calldata, and replay domain;
- a key-free system transaction type with protocol-enforced non-reentrancy;
- contract-enforced atomic settlement instead of separately signed companion transactions;
- blob DA with a byte-exact sidecar binding and fallback policy;
- force inclusion and a trust-minimized exit;
- explicit peer-to-peer lowering for Rollup0, Gnosis Chain, and other EEZ networks;
- a production reserve, bridge accounting, and solvency invariant;
- L1-derived randomness with an activated header rule;
- data-fee accounting and candidate reimbursement; and
- unbounded or checkpoint-based reorganization recovery.

Each change needs a new version, an activation boundary, a schema-valid profile, and byte-exact
fixtures where it affects serialization or hashing. Implementations MUST NOT infer future rules
from this list.

---

*See [§0 Protocol Version](00-protocol-version.md) for activation rules.*
