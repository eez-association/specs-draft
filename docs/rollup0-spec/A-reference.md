# Appendix A. Reference

This appendix summarizes values defined in the main chapters. The chapter text takes precedence.

## A.1 Production Rule Summary

| Name | Value |
|---|---|
| Settlement network | Ethereum |
| Native currency | ETH |
| Nominal Ethereum interval | `12 seconds` |
| Rollup0 block interval | `2 seconds` |
| Positions per nominal interval | `6` |
| Position order | `5 Live, 1 Sync` |
| Operational anchor target | `15 minutes` |
| Unsafe block authentication | producer signature over chain ID and exact block hash |
| Unsafe producer policy | open; no Rollup0 signer allowlist |
| Block gas limit | `30,000,000` |
| EIP-1559 gas target | `15,000,000` |
| EIP-1559 elasticity multiplier | `2` |
| EIP-1559 base-fee-change denominator | `50` |
| Genesis base fee | `1,000,000,000` wei (`1 gwei`) |
| Initial EVM fork | Fusaka, using the Osaka execution-layer rules |
| Later EVM forks | Ethereum execution forks at their Ethereum mainnet activation timestamps |
| Inbound transaction type | unsigned EIP-2718 type `0x45` |
| Inbound transaction encoding | `0x45 || rlp([version, chainId, sourceHash, gasLimit, to, value, input])` |
| Inbound `sourceHash` version | `0`; settlement-context, manifest-index, and call-hash formula in Appendix F |
| Maximum inbound transaction gas limit | `16,777,216` (`2^24`), frozen for envelope version `0` |
| Inbound transaction gas limit | `min(remaining block gas, 16,777,216)` |
| Inbound transaction gas accounting | active fork's ordinary EVM execution gas plus standard non-creation intrinsic gas and calldata floor; displayed formulas are Osaka values |
| Inbound transaction fee | none; `GASPRICE`, RPC `gasPrice`, and receipt `effectiveGasPrice` are `0` |
| System caller | `0xfffffffffffffffffffffffffffffffffffffffe` |
| Inbound transaction access list | empty |
| Inbound transaction blob hashes | empty |
| Ordinary L2 blob transactions | invalid |
| `blobGasUsed` | `0` |
| Genesis `excessBlobGas` | `0` |
| EIP-2935 history update | enabled from genesis |
| `parentBeaconBlockRoot` | 32 zero bytes |
| EIP-4788 beacon-roots update | disabled |
| `requestsHash` | `sha256("")` |
| EIP-6110, EIP-7002, and EIP-7251 requests | disabled |
| `prevRandao` interval | six positions after each Sync timestamp `T` |
| RANDAO source | `prevRandao` of canonical Ethereum block `P(T)` with greatest timestamp `< T` |
| Seed activation | first Rollup0 block after `T`, independent of anchor inclusion |
| `prevRandao` mapping | direct copy of `P(T).prevRandao` throughout the interval |
| Initial RANDAO seed | direct copy from the finalized Ethereum reference block named by genesis |
| Block `beneficiary` | composer-selected and authenticated per block |
| Ordinary transaction fees | base fee burned; priority fee paid to `beneficiary` |
| `extraData` | zero to 32 composer-selected bytes |
| DA channel | Ethereum blobs |
| Ethereum trigger transaction type | non-blob only; type `0x03` and any sidecar-dependent trigger prohibited |
| Candidate `blobIndices` | nonempty canonical `[0, 1, ..., m - 1]`, covering every outer transaction blob |
| Candidate batch `callData` | empty byte string |
| Candidate EEZ message stream | EEZ Core stream version `0x00`; one `ChainOperation(chain_id = rollup0EezRollupId)` first, then zero or more action brackets, then `CloseBlobStream` |
| EEZ state commitment | terminal Rollup0 block hash `H[k]` after `k` successful actions |
| Registered initial commitment | Rollup0 genesis block hash |
| Candidate domain tag | `keccak256(bytes("EEZ_ROLLUP0_CANDIDATE_V1"))` |
| Candidate domain source | production Rollup0 manager `getCustomData(2^64 - 1)` |
| Settlement entry point | active permissionless Rollup0 settlement wrapper |
| V1 transient execution prefix | `1` entry: the anchor |
| V1 transient lookup prefix | `0` entries |
| Rollup0.x settlement update | atomically activate a new wrapper address and candidate-domain tag |
| Anchor acceptance | observed ordered previous-settled-block (`Hparent`) to `H[0]` EEZ commitment transition; `BatchPosted` alone is insufficient |
| Successful-action evidence | retained EEZ `ExecutionConsumed(callHash, rollupId, cursor)` followed by the entry's `L2ExecutionPerformed(rollupId, H[k])` |
| Late synchronization | finalized EEZ commitment as the authenticated checkpoint; standard execution-layer `eth` and `snap` protocols on Rollup0 for block and state data |
| Candidate production | open |
| Candidate relay | permissionless |
| Candidate selection | first applicable candidate in canonical Ethereum transaction order |
| Candidate lifetime | one intended Ethereum child slot |
| Rollup0 batch limit | one EEZ batch that contains Rollup0 per Ethereum block |
| Action identity | authenticated settlement context, manifest index, and EEZ call hash; outer transaction hash excluded |
| EEZ batch `blockNumber` | `2^64 - 1` (current settlement context) |
| Live-anchor endpoint | Sync timestamp equal to containing Ethereum block timestamp |
| Catch-up-anchor endpoint | older Sync timestamp; no synchronous action |
| Catch-up RANDAO behavior | no special case; use the interval value derived from `P(T)` |
| EEZ batch scope | Rollup0-only MUST for candidate protocol V1 |
| Failed application call | must be the terminal manifest action; L1 EEZ failed lookup; no Rollup0 transaction, receipt, commitment transition, or new block variant |
| `EEZL2` genesis balance | `0` |
| `EEZL2` inbound transaction balance rule | post-call balance equals pre-call balance |
| Ordinary genesis native balances | none |
| L1 native-value custody | pooled in EEZ and accounted through Rollup0's per-rollup `etherBalance` |

