# 0. Protocol Version & Compatibility

This chapter is normative. It fixes the sources and precedence for the protocol version described
by this specification. A branch name, repository `HEAD`, package release, or deployed contract
that is not listed here MUST NOT be used to fill a gap or replace a listed revision.

## 0.1 Rollup0-v0 manifest

| Manifest field | Normative value |
|---|---|
| Protocol identifier | `rollup0-v0` |
| EEZ framework dependency | `eez-framework@0.1-draft` |
| EVM compatibility binding | `eez-evm@0.1-rollup0`; this is **not** `eez-evm@0.2-draft` |
| Specification status | **Draft compatibility profile; not activated for a production network** |
| L1/L2 contract ABI and contract-defined hash source | `sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` |
| Contract source tree | `7f45f099440a8c5ff2ec9358950dc2f5e7ccb337` |
| Rollup0 execution-layer and DA-codec source | `eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c` |
| Rollup0 source tree | `85719ee24f3f2902f6441f81156835f5c2ff64e8` |
| Rollup0 ABI mirror | `crates/eez-evm/src/types.rs` at blob `5fbdb9f7ab3c9c19304519f71bfcae9ec5fdd090` |
| DA-codec implementation | `crates/eez-payload-codec/src/lib.rs` at blob `533d978b2e3dd2e91c1d29f3416ffe3da04314a5` |
| System-transaction implementation | `crates/eez-evm/src/system_tx.rs` at blob `be4a48607c55342c1eea87a09fe1d7da561f86aa` |
| `crossProofSystemInteractions` | `bytes32(0)`; nonzero is invalid for Rollup0 v0 |
| Solidity compiler profile for committed proxy init code | solc `0.8.34`, optimizer enabled, 200 runs, `via_ir = true` |
| `CrossChainProxy.creationCode` | 1,111 bytes; `keccak256 = 0x0a2e4d916da3a258d274e03e75d9236477f377b91173aa46c9bde942adfb660c` |
| Calldata DA codec | tag `0x00`, implemented by `crates/eez-payload-codec/src/lib.rs` at the Rollup0 revision above |
| L2 system-transaction framing | signed legacy EIP-155 transaction, implemented by `crates/eez-evm/src/system_tx.rs` at the Rollup0 revision above |

The full commit identifiers are part of the version. The old
`sync-rollups-protocol@fe7bf6644dacd64bb41707feae2d84699a97afb4` baseline is superseded
for this specification and is not wire-compatible with `rollup0-v0`. At the selected Rollup0
commit, `git ls-tree HEAD sync-rollups-protocol` records `5c51e02`; the stale `fe7bf66` prose in
that repository's `.gitmodules` is a comment, not the gitlink and not a version selector.

The ABI mirror is corroborating implementation evidence, not an independent authority. It is
listed because the Rollup0 repository commits the `5c51e02` gitlink and locks the three
layout-sensitive selectors in tests. The byte-exact transcription is in
[Appendix E](E-compatibility-binding.md).

The critical selector fingerprint is:

| Surface | Canonical selector |
|---|---|
| L1 `postAndVerifyBatch(...)` | `0x8b1a095a` |
| L2 `loadExecutionTable(...)` | `0x59683c8b` |
| L2 `executeIncomingCrossChainCall(...)` | `0xeb494246` |
| Rollup manager `getTimestampAndBlockHash(uint64)` | `0x6db96461` |

The full canonical signature strings are fixed in
[Appendix E](E-compatibility-binding.md). A client that computes any other value is not speaking
`rollup0-v0`.

The machine-readable Rollup0 corpus is
[`fixtures/conformance-vectors.json`](fixtures/conformance-vectors.json). It is generated and
checked by `fixtures/verify-conformance.py` against this `5c51e02` binding. The separate EEZ
Framework corpus targets `3a6ca65` and MUST NOT be substituted for it.

## 0.2 Later EEZ revision

The adjacent `eez-core-protocol` repository was cross-checked at
`3a6ca65c4858792fc3a143d34c5484877ef8f68c` (tree
`87edf85dc65a15cd539f12043a08518766ca5cd0`). It is the source snapshot for the separate current
`eez-evm@0.2-draft` binding. It is **not** part of `rollup0-v0` and MUST NOT be mixed with
`eez-evm@0.1-rollup0`. Among other changes, that revision:

- adds `isStatic` to the call tuples;
- adds clear `destinationRollupId` fields to nested call and lookup tuples;
- changes the L1 `ExecutionEntry` field order;
- removes `crossProofSystemInteractions` from the batch tuple; and
- replaces `getTimestampAndBlockHash(uint64)` and its typed fold with
  `getCustomData(uint64)` and an opaque-data fold.

These changes alter ABI encodings, selectors, entry/lookup hashes, proof public inputs, or manager
calls. Adopting any of them requires a new protocol identifier and activation; the fact that
`3a6ca65` is newer does not activate it.

| Surface | `rollup0-v0` / `5c51e02` | separate `3a6ca65` revision |
|---|---|---|
| `postAndVerifyBatch(...)` | `0x8b1a095a` | `0xd1fc6b5a` |
| `loadExecutionTable(...)` | `0x59683c8b` | `0xc1b4427c` |
| `executeIncomingCrossChainCall(...)` | `0xeb494246` | `0xf882a0ad` |
| manager context read | `getTimestampAndBlockHash(uint64)` / `0x6db96461` | `getCustomData(uint64)` / `0x9aeb8564` |

## 0.3 Conflict precedence

For `rollup0-v0`, conflicts MUST be handled in this order:

1. A network activation record selects a protocol identifier and supplies network-specific
   parameters. It cannot redefine that version's layouts or algorithms.
2. This manifest selects the immutable source revision for each protocol surface.
3. For contract ABI, contract behavior, selectors, proxy init code, and contract-defined hash
   preimages, the `5c51e02` source is authoritative.
   [Appendix E](E-compatibility-binding.md) is its normative, self-contained transcription.
4. For the L2 transaction envelope and positive calldata DA encoding, the listed `eez-rollup0`
   revision is authoritative. Appendix C transcribes the envelope. The source-authored DA shape
   and canonical-minimal encoder are transcribed in §4.1, Appendix B, and Appendix E.7.
5. Rollup0 profile acceptance rules that the selected sources do not implement, including strict
   whole-item RLP consumption, nonempty counts, empty `blobIndices`, canonical receipt
   attribution, and full replay validation, are normative additions in §§4 and 6. A source
   decoder that omits one is a nonconforming implementation gap, not an alternate wire grammar.
6. For rules that neither selected source defines, the normative chapters of this specification
   control. Companion documents, examples, comments, review logs, and later repository revisions
   are informative.

A discrepancy between a normative transcription and its selected source is a **release blocker**.
Implementations MUST NOT choose whichever form they prefer or silently follow a current branch.
The specification and vectors must be corrected, and the correction reviewed, before activation.

## 0.4 Upgrade and activation policy

A network MUST publish an immutable activation record before using this profile. The record MUST
include at least:

- protocol identifier and every full source commit in §0.1;
- L1 chain ID, L2 chain ID, rollup ID, and genesis hash;
- L1 `EEZ`, rollup-manager, proof-system, and L2 `EEZL2` addresses plus runtime code hashes;
- `SYSTEM_ADDRESS`, signing-key custody and availability, the funding policy, gas price, and gas
  limit;
- the activation L1 block number and hash, and the first L2 block governed by the version; and
- the DA channel and codec tag.

Protocol versions are immutable after activation. Any change to an ABI tuple, field order or type,
function selector, hash preimage, proxy init code, transaction envelope, DA grammar, or validation
rule requires a new protocol identifier. Nodes MUST select the version from the activation
boundary, MUST use one version for an entire batch, and MUST retain old rules for historical
derivation. A source update or deployment alone is not activation.

An upgrade record MUST identify the old and new versions and an unambiguous L1/L2 boundary.
If an upgrade changes the manager address or proxy init code, it MUST also define proxy and state
migration; CREATE2 addresses from different profiles are not interchangeable. Rollback after an
activated batch requires a separately published recovery activation and MUST NOT reinterpret
already-finalized history under another version.

## 0.5 Current activation blocker

No production activation record satisfying §0.4 is present in this repository, so
`rollup0-v0` remains a draft compatibility profile.

The selected Rollup0 code produces signed legacy outbound-load and inbound-delivery transactions
from `SYSTEM_ADDRESS`. Their byte format is fully specified in Appendix C, but byte-identical derivation
requires the signing key. Publishing that key defeats the contract's system-only authorization;
withholding it makes cross-chain derivation permissioned. A production activation MUST explicitly
accept and secure that trust model, or activate a separately versioned deterministic authorization
design. This document does not present the security and key-distribution blocker as resolved.

---

*Next: [§1 Network Profile](01-profile.md).*
