# Appendix D. Genesis, Network Identity & Block Validity

This appendix is normative. It defines the Rollup0 genesis input, the procedure for deriving and
identifying a deployment genesis, and the checks a conforming client performs before accepting an
L2 block. The Ethereum execution rules remain applicable; the rules below add the Rollup0
constraints that make independently built blocks byte-identical.

## D.1 Network profiles and identity

The implementation repository contains one checked-in L2 genesis, reproduced byte-for-byte as
[`fixtures/genesis-dev.json`](fixtures/genesis-dev.json). It has `chainId = 1`, public development
accounts, and a public development `SYSTEM_ADDRESS` key. It is the **implementation-development
template only**:

- `chainId = 1` identifies the EIP-155 domain used by that development template. It does **not**
  mean that the L2 is Ethereum mainnet, and it is **not** a Rollup0 production network identity.
- The Chiado compose configuration derives a fresh-timestamp artifact from this template but does
  not replace `chainId = 1` or the public system identity. It selects the normative Rollup0
  1-second L2 block time. It is still a development/test configuration, not a production identity.
- The implementation sources do not publish a production L2 chain ID, production genesis
  timestamp, production genesis artifact/hash, or production system identity. A client started in
  production mode MUST fail closed until a production network manifest containing those values is
  published. A client MUST NOT silently treat the development template as that manifest.

A Rollup0 network is identified by the complete tuple:

```
(
  profile_version,
  l1_chain_id,
  l1_genesis_hash,
  eez_registry_address,
  rollup_id,
  rollup_manager_address,
  l2_chain_id,
  l2_block_time,
  system_address,
  genesis_artifact_sha256,
  genesis_state_root,
  genesis_block_hash
)
```

Neither `l2_chain_id` nor `rollup_id` alone identifies a network. In particular, `chainId` is an
EVM/signature-domain input and is not a genesis-header field: changing only `chainId` changes
`CHAINID` and transaction admission, but not the genesis state root or block hash. The manifest
hashes bind the otherwise header-invisible configuration.

For a production profile, `l2_chain_id` MUST be nonzero, MUST NOT be `1`, and MUST differ from
`l1_chain_id`. The chain ID applies to EIP-155 legacy signatures, typed-transaction signature
domains, `eth_chainId`, and the `CHAINID` opcode. A transaction signed for any other chain ID is
invalid.

## D.2 Development configuration and fork schedule

The canonical development template is the exact 30,442-byte JSON artifact linked above. Its raw
SHA-256 is:

```
0xfb1ca15108f3fa320471d344ac24c55925bd88d2ce57cdbfd2d069ced2e94ef6
```

The artifact has no terminal line feed. JSON member order and whitespace do not affect execution
semantics, but the raw digest above applies only to those exact bytes.

### D.2.1 Configuration input

| Input | Development value |
|---|---|
| `chainId` | `1` (development only) |
| `daoForkSupport` | `false`; `daoForkBlock` absent |
| `homesteadBlock` | `0` |
| `eip150Block` | `0` |
| `eip155Block` | `0` |
| `eip158Block` | `0` |
| `byzantiumBlock` | `0` |
| `constantinopleBlock` | `0` |
| `petersburgBlock` | `0` |
| `istanbulBlock` | `0` |
| `berlinBlock` | `0` |
| `londonBlock` | `0` |
| `mergeNetsplitBlock` | `0` |
| `terminalTotalDifficulty` | `0` |
| `terminalTotalDifficultyPassed` | `true` |
| `shanghaiTime` | `0` |
| `cancunTime` | `0` |
| `pragueTime` | `0` |
| `osakaTime` | `0` |

All listed block forks and all time forks through Osaka are active at genesis. The development
deployment transformation also sets `muirGlacierBlock`, `arrowGlacierBlock`, and
`grayGlacierBlock` to `0`; those difficulty-bomb forks do not change post-Merge execution. No fork
after Osaka is active. Activating a later fork requires a new versioned network manifest and
conformance vectors; a client MUST NOT infer activation from its software release date.

The execution revision from block 0 is therefore Osaka, not Cancun. This includes Prague's
execution-request header and EIP-2935 historical-block-hash state change, plus Osaka's
8,388,608-byte maximum RLP block size. Rollup0 adds no opcode or precompile.

### D.2.2 Genesis header input