## A.2 Development Cadence

Chiado development uses:

```text
nominal interval       = 5 seconds
Rollup0 block interval = 1 second
positions              = 5
order                  = 4 Live, 1 Sync
```

These are not production values.

## A.3 Reserved Rollup0 Addresses and Types

| Item | Draft value |
|---|---|
| `EEZL2` predeploy | `0xee50000000000000000000000000000000000000` |
| `EEZL2` implementation | Exact `eez-core-protocol` version and bytecode selected and pinned for genesis; not yet fixed |

The production genesis must bind exact bytecode and exact protocol-transaction behavior.

## A.4 Validator Policy

| Item | Rule |
|---|---|
| Active set size | Dynamic `M >= 1` |
| Required threshold | `N = floor(2M / 3) + 1` |
| Membership authority | EEZ team Safe |
| Change activation | Canonical Ethereum transaction order |
| Membership and threshold update | Atomic when `M` changes |

Validator addresses and keys are active manager configuration, not genesis constants. There is no
protocol maximum for `M`; Ethereum settlement gas limits provide the practical bound.

!!! note "GENESIS PARAMETERS"
    The Rollup0 chain ID and finalized Ethereum reference block are not yet fixed. The initial
    RANDAO seed is copied from that reference block into the genesis header and first interval.
    Deployment-specific beneficiary policy and recipients are operational configuration, not
    genesis consensus fields.

## A.5 DA Format

!!! warning "CONFORMANCE SUITE INCOMPLETE"
    Rollup0 publishes anchored chain data in Ethereum blobs. [Appendix G](G-blob-payload-design.md)
    records the selected design, and [Appendix D](D-wire-formats.md) defines the byte-exact V0
    linear codec and initial codec vectors. Action-manifest, transaction-bearing, terminal-variant,
    and end-to-end derivation vectors remain required for production interoperability.

## A.6 Terms

- **Candidate:** one proposed Rollup0 range and its terminal variants, EEZ batch, DA payload,
  candidate domain, and settlement context. A completed candidate carries the required validator
  attestations. Proposed trigger transactions and prefix bundles are separate delivery data; they
  are checked during validation but are not part of candidate identity.
