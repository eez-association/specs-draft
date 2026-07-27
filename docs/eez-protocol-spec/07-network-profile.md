# 7. Required Network Profile

EEZ leaves deployment and network policy outside the reusable protocol. Every EEZ execution
network MUST publish one complete network profile. Rollup0 and Gnosis Chain are separate peer
execution networks. Neither profile inherits from, hosts, or completes the other.

The machine-readable schema is
[`network-profile.schema.json`](network-profile.schema.json). Profile schema version `2` has one
role, `eez-network`. The published instances are:

- [Rollup0 profile JSON](../rollup0-network-spec/network-profile.json)
- [Gnosis Chain profile JSON](../gnosis-chain-eez-spec/network-profile.json)

Each profile names its own execution network and records its Ethereum settlement configuration
directly. There is no cross-profile host reference and no Gnosis compatibility profile for
Rollup0.

## 7.1 Value states

Every selected field uses exactly one state:

| State | Meaning |
|---|---|
| `fixed` | Normative for this profile. `value` and an auditable `source` are required. |
| `release-blocker` | The repository has no authoritative choice. A stable blocker `id` and an `issue` describing the required decision are required. |
| `not-applicable` | The field does not apply. A `reason` is required. Schema v2 defines every listed field as owned by an `eez-network`, so the validator rejects this state for those fields. |

`release-blocker` is a draft-only placeholder. A production profile containing one is
non-conforming. An implementation MUST NOT substitute a development default for a release
blocker. The root `release_blockers` array MUST contain exactly the unique blocker IDs used by
nested selections.

Conformance uses this semantic algorithm:

1. Recursively collect the `id` of each object whose `status` is `release-blocker`.
2. Require `release_blockers` to contain each distinct collected ID exactly once and no other ID.
3. If `profile.status` is `production`, require both sets to be empty.

The dependency-free [`validate_profiles.py`](validate_profiles.py) validator implements this
algorithm, the typed schema, ruleset path and digest checks, the EVM-fork minimum, settlement
identity checks, timing relations, deployment uniqueness, proof-routing checks, and immutable
EVM-binding artifact checks. It validates Rollup0 and Gnosis Chain as independent peer profiles. It
performs no cross-profile resolution.

## 7.2 Required groups

Schema version `2` requires:

| Group | Required selections |
|---|---|
| Identity | stable profile ID; name; version; status; role `eez-network`; network name; environment |
| EEZ dependency | `eez-framework@0.1-draft`; `eez-evm@0.2-draft`; specification path; conformance source `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` |
| Ruleset dependency | ruleset ID and version; specification path; SHA-256 content-digest selection |
| Chain identity | execution-network EIP-155 chain ID; EEZ rollup ID; native asset; genesis commitment; EVM fork |
| Settlement binding | Ethereum network, chain ID, and genesis hash; `EEZ`, manager, and proof-system deployments; manager proof-context rule; deployment block; settlement and finality rules |
| Execution binding | block cadence and gas limit; complete header construction; fee market and recipient; EEZ predeploys; system address, safety rule, and transaction envelope |
| Operation | candidate admission; authentication mode and parameters; competition; settlement relay; separate `D1`, `D2`, `K`, `P`, `S`, and `C` timing selections; deterministic L1/L2 lowering; candidate-range bound; applied-prefix safety; atomic inclusion; bundle bound; proof-routing mitigation |
| Proof policy | proof model; allowed proof-system deployments and verification keys; threshold |
| Data availability | availability requirement; channel; codec; derivation rule |
| Governance and recovery | manager authority; upgrade policy; reorg and emergency handling |

A ruleset dependency names one complete reusable network-rules document. The `id`, `version`, and
`specification` path are direct selectors. `content_digest` is a value-state selection. A fixed
digest uses `algorithm: sha256` and the lowercase `0x`-prefixed SHA-256 digest of the exact bytes at
the specification path. A draft that has not published that digest MUST mark it as a release
blocker.

The settlement fields describe the Ethereum settlement layer used by that network. They do not
describe another EEZ execution network. A profile MUST identify the precise Ethereum environment,
chain ID, and genesis hash. It MUST pin the `EEZ`, manager, and proof-system deployments, their code
commitments, the deployment record, and the finality rule that consumers apply. The Rollup0 and
Gnosis Chain production-draft profiles both select Ethereum mainnet, chain ID `1`, and mainnet
genesis hash `0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3`.
Chiado is a development settlement environment and requires a separate development profile.

The operation fields describe different authorities:

- `candidate_admission` states whether every valid candidate is eligible or only permissioned
  candidates are eligible.
- `candidate_authentication` states how a candidate producer identity is established.
- `competition_rule` orders conflicting valid candidates and rejects stale candidates.
- `settlement_relay` states who may submit the selected result to Ethereum and how failures are
  handled.

