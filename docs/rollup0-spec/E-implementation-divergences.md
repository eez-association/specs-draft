# Appendix E. Current Implementation Differences

This appendix is informative. It describes known differences between the intended Rollup0
protocol and the current development client. It does not define protocol behavior, and an
independent implementation must not copy these differences. The main chapters and wire-format
appendices take precedence.

## E.1 Anchoring and Data Availability

The current client builds an anchor for every Ethereum head that it observes. Rollup0 instead
requires an anchor when synchronous execution occurs and after the configured maximum unanchored
period. That maximum period is still to be defined.

The current client publishes its Rollup0 payload in Ethereum calldata. Rollup0 will publish chain
data in Ethereum blobs. The current payload is not the Rollup0 blob format and does not bind an
exact, ordered trigger manifest to the blob. The final blob format must contain enough information
to reconstruct the anchored blocks, their boundaries, and the synchronous effects associated with
the Ethereum transactions.

## E.2 Transaction Ingress and Block Distribution

The intended ingress split is:

- pure-L2 transactions are gossiped;
- Ethereum transactions that request synchronous execution go to a composer's private pool; and
- a sequencer may redirect a synchronous request that it detects while building a pure-L2 block.

The current client does not implement this split consistently. Its private node-local queues cover
both inbound and outbound synchronous work, and its forwarding behavior is incomplete.

Followers currently obtain their unsafe view from one configured sequencer RPC endpoint. The
target design uses peer-to-peer block gossip. A follower may filter or prioritize producers by
their gossip signatures, but no producer is allowlisted on Rollup0. Producer identity is relevant
while choosing an unsafe view; it is not part of validity after a block settles on Ethereum.

The current peer-to-peer representation does not contain a standardized producer-signature
envelope. This prevents portable signature-based filtering and prioritization.

## E.3 Inbound Transactions and Test Verification

The current client represents privileged inbound execution as an ordinary signed legacy
transaction from a public development key. Production Rollup0 instead uses an unsigned,
protocol-derived EIP-2718 transaction. It remains in the normal transaction and receipt lists, but
has no private key or transaction nonce and cannot enter through the public transaction pool. The
development key and its restricted capabilities are implementation aids, not protocol rules.

The signed development transaction can provide `msg.value` only from its sender's existing
balance. It does not implement Rollup0's protocol credit for inbound native value or remove that
credit after a verified failure. It also uses a configured `2,000,000` transaction gas limit.
Production protocol transactions instead encode the gas remaining in the block's common gas pool.
The development transaction uses a configured gas price and ordinary transaction fee deduction;
Rollup0's production fee mechanism is still to be selected.

The current client puts zero in `parentBeaconBlockRoot` and applies the standard EIP-4788
pre-execution state update. Production Rollup0 also puts zero in the field, but must disable the
beacon-roots contract update because Rollup0 has no beacon chain.

The current client does not execute failed inbound actions end to end and assumes successful
inbound outcomes while building its privileged transactions. Its generated contract ABI also
targets an older `eez-core-protocol` layout. Production Rollup0 must generate its ABI from the
exact `EEZL2` artifact selected for genesis and implement the verified-failure path defined in
Chapter 3. A verified application failure must create a typed receipt with status `0` and roll back
the temporary value credit. Any other outer `EEZL2` failure invalidates the candidate.

Current `EEZL2` bookkeeping can also leave state, value, or logs after a target application
failure. Production Rollup0 requires the dedicated verified-failure error so the complete inbound
transaction frame rolls back and the `EEZL2` balance returns to its pre-transaction value.

The current transaction format does not contain the production source identifier or typed-envelope
rules. It therefore cannot provide the required origin binding or conformance vectors described in
Appendix D.

Development configurations may use a mock verifier that accepts a fixed digest. This verifier
exists only for tests. It does not validate a Rollup0 candidate and is not an allowed production
proof policy.

## E.4 Bundles and Applied Prefixes

The current submitter sends only the full candidate bundle. It does not submit one atomic bundle
for each possible trigger prefix, and the contracts do not implement a persistent prefix-progress
mechanism. It expects every included outer trigger transaction to succeed, as the target design
does, but it does not offer shorter successful prefixes when a longer choice fails.

The observer, derivation, and Ethereum-scanning paths do not yet derive the processed action prefix
safely in all cases. In particular, block-wide matching can misattribute effects when a block
contains repeated state roots, repeated call hashes, or more than one relevant batch. A conforming
follower uses Ethereum transaction and log order. It also replays a successful outer transaction
when a caught failed lookup leaves no retained EEZ log.

The current rich-batch path starts its EEZ state sequence at the parent root. The intended Sync
block first executes its pure-L2 transaction prefix. Settlement must therefore establish `R0`, the
state root after those pure-L2 transactions and before any synchronous effect. `R0` remains the
Sync-block root when no synchronous effect is applied.

The current contracts and client accept duplicate cross-chain call hashes in one candidate.
Identical calls can consequently be indistinguishable to the EEZ execution queue. The protocol
rule is still under discussion: bind actions to their Ethereum transaction hashes, if a standard
execution mechanism can authenticate that hash, or reject duplicate hashes during validation or
batch posting.

The current EEZ contract can accept more than one same-rollup batch in one Ethereum block when the
stored state root still matches. It does not store the Rollup0 block hash or number needed to make a
later sibling dynamically stale. Rollup0 requires a contract-level rule for one settlement per
Sync timestamp or an exact on-chain cursor check.

Some development fallback paths submit or execute the settlement transaction and its trigger
transactions separately. They do not provide same-block atomic transaction inclusion in the
required order and are not valid production settlement paths.

---

*Next: [Appendix F, Inbound Transaction Design](F-system-transaction-design.md).*
