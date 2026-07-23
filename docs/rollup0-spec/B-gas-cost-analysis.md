# Appendix B. Gas & Cost Analysis

Measured L1 settlement gas, the bundle-size derivation, and the ECDSA-vs-BLS attestation tradeoff
that motivates the Rollup1 signature scheme (§13).

## B.1 Measured settlement gas

Figures below are from the deployed contracts' own gas report (`forge test --gas-report`), averaged
over the test suite. They are indicative, not normative — gas depends on calldata size, entry count,
and warm/cold storage. They are the basis for the `POST_BATCH_GAS_LIMIT` and bundle-size bounds
([Appendix A](A-reference.md)).

| L1 function | Avg gas | Notes |
|---|---:|---|
| `postAndVerifyBatch` | ≈ 268,452 | settlement: verify attestation, fold public inputs, write state roots |
| `registerRollup` | ≈ 98,647 | one-time per rollup |
| `createCrossChainProxy` | ≈ 263,387 | first time a remote contract is referenced |
| `executeCrossChainCall` (consume) | ≈ 24,600 | per consumed cross-chain call |

`postAndVerifyBatch` scales with the number of execution entries and the attestation cost (B.3); the
measured figure is for the suite's representative batch shape.

## B.2 Bundle size & DA cost

A settlement bundle (§7.4) is `[postAndVerifyBatch, trigger]` posted in one L1 block. The number of
L2 user transactions that can ride with one settlement is bounded by **L1 block-gas headroom** after
the settlement transaction's own budget (`POST_BATCH_GAS_LIMIT`, [Appendix A](A-reference.md)) — the
exact bound is a deployment parameter (§12.2).

**DA cost dominates under load.** The payload (§7.1) is posted as calldata in v0 (blobs as the
intended default). Under elevated L1 base fee the per-batch DA cost exceeds settlement compute cost;
the blob-vs-calldata channel is chosen per batch by a submit-time cost comparison (§11.4). Whether
that cost is absorbed by the operator or charged to L2 users is a Rollup0/GC choice (§11.4).

## B.3 Attestation cost: ECDSA multisig vs BLS aggregate

v0 settles with an **N-of-M ECDSA multisig** (§8). The cost the L1 contract pays to verify the
attestation grows with the number of signers; this is the scaling wall that motivates the move to
**BLS aggregation** in Rollup1 (§13).

**ECDSA, N single-signer proof systems verified on-chain.** v0 realises the quorum as N independent
single-signer verifiers (§8.1), each checked by one `verify` STATICCALL doing one `ecrecover`
(`3,000` gas) over its `publicInputsHash[k]`. With `c_sig` the marginal per-attester overhead
(`ecrecover` + the external `verify` call + ~65 bytes of signature calldata), verification cost is
linear in the quorum:

```
gas_ecdsa(N) ≈ N · c_sig        with c_sig ≈ 3,000 (ecrecover) + calldata + membership check
```

For a small permissioned set (v0, `M ≤ 20`) this is acceptable: at, say, `N = 14` the attestation
adds on the order of tens of thousands of gas — small next to the rest of `postAndVerifyBatch`.

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
ECDSA keeps climbing. v0's small permissioned set sits **below** the crossover, so ECDSA is the right
v0 choice. Rollup1's large permissionless set sits far **above** it — a few hundred to thousands of
signers — where the ECDSA term would dominate the whole settlement transaction and BLS's flat cost is
essential. The crossover is exactly why the signature scheme is a Rollup1 axis (§13) and not a v0
one.

> Exact constants depend on the EIP-2537 precompile gas schedule and the aggregation circuit; the
> shape (ECDSA linear vs BLS flat-after-fixed) is what drives the design, and is stable regardless of
> the precise numbers.

---

*See also [Appendix A](A-reference.md). End of appendices.*