- **Action manifest:** the semantic ordered list derived from the candidate-authenticated top-level
  EEZ transaction brackets. Each bracket's zero-based ordinal is its `manifestIndex`; its call hash
  and expected outcome come from its call and return messages. Its initiating `tx_data` is empty,
  and it does not identify an exact outer Ethereum transaction.
- **Trigger:** a signed, non-blob Ethereum transaction whose execution produces the candidate's
  next expected EEZ call. A composer proposes exact triggers for bundle delivery. Within the same
  authenticated settlement context and manifest position, another permitted carrier transaction
  producing the same call hash realizes the same Rollup0 action.
- **Manifest action count (`n`):** the number of ordered actions in the complete candidate action
  manifest.
- **Candidate successful-action count (`s`):** the number of manifest actions whose expected
  outcome is success. If there is no failed action, `s = n`; if the final action is the permitted
  terminal failure, `s = n - 1`. The candidate defines terminal variants `B[0]` through `B[s]`.
- **Selected successful-action count (`k`):** the number of successful manifest actions actually
  consumed in canonical Ethereum order after the anchor, where `0 <= k <= s`. Omitted triggers and
  a caught terminal failure do not increase `k`; the selected endpoint remains `B[k]`.
- **`B[k]`:** the candidate's terminal Sync-block variant containing the pure-L2 transaction
  prefix followed by exactly the first `k` protocol transactions selected by successful actions.
- **`H[k]`:** the Rollup0 block hash of `B[k]`. EEZ stores this value as Rollup0's commitment.
- **`R[k]`:** the EVM state root in the header of `B[k]`; `R[0]` is also called `R0`.
- **Composer:** any party that constructs an anchor candidate from blocks it builds or adopts.
- **Sequencer (block producer):** the party that builds and signs an exact block for announcement
  to the pre-settlement unsafe view. Rollup0 permits any signing key, and the signature grants no
  settlement priority. A peer that merely syncs, relays, or serves the signed block is not its
  sequencer.
- **Validator/prover:** a member of the permissioned validity set that independently checks and
  signs or proves candidates.
- **Relayer:** any party that submits a completed candidate to Ethereum.
- **Follower:** a client that derives Rollup0 from canonical Ethereum.
- **Live block:** an ordinary Rollup0 block in a nominal interval.
- **Sync block:** the block at the scheduled final Rollup0 position for an Ethereum slot. It
  contains a pure-L2 transaction prefix followed by zero or more protocol transactions derived
  from successful synchronous actions.
- **Live anchor:** an anchor whose terminal Sync timestamp equals the containing Ethereum block
  timestamp. It can contain synchronous actions; its inclusion does not select the RANDAO seed.
- **Catch-up anchor:** an anchor whose terminal Sync timestamp is older than the containing
  Ethereum block timestamp. It contains only pure-L2 execution and has no special RANDAO behavior.
- **Protocol transaction:** an unsigned EIP-2718 transaction derived from a successful
  Ethereum-to-Rollup0 action and included after the Sync block's pure-L2 prefix.
- **Rollup0 state commitment:** the exact terminal Rollup0 block hash stored in EEZ fields that use
  the legacy `stateRoot` name. The EVM state root remains a separate field in the authenticated
  Rollup0 block header.
- **`Hparent`:** the hash of the latest Rollup0 block accepted through canonical Ethereum and
  currently stored by EEZ. It is the parent of the first block in a new candidate, not an Ethereum
  block hash.
- **Ethereum-confirmed cursor (settled cursor):** the exact Rollup0 block hash stored as its EEZ
  state commitment, together with the block number and EVM state root from the header authenticated
  by that hash. It is safe but not necessarily finalized and can retreat after an Ethereum
  reorganization.
- **Sibling:** one of several candidates built from the same settled parent.
- **Applicable:** valid and based on the current settled cursor when evaluated on Ethereum.
- **Stale:** based on a cursor that an earlier applicable candidate has superseded.

---

*Next: [Appendix B, Gas and Cost Model](B-gas-cost-analysis.md).*
