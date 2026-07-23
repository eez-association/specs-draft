# 11. Gas, Limits & Economics

## 11.1 L2 gas

- **Block gas limit:** `30_000_000`, a protocol constant ([Appendix A](A-reference.md)).
- **Base fee:** standard EIP-1559 from the parent header; the elasticity multiplier and
  base-fee-change denominator are pinned in [Appendix A](A-reference.md).
- The L2 charges gas in its native token under the standard Cancun schedule (§3.1).

## 11.2 Fees (a Rollup0/GC choice)

How L2 fees are distributed is a **Rollup0/GC choice**, not an EEZ requirement. Rollup0/GC routes
fees to dedicated **fee-vault** recipients (base fee, priority fee, and the L1-data-fee portion)
rather than burning them; the exact recipients are deployment parameters
([Appendix A](A-reference.md)).

## 11.3 L1 settlement cost

Settlement costs the operator one `postAndVerifyBatch` transaction plus the bundle (§7.4), paid on
L1 in the L1 native token. The transaction has a gas budget ([Appendix A](A-reference.md)); the
per-batch user-transaction count bundled with it is bounded by L1 block-gas headroom under that
budget. Measured settlement gas figures and the bundle-size derivation are in
[Appendix B](B-gas-cost-analysis.md).

## 11.4 Data-availability cost

DA is posted on L1 (calldata in v0; blobs as the intended default, §7.1). Under elevated L1 fees
the per-batch DA cost dominates settlement cost. **Who bears the L1 DA cost is a Rollup0/GC choice**
— v0 has the operator absorb it; an L1-data-fee charged to L2 users and routed to a data-fee vault
is the intended production model ([Appendix A](A-reference.md)). The blob-vs-calldata channel is
chosen per batch by a submit-time cost comparison.

## 11.5 Inbound-execution gas and `SYSTEM_ADDRESS`

The inbound system transaction (§3.4) executes within a gas budget ([Appendix A](A-reference.md))
and mints the delivered `value`. `SYSTEM_ADDRESS` pays the L2 gas for inbound execution from its
own balance and is the mint source; its funding/top-up policy — and how minted value is backed by
L1-locked value (reconciled against the rollup's on-chain ether balance) — is a deployment
parameter ([Appendix A](A-reference.md)).

---

*Next: [§12 Open Issues & Limitations](12-open-issues.md).*
