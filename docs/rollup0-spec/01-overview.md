# 1. Overview and Scope

Rollup0 uses EEZ to settle synchronous cross-network execution on Ethereum. The
[EEZ specification](../eez-protocol-spec/index.md) is normative for behavior shared by all EEZ
networks. This specification is normative for Rollup0-specific behavior.

## 1.1 Rollup0 Choices

Rollup0 selects:

- Ethereum as its settlement network;
- a 2-second execution-block interval;
- six execution positions per nominal 12-second Ethereum interval;
- an open candidate market with no composer allowlist;
- a permissioned validator/prover set;
- producer-neutral validation and sibling signing;
- canonical Ethereum transaction order as the candidate-selection rule;
- full calldata data availability; and
- deterministic reconstruction of Rollup0 from Ethereum data.

Any composer MAY construct and submit a candidate. Each validator/prover MUST evaluate every
candidate it receives and MUST sign every candidate that is valid under this specification.
Validator/prover signatures do not select a composer or a canonical candidate. A validator/prover
MAY sign several valid sibling candidates for the same parent.

The first applicable candidate in canonical Ethereum transaction order advances Rollup0. Other
sibling candidates for the old parent are stale.

## 1.2 Cross-Network Scope

This draft supports one top-level, state-changing call from Ethereum into Rollup0, with one return
value. The Ethereum caller can make ordinary nested Ethereum calls before and after that call. The
Rollup0 target can make ordinary nested Rollup0 calls.

Proven read-only calls use the EEZ lookup mechanism. Synchronous calls originating on Rollup0 and
direct calls between execution networks are outside this draft.

## 1.3 Conventions

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

Terms defined by EEZ keep their EEZ meaning. Rollup0 terms are listed in
[Appendix A](A-reference.md). Exact Rollup0 DA bytes are defined in
[Appendix D](D-wire-formats.md).

---

*Next: [Chapter 2, Architecture](02-architecture.md).*
