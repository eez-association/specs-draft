# 11. Gas, Limits, and Economics

## 11.1 Rollup0 Execution Gas

Rollup0 blocks use a gas limit of `30,000,000`. Transaction gas follows the selected EVM fork.
The base fee follows EIP-1559 and is derived from the parent header with:

```text
elasticity multiplier       = 2
base-fee-change denominator = 50
gas target per block        = 15,000,000
```

The gas limit and both EIP-1559 parameters are fixed chain rules. The target is half of the block
gas limit; it is not an additional limit. A block can use up to `30,000,000` gas.

Ordinary and protocol-derived transactions share this limit. Fusaka caps every individual
transaction gas limit at `16,777,216` (`2^24`). An inbound protocol transaction encodes the lower
of that value and the gas remaining when it starts. The value is frozen for inbound envelope
version `0`; ordinary signed transactions follow the active fork if a later Ethereum fork changes
its cap. Rollup0 charges the active fork's standard non-creation intrinsic gas and calldata floor
over the inbound calldata. Intrinsic, calldata-floor, and EVM execution gas contribute to its typed
receipt and the block's `gasUsed`.

Fusaka also limits the RLP-encoded execution block to `8,388,608` bytes under EIP-7934. A block
must satisfy both this byte limit and the `30,000,000` gas limit.

Rollup0 does not admit L2 blob transactions and therefore charges no L2 blob gas. Every Rollup0
block has zero `blobGasUsed`. Ethereum blob gas paid by a settlement transaction is an L1 data
availability cost and is not part of Rollup0 block execution.

Ordinary signed transactions use Ethereum's fee rules with one change: Rollup0 does not burn the
base fee. Every amount that Ethereum would burn is instead credited to the chain's fee-collector
account, `FEE_COLLECTOR`. When an ordinary signed transaction completes, after its gas refund,
Rollup0:

1. credits the composer-selected block `beneficiary` with the priority fee, exactly as Ethereum
   does;
2. credits `FEE_COLLECTOR` with `baseFeePerGas * gasUsed`, where `gasUsed` is the transaction's
   final gas use after refunds; and
3. for a blob-carrying transaction, also credits `FEE_COLLECTOR` with the blob fee
   `blobGasUsed * blobBaseFee` that Ethereum would burn.

The credits are plain balance increases. They do not call or execute code at `FEE_COLLECTOR`, and
they do not change its nonce. They take effect at the end of each transaction, so a later
transaction in the same block observes the increased balance. If `FEE_COLLECTOR` equals the block
`beneficiary`, that account receives both amounts. The sender's deduction, the upfront-balance and
fee-cap checks, `BASEFEE`, `GASPRICE`, and JSON-RPC `effectiveGasPrice` are unchanged from
Ethereum. Only the destination of the base-fee and blob-fee amounts changes.

Rollup0 does not admit L2 blob transactions, so step 3 always credits zero under the current rules.
The rule is defined anyway so that Rollup0's fee routing matches Gnosis Chain's and remains complete
if a later version admits blob transactions.

`FEE_COLLECTOR` is a genesis chain parameter. It is an ordinary account with no reserved code or
privileges. Changing it after genesis changes block state transitions and therefore requires a
Rollup0 hardfork. The Rollup0 value is not yet fixed (Appendix A.3).

The Rollup0 genesis base fee is `1,000,000,000` wei (`1 gwei`), matching Ethereum's standard
initial base fee.

!!! success "DECISION: collect base fees instead of burning them"
    Rollup0 credits base fees and blob fees to `FEE_COLLECTOR` instead of burning them. This is the
    fee-collector rule that Gnosis Chain has applied since the merge, where burning the
    stablecoin-backed native currency would serve no monetary purpose.

    The same reasoning applies to Rollup0. Its native ETH is not issued by Rollup0's own consensus;
    it is a claim backed by Rollup0's `etherBalance` ledger in the L1 EEZ contract (Chapter 5).
    Burning L2 fees would permanently strand the matching L1 backing. Collecting them keeps the L2
    native supply equal to the value that entered through EEZ.

!!! success "DECISION: type-`0x45` pays no L2 fee"
    Type-`0x45` inbound transactions have no fee fields or payer. They consume and report gas but
    skip ordinary fee-cap, upfront-balance, deduction, and refund processing. `GASPRICE`, JSON-RPC
    `gasPrice`, and receipt `effectiveGasPrice` are all zero. Their gas credits nothing to
    `FEE_COLLECTOR` or the block `beneficiary`.

[Appendix B](B-gas-cost-analysis.md) explains why Rollup0 uses `2/50` rather than Ethereum's
`2/8` or the earlier `6/250` proposal.

## 11.2 Candidate Costs and Revenue

Candidate production can create costs for several participants:

- composers bear block construction, Rollup0 execution, and retry costs;
- validators or provers bear validation or proving costs;
- the blob-transaction sender pays Ethereum DA and settlement-execution fees;
- each trigger sender pays its Ethereum transaction fees; and
- relayers, builders, or other parties may bear or receive private inclusion payments.

