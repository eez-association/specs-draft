# Appendix A. Rollup0 Specification Differences

This appendix is informative. It lists the material differences between the
[Rollup0 specification](../rollup0-spec/index.md) and two implementations:

- **`eez-rollup0`** at commit `6ff63ec`, with its EEZ Core gitlink pinned to `9735f53`; and
- **`rollupX`** at commit `3b96266`, with its EEZ Core gitlink pinned to `855fe06`.

The comparison was made on 2026-10-06 by reading source code, tests, deployment scripts, and
committed genesis files. Nothing was built or executed. Paths are relative to each repository's
root. Paths that start with `core@<commit>:` are inside `eez-core-protocol` at that commit.
`rollupX` does not initialize its EEZ Core submodule in the checked tree, so its contract
behavior was read from `core@855fe06` directly.

Cosmetic differences, such as internal type names, are omitted unless they change behavior.
Chapter and section numbers refer to the Rollup0 specification.

## A.1 Summary

A check mark (✓) means the implementation conforms to the specification on that point.

| Area | Rollup0 specification | `eez-rollup0` | `rollupX` |
|---|---|---|---|
| EEZ Core version | One pinned version (Appendix D) | `9735f53` | `855fe06`; ABI and digest incompatible with `9735f53` |
| `EEZL2` predeploy | Fixed bytecode at `0xee50…0000`; hardfork to change (3.2) | Immutable at `0x4200…0007` | Upgradeable proxy at `0x4B27…402C` |
| Inbound transaction | Unsigned six-field type `0x45` with `sourceHash` and `gasLimit`; no version or nonce (3.3, F) | Unsigned type `0x76`, nonce, no `sourceHash` | Same as `eez-rollup0` |
| `SYSTEM_ADDRESS` | `0xffff…fffe` | `0xeeee…0076` | `0xeeee…0076` |
| Inbound gas limit | `min(remaining, 16,777,216)` | Fixed 2,000,000 | ✓ (implicit, not encoded) |
| Inbound value credit, zero fee | Required | ✓ | ✓ (sum over the whole table) |
| `EEZL2` balance neutrality | Checked per protocol transaction | Not checked | Not checked; pooled value allowed |
| Block-start balance burn | None | None ✓ | Zeroes `EEZL2` and `SYSTEM_ADDRESS` every block |
| Base fee | Credited to `FEE_COLLECTOR` (11.1) | Burned | Burned |
| EIP-1559 parameters | Elasticity 2, denominator 50 | 2 / 8 | ✓ |
| `prevRandao` | `P(T).prevRandao`, every interval | Always zero | Seed from the L1 block containing the latest live anchor |
| Genesis RANDAO reference | Finalized L1 block strictly before genesis | None | Reference at the same timestamp as genesis |
| EIP-4788 and EL requests | Disabled; empty `requestsHash` enforced | Stock behavior | ✓ |
| Block grid and timestamps | Consensus rule from genesis | Operational only | ✓ |
| Fixed header fields | Enforced on import | Built correctly, not enforced | ✓ |
| L2 blob transactions | Rejected | ✓ | ✓ |
| EIP-7702 triggers | Permitted | Rejected | Rejected or misclassified |
| Later hardforks | Adopted at mainnet timestamps | Not configured, not prevented | Rejected by code |
| Ordinary genesis balances | None | 22 prefunded accounts | ✓ (production base) |
| Data availability | Blobs, empty `callData` | Calldata | ✓ |
| V0 payload | Appendix D grammar | ✓ (all vectors pass) | Different count encoding; rejects Vectors 1 and 2 |
| Action profile | Inbound only, flat, terminal failure | Outbound and inbound; no failures | Outbound, nested, static, revert spans; non-terminal failures |
| One action per L1 transaction | Enforced | No | No |
| Blob-carrying triggers | Forbidden | n/a | Supported |
| `blockNumber` / `customData` | `2^64 - 1`; nine-field domain | `0`; empty | `2^64 - 1`; two fields |
| Wrapper, `lastSettlementBlock` | Required | Absent | Absent |
| Transient prefix counts | `1` / `0`, wrapper-enforced | `1 + outbound` / `0` | `1 + outbound` / `0` |
| `crossProofSystemInteractions` | Must be zero | Field does not exist | Field does not exist |
| Validator threshold | `N = floor(2M / 3) + 1` signatures | One signer only | One signer only |
| Parent and L1 context binding | Validators bind to canonical settlement | Not bound | ✓ |
| `H[0]` | Sync block after its pure-L2 prefix | Sync block before any transaction | ✓ |
| Prefix bundles | Should be offered | Full bundle only | Full bundle only |
| Public-mempool fallback | Not a settlement path | Present | ✓ (none) |
| Validator transport | Encrypted and authenticated | Plaintext | Plaintext |
| Follower input | Blobs via settlement wrapper | Calldata, direct EEZ call only | Blobs, direct EEZ call only |
| Unsafe-block distribution | Gossip with producer signature | Polls one RPC | Polls one RPC |
| Bootstrap | From finalized EEZ hash via `eth`/`snap` | Full replay | Full replay |
| Finalized view on reorg | Never retreats | Can retreat | Can retreat |

