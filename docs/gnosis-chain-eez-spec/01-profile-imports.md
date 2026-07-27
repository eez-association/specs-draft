# 1. Network Profile and Imported Rules

## 1.1 Independent Network Identity

Gnosis Chain is an EEZ execution network with its own state, blocks, chain identity, genesis,
activation, authorities, and governance. Rollup0 is a different EEZ execution network. Reusing
Rollup0 rules does not create a parent, child, host, or settlement relationship between them.

The production Gnosis network settles on Ethereum. Its intended cadence is:

```text
Ethereum settlement interval: 12 seconds
Gnosis block interval:          2 seconds
Gnosis blocks per interval:     6
```

The imported slot-role algorithm derives the Live/Future/Sync partition from the activated proof
budget and submission slack. Those values are unresolved, so this draft does not invent a
production partition.

The development timing profile settles on Chiado and uses:

```text
Chiado settlement interval:     5 seconds
Gnosis development block:       1 second
Gnosis blocks per interval:     5
```

The development proof budget, submission slack, catch-up bound, maximum candidate range, and
resulting Live/Future/Sync partition also require a development activation record. Chiado is a
development settlement environment. Its identity, deployments, keys, and state do not identify the
production Gnosis network.

The production settlement identity is Ethereum mainnet, chain ID `1`, with genesis block hash
`0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3`.
The Gnosis execution-network identity and genesis, and all production deployments, authorities,
and activation points, remain unresolved. The timing ratios do not select them.

## 1.2 Exact Import Manifest

This profile imports the complete
[`rollup0-common-execution@0.2-draft`](../rollup0-network-spec/common-execution.md) document and no
other Rollup0 text. The imported document is self-contained. Links from it to the Rollup0 chapters
are informative explanations and do not enlarge the import.

Gnosis supplies the common-rules parameters as follows:

| Parameter | Gnosis selection |
|---|---|
| `NETWORK` | the independent Gnosis execution-network identity; exact production identity and genesis are blockers |
| `SETTLEMENT` | Ethereum mainnet chain ID `1` and its exact genesis hash; canonical Ethereum finality under common §6.3; contracts and activation are blockers |
| `D1`, `D2` | `12000 ms` and `2000 ms` for production |
| `P`, `S_lead`, `C` | production blockers |
| `N_max` | maximum accepted candidate range; a production blocker |
| `HEADER` | the Gnosis genesis, fork, and header profile; unresolved fields are blockers |
| `ADMIT(c, p)` | authorization by the active sequencer/composer set under §2 |
| `PROOF_POLICY(c, p)` | the activated proof systems, verification keys, membership, threshold, and verification predicate; blockers |
| `MANAGER(n)` | the selected Gnosis manager's explicit Ethereum-block binding; a blocker |
| `SYSTEM_TX` | the selected Gnosis system transaction construction; a blocker |
| `LOWERING` | the deterministic field-by-field L1/L2 and explicit-inbound construction; a blocker |
| `BUNDLE` | the selected atomic Ethereum operation; a blocker |
| `CURSOR_GUARD` | enforceable exact-parent comparison and selected-cursor advancement; a blocker |
| `PREFIX_GUARD` | enforceable applied-prefix safety for caught failures and equal roots; a blocker |
| `ROUTING` | the activated candidate digest and proof-contract path that bind every effective routing field; a blocker |
| `FEES` | the selected Gnosis execution and settlement-cost policy; unresolved fields are blockers |
| `GOVERNANCE` | the selected Gnosis governance, rotation, upgrade, and recovery policy; a blocker |

The development profile replaces only its environment-specific selections: Chiado settlement,
`D1=5000 ms`, and `D2=1000 ms`. Development identities and deployments MUST be domain-separated
from production.

The import excludes `eez-evm@0.1-rollup0`, every retired compatibility ABI or hash, and every
Rollup0 value or policy that the common rules identify as a profile parameter. In particular, it
does not import Rollup0 identity, open admission, deployment values, proof membership, system
authorization, fees, governance, or development fixtures.

The import is by the named edition, complete document, and exact SHA-256 digest published in
`network-profile.json`, not by section anchors or a moving branch. A client MUST authenticate that
digest before applying the import. A change to an imported normative rule requires a new
`rollup0-common-execution` edition and a new Gnosis profile version or activation.

## 1.3 Gnosis Overrides

The only intentional policy difference between the Gnosis and Rollup0 selections of the common
rules is `ADMIT(c, p)`:

- Gnosis requires an authorization signature from the active sequencer/composer set in addition to
  full validity.
- Rollup0 admits a candidate based on validity without that Gnosis authorization.

Gnosis also has independent profile values. Different identity, genesis, cadence parameters,
settlement deployment, keys, authorities, or governance are profile data, not behavioral changes to
the shared execution algorithms.

If an implementation observes another unlisted behavioral difference, the implementation is not
conforming or the specifications require a new version.

## 1.4 Settlement and Finality

For production, canonical Ethereum transaction execution orders candidate applications and
canonical Ethereum finality finalizes them. A Gnosis block cannot become safe or finalized merely
because a composer published it or an authorized signer signed it.

For development, canonical Chiado execution and finality provide the corresponding settlement
view. Development records MUST be domain-separated from production and MUST NOT be accepted by a
production client.

The exact production Ethereum contract deployments and activation boundary are release blockers.
The Ethereum mainnet chain ID, genesis hash, and canonical-finality rule are fixed above.

---

*Next: [§2 Candidate Admission and Canonical Selection](02-admission.md).*