Ordinary signed Rollup0 transactions use the only protocol-level fee mechanism currently defined:
their base fee is credited to `FEE_COLLECTOR` and their priority fee is paid to the block
`beneficiary`. Fee-collector balances are not a reimbursement mechanism either. Rollup0 defines
no protocol-level reimbursement for candidate construction, validation, proving, DA, settlement,
failed candidates, or losing siblings. Participants may use private funding and payment
arrangements, but open composition does not imply that candidate production is profitable.

A planned permissioned Gnosis sister network, separate from Rollup0, may fund its
sequencer/composer operationally and require that operator to use a Gnosis-designated
`beneficiary`. Gnosis would receive the ordinary priority fees from blocks produced by that
operator and use them to offset its funding costs. This illustrates an operational arrangement;
it is not a Rollup0 reimbursement mechanism or profitability guarantee. Rollup0 itself retains
open composition and the composer-selected-beneficiary rule.

## 11.3 Data Availability Cost

Rollup0 publishes anchored chain data in Ethereum blobs. Cost follows Ethereum blob-gas pricing and
the number of blobs used by a candidate.

After a long anchoring outage, several catch-up anchors can be needed. Their total DA and
settlement cost grows with the backlog. Recovery-rate reporting remains open. Pure-L2 intake
backpressure is operational policy: composers SHOULD reduce or stop intake when that helps their
branch catch up.

V0 has no separate payload-size, block-count, or user-transaction-count cap below its natural
uncompressed DA bound. Appendix G explains the early byte-availability checks that prevent
declared counts from causing unbounded allocation. It also has no candidate-wide execution-work
cap: each block remains subject to the existing block gas limit, regardless of how composers split
the sequence into anchors.

There is no separate maximum number of catch-up intervals. Within the authenticated payload and
resource limits, a catch-up composer SHOULD use the largest blob allotment it can reasonably get
included and fill it with the longest complete valid historical prefix. Maximality is not a
validity rule, and a smaller candidate remains valid.

!!! note "CURRENT ETHEREUM DA CAPACITY, NOT A ROLLUP0 CONSTANT"
    Under Ethereum's Fusaka rules, [EIP-7594](https://eips.ethereum.org/EIPS/eip-7594) permits at
    most six blobs in one blob transaction. With the EEZ transport's 31 payload bytes per 32-byte
    field element, one blob carries at most
    `4,096 * 31 = 126,976` payload bytes and six carry at most `761,856` bytes before EEZ framing
    and message overhead. The usable Rollup0 V0 `operations` slice is therefore smaller.

    If a composer waits the complete 15-minute operational target, the unsettled range contains
    `900 / 2 = 450` scheduled Rollup0 blocks. One six-blob candidate then provides an absolute
    pre-overhead average of about `1,693` bytes per block. A busy composer must anchor earlier. If
    it publishes one maximum-size candidate every Ethereum slot, the corresponding absolute
    pre-overhead average is `761,856 / 6 = 126,976` bytes per newly scheduled Rollup0 block.

    These figures describe the current settlement fork, not Rollup0 consensus constants. A future
    Ethereum hardfork may change the per-transaction blob allowance or physical transport
    capacity, and Rollup0 V0 automatically uses the capacity admitted by that active fork and the
    selected EEZ stream version. Implementations MUST calculate limits from the active settlement
    rules rather than freeze the six-blob figure. Rollup0 still deliberately imposes no DA-derived
    per-block validity limit: an oversized unsafe block simply cannot become canonical through a
    valid anchor.

!!! note "PHYSICAL DA AND OPERATIONAL PROVING LIMITS"
    A validator or prover may reject or defer a request that exceeds its local capacity, but this
    does not make the candidate invalid. A future proof system that cannot cover all valid V0
    candidates needs an explicit activation rule. Rollup0 V1 does not add a protocol-level DA fee
    or reimbursement mechanism; the Ethereum blob-transaction sender pays the canonical L1 fees.
    A composer chooses whether a candidate is worth publishing, so an unwanted proposal cannot
    force it to incur blob cost.

## 11.4 Settlement and Bundle Limits

The settlement transaction, trigger, and all other transactions in their Ethereum block must fit
within the Ethereum block gas limit. The encoded proof or signatures and settlement calldata must
fit the selected inclusion mechanism. A validator or prover may decline an oversized request, but
its local capacity does not alter candidate validity.

Rollup0 imposes no smaller settlement-transaction gas budget of its own. The active Ethereum
per-transaction gas cap and the gas remaining in the containing Ethereum block are the validity
limits. Practical bundle capacity still depends on the final batch shape, proof threshold,
triggers, and the headroom a builder is willing to allocate.

## 11.5 Inbound Transaction Gas and Value

Chapter 3 defines the common gas pool and the protocol credit used for inbound value. Every
composer, validator or prover, and follower must reproduce the same gas use and value movement.

Type-`0x45` pays no L2 fee under the V1 rule in Chapter 3. Its inbound application value remains
separate: that value is backed by ETH held on Ethereum and temporarily credited for the exact
application call under Chapter 5.

A failed inbound action creates no Rollup0 transaction, consumes no Rollup0 block gas, and cannot
debit or credit fees in Rollup0 state. Its block hash and state root remain unchanged. Rollup0
defines no fee or reimbursement for simulating or proving that failure; the participant bears the
cost unless a private arrangement assigns it elsewhere.

---

*Next: [Chapter 12, Limitations and Open Issues](12-open-issues.md).*
