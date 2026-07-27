# 4. Implementation and Conformance Status

## 4.1 Current Status

This specification is not production complete. No adjacent implementation provides the Gnosis
authorization mechanism in §2. In particular, `eez-rollup0` does not implement the additional
Gnosis candidate signature or an Ethereum proof contract that checks it. Rollup0 behavior is not
implementation evidence for Gnosis admission.

The selected `eez-core-protocol` revision supplies the reusable `eez-evm@0.2-draft` binding source.
It does not supply Gnosis network identity, cadence activation, candidate authorization, canonical
winner selection, deployment records, or governance.

An implementation MUST NOT claim Gnosis network conformance by implementing only the EEZ framework
or the imported shared execution rules.

## 4.2 Production Release Blockers

The following blocker set is normative:

| ID | Missing decision or artifact |
|---|---|
| `GC-IDENTITY` | Production Gnosis chain ID, rollup ID, native asset, name, and authenticated network identifier |
| `GC-GENESIS` | Exact genesis artifact, state root, block hash, allocations, fork schedule, and artifact digest |
| `GC-EEZ-DEPLOYMENT` | Exact deployment blocks, addresses, runtime-code hashes, proxy implementations, activation state, and settlement-event identity for `EEZ`, manager, proxy, and related `eez-evm@0.2-draft` contracts |
| `GC-PROOF-CONTEXT` | Exact manager custom-data encoding and authenticated settlement-block binding |
| `GC-HEADER` | Complete genesis, fork, block-environment, and per-field header-construction rules |
| `GC-LOWERING` | Deterministic field-by-field semantic-action, L1-entry, L2-sidecar, explicit-inbound, and system-transaction construction with failure rules and vectors |
| `GC-PROOF-CONTRACT` | Ethereum proof-contract address, code hash, verification key, public inputs, and binding to the EEZ call |
| `GC-AUTH-SCHEME` | Signature envelope, canonical candidate encoding, digest, replay domain, accepted signature form, and vectors |
| `GC-AUTH-SET` | Initial authorized sequencer/composer set, threshold, custody, and compromise procedure |
| `GC-AUTH-ROTATION` | Canonical rotation mechanism, delays, boundary semantics, historical verification, and reorg handling |
| `GC-PROOF-ROUTING` | Binding of the exact batch, relayer-independent authorization, both transient prefix counts, and all other effective routing inputs |
| `GC-ECONOMICS` | Gas limits, fee rules, recipients, funding, value custody/backing, and capacity bounds |
| `GC-SYSTEM-SAFETY` | System address, transaction envelope, funding, code-execution restriction, reentrancy protection, and one-inbound-call enforcement |
| `GC-TIMING` | Production and development proof budgets, submission slack, catch-up bounds, and derived Live/Future/Sync partitions |
| `GC-ATOMIC-INCLUSION` | Exact Ethereum inclusion mechanism, ordering, failure semantics, and partial-inclusion detection |
| `GC-CURSOR-SAFETY` | Enforceable exact-parent comparison and atomic selected-cursor advancement, including equal-root transitions |
| `GC-PREFIX-SAFETY` | Enforceable prevention of an applied effect after a non-applied anchor or effect, including equal-root cases |
| `GC-CAPACITY` | Maximum candidate range and production bundle capacity derived from proof, gas, DA, and relay measurements |
| `GC-GOVERNANCE` | Upgrade, emergency, recovery, authority, notification, and activation procedures |
| `GC-ACTIVATION` | Authenticated record containing every §0.4 value and an unambiguous Ethereum/Gnosis boundary |
| `GC-IMPLEMENTATION` | Independent composer, validator, prover, proof-contract, relayer, and follower support for this profile |
| `GC-CONFORMANCE` | Complete positive and negative machine-readable vectors and cross-client tests |

No blocker may be satisfied by an address, key, script output, or deployment found only in an
adjacent repository. The value and its authentication source must appear in a versioned profile or
activation record.

The common-rules edition and immutable content digest are fixed in `network-profile.json`.
A digest mismatch is a conformance failure, not an unresolved production choice.

`network-profile.json` lists all unresolved profile selections. `GC-IMPLEMENTATION` and
`GC-CONFORMANCE` are release gates over software and test artifacts rather than profile-value
leaves, so they appear only in this normative status chapter.

## 4.3 Role Conformance

A conforming implementation of a role MUST satisfy the framework, binding, imported rules, and
Gnosis-specific requirements that apply to that role:

| Role | Minimum Gnosis-specific obligation |
|---|---|
| Composer | Construct the canonical candidate bytes and request authorization without changing the fully validated candidate |
| Authorized signer | Sign only the activated digest and use the active authorization domain |
| Validator | Re-execute and check full validity independently of authorization |
| Prover | Bind its proof to the same complete candidate and authorization result |
| Gnosis authorization proof contract | Verify the candidate signature, active membership, replay protection, and binding to the exact validity statement and settlement routing |
| Ethereum settlement path | Verify full validity and authorization for the same candidate; compose the selected verifier, authorization proof contract, and EEZ call exactly as the profile specifies |
| Relayer | Submit the exact authorized, proven batch; no signer membership is required |
| Follower | Derive only the first applicable candidate in canonical settlement order and handle reorgs and rotations |

Implementing one role does not imply conformance for another role or for the whole network.

## 4.4 Required Conformance Corpus

Before production activation, machine-readable fixtures MUST cover at least:

- canonical candidate encoding, digest, signature recovery/verification, and proof public inputs;
- a valid candidate submitted by a relayer that is not its signer;
- rejection of an authorized invalid candidate and of a valid unauthorized candidate;
- mutation of every digest field, including both transient prefix counts;
- replay across chain IDs, rollup IDs, profiles, contracts, epochs, parents, and development versus
  production;
- signer addition/removal and a reorg across the exact rotation boundary;
- competing authorized valid candidates for one parent, including same-block ordering and stale
  rejection;
- an equal-root winner followed by a correctly signed sibling for the old parent, proving that the
  sibling is rejected by exact cursor identity;
- empty and nonempty anchor-only candidates with exact `A -> F` settlement;
- rich candidates with exact `A -> Z -> R[k]` chains, including `q = 0`, every proper effect
  prefix, full settlement, and omission of both transactions in a dropped outbound group;
- equal consecutive effect roots with a caught earlier failure, proving that a later effect cannot
  commit across the resulting prefix hole;
- distinct one-to-one inbound triggers, consecutive bundle indices, and rejection of interleaving
  or one trigger claimed for several effects;
- Ethereum reorg replacement of a previously selected candidate;
- complete production and Chiado-development cadence, timestamp, header, Sync, DA, and derivation
  vectors; and
- end-to-end composer-to-settlement-to-follower traces with positive and negative proof-contract
  cases.

At least two independent clients MUST produce the same result for the complete corpus. Unit tests
of signature recovery or imported Rollup0 code alone are insufficient.

## 4.5 Development Profile

The Chiado cadence in §1.1 may be used for development after a development activation record fixes
its chain identities, genesis, deployments, keys, authorization set, proof contract, replay domain,
and maximum candidate range. Development keys or contracts MUST NOT be accepted in production.

Until such a record and the signature/proof fixtures exist, the development cadence is a parameter
selection, not a conforming deployed network.

---

*End of the Gnosis Chain EEZ Network Specification.*
