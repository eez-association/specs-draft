# 7. Required Network Profile

EEZ deliberately leaves deployment and network policy outside the reusable protocol. Every
network specification that uses EEZ MUST therefore publish a complete network profile.

The machine-readable schema is
[`network-profile.schema.json`](network-profile.schema.json). The published instances are:

- [Rollup0 profile JSON](../rollup0-network-spec/network-profile.json)
- [Gnosis Chain current EEZ profile JSON](../gnosis-chain-eez-spec/network-profile.json)
- [Gnosis Chain Rollup0 compatibility profile JSON](../gnosis-chain-eez-spec/network-profile-rollup0.json)

## 7.1 Value states

Every field selected by the schema MUST use exactly one state:

| State | Meaning |
|---|---|
| `fixed` | Normative for this profile. `value` and an auditable `source` are required. |
| `not-applicable` | The field does not apply to the profile's declared role. A `reason` is required. |
| `release-blocker` | The repository does not contain an authoritative choice. A stable blocker `id` and an `issue` describing what must be decided are required. |

`release-blocker` is a draft-only placeholder. A production profile containing one is
non-conforming. Implementations MUST NOT silently substitute a development default for a release
blocker. The root `release_blockers` array MUST contain exactly the unique set of blocker IDs used
by nested selections: no omitted, stale, or duplicate IDs are permitted.

Conformance uses this semantic algorithm:

1. Recursively visit every object below the profile root and collect the `id` of each object whose
   `status` is `release-blocker`.
2. Require `release_blockers` to contain each distinct collected ID exactly once and no other ID.
   The order of the root array is not significant.
3. If `profile.status` is `production`, require the collected set and the root array to be empty.

JSON Schema cannot express the recursive set equality in step 2 or reliably exclude a blocker at
an arbitrary future nesting depth. The dependency-free
[`validate_profiles.py`](validate_profiles.py) validator implements this algorithm, the typed
schema checks, the EVM-fork minimum, the proxy-artifact hash check, and the conditional
proof-routing rule. A profile is not conforming unless it passes both the schema and the semantic
checks.

## 7.2 Required fields

The schema requires the following groups:

| Group | Required selections |
|---|---|
| Identity | stable profile ID; profile name/version/status/role; network name and environment |
| EEZ dependency | exact EEZ framework ID/version and EVM-binding ID/version/specification path |
| Chain identity | EIP-155 chain ID; EEZ rollup ID; native asset; genesis commitment; EVM fork |
| Settlement binding | settlement profile/network/chain ID; `EEZ`, manager, and proof-system deployments; deployment block; settlement and finality rules |
| Execution binding | block cadence and gas limit; fee-market parameters and recipient; EEZ predeploys; system address and system-transaction envelope |
| Operation | sequencing model and authority; slot construction; atomic-inclusion mechanism; bundle bound; binding-specific proof-routing mitigation |
| Proof policy | proof model; allowed proof systems and verification keys; threshold |
| Data availability | availability requirement; channel; codec; derivation rule |
| Governance and recovery | manager authority; upgrade policy; reorg/emergency handling |

The schema rejects undeclared fields. A value is fixed only for the profile version that contains
it; changing a normative fixed value, a role assignment, a dependency version, or a conformance
vector requires a new applicable version.

Fixed chain IDs, rollup IDs, block numbers, durations, gas values, bounds, and thresholds use
non-negative JSON integers where the schema permits zero and positive JSON integers otherwise.
They are not decimal or hexadecimal strings and MUST be at most `9007199254740991` (`2^53 - 1`),
so an implementation can parse them exactly in both arbitrary-precision and IEEE-754 JSON
environments. A future profile schema that needs a wider EVM integer must define a canonical
string encoding instead of an imprecise JSON number. Fixed addresses and `bytes32` commitments use
`0x`-prefixed fixed-width hexadecimal strings. A deployment address,
runtime-bytecode hash, deployment-transaction hash, and deployment-block hash MUST also be
non-zero, and a transaction deployment block number MUST be positive. Proof-system deployment
addresses MUST be unique after case normalization. A fixed `host_profile` is exactly an object
with `profile_id` and `profile_version`. The canonical-header form of `block_gas_limit` selects a
header field and its validation rule rather than freezing one observed block's integer value.
A fixed `evm_fork` value is an object whose `minimum_execution_fork` is an explicit recognized
execution fork at or after Cancun. It MUST also contain:

- `activation`: exactly `{"kind": "genesis"}`, or a `block` or `timestamp` kind with one
  non-negative integer `value`;
- `opcode_semantics`: exactly `transient_storage: EIP-1153`, `blobhash: EIP-4844`, and
  `mcopy: EIP-5656`; and
- `validation`: a non-empty rule for checking the activation against the canonical chain.

Mentioning a fork or EIP name in free text, including a negated statement, does not select or
affirm it. `Deneb` alone is not a valid `minimum_execution_fork` because it names the consensus
fork, not the required EVM execution semantics.

The selections above MUST be complete enough to answer these security-critical questions:

- **Cross-side construction:** How does each supported interaction become the exact, distinct L1
  and L2 tuples in §4.2? Which entries produce which inbound system transactions, and in what
  order?
- **Action consistency:** How are explicit inbound parameters tied field-by-field to the first L2
  incoming call and to the action observed on the other side?
- **Value and custody:** Where does inbound `msg.value` come from? How do L1 physical custody,
  per-rollup book balances, L2 supply or burn, residual balances, failures, and withdrawals
  reconcile?
- **Partial settlement:** Which consumed entries and genuine ordered events define the network
  endpoint when entries are skipped, discarded, replaced, or left unconsumed?
- **Replay domain:** What exact manager custom data binds a proof to the host, deployment, binding
  version, and batch position? What prevents stale resubmission?
- **Submitter-controlled routing:** If the selected binding does not prove its dispatch partition
  or submitter, what versioned mechanism authenticates both before contract execution and prevents
  proof reuse or front-running?
- **Authority:** Which identities can sequence, submit, change proof policy, replace roots, upgrade
  code, supply system transactions, or invoke emergency recovery?

A field is not fixed merely because its `value` names a component. The value or its auditable
source MUST define the component's byte-level behavior and failure rule.
Required names, reasons, issues, sources, and validation rules MUST contain a non-whitespace
character. Profiles use strict JSON: objects MUST NOT contain duplicate member names, and numeric
values MUST NOT use `NaN`, `Infinity`, or `-Infinity`. Conforming parsers reject these inputs
instead of choosing a first or last member or accepting a language-specific numeric extension.

A role-owned selection MUST be `fixed` or, in a non-production profile, `release-blocker`; it MUST
NOT be `not-applicable`. For a rollup, these selections include its chain and genesis identity,
settlement-host reference, manager and proof deployments, execution parameters, operation and
proof policy, DA, and governance/recovery rules. For a settlement host, they include its chain and
genesis identity, `EEZ` deployment, deployment block, execution parameters, atomic-inclusion
capability, and governance/recovery rules. Conversely, every role-excluded selection MUST be
`not-applicable`; it cannot claim a fixed value or introduce a release blocker. In particular, a
rollup profile cannot override the host-owned shared `EEZ` deployment or its deployment block.
The validator enforces both complete field lists. The role semantics in §7.4 determine ownership.

Every `rollup` profile MUST select `operation.proof_routing_mitigation`. A development profile MAY
mark it `release-blocker`. A production profile MUST fix a versioned access, relay, builder,
contract, or wrapper rule that authenticates the submitter and every routing input that the
selected proof statement leaves unbound before the call reaches `EEZ`. The rule MUST specify
replay, front-running, and failure behavior. If the selected binding itself commits all of these
values, the profile MAY satisfy this requirement by citing that normative binding rule and its
conformance vector.

A fixed mitigation is a structured object. It MUST provide non-empty `mechanism`,
`binding_evidence`, and `failure_rule` values; set `authenticates_caller`, `prevents_replay`, and
`prevents_front_running` to the JSON boolean `true`; and list every authenticated calldata field
in `authenticated_calldata_fields`. Prose that merely contains these terms, or states that a
property is absent, does not satisfy the rule.

