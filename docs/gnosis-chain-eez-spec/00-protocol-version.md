# 0. Protocol Version and Precedence

## 0.1 Selected Protocols

`gnosis-chain-eez@0.2-draft` selects these exact protocol editions:

```text
Gnosis network protocol:  gnosis-chain-eez@0.2-draft
Gnosis network profile:   gnosis-chain-eez-ethereum@0.2-draft
EEZ framework:            eez-framework@0.1-draft
EEZ EVM binding:          eez-evm@0.2-draft
EEZ binding source:       eez-core-protocol@
                          3a6ca65c4858792fc3a143d34c5484877ef8f68c
Shared execution rules:   rollup0-common-execution@0.2-draft
```

The binding identifier and edition are normative. The full `eez-core-protocol` commit is
reproducible source evidence for that edition; the commit hash is not part of the binding
identifier. A change to an ABI, selector, hash preimage, proxy bytecode, state transition, or proof
public-input rule requires a new binding edition and a new Gnosis protocol version. A source-only
change that preserves every normative behavior does not.

`rollup0-common-execution@0.2-draft` is the self-contained normative text import in the
[common-rules document](../rollup0-network-spec/common-execution.md).
[§1.2](01-profile-imports.md#12-exact-import-manifest) maps every parameter to a Gnosis selection.
The ruleset is not an import of Rollup0 network identity, open admission, or
`eez-evm@0.1-rollup0`.

## 0.2 Edition Boundary

Gnosis Chain uses `eez-evm@0.2-draft`. It MUST NOT use the Rollup0 v0 compatibility binding,
`eez-evm@0.1-rollup0`. In particular, an implementation MUST use the 0.2 tuple layouts, selectors,
hash preimages, proxy creation code, manager interface, proof inputs, and transition rules specified
by the EEZ framework and the selected `eez-core-protocol` commit.

No Rollup0 chapter or compatibility text is part of the import. The imported common document and
this profile both select only `eez-evm@0.2-draft`.

## 0.3 Conflict Precedence

Apply normative material in this order:

1. An authenticated Gnosis activation record selects one immutable network-profile version and its
   activation boundaries. It cannot change that version's algorithms or wire formats.
2. This chapter selects the framework, binding, and imported-rule edition and records the source
   revision used as conformance evidence.
3. The EEZ framework controls reusable concepts and `eez-evm@0.2-draft` behavior.
4. This Gnosis specification controls network identity, cadence, settlement, authorization,
   canonical candidate selection, activation, and governance.
5. The exact imported rules in §1.2 control the remaining Gnosis execution-network behavior.
6. Examples, adjacent repositories, source comments, deployment scripts, and later revisions are
   informative unless an activation record explicitly identifies their normative artifact.

The Gnosis override table is exhaustive. Silence is not permission to inherit Rollup0 identity,
Rollup0 admission, or the Rollup0 compatibility binding. A conflict that this precedence cannot
resolve blocks activation.

## 0.4 Versioning and Activation

A production activation record MUST identify:

- `gnosis-chain-eez@0.2-draft` and `gnosis-chain-eez-ethereum@0.2-draft`;
- every exact dependency and imported-rule version in §0.1;
- the Gnosis EIP-155 chain ID, rollup ID, native asset, genesis artifact, genesis state root, and
  genesis block hash;
- the Ethereum settlement chain ID and genesis hash;
- the Ethereum `EEZ`, manager, proof-contract, and other protocol addresses and runtime-code hashes;
- the initial sequencer/composer authorization set and the mechanism that governs it;
- the signature scheme, candidate digest, replay domain, and rotation boundary;
- the production fork schedule, cadence activation, DA selection, proof policy, and finality rule;
- the activation Ethereum block number and hash and the first Gnosis block governed by the version;
  and
- governance, upgrade, emergency, recovery, and historical-version-selection rules.

Protocol versions are immutable after activation. A change to any item above requires an
authenticated versioned activation or upgrade record. A client MUST retain the old rules for
historical derivation and MUST NOT reinterpret finalized history under a later version.

No conforming production activation record currently exists.

---

*Next: [§1 Network Profile and Imported Rules](01-profile-imports.md).*
