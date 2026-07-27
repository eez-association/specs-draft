# 0. Protocol Version and Activation

This chapter is normative.

## 0.1 Version Manifest

| Item | Selected value |
|---|---|
| Rollup0 specification | `rollup0@0.2-draft` |
| Rollup0 Ethereum profile | `rollup0-ethereum@0.2-draft` |
| EEZ framework | `eez-framework@0.1-draft` |
| EVM binding | `eez-evm@0.2-draft` |
| Binding evidence snapshot | `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` |
| Implementation evidence | `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` |
| Production settlement network | Ethereum |
| Development settlement network | Gnosis Chiado |
| Status | Draft; no production activation |

The EEZ specification, not a source repository, is normative for the selected binding. The source
snapshot identifies reproducible evidence for the binding vectors. Implementations MUST take the
ABI, selectors, tuple layouts, hash preimages, event encodings, proxy code, and proof-input rules
from [EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md).

The historical
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`
binding is not selected. It differs from
`eez-evm@0.2-draft`, including tuple fields and order, function selectors, the batch shape, and the
manager custom-data interface. A client MUST NOT combine either binding's fields, selectors,
hashes, or vectors with the other.

The stable identifier `rollup0-common-execution@0.2-draft` names the self-contained,
parameterized rules in [the common-rules document](common-execution.md). Importing that identifier
does not import Rollup0 identity, candidate admission, header values, fees, or governance.

## 0.2 Precedence

Conflicts are resolved in this order:

1. An authenticated activation record selects a Rollup0 profile version and supplies its fixed
   deployment values.
2. This specification defines Rollup0-specific consensus and operational rules.
3. The selected EEZ specification defines the reusable framework and EVM binding.
4. Machine-readable profiles and Rollup0 fixtures reproduce the normative prose.
5. Implementation source, tests, branches, deployment scripts, and comments are evidence only.

A profile cannot redefine an EEZ wire format. This specification cannot silently adopt a later
implementation behavior. A consensus-relevant change requires a new profile version and an
unambiguous activation boundary.

## 0.3 Activation Record

A production activation record MUST publish and authenticate:

- the full identifiers in §0.1;
- Ethereum chain ID and genesis hash;
- Rollup0 EIP-155 chain ID, EEZ rollup ID, native asset, genesis artifact hash, state root, and
  genesis block hash;
- the activation Ethereum block number and hash and first governed Rollup0 block;
- the Ethereum EEZ address and code hash;
- the Rollup0 manager, proof-system, and L2 predeploy addresses and code hashes;
- validator/prover identities, verification keys, threshold, authorization, and rotation rules;
- the exact proof-unbound routing mitigation required by the selected EEZ binding;
- DA channel, codec tag, maximum payload and transaction counts;
- system-transaction authorization, signer identity, funding, and recovery;
- the Ethereum builder/inclusion mechanism, exact guarantees, and failure handling;
- fee funding, custody, upgrade, emergency, and deep-reorg authorities; and
- all timing and fork-activation parameters.

The record MUST contain no release-blocker value. A node MUST fail closed on an unknown version,
missing record, invalid authentication, mismatched code or genesis, or an ambiguous activation
boundary.

## 0.4 Upgrade Rule

One candidate range uses one Rollup0 profile and one EEZ binding. Nodes MUST retain old rules for
historical derivation.

The following require a new activated version:

- an EEZ binding change;
- a DA grammar or system-transaction envelope change;
- a proof-input, proof-policy, or routing-mitigation change;
- a block-validity, timing, state-delta, or candidate-selection change;
- a genesis, chain identity, or settlement-network change; or
- a change to the meaning of canonical settlement evidence.

In particular, replacing a collapsed final-root state-delta chain with exact per-effect prefix
roots is consensus relevant. Version 0.2 requires exact per-effect roots. Historical collapsed
roots are not valid under this profile.

## 0.5 Current Implementation Boundary

`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d` is the latest
reviewed implementation evidence. It includes competitive composer handling, a helper that
computes roots after effect prefixes, and optional remote batch-binding ECDSA proving. These
features do not establish exact state-delta construction or derivation conformance.

It is not a conforming 0.2 implementation:

- its checked-in contract gitlink is the historical
  `5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` binding;
- its default deployment still uses a non-binding mock proof system;
- that recorded 0.1 binding omits nested outbound value from entry accounting; the selected latest
  core binding fixes the defect, but the reviewed client has not ported to it;
- its composer builds a timeless `blockNumber = 0` batch and supplies no Ethereum proof-context
  hash; its optional remote prover rejects a nonzero `blockNumber`;
- its rich-candidate anchor ends at the pre-Sync parent root instead of zero-effect Sync root `Z`,
  so the first effect delta absorbs mandatory pre-execution changes;
- its settlement path has no exact Rollup0 cursor-height and block-hash commitment, so equal-root
  old-parent siblings remain applicable to the EEZ root check;
- its remote settlement gate checks exact indexed effect-prefix roots but still accepts synthetic
  interim roots and value-based membership for broader interior-root provenance;
- its proper-prefix derivation retains user transactions from omitted outbound effect groups;
- its derivation and settlement paths omit required validation listed in §8; and
- it does not load or authenticate a 0.2 activation record.

These facts do not weaken the normative rules. They block activation.

---

*Next: [§1 Network Profile](01-profile.md).*
