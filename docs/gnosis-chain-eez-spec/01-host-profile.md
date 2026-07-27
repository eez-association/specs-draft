# 1. Host Profile

## 1.1 EEZ dependency

This specification publishes two Chiado host profiles:

| Profile | EEZ framework | EVM binding |
|---|---|---|
| `gnosis-chain-eez-chiado@0.1-draft` | `eez-framework@0.1-draft` | `eez-evm@0.2-draft` |
| `gnosis-chain-eez-chiado-rollup0@0.1-draft` | `eez-framework@0.1-draft` | `eez-evm@0.1-rollup0` |

The profiles are not interchangeable. Each profile identifies a distinct binding-specific `EEZ`
deployment and has distinct deployment and governance blockers. A consumer MUST match both the
profile ID and version and the declared EVM binding version.

The Gnosis host profiles do not redefine EEZ contract semantics. The
[EEZ framework network-profile schema](../eez-protocol-spec/07-network-profile.md) remains
authoritative.

## 1.2 Chiado selection

The current implementation target is Gnosis Chiado:

| Field | Selection |
|---|---|
| Network | Gnosis Chiado testnet |
| EIP-155 chain ID | `10200` |
| Native asset | Chiado xDAI |
| Nominal slot | `5 s` |
| Minimum EEZ execution fork | Chiado Dencun, timestamp `1706724940` |
| Block gas limit | Canonical execution payload `gasLimit`, validated under the active Chiado chain configuration |
| Fee market | Canonical Chiado EIP-1559 and EIP-4844 header-transition rules |
| EEZ role | Settlement host |

Chain ID, native asset, and nominal slot time come from the
[official Chiado network definition](https://docs.gnosischain.com/about/networks/chiado), not
from a consumer-rollup configuration. The
[official Gnosis Dencun specification](https://docs.gnosischain.com/about/specs/hard-forks/dencun)
fixes Chiado activation at timestamp `1706724940` and activates EIP-1153, EIP-4844, and EIP-5656.
The deployment and every EEZ transaction MUST be in a canonical block at or after that activation.
A later fork is acceptable only while it retains the required Cancun-compatible opcode semantics.

Each host profile provides standard EVM transaction execution and canonical logs for its
binding-specific L1 `EEZ` contract. Rollup-specific state-transition verification, proof
thresholds, DA codecs, and derivation rules are selected by the rollup's own profile and manager.

The gas limit is not an EEZ constant. A client MUST read `gasLimit` from the canonical Chiado
execution payload and validate its transition under the canonical chain configuration active at
that block. Transaction base fees and blob fees likewise follow the canonical Chiado EIP-1559 and
EIP-4844 rules and header fields. Marking these fields `fixed` selects those consensus rules; it
does not freeze one observed header value.

## 1.3 Host requirements

For an EEZ rollup to claim conformance against either profile:

- the selected host service MUST provide whole, ordered, same-block inclusion for the `EEZ`
  transaction and every triggering transaction that the consumer treats as atomic;
- clients MUST identify the host by chain ID `10200`, not by the ambiguous label “GC”;
- clients MUST reject an EEZ execution before the Chiado Dencun activation or under an execution
  engine that lacks Cancun-compatible `TLOAD`, `TSTORE`, `BLOBHASH`, or `MCOPY`;
- clients MUST validate the block gas limit, base fee, gas use, blob-gas fields, and blob fee
  against the canonical Chiado execution configuration and parent-header transition rules;
- settlement evidence MUST identify the exact canonical transaction receipt and ordered log
  occurrence from the pinned `EEZ` address and, for a rollup-scoped event, the rollup ID selected by
  the consumer profile; matching only a root value or event signature elsewhere in the block is
  insufficient;
- host finality MUST be obtained from the canonical Chiado consensus view.

The atomic-inclusion mechanism remains binding-specific: `GC-ATOMIC-INCLUSION` applies to
`gnosis-chain-eez-chiado@0.1-draft`, and `GC-R0-ATOMIC-INCLUSION` applies to
`gnosis-chain-eez-chiado-rollup0@0.1-draft`. No production claim may infer one from a development
builder. If a consumer relies on this mechanism to protect submitter-controlled routing, it MUST
authenticate every caller and calldata field that its proof leaves unbound and MUST prevent proof
reuse or front-running. For `eez-evm@0.2-draft`, those fields include both transient prefix counts.
For `eez-evm@0.1-rollup0`, the Rollup0 profile defines the exact required caller, calldata, and
prefix-count authentication.

Bundle size is consumer policy and is not selected by either host profile. Atomic inclusion is an
external builder, relay, access, or wrapper guarantee. Ordinary EVM transaction execution does not
make two or more submitted transactions atomic and does not bind uncommitted routing inputs to a
proof.

---

*Next: [§2 Deployment & Release Blockers](02-deployment.md).*
