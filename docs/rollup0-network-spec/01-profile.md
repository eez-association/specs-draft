# 1. Network Profile

## 1.1 Dependency and identity

This profile normatively selects:

```text
Rollup0 protocol:     rollup0-v0
Rollup0 profile:      rollup0-chiado@0.1-draft
EEZ framework:        eez-framework@0.1-draft
EVM binding:          eez-evm@0.1-rollup0
Settlement host:      gnosis-chain-eez-chiado-rollup0@0.1-draft
```

The EVM compatibility binding is pinned to
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` by
[§0](00-protocol-version.md). It is not wire-compatible with the current
`eez-evm@0.2-draft` binding sourced from `eez-core-protocol@3a6ca65`. A client implementing the
0.2 ABI does not implement Rollup0 v0.

`Rollup0` identifies the L2. `Gnosis Chiado` identifies its settlement network.
`MAINNET_ROLLUP_ID = 0` is the compatibility binding's label for that settlement-host execution
domain. It is not an EIP-155 chain ID and does not mean Ethereum mainnet.

Ownership is disjoint:

| Owner | Normative choices |
|---|---|
| [EEZ Framework](../eez-protocol-spec/index.md) | Reusable execution and settlement concepts and the network-profile contract |
| Rollup0 v0 compatibility binding | Exact `5c51e02` ABI, selectors, hashes, proxy code, and manager context call |
| Rollup0 Chiado profile | L2 identity, genesis, timing, headers, sequencing, DA, system transactions, derivation, fees, and proof policy |
| [Gnosis Chiado host](../gnosis-chain-eez-spec/index.md) | Host identity, consensus/finality, shared `EEZ` deployment, and atomic-inclusion capability |

## 1.2 Selected behavior

- **Cross-chain scope:** one flat call per accepted entry in either direction. An inbound entry
  delivers one L1→L2 call. An outbound entry loads one precomputed L2→L1 result immediately before
  its consuming L2 user transaction. Multi-call, nesting, and cross-chain reentrancy are disabled.
- **Settlement host:** Gnosis Chiado, EIP-155 chain ID `10200`, nominal block interval `5,000 ms`.
- **Timing:** `D1=5,000 ms`, `D2=1,000 ms`, proof budget `P=500 ms`, and submission slack
  `S=1,300 ms`. Thus `K=5`, with 3 Live, 1 Future, and 1 Sync block in a steady slot.
- **Headers:** `gasLimit=30,000,000`, zero beneficiary, zero `prev_randao`, empty `extraData`, and
  deterministic parent-derived timestamps. The complete 23-field rules are in §2.
- **Fees:** EIP-1559 elasticity `2`, change denominator `8`, genesis base fee `1 gwei`; base fees
  burn, tips accrue to the zero beneficiary, and v0 has no fee vault, oracle, or L1-data surcharge.
- **System transactions:** signed legacy EIP-155, RPC type `0x0`, from the prefunded
  `SYSTEM_ADDRESS`; `gasPrice=1,000,000,000 wei`, `gasLimit=2,000,000`
  ([Appendix C](C-system-transactions.md)).
- **Sequencing:** one centralized, permissioned operator. The default maximum speculative depth is
  64; zero disables that operational bound. One catch-up chunk contains at most 300 blocks.
- **Proof policy:** a manager-enforced threshold of independent single-signer ECDSA proof-system
  contracts; `crossProofSystemInteractions = bytes32(0)`.
- **Data availability:** full tag-`0x00` calldata with the user transactions and L1-shape
  derivation entries required for replay; `blobIndices` is empty.
- **Atomic inclusion:** `postAndVerifyBatch` and all inbound trigger transactions land whole and in
  order in one Chiado block, or none land. An outbound-only batch may contain only
  `postAndVerifyBatch`; at most three inbound user transactions may follow it.

## 1.3 Development genesis

This profile is machine-resolved as a development profile. It fixes EIP-155 chain ID `1`, EEZ
rollup ID `1`, the public development `SYSTEM_ADDRESS`, the byte-exact genesis template, and the
Appendix D deployment-derivation procedure. Those values are pinned in
[`network-profile.json`](network-profile.json) and [Appendix D](D-genesis-validity.md). They are
not production choices.

The Chiado development procedure replaces the template timestamp with a selected Chiado block
timestamp and retains the development chain ID and public keys. Its activation record supplies the
timestamp-source block and the resulting artifact and header commitments. Production requires a
separate profile version. A conforming production client MUST fail closed until that profile and
an authenticated activation record publish a production chain ID, genesis artifact and hashes,
contract addresses and code hashes, system identity, proof policy, and activation boundary.

## 1.4 Completion status

The machine-readable profile is [`network-profile.json`](network-profile.json). Production
activation remains blocked by:

- a unique L2 chain ID and authenticated genesis;
- canonical Chiado `EEZ`, Rollup0 manager, proof-system, and rollup-ID deployments;
- production native-asset custody and backing;
- production `SYSTEM_ADDRESS`, private-key custody/distribution, reserve, and top-up rules;
- validator identities, verification keys, threshold, and resolution of
  `R0-PROOF-ROUTING` with a versioned mitigation for the `5c51e02` proof digest's omission of both
  transient routing counts;
- sequencing authority, exact atomic relay, and upgrade/recovery procedures;
- production system/host funding and custody backing; and
- full implementation of the validation and recovery requirements in §§2, 4, 6, and 9.

The transaction envelope itself is not unresolved: Appendix C fixes the current signed legacy
format.
The blocker is the security and operational consequence of sharing its signing key.

## 1.5 Conventions

Normative key words have the meaning defined by the
[EEZ Framework conformance chapter](../eez-protocol-spec/01-scope-conformance.md). A profile value
change requires a versioned Rollup0 activation. An ABI, hash, selector, proxy-code, envelope, DA
grammar, or validation change requires a new protocol identifier under §0.4.

---

*Next: [§2 Timing, Slot Production & Header Rules](02-block-production.md).*
