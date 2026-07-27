# Appendix D. Genesis and Block Validity

Rollup0 has no production genesis in `rollup0@0.2-draft`. The production EIP-155 chain ID, EEZ
rollup ID, native asset, fork schedule, system mechanism, predeploy bytes, allocations, timestamp,
state root, block hash, and activation record are release blockers.

## D.1 Production requirements

A production genesis commitment MUST bind at least:

```text
(
  profile ID and version,
  Ethereum chain ID and activation block,
  EEZ deployment and rollup ID,
  L2 EIP-155 chain ID,
  fork schedule,
  block interval and gas limit,
  system address and authorization mechanism,
  complete allocation and predeploy bytecode,
  genesis header,
  genesis state root,
  genesis block hash,
  raw genesis artifact digest
)
```

Changing an input that is not present in the genesis header, such as the EIP-155 chain ID, still
changes network identity and transaction validity. Clients MUST authenticate the complete
commitment, not only the genesis block hash.

Production predeploy bytecode MUST implement `eez-evm@0.2-draft` and match the activated
deployment commitments. Source equivalence is insufficient where bytecode or immutable values
differ.

## D.2 Historical implementation-development fixture

The checked-in [`fixtures/genesis-dev.json`](fixtures/genesis-dev.json) is retained only to
reproduce current implementation behavior. It is not a Rollup0 production genesis and is not
`eez-evm@0.2-draft` conformance evidence.

Important fixture properties are:

| Input | Historical development value |
|---|---|
| EIP-155 chain ID | `1` |
| Timestamp | `1687223762` |
| Gas limit | `30_000_000` |
| Genesis base fee | `1_000_000_000 wei` |
| Active execution fork | Osaka from genesis |
| Historical L2 interval | `1 second` |
| `EEZL2` address | `0x4200000000000000000000000000000000000007` |
| `BridgeReceiver` address | `0x4200000000000000000000000000000000000008` |
| Public system address | `0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266` |
| Raw artifact SHA-256 | `0xfb1ca15108f3fa320471d344ac24c55925bd88d2ce57cdbfd2d069ced2e94ef6` |
| State root | `0xd381d828f650845aa890778c74ad2de245f5b3f2a24763f243e19a6bafb4fec5` |
| Genesis block hash | `0xcc2334a5f46d86829de4f761b295ee171731bdde1dcb20be6e2ccb6d504a0b56` |

The allocated `EEZL2` runtime was built from
`sync-rollups-protocol@5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`. Its ABI and selectors differ
from the selected `eez-evm@0.2-draft` binding. It MUST NOT be relabeled or activated as a 0.2
genesis.

The chain ID `1`, known private keys, large test balances, and the immutable historical rollup ID
are additional reasons this artifact is development-only.

## D.3 Block validity

A conforming Rollup0 client first applies all ordinary Ethereum execution-block validity rules
under the activated fork. It then applies the Rollup0 rules in §2, §6, and Appendix C:

- exact parent link, block number, timestamp, and activated fixed header fields;
- exact ordered body, transaction envelopes, and receipts;
- exact gas, fee, state, transaction, receipt, withdrawals, request, and blob-field computation;
- no unauthorized or misplaced system transaction;
- deterministic execution from the authenticated parent;
- exact comparison of every sealed header and body field; and
- endpoint agreement with the last applied effect selected from canonical Ethereum evidence.

A locally valid unsafe block does not become safe until derivation performs all these checks.

## D.4 Executable historical checks

The retained fixtures reproduce the historical development artifact:

```console
python3 docs/rollup0-network-spec/fixtures/genesis-hash-fixture.py --check-dev
python3 docs/rollup0-network-spec/fixtures/timing-header-fixture.py
```

Expected values are in
[`fixtures/genesis-validation-vector.json`](fixtures/genesis-validation-vector.json). These
fixtures test current implementation parsing and Ethereum header mechanics. They do not validate
the selected 0.2 predeploy ABI.

A new production genesis fixture MUST be generated only after the production profile and 0.2
predeploy bytes are fixed.
