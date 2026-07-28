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

## E.3 System Calls and Test Verification

The current client represents privileged system execution as an ordinary signed transaction from
a public development key. Production Rollup0 uses an EIP-4788-style system call with no private
key, signature, transaction nonce, or transaction envelope. Its remaining gas, value, log, and
block-commitment rules are still to be defined. The development key and its restricted capabilities
are implementation aids, not protocol rules. Current manager bookkeeping can also leave persistent
state after a target failure. Production lowering must keep a failed action state-root-neutral while
committing its call and result in the block.

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

*This is the final appendix.*
