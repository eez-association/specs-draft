# 1. Network Profile

## 1.1 Ownership

Rollup0 selects:

```text
Rollup0 protocol:       rollup0@0.2-draft
Rollup0 profile:        rollup0-ethereum@0.2-draft
EEZ framework:          eez-framework@0.1-draft
EVM binding:            eez-evm@0.2-draft
Settlement network:     Ethereum
Development network:    Gnosis Chiado
```

The [EEZ Framework](../eez-protocol-spec/index.md) owns reusable execution, proof, settlement,
proxy, ABI, and hash behavior. Rollup0 owns the choices in this chapter. Gnosis Chain owns its own
peer-network profile and is not referenced as Rollup0's host.

## 1.2 Production Choices

| Surface | Rollup0 0.2 rule |
|---|---|
| Settlement | Canonical Ethereum |
| Cadence | nominal `D1 = 12,000 ms`, `D2 = 2,000 ms`, `K = 6` |
| Candidate production | open; no composer allowlist |
| Candidate validation | producer-blind; evaluate and sign every supported valid candidate |
| Sibling candidates | permitted; a validator MAY sign several valid siblings |
| Winner | first applicable transition in canonical Ethereum transaction order |
| Stale sibling | does not advance Rollup0 |
| Settlement relay | permissionless; no producer or relayer allowlist |
| Headers | deterministic parent-derived construction in §2 |
| DA | complete tag-`0x00` Ethereum calldata; `blobIndices = []` |
| State deltas | exact per-effect prefix roots with enforceable prefix safety; collapsed final roots are invalid |
| Proof systems | permissioned set selected by the activation record |
| Cross-network scope | one flat, non-static, successful top-level call per interaction |
| System transactions | deterministic Rollup0 envelopes selected in Appendix C |
| Fees | EIP-1559 execution fees; no Rollup0 L1-data fee mechanism in this draft |

The production proof budget, submission slack, maximum candidate range, maximum bundle size, chain
ID, rollup ID, genesis, contract deployments, system authorization, validator set, proof threshold,
exact-cursor guard, applied-prefix guard, builder mechanism, fee funding, and upgrade authorities
are not yet selected. They are release blockers, not local defaults.

## 1.3 Open Composer and Validator Rule

A candidate is identified by its exact parent height, block hash, and state root, ordered Rollup0
block range, complete EEZ batch, proof context, DA, and intended Ethereum transaction bundle.
Producer identity is not included.

Every active validator/prover MUST:

1. authenticate the selected profile and candidate inputs;
2. independently execute the complete candidate;
3. validate DA, system transactions, headers, per-effect prefix roots, and intended Ethereum
   bundle;
4. sign when and only when the candidate is valid and supported;
5. apply the same decision to identical candidate bytes from every producer; and
6. continue evaluating valid siblings after signing one candidate.

A validator MUST NOT impose first-seen exclusivity, a producer allowlist, or a one-signature-per-
height rule. Signing siblings is not equivocation in Rollup0. Ethereum ordering resolves them.

The settlement transition is applicable only when the candidate's exact parent height, block hash,
and state root equal the current settled Rollup0 cursor identity. The activated cursor guard MUST
enforce this comparison and atomically advance the identity; the EEZ contract's state-root check is
not sufficient when different blocks have equal roots. Within one canonical Ethereum block,
candidates are processed in transaction order. The first applicable valid candidate advances the
cursor. A later candidate can advance only if it starts from the cursor left by earlier canonical
execution. A stale sibling is not reinterpreted against another parent and does not consume an L2
range.

## 1.4 Timing Profiles

Production fixes:

```text
D1 = 12,000 ms
D2 =  2,000 ms
K  = 6
```

Each nominal Ethereum interval has six Rollup0 timestamp positions. The activated proof budget
and submission slack determine how many positions are built live and how many are prebuilt, but do
not change `K`.

The implementation-development Chiado profile uses:

```text
D1 = 5,000 ms
D2 = 1,000 ms
P  =   500 ms
S  = 1,300 ms
K  = 5
```

These Chiado values are not production fallback values.

## 1.5 Data and System Transactions

Rollup0 publishes every transported user transaction and every Rollup0 derivation sidecar required
to reconstruct the range. The outer codec is specified in §4 and Appendix B. The exact
`eez-evm@0.2-draft` objects embedded in that sidecar come from EEZ Appendix B.

Version 0.2 retains signed deterministic system transactions as a network choice, but the
production authorization is unresolved. A private EOA key conflicts with permissionless
independent reconstruction: withholding it prevents open following, while distributing it permits
forgery. Production activation MUST select and specify a design that resolves this conflict.

## 1.6 Proof Policy States

Three states must remain distinct:

- **Current default development path:** one threshold-1 mock verifier that ignores the batch
  public-input hash. It is unsafe and nonconforming.
- **Current optional implementation path:** one remote ECDSA attester that independently
  re-executes a window and signs a batch-bound public-input hash. It is evidence for a future
  implementation, not the production policy.
- **Production Rollup0 policy:** an authenticated validator/prover set, accepted proof-system
  contracts, verification keys, threshold, authorization, and rotation rules. All are unresolved.

An activation record MUST also define how validators bind their decision to every submitted field
that the selected EEZ public-input hash omits.

## 1.7 Development Genesis

Appendix D retains the reviewed implementation-development genesis template and its Chiado
timestamp-derivation procedure. It has EIP-155 chain ID `1`, a public system key, and test
allocations. It MUST NOT be used as a production identity.

Production requires a separate byte-exact genesis and manifest. No production chain ID, genesis,
native-asset policy, or deployment tuple is specified by this draft.

---

*Next: [§2 Timing, Production, and Header Rules](02-block-production.md).*