## A.2 EEZ Core Dependency

**Specification.** Appendix D requires one complete EEZ Core wire and digest version to be pinned.
Section 8.3 and Appendix D.1 require `crossProofSystemInteractions = bytes32(0)`. Sections 3.3,
9.5, and Appendix F rely on a terminal failed L1 lookup.

**Both implementations.**

- Neither pinned EEZ Core has a `crossProofSystemInteractions` field, so that requirement cannot be
  implemented. Both fold `customDataHashes` and a bound sender into the public input
  (`crates/eez-protocol/src/public_inputs.rs:33-50`, identical in both).
- Both force `bindMsgSenderInPublicInput = false`. The specification does not mention this field.
- Neither pin has a failed-lookup object. Both use `ExecutionEntry.success` and read-only
  `StaticExecutionEntry` instead of `LookupCall`.
- Both pins scan forward and skip non-matching queue entries (`_findMatchingEntry`;
  `core@855fe06:src/EEZ.sol:927-946`). Because each Rollup0 entry is chained by its
  `currentRoot` pin, this does not change the successful prefix, and `cursor = k - 1` still holds.

**Differences between the pins.** `855fe06` is 64 commits after `9735f53`. Several changes break
compatibility:

- `StateUpdate{rollupId, currentState, newState, int256 etherDelta}` became
  `RollupUpdate{rollupId, int192 etherDelta, currentRoot, newRoot}`. Entry hashes and
  `publicInputsHash` therefore differ between the two clients.
- `L2ExecutionPerformed` gained an `etherBalance` field, which changes its topic. `BatchPosted` and
  `StateUpdated`/`RootUpdated` also changed.
- `EEZL2.executeIncomingCrossChainCall` changed from explicit `destination`, `value`, `data`,
  `sourceAddress`, and `sourceRollup` arguments (selector `0x8d8461d9`) to
  `(ExecutionEntry[], StaticExecutionEntryL2[])` (selector `0xc3fb5f3d`). The `msg.value == value`
  check was removed (`core@855fe06:src/L2/EEZL2.sol:300-318`).
- `EEZ`, the `Rollup` manager, and `EEZL2` became upgradeable proxies. The reference manager accepts
  registration only from its owner.

`eez-rollup0`'s ABI mirror comments and test fixtures still name an older pin, `6fcc90b`
(`crates/eez-protocol/src/abi.rs:244`). The L2 ABI did not change between `6fcc90b` and `9735f53`.
`rollupX`'s selector-lock comment names `e84c2b6`.

## A.3 Genesis, Addresses, and Hardforks

| Item | Specification | `eez-rollup0` | `rollupX` |
|---|---|---|---|
| Chain ID | Not yet fixed | `6290` | `696990` |
| `EEZL2` | `0xee50…0000`, fixed bytecode | `0x4200…0007` (OP Stack namespace), immutable | `EEZProxy` at `0x4B27…402C`; ProxyAdmin owner in committed genesis is public Anvil key `0xf39F…2266` |
| `SYSTEM_ADDRESS` | `0xffff…fffe` (shared with EIP-2935) | `0xeeee…0076` | `0xeeee…0076` |
| `FEE_COLLECTOR` | Genesis parameter | Absent | Absent (`EEZ_L2_FEE_RECIPIENT` is only the coinbase) |
| Ordinary balances | None | 20 Anvil keys, `0xdead…dead`, and one other | None in `genesis.json`; `genesis.dev.json` is funded |
| Extra predeploys | None | Accept-all contract at `0x4200…0008` | None |
| RANDAO reference | Finalized L1 block strictly before genesis | None; `mixHash = 0` | Authenticated reference, but at the genesis timestamp; committed `genesis.json` uses a placeholder (Ethereum block 0) |
| Initial EEZ commitment | Genesis block hash | ✓ (`scripts/deploy.sh:240-251`) | ✓ (`scripts/deploy.sh:296-314`) |
| Forks | Osaka at genesis; later forks at mainnet timestamps | Through Osaka at 0; later forks not configured but not prevented | Through Osaka at 0; `amsterdam_time` and `bogota_time` rejected (`crates/eez-evm/src/profile.rs:85-117`) |
| Rollup ID | Assigned at registration | Assumed `1` | Assumed `1` |

