# Appendix A. Gas & Cost Analysis

> **Informative.** These measurements and comparative estimates are not conformance requirements.

Measured host settlement gas, the bundle-size derivation, and the ECDSA-vs-BLS attestation
tradeoff that motivates the prospective Rollup1 design (§10).

## A.1 Measured settlement gas

Figures below are from the deployed contracts' own gas report (`forge test --gas-report`), averaged
over the test suite. They are indicative, not normative — gas depends on calldata size, entry count,
and warm/cold storage. They are the basis for the `POST_BATCH_GAS_LIMIT` and bundle-size bounds
([network profile](01-profile.md)).

| L1 function | Avg gas | Notes |
|---|---:|---|
| `postAndVerifyBatch` | ≈ 268,452 | settlement: verify attestation, fold public inputs, write state roots |
| `registerRollup` | ≈ 98,647 | one-time per rollup |
| `createCrossChainProxy` | ≈ 263,387 | first time a remote contract is referenced |
| `executeCrossChainCall` (consume) | ≈ 24,600 | per consumed cross-chain call |

`postAndVerifyBatch` scales with the number of execution entries and the attestation cost (A.3); the
measured figure is for the suite's representative batch shape.

## A.2 Bundle size & DA cost

A settlement bundle (§4.4) is `[postAndVerifyBatch, inbound source transactions...]` posted in one
Chiado block. The number of interactions that can ride with one settlement is bounded by Chiado
block-gas headroom after the settlement transaction's own budget
(`POST_BATCH_GAS_LIMIT`, [profile](01-profile.md)) and by the v0 maximum of three user
transactions.

**DA cost dominates under load.** The payload (§4.1) is posted as calldata. Under elevated host
base fee the per-batch DA cost can exceed settlement compute cost. Whether that cost is absorbed by
the operator or charged to L2 users is not variable in v0: the operator absorbs it, and there is no
L2 data surcharge (§7.4). A future cost-recovery mechanism requires a new profile version.

## A.3 Attestation cost: ECDSA multisig vs BLS aggregate

Rollup0 selects an **N-of-M ECDSA policy** whose production membership remains unpinned. The host
contract's attestation-verification cost grows with the number of signers; this scaling wall
motivates the move to **BLS aggregation** in the informative Rollup1 proposal (§10).

**ECDSA, N single-signer proof systems verified on-chain.** Rollup0 realises the quorum as N independent
single-signer verifiers
([EEZ Framework §5.1](../eez-protocol-spec/05-proving-settlement.md#51-proof-system-interface-and-policy)),
each checked by one `verify` STATICCALL doing one `ecrecover`
(`3,000` gas) over its `publicInputsHash[k]`. With `c_sig` the marginal per-attester overhead
(`ecrecover` + the external `verify` call + ~65 bytes of signature calldata), verification cost is
linear in the quorum:

```
gas_ecdsa(N) ≈ N · c_sig        with c_sig ≈ 3,000 (ecrecover) + calldata + membership check
```

For an illustrative small permissioned set, `N = 14` adds on the order of tens of thousands of
gas — small next to the rest of `postAndVerifyBatch`. Rollup0's production membership and threshold
remain release blockers, so this example does not select them.

**BLS, one aggregate verification.** A BLS aggregate signature verifies the whole signer set in a
single pairing check regardless of set size — on L1 (post-EIP-2537) a fixed cost `c_pair` plus the
work to aggregate the participating public keys:

```
gas_bls(N) ≈ c_pair + N · c_agg      with c_agg ≪ c_sig   (a G1 add/membership, not a pairing)
```

The constant `c_pair` (the pairing + final-exp) is large relative to a single `ecrecover`, but it is
**paid once**, and `c_agg` (a curve addition per participating key) is far cheaper than an
`ecrecover`.

**Crossover.** The two schemes cost roughly the same at the signer count where the ECDSA linear term
catches the BLS fixed cost:

```
N* ≈ c_pair / (c_sig − c_agg)
```

Below `N*`, ECDSA is cheaper (no pairing to amortize); above `N*`, BLS wins and then stays flat while
ECDSA keeps climbing. ECDSA can therefore be economical for a small Rollup0 permissioned set. The
informative Rollup1 proposal instead assumes a much larger permissionless set — a few hundred to
thousands of signers — where the ECDSA term would dominate the settlement transaction and BLS's
flat cost could be essential. The crossover motivates a prospective Rollup1 design axis (§10); it
is not a current Rollup0 requirement.

> Exact constants depend on the EIP-2537 precompile gas schedule and the aggregation circuit; the
> shape (ECDSA linear vs BLS flat-after-fixed) is what drives the design, and is stable regardless of
> the precise numbers.

---

*See also the [Rollup0 profile](01-profile.md).*
