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

The current payload contains per-block transaction counts, raw user transactions, and L2 execution
entries. It does not carry the production non-derived header inputs or exact production protocol
transaction envelopes. The current follower instead rebuilds blocks with development constants for
the beneficiary, `extraData`, `prevRandao`, and gas limit. Production validators and followers must
derive every root and the exact block hash from the blob inputs and the Rollup0 header rules.

The current remote-validator path receives full block data and execution witnesses separately from
the batch payload. It re-executes those blocks, but it does not yet derive the complete window from
the published payload or byte-compare every reconstructed block against it. Production validation
must close this gap before signing: the blocks being replayed must be the unique blocks derived from
the exact blobs committed by the EEZ public-input hash.

## E.2 Transaction Ingress and Block Distribution

The intended ingress split is:

- pure-L2 transactions are gossiped;
- Ethereum transactions that request synchronous execution go to a composer's private pool; and
- a sequencer should reject a pure-L2 transaction that reaches a cross-network proxy as an
  admission policy.

The current client does not implement this split consistently. Its private node-local queues cover
both inbound and outbound synchronous work. Routing a rejected Rollup0 transaction to a composer
for outbound synchronous execution is a Rollup0.x feature, not part of the initial protocol.
If a producer includes such a transaction without prepared EEZ data, the proxy reverts under
ordinary EVM rules; the block is not invalid solely because the transaction attempted the call.

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
balance. It does not implement Rollup0's protocol credit for successful inbound native value. It
also uses a configured `2,000,000` transaction gas limit.
Production protocol transactions instead encode the lower of the gas remaining in the block's
common gas pool and the Fusaka transaction cap of `16,777,216`. The development transaction uses
a configured gas price and ordinary transaction fee deduction; Rollup0's production fee mechanism
is still to be selected.

The current client puts zero in `parentBeaconBlockRoot` and applies the standard EIP-4788
pre-execution state update. Production Rollup0 also puts zero in the field, but must disable the
beacon-roots contract update because Rollup0 has no beacon chain.

The current client does not handle failed inbound actions end to end. Its composition path can omit
both the target delivery and the required L1 failed lookup. If the outer Ethereum transaction
catches the resulting EEZ missing-execution error, the bundle can still land even though the proxy
returned different revert data from the simulated Rollup0 application. An Ethereum contract that
branches on the revert data can then execute a different path. This is a production correctness
blocker, not only a missing receipt feature.

Production Rollup0 must publish one failed L1 lookup pinned to the correct Rollup0 pre-state, bind
it to the trigger manifest, and have every validator/prover reproduce its exact failure data. It
must not create an L2 protocol transaction for that action, and the failed action must end the
candidate manifest. The current `EEZL2` contract can encode a failed inner call inside a normally
returning system transaction, but that path can retain table, proxy, or value effects and is not
the selected Rollup0 behavior.

The generated client ABI also targets an older `eez-core-protocol` layout. Production Rollup0 must
generate its ABI from the exact `EEZL2` artifact selected for genesis.

The current `EEZL2` inbound entry point accepts arrays containing more than one execution entry or
top-level lookup, even though it executes only the first entry directly. Rollup0 keeps these array
fields for later protocol versions, but requires every supplied object to be consumed. Under the
initial rules, a successful inbound protocol transaction therefore contains exactly one L2
execution entry and no top-level L2 lookup. Candidate validation must reject extra or unused table
data.

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

The current client does not enforce the rule that a failed action ends the candidate manifest.
The current EEZ contract also has no unified cursor across successful execution entries and failed
lookups. A failed lookup remains reusable while its state-root pins match. The terminal-failure
rule therefore removes a prepared successful suffix, but does not prevent builder repackaging or
an appended transaction with the same call hash. Chapter 7 treats these as production blockers.

The observer, derivation, and Ethereum-scanning paths do not yet derive the processed action prefix
safely in all cases. In particular, block-wide matching can misattribute effects when a block
contains repeated state roots, repeated call hashes, or more than one relevant batch. A conforming
follower uses Ethereum transaction and log order. It also replays a successful outer transaction
when a caught failed lookup leaves no retained EEZ log.

The current rich-batch path starts its EEZ state sequence at the parent root. The intended Sync
block first executes its pure-L2 transaction prefix. Settlement must therefore establish `R0`, the
state root after those pure-L2 transactions and before any synchronous effect. `R0` remains the
Sync-block root when no synchronous effect is applied. Production anchors use a leading immediate
entry for the combined transition from the root currently stored by EEZ to `R0`; the blob, rather
than that entry, contains the individual blocks.

The current EEZ contract catches and skips an immediate entry that fails its checks, while the
outer `postAndVerifyBatch` call continues. `BatchPosted` can therefore be emitted without applying
the Rollup0 anchor root. Until Rollup0 selects contract-level enforcement, followers must require
the actual ordered root update and must not treat `BatchPosted` as anchor acceptance.

The current contracts and client accept duplicate cross-chain call hashes in one candidate.
Identical calls can consequently be indistinguishable to the EEZ execution queue. The protocol
rule is still under discussion: bind actions to their Ethereum transaction hashes, if a standard
execution mechanism can authenticate that hash, or reject duplicate hashes during validation or
batch posting.

The current client can collect more than one Ethereum-to-Rollup0 action from one Ethereum
transaction. Production Rollup0 permits exactly one such top-level action in the transaction's
complete execution trace. Validators and composers must inspect the full trace, including calls
made through intermediate Ethereum contracts, and reject a candidate containing a second action.

The current EEZ contract can accept more than one same-rollup batch in one Ethereum block when the
stored state root still matches. It does not store the Rollup0 block hash or number needed to make a
later sibling dynamically stale. Rollup0 requires a contract-level rule for one settlement per
Sync timestamp or an exact on-chain cursor check.

Some development fallback paths submit or execute the settlement transaction and its trigger
transactions separately. They do not provide same-block atomic transaction inclusion in the
required order and are not valid production settlement paths.

## E.5 Block Scheduling and Settlement Context

The development scheduler reserves some ordinary positions as `Future` positions and builds them
before their timestamps. This leaves enough time to generate a ZK proof before the target settlement
slot. `Future` is local scheduling metadata, not a Rollup0 block type. The ECDSA validator path does
not require a reserved proof window. A composer can still pre-build blocks or close transaction
intake early as an implementation choice.

A conforming chain always classifies the five non-Sync positions as Live positions. The development
catch-up scheduler can also label an intermediate scheduled Sync position as Live. Followers instead
derive Sync positions from the genesis-aligned timestamp and block-number grid.

The current client uses an EEZ batch without Ethereum settlement context. Its validator signatures
therefore do not commit the target timestamp and parent Ethereum block hash. Builder-side target
parameters do not provide this contract-level binding. Rollup0 batches use the EEZ current-settlement
context described in Chapter 4.

The current client puts zero in `prevRandao` for every Rollup0 block. Production Rollup0 derives a
different value for every block from the seed established by the latest successful canonical
anchor. The client does not yet read the post-block RANDAO mix from the corresponding Ethereum
beacon state, activate it after the anchored endpoint, or restore the preceding seed during an
anchor reorganization.

## E.6 Fee Market

The current client uses reth's standard Ethereum EIP-1559 calculation, with elasticity `2` and
denominator `8`. Rollup0 uses elasticity `2` and denominator `50`. The production client needs a
Rollup0 chain specification that applies `2/50` in both payload construction and header
validation.

---

*Next: [Appendix F, Inbound Transaction Design](F-system-transaction-design.md).*