For `eez-evm@0.2-draft`, the fixed rule MUST authenticate `msg.sender` and list exactly
`transientExecutionEntryCount` and `transientLookupCallCount`; that binding does not itself prove
them. The historical `eez-evm@0.1-rollup0` rule has the same required field names, but it is a
separate binding claim and requires its own evidence. Other binding editions MUST state their own
exact unbound caller and calldata fields. Similar field names are not evidence that two editions
have the same proof-routing statement.

## 7.3 Binding editions and precedence

This framework edition is `eez-framework@0.1-draft`. The current EVM binding specified by
§§3–5 and Appendix B is `eez-evm@0.2-draft`, with conformance evidence reproduced from
`eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c`.

Every profile that selects this EVM binding MUST select an EVM fork or activation rule with
Cancun-compatible `TLOAD`, `TSTORE`, `MCOPY`, and `BLOBHASH` semantics. A fork selection older
than Cancun is invalid. Selecting a later fork is valid only when those Cancun semantics remain
available.

The schema records an exact binding version and a documentation-root-relative `specification`
path rather than forcing every profile onto `0.2-draft`. The conformance validator maintains the
binding registry for this specification set. It currently recognizes
`eez-evm@0.2-draft` at `eez-protocol-spec/index.md` and `eez-evm@0.1-rollup0` at
`rollup0-network-spec/E-compatibility-binding.md`. A profile MAY select another binding edition
only after the registry and this specification are versioned to identify its own self-contained
normative layouts, algorithms, selectors, and vectors. An arbitrary version string, source
commit, branch, repository `HEAD`, or similarity of Solidity struct names is not a binding
edition.

For behavior governed by this specification, precedence is:

1. a network activation record selects the profile and exact binding edition;
2. the selected binding specification controls contract behavior, layouts, selectors, and hashes;
3. the network profile controls only the choices delegated to it by that binding; and
4. source repositories and companion implementation notes are conformance evidence, not silent
   protocol amendments.

An implementation MUST NOT decode a batch, entry, lookup, or proof input using types from another
binding edition. A network upgrade that changes any ABI type, selector, hash preimage, proxy
creation code, or verification input requires a new binding edition and an explicit activation
boundary.

## 7.4 Role semantics

This edition defines two profile roles:

- `rollup` — an EEZ-managed execution network whose state is settled through an `EEZ` deployment;
- `settlement-host` — the EVM network on which a shared `EEZ` deployment executes.

Rollup-only fields in a settlement-host profile remain present and are marked `not-applicable`.
This keeps profiles mechanically comparable without pretending the settlement host is itself the
rollup. The rollup profile owns its rollup ID, manager and proof-system deployments, L2 execution,
sequencing, proof policy, DA codec, and derivation rule even when the corresponding contracts or
data are located on the host. The settlement-host profile owns host-chain identity and finality,
the shared `EEZ` deployment, and the host capability needed for atomic inclusion. A
`not-applicable` selection means that the role does not own the choice; it does not mean that a
consumer may leave the choice unspecified.

## 7.5 Cross-profile references

A profile reference MUST include the referenced profile's stable ID and exact version. A Rollup0
profile that says only “Gnosis” does not fix whether it means Gnosis Chain mainnet, Chiado, or
another environment. It also does not select an EVM binding edition. The Rollup0 development
profile therefore selects
`gnosis-chain-eez-chiado-rollup0@0.1-draft`, while a current `eez-evm@0.2-draft` consumer selects
`gnosis-chain-eez-chiado@0.1-draft`.

The referenced host profile MUST be loaded when the profile set is validated. It MUST have role
`settlement-host`; select the exact same EEZ framework and EVM binding IDs and versions; and agree
with the rollup profile's fixed host network and EIP-155 chain ID. The dependency-free validator
enforces these relationships. A production rollup MUST reference a production host profile with
no release blockers. Two host profiles for the same underlying chain are distinct when they
select different EVM binding editions or deployments.

When a rollup profile and its settlement-host profile disagree, neither profile conforms. The
rollup profile remains authoritative for L2 execution choices; the settlement-host profile remains
authoritative for host-chain identity and host capabilities. A consumer MUST also treat unresolved
blockers in the referenced host profile as unresolved dependencies of its own deployment claim.

---

*Appendices: [Protocol Reference](A-reference.md) and
[Wire Formats](B-wire-formats.md).*
