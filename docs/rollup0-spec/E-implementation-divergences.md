# Appendix E. Current Implementation Differences

This appendix is informative. It describes known differences between the intended Rollup0
protocol and the current development client. It does not define protocol behavior, and an
independent implementation must not copy these differences. The main chapters and wire-format
appendices take precedence.

## E.1 Anchoring and Data Availability

The current client builds an anchor for every Ethereum head that it observes. Rollup0 instead
requires an anchor when synchronous execution occurs and uses 15 minutes as its operational target
for the maximum unanchored period.

The current client does not implement production historical catch-up anchors. Rollup0 can settle
several contiguous old pure-L2 ranges over successive Ethereum blocks. Each range ends at an old
Sync position, has no synchronous action, and keeps the seed from the latest live anchor. The
current development catch-up scheduler is only local scheduling behavior and does not provide
these settlement and RANDAO rules.

The current client publishes its Rollup0 payload in Ethereum calldata. Rollup0 will publish chain
data in Ethereum blobs. The current payload is not the Rollup0 blob format and does not bind an
exact, ordered action manifest to the blob. Appendix D's normative V0 payload and its surrounding
EEZ messages contain the authenticated inputs needed to reconstruct the anchored blocks, their
boundaries, and the synchronous effects selected by canonical Ethereum.

The current payload contains per-block transaction counts, raw user transactions, and L2 execution
entries. It does not carry all production non-derived header and protocol-transaction inputs. The
production payload does not duplicate derived type-`0x45` envelope bytes. The current follower
instead rebuilds blocks with development constants for the beneficiary, `extraData`, `prevRandao`,
and gas limit. Production validators and followers must derive every transaction, root, and exact
block hash from the authenticated inputs and the Rollup0 rules.

The current client registers the Rollup0 genesis EVM state root in EEZ and uses EVM state roots in
its state deltas, lookup pins, prover checks, and settled-cursor matching. Production Rollup0
registers the genesis block hash and uses terminal block hashes for all of those EEZ values. The
composer, prover, observer, and deriver must still calculate each EVM state root, but must compare
EEZ's legacy state-named fields with the corresponding reconstructed block hash.

The current `prove.v1` gRPC path is the reference implementation's composer-to-validator
transport. It is not a Rollup0 consensus interface. A composer streams a header followed by block
data and execution witnesses; the remote prover re-executes the window, recomputes the
public-input hash, and returns an ECDSA signature.

The current composer uses one configured remote prover rather than collecting an `N`-of-`M`
signature set. The stream carries one realized block window, not the complete action manifest,
terminal variants, prefix bundles, and final blob bytes required by this specification. It also
does not yet derive the complete window from the published payload or byte-compare every
reconstructed block against it. Production validation must close these gaps before signing: the
blocks being replayed must be the unique blocks derived from the exact blobs committed by the EEZ
public-input hash.

The current reference Rollup manager stores its active proof systems and threshold independently.
It does not count `M`, derive `floor(2M / 3) + 1`, or reject zero and impossible thresholds.
Production Rollup0 uses atomic EEZ team Safe transactions to keep membership and threshold aligned.
The contract therefore relies on the configuration trust assumption in Chapter 8.

The current gRPC client and server do not configure encrypted transport. A production deployment
that sends private signed Ethereum trigger transactions through this interface must encrypt the
channel and authenticate the validator endpoint.

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
target design uses peer-to-peer block gossip and requires an Appendix D producer signature before
a follower adopts a remotely announced block as unsafe. Rollup0 does not restrict the producer
key; the recovered identity supports local filtering and prioritization. Any peer may relay the
signed announcement and block. Producer identity is not part of validity after a block settles on
Ethereum.

The current follower also lacks the production bootstrap flow that reads a finalized Rollup0 block
hash from EEZ and uses that exact header as its `eth` chain checkpoint. The authenticated header's
EVM state root is the `snap` state target. Production peers serve normal Rollup0 chain and state
data; they do not need to archive blob sidecars.

The current peer-to-peer representation does not contain the standardized unsafe-block
announcement. Production clients must encode, verify, retain, and relay the Appendix D envelope and
associate it with the block identified by its signed hash.

The current implementation names its main block-production loop the sequencer and uses the
composer mainly for Sync-block contents and settlement. The Rollup0 specification uses
**composer** for any party that constructs candidates and **sequencer** for a producer that signs
unsafe blocks. Block relay, synchronization, and RPC do not themselves make a peer the producer.
Implementers must follow the protocol roles, not the current internal type names.