`rollupX`'s fork rule conforms today because no later fork has been adopted. However, adopting
one will require a code change, not only a chain-specification entry.

`rollupX`'s upgradeable `EEZL2` contradicts Section 3.2: an ordinary L2 transaction from the proxy
owner can replace the implementation without a Rollup0 hardfork.

## A.4 Block Production and Headers

| Rule (Chapter 4) | `eez-rollup0` | `rollupX` |
|---|---|---|
| Sync positions at `n mod 6 = 0`; `timestamp = parent + 2` | Timing comes from environment variables (`crates/eez-driver/src/timing.rs:56-135`). Sync heights come from observed L1 heads. Import checks only that timestamps increase. | Enforced from genesis: (2 s, 6) for L1 chain 1 and (1 s, 5) for chain 10200 (`crates/eez-protocol/src/l2/derivation.rs:64-133`). |
| Genesis on the settlement slot grid | Depends on `scripts/deploy.sh` rewriting the timestamp. The committed `genesis.json` is off-grid. | Enforced. |
| `prevRandao = P(T).prevRandao` for all six blocks after `T` | Always zero (`crates/eez-driver/src/sequencer.rs:118-124`, `crates/eez-deriver/src/deriver.rs:783`). | `mix_hash` of the L1 block that contains the latest accepted live anchor. Catch-up anchors and intervals without an anchor keep the old seed (`crates/eez-l1/src/derivation.rs:309-326, 366-384`). |
| `parentBeaconBlockRoot = 0`, no EIP-4788 call | Root is zero, but the stock EIP-4788 call runs; it is a no-op only because the contract is absent from genesis. | ✓ Enforced (`crates/eez-evm/src/block.rs:136-160`). |
| No EL request processing; `requestsHash = sha256("")` | Stock Prague processing; hash not enforced. | ✓ Enforced (`crates/eez-evm/src/block.rs:204-222`). |
| Fixed `gasLimit` 30,000,000 and other fixed fields | Builder uses the right values. Import allows the stock ±1/1024 gas-limit drift. | ✓ Enforced on headers and Engine payloads (`crates/eez-protocol/src/l2.rs:43-77`). |
| Beneficiary chosen per block and carried in the payload | ✓ Carried. Always `0x0` in practice, so all priority fees go to the zero address. | ✓ Configurable via `EEZ_L2_FEE_RECIPIENT`. |
| No L2 blob transactions | ✓ Pool, executor, builder, and composer. | ✓ Same, plus `blobGasUsed` and `excessBlobGas` enforced. |

`rollupX`'s seed rule is the rule the specification rejected: the seed has a one-slot lag, depends
on whether an anchor landed, and treats catch-up anchors specially. On a reorg it restores the
last surviving live seed instead of recomputing `P(T)`.

`rollupX` lets any other settlement chain pick its own whole-second schedule. `genesis.dev.json`
uses 1 s and 4 positions. The specification defines only Ethereum and Chiado.

Both drivers keep a local `Future` label for positions built ahead of time. In `rollupX` this is
scheduling metadata only. In `eez-rollup0`, the catch-up path can also label an on-grid Sync
position `Live`.

## A.5 Fee Market

**Specification.** Section 11.1 credits `baseFeePerGas * gasUsed` and any blob fee of every
ordinary transaction to `FEE_COLLECTOR`. Nothing is burned. EIP-1559 uses elasticity 2 and
denominator 50, with a genesis base fee of 1 gwei.

| Rule | `eez-rollup0` | `rollupX` |
|---|---|---|
| Base-fee routing | Burned by stock reth execution (`crates/eez-evm/src/lib.rs:96-108`) | Burned by stock reth execution (`crates/eez-evm/src/block.rs:183-199`) |
| EIP-1559 parameters | Stock 2 / 8 | ✓ 2 / 50 (`crates/eez-protocol/src/l2.rs:29-33`) |
| Genesis base fee | ✓ 1 gwei (reth default) | ✓ 1 gwei, enforced |