These fields are independent of `proof_policy.allowed_proof_systems_and_vkeys`. Candidate
admission identifies who may propose a network block. Proof-system membership identifies which
verifier contracts or attestations can authorize an EEZ batch. A profile MUST NOT use one field as
an implicit substitute for the other.

Rollup0 selects permissionless-validity candidate admission: validators and provers accept a
candidate from any producer when it is valid under the Rollup0 rules. Gnosis Chain selects
permissioned candidate admission. Their remaining rules can be identical without making either
network a profile of the other.

## 7.3 Typed operation rules

A fixed `candidate_admission` value contains:

```text
mode: permissionless-validity | permissioned
acceptance_rule: non-empty string
invalid_candidate_rule: non-empty string
```

A `candidate_authentication` object contains separate `mode` and `parameters` selections. A fixed
`mode` value is:

```text
mode: none | signature | allowlist | protocol
```

A fixed `parameters` value contains:

```text
identity_rule: non-empty string
verification_rule: non-empty string
```

A fixed `signature` mode additionally requires non-empty
`canonical_candidate_encoding`, `digest_rule`, `replay_domain`, `signature_scheme`,
`accepted_signature_form`, `authorization_set_rule`, and `test_vectors` parameters. A profile can
therefore fix that signatures are required while keeping the exact signature and authorization
parameters as a release blocker.

A fixed `competition_rule` value contains:

```text
mode: first-valid | priority | leader-election | single-authority | other
ordering_rule: non-empty string
conflict_rule: non-empty string
stale_candidate_rule: non-empty string
```

A fixed `settlement_relay` value contains:

```text
mode: permissionless | permissioned | single-authority
authorization_rule: non-empty string
submission_rule: non-empty string
failure_rule: non-empty string
```

The enumerated `mode` is machine-readable. The accompanying rules are normative and MUST define
acceptance, conflicts, staleness, and failure without relying on an unnamed operator.

A `slot_construction` object contains six independent selections:

```text
settlement_interval_ms: D1, positive integer
block_interval_ms: D2, positive integer
blocks_per_settlement_interval: K, positive integer
proof_budget_ms: P, positive integer
submission_slack_ms: S, non-negative integer
max_catch_up_blocks: C, positive integer producer-output bound
```

`D2` MUST be a whole number of seconds, `K` MUST be at least `2`, and a fixed
`execution_binding.block_time_ms` MUST equal `D2`. When `D1`, `D2`, and `K` are fixed, `D1` MUST
be divisible by `D2`, and `K = D1 / D2`. When `P` and `S` are also fixed, `P + S < D1` and
`P + S <= (K - 1) * D2`. A profile MUST NOT hide fixed cadence values inside a blocker for the
remaining parameters.

`max_catch_up_blocks` is `C`, the producer-side maximum number of blocks emitted at one catch-up
trigger. It does not make a longer candidate invalid. `operation.max_candidate_range_blocks` is
`N_max`, the separate positive-integer consensus validity bound for every candidate range.

A fixed `manager_proof_context` value contains:

```text
context_block_rule: non-empty string
manager_method: getCustomData(uint64)
custom_data_encoding: non-empty string
authentication_rule: non-empty string
failure_rule: non-empty string
```

This selection supplies `MANAGER(n)` for the common ruleset. Naming a manager deployment does not
select the recent block-number rule, opaque custom-data bytes, or their authentication.

A fixed `header_construction` value defines every canonical header field from `parentHash` through
the activated optional fields, plus the exact body and validation rules. Its required members are:

```text
parent_hash, ommers_hash, beneficiary, state_root, transactions_root,
receipts_root, logs_bloom, difficulty, number, gas_limit, gas_used,
timestamp, extra_data, prev_randao, nonce, base_fee_per_gas,
withdrawals_root, blob_gas_fields, parent_beacon_block_root,
requests_hash, later_optional_fields, body_rule, validation_rule
```

Genesis, fork, fee, and header-construction selections remain independent. Fixing one does not
supply a missing value in another.

A fixed `l1_l2_lowering` value contains exact rules for:

```text
semantic_action_rule
l1_entry_rule
l2_sidecar_rule
explicit_inbound_arguments_rule
system_transaction_rule
validation_rule
failure_rule
conformance_vectors
```

The common rules require this field-by-field construction but do not invent a network's lowering
algorithm. A profile with this selection blocked cannot claim that its cross-layer execution path
is implementable.

`operation.cursor_applicability` selects an enforceable settlement rule that authenticates the
current execution-network cursor and compares it with the candidate's exact named parent. The
identity MUST commit to the parent height, block hash, and state root, or to an unambiguous
collision-resistant encoding of those values. Applying a candidate atomically advances this
identity to the authenticated selected prefix endpoint. The rule MUST bind every endpoint that
partial settlement can select. State-root equality alone is insufficient because different blocks
and competing ranges can have the same state root.

