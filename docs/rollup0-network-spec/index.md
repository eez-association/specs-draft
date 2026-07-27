# Rollup0 Network Specification

**An open-composer EEZ network settled on Ethereum**

| | |
|---|---|
| **Specification ID** | `rollup0` |
| **Protocol version** | `0.2-draft` |
| **Profile ID** | `rollup0-ethereum@0.2-draft` |
| **Status** | Draft; no production activation record exists |
| **EEZ dependency** | `eez-framework@0.1-draft`, `eez-evm@0.2-draft` |
| **Settlement network** | Ethereum |
| **Production cadence** | 12-second nominal Ethereum interval; six 2-second Rollup0 timestamp positions |
| **Composition and relay** | Open and competitive; settlement relay is permissionless |
| **Proof policy** | Permissioned validator/prover set; production membership and threshold are unresolved |

Rollup0 is one EEZ network. Gnosis Chain is another EEZ network. Neither network is the other
network's settlement layer. Both select EEZ and settle on Ethereum. This edition does not define
direct execution-network-to-execution-network effects.

This specification selects the reusable [EEZ Framework](../eez-protocol-spec/index.md) and its
`eez-evm@0.2-draft` binding. The exact ABI, hash preimages, proxy code, events, and wire vectors are
owned by that specification, especially
[EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md). This document specifies only Rollup0
choices: timing, candidate admission, data availability, deterministic L2 construction, proof
policy, derivation, fees, genesis requirements, and operations.

The network-neutral subset of these Rollup0 choices is published as
[`rollup0-common-execution@0.2-draft`](common-execution.md). That document is a self-contained,
parameterized ruleset. A peer network can import it without importing Rollup0 candidate admission,
identity, proof membership, header values, fees, or governance.

## Network Model

Rollup0 does not authorize one sequencer or composer. Any composer MAY construct and submit a
candidate. Every active Rollup0 validator/prover:

1. MUST evaluate every supported candidate that it receives without considering producer identity;
2. MUST sign each candidate that is valid under the activated Rollup0 rules;
3. MUST NOT reject a valid candidate because it conflicts with another valid candidate; and
4. MAY therefore sign several valid sibling candidates for the same parent.

Ethereum orders the submitted candidates. The first candidate in canonical Ethereum transaction
order whose exact named parent is the current settled cursor advances Rollup0. A candidate whose
parent identity is stale is a losing sibling and does not advance Rollup0, even if its parent root
equals the current root. Producer identity is not a validity input.

Permissionless composition does not make validation permissionless. The active proof-system
membership and threshold remain network-governed. Censorship resistance depends on candidate
delivery to that validator set, validator willingness to evaluate valid work, proof availability,
and Ethereum inclusion.

## Status

The normative production cadence is fixed, but the production network is not activated.
Production still requires an authenticated activation record that selects at least:

- the Rollup0 EIP-155 chain ID, EEZ rollup ID, native asset, and byte-exact genesis;
- the Ethereum EEZ, Rollup0 manager, proof-system, and predeploy addresses and code hashes;
- validator/prover membership, verification keys, threshold, authorization, and rotation;
- a mitigation for proof-unbound routing controls in `eez-evm@0.2-draft`;
- the maximum accepted candidate range, exact-cursor applicability, and enforceable applied-prefix
  safety;
- the system-transaction authorization and key-distribution design;
- the exact Ethereum builder/inclusion policy and fee funding;
- fee funding, custody, upgrade, emergency, and recovery authorities; and
- an activation boundary and historical-version transition procedure.

Chiado remains an implementation-development environment only. It uses a nominal 5-second
settlement interval and five 1-second Rollup0 timestamp positions. Chiado chain IDs, deployments,
keys, genesis derivatives, and relay behavior are not production values.

The current implementation evidence is
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`. Its checked-in
`sync-rollups-protocol` gitlink remains at the historical
`5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` binding and is not compatible
with the selected `eez-evm@0.2-draft` binding. The implementation is therefore not a conforming
0.2 client until that dependency and the deviations in [§8](08-limitations.md) are resolved.

## Reading Order

1. [Protocol Version and Activation](00-protocol-version.md)
2. [Network Profile](01-profile.md)
3. [Timing, Production, and Headers](02-block-production.md)
4. [Composer and Candidate Competition](03-composer.md)
5. [Data Availability, Batches, and Ethereum Bundles](04-da-batches-bundles.md)
6. [Cross-Network Flows](05-l1-to-l2.md)
7. [Derivation and Following](06-derivation-following.md)
8. [Gas and Economics](07-gas-economics.md)
9. [Open Issues and Limitations](08-limitations.md)
10. [Security and Trust Model](09-security-trust-model.md)
11. [Future Design](10-future-design.md)

Network-specific appendices:

- [Appendix A: Gas Cost Analysis](A-gas-cost-analysis.md)
- [Appendix B: Rollup0 DA Codec](B-da-codec.md)
- [Appendix C: Rollup0 System Transactions](C-system-transactions.md)
- [Appendix D: Genesis and Block Validity](D-genesis-validity.md)

There is no Rollup0-local ABI appendix. Implementations MUST use the selected EEZ binding and its
conformance vectors directly.

[Return to the specification set](../index.md).