| JSON input | Development value |
|---|---|
| `parentHash` | `0x00…00` |
| `number` | `0` |
| `timestamp` | `0x6490fdd2` = `1687223762` = `2023-06-20T01:16:02Z` |
| `coinbase` | zero address |
| `gasLimit` | `0x1c9c380` = `30,000,000` |
| `difficulty` | `0` |
| `nonce` | `0x0000000000000000` after fixed-width header encoding |
| `mixHash` | `0x00…00` |
| `extraData` | empty |
| `baseFeePerGas` | absent; the London genesis default is `1,000,000,000` wei |

Because Shanghai, Cancun, and Prague are active, construction also supplies an empty withdrawals
root, `blobGasUsed = 0`, `excessBlobGas = 0`, a zero `parentBeaconBlockRoot`, and
`requestsHash = SHA-256("")`.

## D.3 Complete development allocation

The `alloc` object in [`genesis-dev.json`](fixtures/genesis-dev.json) is incorporated into this
specification as the byte-exact allocation. It contains exactly 24 accounts. A conforming
development client MUST reject an added, removed, or modified allocation entry.

Twenty EOAs each have nonce `0`, empty code, empty storage, and
`1,000,000,000,000,000,000,000,000` wei (`1,000,000` native units):

```
0x14dc79964da2c08b23698b3d3cc7ca32193d9955
0x15d34aaf54267db7d7c367839aaf71a00a2c6a65
0x1cbd3b2770909d4e10f157cabc84c7264073c9ec
0x23618e81e3f5cdf7f54c3d65f7fbc0abf5b21e8f
0x2546bcd3c84621e976d8185a91a922ae77ecec30
0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc
0x70997970c51812dc3a010c7d01b50e0d17dc79c8
0x71be63f3384f5fb98995898a86b02fb2426c5788
0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199
0x90f79bf6eb2c4f870365e785982e1f101e93b906
0x976ea74026e726554db657fa54763abd0c3a0aa9
0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc
0xa0ee7a142d267c1f36714e4a8f75612f20a79720
0xbcd4042de499d14e55001ccbb24a551f3b954096
0xbda5747bfd65f08deb54cb465eb87d40e51b197e
0xcd3b766ccdd6ae721141f452c550ca635964ce71
0xdd2fd4581271e230360230f9337d5c0430bf44c0
0xdf3e18d64bc6a983f673ab319ccae4f1a57c7097
0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266
0xfabb0ac9d68b0b445fb7357272ff202c5651694a
```

The account at `0xf39f…2266` is the development `SYSTEM_ADDRESS`. Its exact public test private
key is:

```text
0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

The corresponding uncompressed secp256k1 public key derives
`0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` under Appendix C.2. A development client that
constructs or follows cross-chain Sync blocks MUST use this key and MUST reject an address
mismatch before signing or replay. Its balance is included in the twenty balances above. The key
is public test material and MUST NOT be used for a production identity.

The burn/test account `0xdeaddeaddeaddeaddeaddeaddeaddeaddeaddead` has nonce `0`, empty code,
empty storage, and `10,000,000,000,000,000,000,000,000,000,000` wei
(`10,000,000,000,000` native units).

The remaining three accounts are the predeploys in §D.4 and have zero balance. Total genesis
supply is `10,000,020,000,000,000,000,000,000,000,000` wei
(`10,000,020,000,000` native units). These conspicuous balances and known keys are another reason
the artifact MUST NOT be used as production identity.

## D.4 Predeploy code, immutables, nonce, and storage

Exact runtime code bytes are the `code` values in the normative allocation. The hashes below use
legacy Ethereum Keccak-256 over those bytes.

| Address | Account and runtime |
|---|---|
| `0x4200000000000000000000000000000000000007` | `EEZL2`; balance `0`, nonce `0`, empty storage; 13,406-byte runtime; code hash `0xb443cc3f745ada484c302b9ba255b44e85bf04b1c14ba486e2498640934fcdb6` |
| `0x4200000000000000000000000000000000000008` | `BridgeReceiver`; balance `0`, nonce `0`, empty storage; 64-byte runtime; code hash `0x2867570fb0a81631762d16010f1afeb0dc2aace809800dd110b78c0ad460639a` |
| `0x0000f90827f1c53a10cb7a02335b175320002935` | EIP-2935 history-storage contract; balance `0`, nonce `1`, empty storage at genesis; 83-byte runtime; code hash `0x6e49e66782037c0555897870e29fa5e552daf4719552131a0abce779daec0a5d` |

These are the only allocated predeploy accounts. In particular, the artifact has no account at
the EIP-4788 beacon-roots address `0x000f3df6d732807ef1319fb7b8bb8522d0beac02`,
the EIP-7002 withdrawal-request address
`0x00000961ef480eb55e80d19ad83579a64c007002`, or the EIP-7251
consolidation-request address `0x0000bbddc7ce488642fb579f8b00f3a590007251`.
A client MUST preserve that absence and MUST NOT synthesize extra genesis code. Active-fork
system calls execute against this exact state; the required zero parent beacon root and the absent
request contracts produce no additional persistent change in the empty-child vector.

`EEZL2` has constructor immutables `ROLLUP_ID = 1` and
`SYSTEM_ADDRESS = 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266`. Each value occurs at four
immutable-reference locations in the allocated runtime. Constructor execution is not replayed at
genesis; clients install the already-substituted runtime and the empty storage trie from the
artifact. A deployment whose registered L1 rollup ID differs from the immutable `ROLLUP_ID` is
invalid.

`BridgeReceiver` has no initialized storage and accepts plain value transfers through its
`receive` function. The EIP-2935 account starts with empty storage; before transactions in child
block `n`, the Osaka/Prague state transition writes the parent hash to storage index
`(n - 1) mod 8191`. This pre-block write is consensus state and MUST be applied even in an otherwise
empty block.

The runtime artifacts were cross-checked against the implementation repository at
`eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c`, whose genesis pins
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`. This provenance is
informative; conformance depends on the bytes and hashes above, not access to those repositories.
The pinned source build profile uses Solidity `0.8.34`, optimization with 200 runs, and
IR-based compilation. Compiler metadata and the complete build graph affect the result, so source
recompilation is not a substitute for matching the allocated runtime bytes.