`operation.applied_prefix_safety` selects an enforceable rule that prevents a non-applied anchor or
effect from allowing a later effect to apply. The rule MUST preserve occurrence indices and
multiplicity when consecutive effects have repeated or equal root values. A description of
expected ordering without an enforcement mechanism is not a fixed safety rule.

## 7.4 System-address safety

`EEZL2` trusts `SYSTEM_ADDRESS` to load and replace execution tables. The contract also sends ETH
to `SYSTEM_ADDRESS` before it resolves an L2-originated action. The binding is conforming only
inside an execution-layer envelope that:

1. prevents `SYSTEM_ADDRESS` code from reentering either table-loading function during execution;
2. permits at most one top-level `executeIncomingCrossChainCall` in one transaction; and
3. starts that call with fresh transaction-scoped cursors.

A fixed `system_address_safety` value contains:

```text
mode: node-controlled-non-reentrant | contract-guarded
can_execute_code: boolean
prevents_reentrant_table_replacement: true
enforces_single_inbound_call_per_transaction: true
enforcement: non-empty string
failure_rule: non-empty string
```

For `node-controlled-non-reentrant`, `can_execute_code` MUST be `false`. A
`contract-guarded` design MAY execute code, but its cited guard MUST provide the two required
properties. The unmodified `EEZL2` contract does not enforce them. A second or reentrant inbound
call in the same transaction is outside the conforming envelope; an implementation MUST NOT
invent deterministic fresh-cursor behavior for it.

## 7.5 Proof-routing mitigation

`eez-evm@0.2-draft` does not bind `msg.sender`,
`transientExecutionEntryCount`, or `transientLookupCallCount` in proof public inputs.
Every profile MUST select `operation.proof_routing_mitigation`. A development profile MAY mark it
`release-blocker`. A production profile MUST fix a versioned access, relay, builder, contract, or
wrapper rule that authenticates the submitter and the unbound routing fields before the call
reaches `EEZ`.

A fixed mitigation MUST:

- provide non-empty `mechanism`, `binding_evidence`, and `failure_rule` values;
- set `authenticates_caller`, `prevents_replay`, and `prevents_front_running` to `true`; and
- list exactly `transientExecutionEntryCount` and `transientLookupCallCount` in
  `authenticated_calldata_fields`.

This mitigation concerns batch routing. It does not determine candidate admission, candidate
authentication, proof-system membership, or settlement-relay competition.

## 7.6 Encoding and completeness

The schema rejects undeclared fields. Fixed chain IDs, rollup IDs, block numbers, durations, gas
values, bounds, and thresholds use JSON integers no larger than `9007199254740991`
(`2^53 - 1`). A future schema that needs a wider EVM integer must define a canonical string
encoding.

Addresses and `bytes32` commitments use fixed-width `0x`-prefixed hexadecimal strings. Deployment
addresses, code hashes, transaction hashes, and deployment-block hashes are non-zero. A deployment
block number is positive. Proof-system deployment addresses are unique after case normalization.

A fixed `evm_fork` selects a recognized execution fork at or after Cancun, its activation, exact
EIP-1153, EIP-4844, and EIP-5656 opcode semantics, and a validation rule. A consensus-fork name
alone does not establish the required execution semantics.

The profile MUST answer:

- how each supported interaction becomes the distinct L1 and L2 tuples in §4.2;
- how explicit inbound parameters match the first incoming call;
- how L1 custody and book balances reconcile with L2 value;
- which committed effects define a network endpoint after partial consumption;
- which manager custom data supplies the deployment and replay domain;
- how unbound proof-routing inputs are authenticated;
- who may propose, authenticate, select, and relay a candidate; and
- who may change proof policy, replace roots, upgrade code, or invoke recovery.

A component name is not a fixed rule. Its value or source MUST define byte-level behavior and
failure handling. Profiles use strict JSON: duplicate members, `NaN`, `Infinity`, and
`-Infinity` are invalid.

## 7.7 Binding and precedence

Schema version `2` selects `eez-framework@0.1-draft` and `eez-evm@0.2-draft`. A network profile
also selects its reusable network ruleset independently. The source revision is reproducible
conformance evidence, not the protocol version. For behavior governed here:

1. a network activation record selects the profile and binding;
2. the binding specification controls contract behavior, layouts, selectors, and hashes;
3. the selected ruleset controls its complete reusable network algorithms;
4. the network profile controls only delegated network choices; and
5. source repositories are evidence, not silent amendments.

An upgrade that changes an ABI type, selector, hash preimage, proxy creation code, or verification
input requires a new binding edition and an explicit activation boundary.

---

*Appendices: [Protocol Reference](A-reference.md) and
[Wire Formats](B-wire-formats.md).*
