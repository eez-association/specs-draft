# 2. Deployment & Release Blockers

## 2.1 Deployment identity

An actual EEZ deployment on Chiado is identified by all of:

- the Chiado chain ID;
- the exact Gnosis host profile ID and version;
- the selected `eez-evm` binding ID and version;
- the `EEZ` contract address and runtime-bytecode hash;
- the deployment block number and block hash; and
- the owner, manager, upgrade, and emergency authorities that can change shared EEZ behavior.

Each consuming rollup separately identifies its rollup ID, manager, proof-system deployments, and
verification policy. Locating those contracts on Chiado does not transfer ownership of their
configuration to this host profile.

No authenticated deployment record containing these values is present in this specification.
Development tooling may emit ephemeral deployment values, but a script, environment file, adjacent
repository, or current local deployment is not a normative source. A release MUST publish the
values in a new profile version.

An address alone is not a stable deployment identity. A runtime-code change, proxy implementation
change, ownership transfer, or emergency-authority change MUST produce a new authenticated
deployment record. A consumer MUST stop treating the previous record as current unless the
profile's activation rule authorizes that transition. Values published for
`gnosis-chain-eez-chiado@0.1-draft` MUST NOT be used for
`gnosis-chain-eez-chiado-rollup0@0.1-draft`, or conversely.

## 2.2 Release blockers

The `gnosis-chain-eez-chiado@0.1-draft` profile remains non-production while the following are
unresolved:

- **GC-DEPLOYMENT:** no canonical shared `EEZ` address, runtime-bytecode hash, and deployment block
  are pinned;
- **GC-GENESIS:** the exact Chiado genesis or chain-spec commitment used to identify the host is
  not stored in this specification repository;
- **GC-ATOMIC-INCLUSION:** no normative builder/relay interface and failure semantics are pinned
  for the all-or-nothing ordered bundle, exact caller/calldata authentication, or modified-proof
  reuse and front-running prevention; and
- **GC-UPGRADES:** shared deployment ownership, upgrade, and emergency procedures are not
  published.

These are release blockers, not assertions that a production choice has been made. The local
Chiado workflow remains a development target. The minimum execution fork is not a blocker:
Chiado's Dencun activation at timestamp `1706724940` provides the Cancun opcodes required by the
binding. The deployment identity remains blocked and MUST place the deployment after that
activation.

The `gnosis-chain-eez-chiado-rollup0@0.1-draft` profile has the equivalent binding-specific
blockers `GC-R0-DEPLOYMENT`, `GC-R0-GENESIS`, `GC-R0-ATOMIC-INCLUSION`, and `GC-R0-UPGRADES`.
Resolving a current-profile blocker does not resolve the corresponding Rollup0 compatibility
blocker.

## 2.3 Mainnet boundary

[Gnosis Chain's network definitions](https://docs.gnosischain.com/about/networks/) assign mainnet
EIP-155 chain ID `100` and Chiado chain ID `10200`. Mainnet is outside this profile version. A
future mainnet profile MUST have a distinct profile ID, deployment identity, and version; changing
`10200` to `100` in this document would not be sufficient.

---

*Next: [§3 Security & Trust Model](03-security-trust-model.md).*