## D.5 State root and genesis header

Clients construct the state root as Ethereum's secure hexary Merkle-Patricia trie:

1. For each allocation address `a`, the state-trie key is `keccak256(bytes20(a))`.
2. The value is
   `rlp([nonce, balance, storageRoot, keccak256(code)])`, using minimal unsigned integer
   encodings.
3. A storage key is a 32-byte big-endian word before secure-trie hashing. Zero storage values are
   absent. A stored value is the RLP encoding of its minimal unsigned integer.
4. The empty trie root is
   `0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421`.

The development allocation produces:

```
stateRoot =
0xd381d828f650845aa890778c74ad2de245f5b3f2a24763f243e19a6bafb4fec5
```

The genesis header is the following 21-item RLP list, in order:

| Index | Header field | Development value |
|---:|---|---|
| 0 | `parentHash` | zero hash |
| 1 | `ommersHash` | `keccak256(rlp([]))` = `0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347` |
| 2 | `beneficiary` | zero address |
| 3 | `stateRoot` | value above |
| 4 | `transactionsRoot` | empty trie root |
| 5 | `receiptsRoot` | empty trie root |
| 6 | `logsBloom` | 256 zero bytes |
| 7 | `difficulty` | `0` |
| 8 | `number` | `0` |
| 9 | `gasLimit` | `30,000,000` |
| 10 | `gasUsed` | `0` |
| 11 | `timestamp` | `1687223762` |
| 12 | `extraData` | empty |
| 13 | `prevRandao` / `mixHash` | zero hash |
| 14 | `nonce` | eight zero bytes |
| 15 | `baseFeePerGas` | `1,000,000,000` |
| 16 | `withdrawalsRoot` | empty trie root |
| 17 | `blobGasUsed` | `0` |
| 18 | `excessBlobGas` | `0` |
| 19 | `parentBeaconBlockRoot` | zero hash |
| 20 | `requestsHash` | `SHA-256("")` = `0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The RLP is 610 bytes. Its Keccak-256 is the development genesis block hash:

```
0xcc2334a5f46d86829de4f761b295ee171731bdde1dcb20be6e2ccb6d504a0b56
```

The executable fixture can print the complete RLP; clients need not trust an abbreviated value in
this document.

## D.6 Canonical deployment artifact and manifest

The allocation, code, fork schedule, and header inputs MUST come from one immutable genesis
artifact. Operators MUST NOT assemble genesis from independently configured client flags.

For an implementation-development deployment derived from the bundled template:

1. Verify the template's byte length and SHA-256 from §D.2.
2. Read the canonical L1 block numbered by `EEZ_REGISTRY_DEPLOY_BLOCK`, which the implementation
   records immediately after deploying the EEZ registry. Let its timestamp be `T`, and record the
   block number and hash. This is the implemented timestamp source; it is not the later
   rollup-registration block.
3. Deep-copy the normative development template. Retain `config.chainId = 1` and replace
   `timestamp` with the minimal lower-case hexadecimal quantity for `T`.
4. Set every block/time fork named in §D.2.1 to `0`, and additionally set
   `muirGlacierBlock`, `arrowGlacierBlock`, and `grayGlacierBlock` to `0`. Retain
   `terminalTotalDifficulty = 0` and `terminalTotalDifficultyPassed = true`.
5. Do not change `alloc`, `nonce`, `extraData`, `gasLimit`, `difficulty`, `mixHash`, `coinbase`,
   `number`, or `parentHash`.
6. For the canonical raw artifact used by the fixture, serialize UTF-8 JSON with two-space
   indentation and no terminal line feed.
7. Compute and record the artifact SHA-256, state root, genesis-header RLP, and genesis block hash
   by §D.5.

This transformation intentionally retains public keys and is suitable only for development/test
deployments. The implementation does not override the chain ID. The command in §D.8 implements
the exact transformation and labels it accordingly; its optional chain-ID override is a synthetic
test demonstrating that `chainId` is not a header field.

A production genesis MUST instead be released as a separate, byte-exact artifact because changing
the system identity or `ROLLUP_ID` changes predeploy runtime bytes and the allocation root. It MUST
not be inferred by patching only `chainId` or `timestamp` into the development artifact.

Every released network manifest MUST include:

| Manifest field | Required validation |
|---|---|
| `profileVersion` | recognized specification/profile version |
| `l1ChainId`, `l1GenesisHash` | exact settlement chain |
| `eezRegistryAddress` | exact L1 registry/manager deployment |
| `rollupManagerAddress` | equals the contract registered for `rollupId` |
| `genesisTimestampSourceBlockNumber`, `genesisTimestampSourceBlockHash` | canonical L1 block from which the genesis timestamp was selected |
| `registrationBlockNumber`, `registrationBlockHash` | canonical L1 registration anchor |
| `rollupId` | equals the `EEZL2.ROLLUP_ID` immutable |
| `l2ChainId` | equals genesis config and runtime RPC result |
| `l2BlockTime` | exact post-genesis timestamp increment |
| `genesisArtifactSha256` | SHA-256 of the selected raw JSON |
| `genesisStateRoot` | recomputed allocation root |
| `genesisBlockHash` | recomputed 21-field header hash |
| `systemAddress` | equals the `EEZL2.SYSTEM_ADDRESS` immutable |
| `forkActivations` | exact schedule; no implicit future forks |

The manifest itself MUST be authenticated by the network release process. A client MUST reject an
unknown profile version, a manifest/artifact mismatch, a production manifest using development
identity, or a local database initialized from another genesis.

## D.7 Block-validity rules

A block is canonical Rollup0 state only if it passes all three layers below. Passing a generic
Ethereum Engine API check is necessary but not sufficient.

### D.7.1 Ethereum execution validity

The client MUST apply every standard Ethereum execution-layer validity rule for the fork selected
by the manifest, Osaka for the profile in this appendix. The following checklist is not a
relaxation of any active-fork rule:

- decode the header and body canonically and enforce the active-fork field presence;
- require the empty ommers hash/body, post-Merge zero difficulty, and zero nonce;
- verify parent hash, `number = parent.number + 1`, and a strictly increasing timestamp;
- verify `gasUsed <= gasLimit`, the EIP-1559 base-fee recurrence, and the allowed gas-limit range;
- verify the ordered EIP-2718 transaction encodings, signatures, chain-ID domains, intrinsic gas,
  nonces, balances, fee caps, and active transaction types;
- recompute `transactionsRoot` and the withdrawals root, and require the body withdrawals list to
  match the header;
- validate EIP-4844 `blobGasUsed` against type-3 transactions and `excessBlobGas` against the
  parent;
- reject an Osaka block whose complete RLP encoding exceeds 8,388,608 bytes;
- execute all pre-block system changes and transactions under the active EVM rules; and
- recompute and compare `stateRoot`, `receiptsRoot`, `logsBloom`, `gasUsed`, and Prague
  `requestsHash`.

Transactions that revert remain valid transactions and produce failed receipts; a transaction that
cannot enter the state transition is invalid. Receipt trie values use the active typed-receipt
encoding.

### D.7.2 Rollup0 deterministic-header validity

For the v0 profile, the stronger Rollup0 checks are:

| Field or body item | Required value |
|---|---|
| `parentHash`, `number` | exact parent link and increment |
| `timestamp` | exactly `parent.timestamp + 1` second for `rollup0-v0`; see §2 |
| `beneficiary` | zero address |
| `gasLimit` | exactly `30,000,000` |
| `extraData` | empty |
| `prevRandao` | zero hash for the implemented v0 profile |
| `difficulty`, `nonce`, ommers | zero, zero, empty |
| `baseFeePerGas` | standard EIP-1559 with elasticity `2` and denominator `8` |
| `withdrawals` | present and empty; header root is the empty trie root |
| `parentBeaconBlockRoot` | present and zero |
| blob fields | standard EIP-4844 values; both are zero iff the block has no blob transactions and inherited excess is zero |
| `requestsHash` | hash of the execution requests; `SHA-256("")` when the list is empty |
| roots, bloom, `gasUsed` | exact recomputation from the ordered body and state transition |

The zero `prevRandao` is the value used by every current construction path. Applications MUST NOT
use it as randomness. Replacing it with an L1 value is a protocol-version change and cannot be
enabled by one client locally.

Before executing transactions, a Prague-active client MUST perform the EIP-2935 history-contract
write described in §D.4. System transactions in a Sync block MUST satisfy
[Appendix C](C-system-transactions.md). User and system transactions together determine the
header roots.

### D.7.3 Derivation and canonicality

For an L1-confirmed block, the client MUST also:

1. decode the canonical batch payload and obtain the exact block partition and ordered raw user
   transactions (§4 and Appendix E);
2. reconstruct the required system transactions and their exact positions;
3. build on the preceding L1-derived L2 block using the selected manifest;
4. execute the block and compare every header field and the block hash with the locally derived
   result; and
5. compare the terminal derived state root with the final settled state for the batch (§6).

Any mismatch makes the block invalid for Rollup0 even if the block is otherwise Ethereum-valid.
The client MUST halt derivation at the last valid L1-confirmed L2 block; it MUST NOT repair a
mismatch by trusting an operator-provided root or header. Unsafe blocks may be exposed separately,
but only the L1-derived branch can become safe or finalized.

## D.8 Executable fixtures

[`fixtures/genesis-hash-fixture.py`](fixtures/genesis-hash-fixture.py) is dependency-free. It
implements Keccak-256, canonical
RLP, the secure state/storage trie, the 21-field genesis header, the deployment transformation,
EIP-1559's first empty-block base fee, and the EIP-2935 pre-block write.

Run all published development assertions:

```console
python3 docs/rollup0-network-spec/fixtures/genesis-hash-fixture.py --check-dev
```

Print the complete genesis-header RLP:

```console
python3 docs/rollup0-network-spec/fixtures/genesis-hash-fixture.py --check-dev --dump-header-rlp
```

Reproduce the implementation's development deployment transformation:

```console
python3 docs/rollup0-network-spec/fixtures/genesis-hash-fixture.py \
  --derive-timestamp 0x65000000
```

Demonstrate separately that a synthetic chain-ID change affects the artifact and signature domain,
but not this state root or genesis block hash:

```console
python3 docs/rollup0-network-spec/fixtures/genesis-hash-fixture.py \
  --derive-timestamp 0x65000000 \
  --derive-chain-id 0x3039
```

The expected values are in
[`fixtures/genesis-validation-vector.json`](fixtures/genesis-validation-vector.json). That vector
also constructs empty block 1 above the exact development genesis using the normative v0 1-second
block time. Although the block contains no transactions, EIP-2935 changes the history account's
storage root and produces:

```
stateRoot = 0xfd75dc8a45e5f8ed14c051b2477fc288c4978a4ac204bf0799da22413ffba3c3
blockHash = 0xf3dc1444419145cfbf018cccdb7e85fc92db53194e1d20c79420d85683126653
```

These fixtures are conformance vectors. Their timestamps and the synthetic chain-ID override are
sample inputs only and do not name a live or production network.

---

*See also [§2 Timing, Slot Production, and Header Rules](02-block-production.md),
[§6 Derivation and Following](06-derivation-following.md), and
[Appendix E Compatibility Binding](E-compatibility-binding.md).*