## E.3 Inbound Transactions and Test Verification

The current client represents privileged inbound execution as an ordinary signed legacy
transaction from a public development key. Production Rollup0 instead uses an unsigned,
protocol-derived type-`0x45` EIP-2718 transaction. It remains in the normal transaction and receipt
lists, but has no private key or transaction nonce and cannot enter through the public transaction
pool. The development key and its restricted capabilities are implementation aids, not protocol
rules.

The signed development transaction can provide `msg.value` only from its sender's existing
balance. It does not implement Rollup0's protocol credit for successful inbound native value. It
also uses a configured `2,000,000` transaction gas limit.
Production protocol transactions instead encode the lower of the gas remaining in the block's
common gas pool and the Fusaka transaction cap of `16,777,216`. The development transaction uses
a configured gas price and ordinary transaction fee deduction; production type-`0x45` transactions
have no fee fields or payer, report a zero gas price, and cause no fee deduction, burn, or
beneficiary credit.

The current client puts zero in `parentBeaconBlockRoot` and applies the standard EIP-4788
pre-execution state update. Production Rollup0 also puts zero in the field, but must disable the
beacon-roots contract update because Rollup0 has no beacon chain.

The current execution paths also use standard Prague request processing. That processing can
extract EIP-6110 deposit requests and run the EIP-7002 withdrawal and EIP-7251 consolidation
request system calls. The current genesis omits the associated contracts, so these paths are
usually empty or no-ops, but absence is not an explicit Rollup0 rule. Production execution must
disable these consensus-layer request paths and enforce the empty `requestsHash` defined in
Chapter 4.

The current node uses standard Ethereum transaction admission and block validation and does not
enforce Rollup0's ban on L2 blob transactions. Production transaction-pool, RPC, payload-building,
and block-validation paths must reject type-`0x03` transactions. This is separate from the L1 blob
transaction used to publish Rollup0 data.

The current client does not handle failed inbound actions end to end. Its composition path can omit
both the target delivery and the required L1 failed lookup. If the outer Ethereum transaction
catches the resulting EEZ missing-execution error, the bundle can still land even though the proxy
returned different revert data from the simulated Rollup0 application. An Ethereum contract that
branches on the revert data can then execute a different path. This is a production correctness
blocker, not only a missing receipt feature.

Production Rollup0 must publish one failed L1 lookup pinned to the correct Rollup0 pre-state, bind
it to the action manifest, and have every validator/prover reproduce its exact failure data. It
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

The current transaction format does not contain the production `sourceHash` or type-`0x45` envelope.
It therefore does not implement the required origin binding or match the transaction and RPC
schemas in Appendices D and F.

Development configurations may use a mock verifier that accepts a fixed digest. This verifier
exists only for tests. It does not validate a Rollup0 candidate and is not an allowed production
proof policy.

## E.4 Bundles and Applied Prefixes

The current submitter sends only the full candidate bundle. It does not offer shorter proposed
trigger prefixes when a longer choice fails. The exact prefix-bundle submission strategy remains
operational policy, but production delivery should make useful shorter prefixes available and
should not broadcast the transactions independently through the public mempool.

The current remote-validator path receives one realized Rollup0 block window. It does not receive
and validate the complete ordered action manifest, every terminal variant `B[0]` through `B[s]`,
or every proposed Ethereum prefix bundle. Production validators must check that complete candidate
before providing its single proof or signature set.

The current client does not enforce the rule that a failed action ends the candidate manifest.
Production V1 requires that terminal rule. A failed lookup remains reusable while its block-hash
commitment pins match; this is allowed because it creates no Rollup0 transition and no successful
suffix exists. A Rollup0 follower need not record whether the terminal failed lookup was used.

The observer, derivation, and Ethereum-scanning paths do not yet derive `k` safely in all cases. A
conforming follower uses Ethereum transaction and log order and assigns successful matching calls
to manifest positions in EEZ queue order. An L1 indexer may separately replay an outer transaction
to report a caught failed lookup, but that lookup does not affect Rollup0 derivation.

The current rich-batch path starts its EEZ state sequence at the parent EVM state root. Production
settlement instead starts from the parent block-hash commitment. The Sync block first executes its
pure-L2 transaction prefix, producing EVM state root `R0` and terminal block hash `H[0]`.
Production anchors use a leading immediate entry from `Hparent` to `H[0]`; the blob, rather than
that entry, contains the individual blocks.