Both clients would compute a different state root from a conforming client in every block with a
non-zero-gas ordinary transaction.

## A.6 Inbound Protocol Transactions

**Specification.** Section 3.3 and Appendix F define an unsigned type-`0x45` transaction with
payload `rlp([chainId, sourceHash, gasLimit, to, value, input])`, sent from `SYSTEM_ADDRESS`
to `EEZL2`. It has no version, nonce or fee. Its `SOURCE_ENTRY_V1` source hash binds the L2 chain
ID, intended L1 parent hash and original native execution-group index; candidate authorization
separately binds the remaining settlement context and call contents. A failed outer call invalidates
the candidate. `EEZL2`'s balance must be unchanged by each protocol transaction.

Both implementations replaced the signed development-key transaction described in Rollup0
Appendix E.3 with a native unsigned transaction (`docs/native-system-transactions.md` in
`eez-rollup0`). It differs from the specification as follows:

| Rule | `eez-rollup0` | `rollupX` |
|---|---|---|
| Envelope | Type `0x76`, `rlp([chainId, nonce, to, value, input])` (`crates/eez-primitives/src/lib.rs:13, 34-44`) | Same (`crates/eez-primitives/src/lib.rs:13, 60-69`) |
| `sourceHash` and origin binding | Absent; identical actions differ only by nonce | Absent |
| Nonce | Checked and incremented, so `SYSTEM_ADDRESS` becomes a persistent account | Same |
| Gas limit | Fixed 2,000,000; composer reserves 2M per delivery | `min(remaining, cap)`, not encoded; cap is read from revm instead of frozen at 2^24 |
| Fee | ✓ Zero gas price, no deduction | ✓ Same, plus empty access list, blobs, and authorization list enforced |
| Value credit | ✓ Mints exactly `value`; rolled back on failure | Mints the sum of every incoming call value in the table, including nested callbacks |
| Status-0 receipt | Block execution accepts it; only the signer and composer reject it | Same |
| `EEZL2` balance neutrality | Not checked | Not checked; `855fe06` treats `msg.value` as pooled funding |
| EIP-4788 call before execution | Runs | ✓ Skipped |
| RPC object | No `sourceHash` or `yParity`; real nonce; `gas` = 2M | Same, but `gas` reports the cap, not the applied budget |
| Pool and gossip | ✓ Type cannot enter the pool | ✓ Same, plus rejected by the payload builder and by the EVM for non-native senders |

**`rollupX` block-start burn.** `rollupX` zeroes the balances of `EEZL2` and `SYSTEM_ADDRESS` as a
pre-execution state change in every L2 block (`crates/eez-evm/src/block.rs:71-110, 157`). Rollup0
has no such rule. It changes the state root whenever either account holds ether, and it destroys L2
supply that is still backed on Ethereum, contradicting the no-burn supply argument in Sections 5.5
and 11.1.

**Extra protocol-transaction kind.** Both clients also emit a `loadExecutionTable` system
transaction followed by a signed user transaction that consumes it. These `[load, user]` pairs
carry outbound Rollup0-to-Ethereum calls. Section 9.4 says Rollup0 V1 has no such path, and the
specification defines only `executeIncomingCrossChainCall`. In both clients the Sync block orders
all outbound pairs first, then inbound deliveries.

**Entry shape.** Both `EEZL2` versions accept several execution entries and static entries but run
only `entries[0]`. Both signers narrow this to one entry and no static entries
(`crates/eez-proof-signer/src/settlement/inbound.rs:95-104` in `eez-rollup0`, `:122-131` in
`rollupX`). `eez-rollup0` also requires a flat entry. `rollupX` allows nested
`expectedOutgoingCalls`, which are Ethereum-to-Rollup0-to-Ethereum callbacks beyond V1.

### A.6.1 Native Format Alignment

The shared envelope and source-identity rules were checked on 2026-11-10 against:

- Rollup0 [PR #235](https://github.com/eez-association/eez-rollup0/pull/235), head
  [`d2b6359d`](https://github.com/eez-association/eez-rollup0/blob/d2b6359d5a325bcb505334c89dd613031be485a7/docs/native-system-transactions.md),
  open and unmerged at the time of comparison; and
- RollupX
  [`ff7a5cdc`](https://github.com/eez-association/eez-rollupX/blob/ff7a5cdc81ce02ad30c6c267c4554de77cecb753/docs/proposals/native-system-transactions.md).

Both use Appendix F's versionless six-field type-`0x45` envelope and `SOURCE_ENTRY_V1` formula.
They use the reserved sender, no native nonce increment, zero fees, an encoded remaining-block-gas
budget capped at `16,777,216`, and Ethereum RPC placeholders without a `version` field. The old
signed-legacy description in Rollup0 Appendix E.3 does not describe these revisions.

This alignment selects the common transaction representation and identity only. The following
execution and deployment differences remain; shared bytes do not establish full conformance:

| Rule | Rollup0 specification | PR #235 | RollupX |
|---|---|---|---|
| EEZL2 predeploy | `0xee50000000000000000000000000000000000000` | `0x4200000000000000000000000000000000000007` | `0x4B2760F84B83d6b3829E30A7573B0172B6d6402C` |
| Action profile | One successful inbound action per trigger | Inbound and outbound `[load, user]` groups; single-call profile | Broader grouped roots, nested callbacks and static lookups |
| Native value | Exact inbound action value | Exact inbound value; outbound loads have zero value | Checked incoming-value sum across the complete table, including callbacks |
| Protocol balances | Per-inbound EEZL2 balance neutrality; residual SYSTEM funds retained | Residual SYSTEM and EEZL2 funds retained | Both balances cleared after complete groups and at block finalization |
| Failed inbound action | Verified terminal L1 failed lookup, no L2 transaction | Unsupported by the settlement profile | Nonapplying inbound roots emit no standalone delivery within the broader group profile |
| Additional native type | No HistoryUpdate transaction | No HistoryUpdate transaction | Optional history type `0x46` |

The candidate, DA and settlement-authorization rules remain separate from `sourceHash`. Neither
the common source formula nor its conformance vector establishes those wider rules. Rollup0
PR #236's balance-clearing changes are not part of the #235 baseline compared here.

## A.7 Action Profile and Failed Actions

**Specification.** V1 candidates contain only Ethereum-to-Rollup0 actions. Each bracket has one
`Call`, with no `StaticCall`, `Snapshot`, `Revert`, or nested calls (Appendix D.4.1). A failed
action is an L1-only lookup that creates no L2 transaction, and it must be the final manifest
action. Each Ethereum trigger produces at most one action.

| Rule | `eez-rollup0` | `rollupX` |
|---|---|---|
| Directions | Anchor, outbound, inbound | Anchor, outbound, inbound effects and lookups |
| Nesting and static calls | Flat only | Nested and reentrant calls, top-level static calls, `Snapshot`/`Revert` regions (`crates/eez-proof-signer/SPEC.md:39-72`) |
| Failed actions | Not supported. The composer evicts reverting triggers and the protocol layer rejects `success = false`. | ✓ Lookup-only with no L2 transaction (`crates/eez-protocol/src/entries/materialize.rs:71-124`) |
| Failure is terminal | n/a | Not required. A later success may follow a failure (`crates/eez-proof-signer/src/settlement/effect_binding.rs:513-528`). |
| Revert spans in inbound tables | n/a | Allowed; inner effects can roll back inside a committed delivery |
| One action per L1 transaction | Not enforced; one trigger can yield several inbound deliveries | Same; several outbound calls per transaction are also allowed |
| L1 per-transaction consumption guard | Absent from `core@9735f53` | Absent from `core@855fe06` |
| Blob-carrying triggers | No blob support | Supported as "companion blobs"; blob capacity is reserved for them (`crates/eez-blob-codec/src/limits.rs:35-56`) |
| EIP-7702 triggers | Rejected by the cross-chain front (`crates/eez-node/src/ingress.rs:165-180`) | Allowlist applies only after a trace classifies the transaction as cross-chain. The trace omits the authorization list, so a trigger that reaches a proxy only through delegated code is likely forwarded to the L1 mempool. |
| `Call.gas` | Composer produces only zero | Decoder rejects any non-zero value (`crates/eez-protocol/src/blob_semantics.rs:282-284`) |

## A.8 Data Availability and Wire Formats

**Carrier.** `eez-rollup0` publishes the EEZ stream in `postAndVerifyBatch` calldata, without a
`CloseBlobStream` marker. Under EEZ Core's blob format, that stream is not valid. Public-input
hashing requires empty `blobIndices` (`crates/eez-protocol/src/public_inputs.rs:166-215`).
`rollupX` conforms: it sends a type-3 transaction with `blobIndices = [0..m)`, empty `callData`,
and a `ChainOperation`, brackets, and `CloseBlobStream` stream. Its field-element packing matches
EEZ Core's `BlobPacking.sol` and c-kzg. It rejects non-zero padding after the close marker. EEZ
Core says only that padding must be zeroed and that readers skip it.

**V0 payload.** `eez-rollup0` implements Appendix D.4.2 and D.4.3 exactly, and passes all seven
specification vectors (`crates/eez-payload-codec/src/lib.rs:703-815`). `rollupX` replaces the
`uvarint32` count column with run tokens (`crates/eez-payload-codec/src/v0/counts.rs`):

| Bytes | Meaning |
|---|---|
| `00` | One empty block |
| `01`–`7f` | 1–127 transactions |
| `80`–`bf` + 1 byte | 128–16,383 transactions |
| `c0`–`fe` | 2–64 empty blocks |
| `ff` + `uvarint` | 65 or more empty blocks |

`rollupX` rejects two adjacent empty tokens, so it rejects specification Vectors 1 and 2. It caps
each block at 16,383 transactions and drops the `block_count <= remaining` pre-check. Its
documentation describes this as a deliberate amendment (`docs/proposals/two-byte-da-v0.md`). Both
clients use payload version `0x00`, but neither can decode the other's payloads.

Both clients conform on `uvarint32` canonicality, maximal beneficiary and `extraData` runs, the
`T <= remaining / 2` check, exact body consumption, no compression, and the EEZ message field
encodings.

**Bracket profile.**

- `eez-rollup0` reads `tx_data` and discards it, so non-empty values are accepted; a test asserts
  this (`crates/eez-payload-codec/src/container.rs:431-445`). It emits outbound brackets.
- `rollupX` admits the full EEZ grammar inside the frame. For Rollup0-origin actions,
  `Initiate.tx_data` holds the signed L2 user transaction, which is published nowhere else. For
  Ethereum-origin brackets it requires empty `tx_data`.
- Neither enforces "no bracket after `ReturnFail`".
- `eez-rollup0`'s deriver skips a payload whose `ChainOperation` names another chain instead of
  rejecting it.

**Other wire formats.**

- Neither client implements the Appendix D.6 unsafe-block announcement or its domain tag.
- Both use the type-`0x76` envelope described in [A.6](#a6-inbound-protocol-transactions) instead
  of the Appendix D.5 envelope.
- `rollupX`'s `crates/eez-control-rpc/SPEC.md` Section 3.1 lists `blockNumber` as zero in a table
  but requires `uint64.max` a few paragraphs later. The code uses `uint64.max`.

## A.9 Composer, Validation, and Settlement

**Settlement contracts.** Neither repository contains a Rollup0 manager, settlement wrapper,
candidate domain, transaction-scoped manager authorization, or `lastSettlementBlock` gate. Both
deploy the reference `Rollup.sol` from their EEZ Core pin and call `postAndVerifyBatch` directly.
Both followers work around several batches in one Ethereum block off-chain. Neither treats
`BatchPosted` alone as anchor acceptance, which matches Section 8.4.

| Rule | `eez-rollup0` | `rollupX` |
|---|---|---|
| `blockNumber` | `0`, so `customData` is empty and signatures commit no slot | ✓ `2^64 - 1` |
| `customData` | Empty | `abi.encode(timestamp, parentHash)` only; no tag, chain IDs, or addresses |
| Transient prefix counts | `immediateEntryCount = 1 + outbound`; checked only by the signer and not in the digest | Same |
| Validators | One proof system, threshold 1; signer rejects any other shape | Same |
| Manager ownership | Deployer EOA, non-upgradeable | Deployer EOA; `EEZ` and manager are upgradeable proxies |
| Parent binding | Stateless backend binds nothing; stateful backend trusts the local follower database | ✓ Signer authenticates the parent settlement, the canonical L1 parent hash, and the registry root |
| `H[0]` | Terminal block before any transaction, so a Sync block cannot hold pure-L2 transactions | ✓ Includes the pure-L2 prefix |
| Intermediate `H[k]` | ✓ Checked through state checkpoints | ✓ Same |
| Trigger simulation | Not in the proof request | Not in the proof request |
| Prefix bundles | Full bundle only | Full bundle only |
| Public-mempool fallback | Falls back to sequential `send_raw_transaction` and continues after a rejected trigger (`crates/eez-l1/src/submitter.rs:277-360`) | ✓ No fallback; fans out to several relays |
| Historical catch-up | Ends only at empty Sync blocks and is not bound to a slot | ✓ Bound to the observed head's child |
| Anchoring policy | ✓ Anchors on every head, one bundle in flight | ✓ Configurable; meets the 15-minute target only if configured to |
| Validator transport | No TLS or caller authentication | Same; tracked in `PRODUCTION_READINESS_TODO.md` |
| Dedicated validator key | Only checked against `SYSTEM_ADDRESS` | Same |
| Mock verifier | ✓ Test-only | ✓ Test-only |

Both clients ship the same local `ECDSAProofSystem.sol`, which conforms to Appendix D.1.

An in-place upgrade of `rollupX`'s proxied manager keeps its address. The Appendix D.2 candidate
domain binds the manager by address, so it cannot detect such an upgrade. The `EEZ` upgrade owner
is a trust holder that Section 12.1 does not list.

## A.10 Derivation and Following

| Rule (Chapter 10) | `eez-rollup0` | `rollupX` |
|---|---|---|
| Data source | Calldata (`crates/eez-l1/src/scan.rs:600, 652`) | ✓ Beacon `blobs/{slot}` with a `blob_sidecars` fallback; recomputes KZG commitments and versioned hashes |
| Only applicable candidates are derived | ✓ Settlement is checked before decoding | Fetches and decodes blobs for every `BatchPosted`. Another rollup's batch, a failed batch, or pruned sidecars stall the follower (`crates/eez-l1/src/blob_source.rs:94`). |
| Wrapper-routed settlement | Decodes the transaction input as a direct `postAndVerifyBatch` call; a wrapper call is a hard error | Same |
| Deriving `k` | Reads `ExecutionConsumed`, but sorts applied indices and checks only counts and the final root | Ignores `ExecutionConsumed`; matches `newRoot` values against the claimed chain by position |
| Per-action cursor, call hash, and `H[k]` checks | No | No |
| Irreconcilable data | Retries forever; no halt | Logs `settlement_unmatched`, skips the batch, and retries; no halt |
| Finalized view on reorg | Clamped down to the new cursor | Same; halts also if the reorg crosses the genesis L1 reference |
| Reorg depth | Halts beyond a local 62-block limit | Same |
| Several settlements in one L1 block | Accepted; safe can be rewritten | Accepted; anchor-only batches dropped in favor of richer siblings |
| Anchor endpoint | Any block in range whose hash matches | Same |
| L1 evidence | Logs from RPC, not checked against `receiptsRoot` | Same; recomputes header hashes for the seed source |
| Live versus catch-up classification | None | ✓ Classified by schedule |
| Bootstrap | Replays from the deployment block or a local checkpoint | Same. Because blobs are mandatory, a new follower cannot sync history older than the beacon blob retention window (about 18 days). |

Both clients conform on these points: they accept a batch only after observing `L2ExecutionPerformed`
for Rollup0, check that the first block extends the settled commitment, compare the replayed
endpoint hash, and advance safe only after replay.

## A.11 Ingress and Block Distribution

**Unsafe blocks.** `crates/eez-follower/src/unsafe_head.rs` is identical in both clients. With
`EEZ_SEQUENCER_RPC` set, the follower polls one RPC once per block time, trusts the reported hash,
and fetches bodies through reth's normal sync. There is no gossip topic, no announcement envelope,
and no producer signature. Without that variable there is no unsafe view.

**Transaction ingress.** Both clients run private cross-chain fronts for Ethereum-originated and
Rollup0-originated synchronous transactions, so the outbound execution deferred to Rollup0.x is
already implemented. Pure-L2 transactions use reth's pool and devp2p gossip, as specified. Neither
rejects a pure-L2 transaction that reaches a proxy; such a transaction reverts at execution, which
the specification allows.

- `eez-rollup0` does not classify transactions. The endpoint chooses the direction, and a
  misdirected pure transaction is held and later evicted.
- `rollupX` classifies with a read-only trace, forwards ordinary transactions to the source chain's
  mempool, and fails closed when tracing is unavailable. It adds `eez_getCrossChainQueueStatus`,
  `eez_getCrossChainTransaction`, and an L1–L2 correlation RPC.

**Roles.** Both clients still call the block-production loop the sequencer and use the composer for
Sync-block contents and settlement. Implementers should follow the protocol roles in Section 2.1.

## A.12 Differences Between the Two Implementations

The two clients cannot interoperate. A chain produced by one cannot be derived or validated by
the other, for these reasons:

1. **EEZ Core.** Entry layout, event topics, and `publicInputsHash` differ between `9735f53` and
   `855fe06`.
2. **`EEZL2`.** The address, ABI, value check, and upgradeability differ.
3. **DA carrier and payload.** Calldata versus blobs, and different V0 count encodings under the
   same version byte.
4. **State transition.** `rollupX` burns protocol balances at each block start, applies 2/50 fees,
   disables EIP-4788 and requests, derives a non-zero `prevRandao`, and uses a different inbound gas
   limit and value credit.
5. **Settlement context.** `blockNumber = 0` versus `2^64 - 1`.
6. **Action profile.** `rollupX` accepts nested, static, revert-span, failed-lookup, and
   L2-origin `tx_data` actions that `eez-rollup0` rejects.

They share the type-`0x76` envelope, `SYSTEM_ADDRESS`, the unsafe-head follower, the proof-system
contract, the absence of a wrapper and `FEE_COLLECTOR`, and the single-signer validator path.

## A.13 Findings That Affect the Specification Text

The comparison also found places where the specification itself may need revision. They are listed
here, not changed in the normative chapters.

- **Skipped anchors.** Section 8.4, Section 12.1, and Rollup0 Appendix E.4 say that EEZ catches a
  stale immediate anchor, continues, and can still replace the action queues. Both pins revert the
  whole `postAndVerifyBatch` when every leading immediate entry fails (`AllImmediateL2TxsFailed`,
  `core@9735f53:src/EEZ.sol:413`). Both pins also reject an `immediateEntryCount` that leaves the
  leading entry in the queue (`ImmediateCountStrandsLeadingL2Tx`). For a V1 anchor-only leading run,
  a stale sibling therefore reverts and replaces no queue. The wrapper is still needed for the
  unsigned counts, V1 shape, blob binding, domain, and one-settlement-per-block rule.
- **EEZ protocol chapters.** The bundled [EEZ specification](../eez-protocol-spec/index.md) still
  describes `getTimestampAndBlockHash`, `crossProofSystemInteractions`, `LookupCall`, and
  `transientExecutionEntryCount`/`transientLookupCallCount`. Neither pinned EEZ Core has these.
- **Sequential consumption.** EEZ Core scans forward and skips non-matching entries. Rollup0's
  result is unchanged because entries are root-chained, but the normative text describes
  stop-on-mismatch semantics.
- **Blob padding.** EEZ Core does not say whether a reader rejects or ignores non-zero padding
  after `CloseBlobStream`. `rollupX` rejects it. This affects consensus and should be pinned.
- **`bindMsgSenderInPublicInput`.** The specification does not pin this field. It should be
  `false` for permissionless relay, or `true` with the wrapper as the bound sender.

## A.14 Status of Rollup0 Appendix E

[Rollup0 Appendix E](../rollup0-spec/E-implementation-divergences.md) was checked against
`eez-rollup0` commit `a4b9b2f1`. Several of its statements no longer hold:

| Appendix E statement | `eez-rollup0` now | `rollupX` now |
|---|---|---|
| E.1: genesis EVM state root registered; state roots used in EEZ | Block hashes registered and compared | Same |
| E.1: follower uses development constants for beneficiary and `extraData` | Taken from the payload; `prevRandao` still zero | Taken from the payload; seed rule differs (A.4) |
| E.1: payload in calldata | Still true, but now a V0 span inside an EEZ stream | Blobs |
| E.1, E.4: validator does not check every terminal variant | Every `H[k]` checked through checkpoints | Same |
| E.3: signed legacy transaction from a development key, 1 gwei fee, no value credit | Unsigned type `0x76`, zero fee, exact value credit | Same |
| E.3: fixed 2,000,000 gas | Still true | `min(remaining, cap)` |
| E.3: EIP-4788 call and Prague requests | Still true | Disabled |
| E.3: no L2 blob ban | Ban enforced | Ban enforced |
| E.3: ABI pinned to `6fcc90b6` | Pinned to `9735f53` | Pinned to `855fe06` |
| E.4: scanner matches the root chain by position | Uses `ExecutionConsumed` queue slots | Still true |
| E.4: EEZ silently skips a failing immediate anchor | Partly stale (A.13) | Partly stale (A.13) |
| E.4: public-mempool fallback | Still true | Removed |
| E.5: `blockNumber = 0` | Still true | `2^64 - 1` with two-field `customData` |
| E.5: `prevRandao` zero | Still true | Non-zero, anchor-driven |
| E.6: 2/8 fee parameters | Still true | 2/50 |
| E.6: base fee burned | Still true | Still true |

Other Appendix E statements still hold for both clients.

---

*This is the final appendix of the Implementations chapter.*
