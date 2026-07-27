# Gnosis Chain EEZ Network Specification

**A permissioned EEZ execution network settled on Ethereum**

| | |
|---|---|
| **Network protocol** | `gnosis-chain-eez@0.2-draft` |
| **Network profile** | `gnosis-chain-eez-ethereum@0.2-draft` |
| **Status** | Draft; no production activation exists |
| **EEZ framework** | [`eez-framework@0.1-draft`](../eez-protocol-spec/index.md) |
| **EVM binding** | `eez-evm@0.2-draft` |
| **Binding source** | `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c` |
| **Settlement network** | Ethereum mainnet; canonical Ethereum finality under common §6.3; contract deployments and activation are unresolved |
| **Candidate admission** | Full validity plus an authorized sequencer/composer signature |
| **Submission** | Any relayer may submit an authorized, proven batch |

Gnosis Chain and Rollup0 are separate EEZ execution networks. Neither network is the other
network's settlement host. They make nearly the same execution, block-production, data-availability,
and derivation choices. Gnosis Chain adds permissioned candidate authorization. Rollup0 does not.

This specification imports the exact, self-contained
`rollup0-common-execution@0.2-draft` ruleset instead of copying its algorithms. The import does not
include Rollup0's identity, activation, governance, admission policy, header parameters, fees, or
compatibility binding. [§1](01-profile-imports.md) maps every common parameter to its Gnosis
selection or explicit blocker.

An authorized Gnosis candidate is not valid merely because an authorized party signed it. The
Ethereum settlement path MUST verify both:

1. the complete network validity statement; and
2. a candidate authorization signature from the active Gnosis
   sequencer/composer set, checked by the Gnosis proof contract.

This draft does not assume that one contract performs both checks. The exact
composition of the validity verifier, authorization proof contract, and `EEZ`
call is a release blocker.

The signature authorizes a candidate, not a relayer. Any relayer may submit the exact authorized and
proven batch. When several authorized valid candidates extend the same settled parent, the first
applicable candidate in canonical Ethereum execution order wins. Later candidates for the stale
parent are not applicable.

No production Gnosis execution-network identity, genesis, deployment, authority set, signature
scheme, proof-contract deployment, or activation record is selected by this draft. The explicit
blockers are in [§4](04-implementation-conformance-status.md).

## Normative Reading Order

1. [Protocol Version and Precedence](00-protocol-version.md)
2. [Network Profile and Imported Rules](01-profile-imports.md)
3. [Candidate Admission and Canonical Selection](02-admission.md)
4. [Security and Trust Model](03-security-trust-model.md)
5. [Implementation and Conformance Status](04-implementation-conformance-status.md)
6. The EEZ framework chapters and the common execution rules named in §1

The machine-readable profile is [`network-profile.json`](network-profile.json). A human-readable
chapter controls when it is more restrictive than the draft profile. A conflict between two
supposedly identical fixed values is a release blocker.

[Return to the specification set](../index.md).