The current EEZ contract catches and skips an immediate entry that fails its checks, while the
outer `postAndVerifyBatch` call continues. `BatchPosted` can therefore be emitted without applying
the Rollup0 anchor commitment. Rollup0 therefore accepts an anchor only after observing the actual
ordered `Hparent -> H[0]` commitment update. It does not treat `BatchPosted` as anchor acceptance.
Production Rollup0 also requires its settlement wrapper to verify this update and revert the whole
transaction when it was skipped. The production manager blocks direct EEZ submission, which makes
the wrapper check enforceable without changing EEZ.

The fixed EEZ public-input hash does not include `transientExecutionEntryCount` or
`transientLookupCallCount`. This is EEZ behavior, not an EL implementation bug. Rollup0 requires
the values `1` and `0`, respectively, but the current proof or signatures cannot prevent a
submitter from changing them. They define immediate-versus-deferred array prefixes; they do not
count synchronous triggers or protocol transactions. The production wrapper enforces `1` and `0`
for candidate protocol V1.

The current contracts and client accept duplicate cross-chain call hashes in one candidate.
Production Rollup0 also permits them, but defines their identity by ordered manifest position. The
current observer and protocol-transaction format do not yet implement that rule or derive the
settlement-context-and-manifest-index `sourceHash` required by Appendix F.

The current client can collect more than one Ethereum-to-Rollup0 action from one proposed trigger.
Production validators and composers must inspect its full trace, including calls made through
intermediate Ethereum contracts, and reject a proposal containing a second action. Because
ordered-call identity permits a substituted carrier transaction, the production L1 EEZ path must
also enforce at most one successful Rollup0 consumption per outer transaction and reject
blob-carrying triggers. The current contract does neither.

The current EEZ contract can verify more than one batch that contains Rollup0 in one Ethereum
block. A later sibling cannot apply its stale anchor-commitment transition, but the later batch
still replaces Rollup0's execution and lookup queues. Rollup0 requires at most one such batch per
Ethereum block. The production manager and settlement wrapper enforce this with the
`lastSettlementBlock` gate from Appendix D; the current implementation does not have that gate.

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

The current client submits `blockNumber = 0`, so its validator signatures do not commit the target
timestamp and parent Ethereum block hash. Builder-side target parameters do not provide this
contract-level binding. Its vendored EEZ interface also uses the older
`getTimestampAndBlockHash` manager call. The latest core protocol instead folds opaque manager
`getCustomData` into the public-input hash.

Production Rollup0 sets `blockNumber = 2^64 - 1` and uses the current-settlement context described
in Chapter 4.

The reference manager currently returns only the current Ethereum timestamp and parent block hash
for that sentinel. Production Rollup0 requires the expanded `customData` domain in Appendix D,
including the chain IDs and the EEZ, manager, wrapper, and rollup identities. It also requires the
manager's transaction-scoped wrapper authorization. The current client, manager, and submission
path do not implement that domain or gate. This requires Rollup0 manager and wrapper contracts, not
an EEZ change.

The current remote-validator path does not prove that the first supplied Rollup0 block extends the
current Ethereum-confirmed Rollup0 cursor. It checks a supplied block window, but does not bind the
window's first parent block number and hash to canonical Ethereum settlement evidence. Production
validators may pre-validate speculative work, but must perform this binding before signing.

The current client puts zero in `prevRandao` for every Rollup0 block. Production Rollup0 copies the
seed established by the latest successful canonical live anchor into every block until the next
refresh. The client does not yet read `prevRandao` from the authenticated header of the Ethereum
execution block containing that anchor, activate it after the live anchored endpoint, preserve it
across catch-up anchors, or restore the preceding seed during a live-anchor reorganization. It must
also initialize the genesis seed from the finalized Ethereum reference block named by the genesis
configuration.

## E.6 Fee Market

The current client uses reth's standard Ethereum EIP-1559 calculation, with elasticity `2` and
denominator `8`. Rollup0 uses elasticity `2` and denominator `50`. The production client needs a
Rollup0 chain specification that applies `2/50` in both payload construction and header
validation.

---

*Next: [Appendix F, Inbound Transaction Design](F-system-transaction-design.md).*
