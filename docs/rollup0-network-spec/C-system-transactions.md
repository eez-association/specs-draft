# Appendix C. System Transactions

This appendix defines the Rollup0 placement and reconstruction rules for calls to the L2
`EEZL2` predeploy. The ABI, tuple layouts, selectors, and contract behavior come from
`eez-evm@0.2-draft`; this appendix MUST NOT redefine them.

## C.1 Operations

Rollup0 uses two L2 system operations:

| Operation | Selected EEZ selector | Purpose |
|---|---|---|
| `loadExecutionTable` | `0xc1b4427c` | Load the L2 execution and lookup tables immediately before an outbound user call. |
| `executeIncomingCrossChainCall` | `0xf882a0ad` | Load the tables and execute one inbound action. |

The fully expanded canonical signatures and the distinct L1 and L2 tuple families are in
[EEZ Appendix B](../eez-protocol-spec/B-wire-formats.md). A client MUST compute or verify calldata
against that appendix. The selectors `0x59683c8b` and `0xeb494246` belong to the retired historical
binding and are invalid for this profile.

## C.2 Lowering

The DA sidecar carries every object needed to lower the settlement-side L1 tuple family to the L2
tuple family. Lowering MUST preserve:

- the exact cross-chain action hash;
- target and source network IDs and addresses;
- value and calldata;
- return data and success or failure;
- call and lookup order with multiplicity; and
- the rolling-hash and cursor conditions required by the EEZ L2 state machine.

A client MUST NOT reinterpret an L1 tuple as an L2 tuple, copy a historical field layout, fill a
missing call with zero values, or accept trailing ABI bytes.

For an outbound action, encode one `loadExecutionTable` call and place it immediately before the
user transaction that consumes the loaded table. For an inbound action, encode one
`executeIncomingCrossChainCall` call with the exact action parameters, L2 entries, lookups, and
transaction value.

The current binding does not itself prove field-by-field consistency between all explicit inbound
arguments and the first entry. Producers, validators, provers, and followers MUST apply the
profile's deterministic lowering check before accepting the transaction.

## C.3 Ordering and nonce

For a rich candidate, let `O` be its ordered outbound effects, let `I` be its ordered inbound
effects, and let `user[k]` be the transported user transaction paired with `O[k]`. Rollup0 orders
all outbound groups before all inbound groups:

```text
load(O[0]), user[0],
load(O[1]), user[1],
...,
load(O[len(O)-1]), user[len(O)-1],
deliver(I[0]), deliver(I[1]), ...
```

Each `load(O[k]), user[k]` pair is one outbound effect group. Each `deliver(I[k])` transaction is
one inbound effect group. The rich Sync body MUST be exactly the concatenation of these groups. It
MUST NOT contain an unrelated user transaction before, between, or after them. The rich final
`blockTxCounts` value is therefore `len(O)`.

The sidecar MUST contain exactly one corresponding execution object per effect group in the same
outbound-then-inbound order. On proper-prefix repair, a follower retains the first `q` complete
groups and omits every later group. Omitting an outbound group removes both its load and its user
transaction.

An anchor-only candidate has no effect group, no corresponding sidecar entry, and no
cross-network system transaction. Its Sync body MAY contain a complete ordered list `U` of
ordinary user transactions that produce no claimed EEZ effect. This user body is part of the sole
`A -> F` anchor transition defined in §3.3 and is never split by effect-prefix settlement.

Every system transaction uses the next nonce of the selected system authority in rich-body order.
Nonce arithmetic is checked. Intermediate blocks MUST contain no system-authority transaction.
The Sync block MUST contain no other transaction from that authority.

Loading a table replaces prior table state. Therefore a load and its user transaction are
inseparable for construction and prefix repair. A failed load does not suppress the following
user transaction; both receipts remain ordinary EVM receipts.

## C.4 Production authorization blocker

`eez-evm@0.2-draft` requires the profile-selected `SYSTEM_ADDRESS` for these entry points, but
Rollup0 has not selected a production authorization or envelope.

The selected mechanism MUST specify:

- sender derivation and authentication;
- exact transaction type and byte encoding;
- chain-ID domain;
- nonce source;
- fee fields and gas limit;
- inbound value source;
- deterministic reconstruction inputs;
- prevention of arbitrary system-sender transactions;
- prevention of reentrant table replacement; and
- enforcement of at most one inbound action per system transaction.

Every producer, validator, prover, and follower MUST enforce the same rule. A missing key or
authorization input is a construction failure, not permission to omit the system transaction.

## C.5 Current development behavior

At `eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`, the
development path constructs EIP-155-signed legacy transactions. Its
fixture account is:

```text
private key    = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
address        = 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266
gas price      = 1_000_000_000 wei
gas limit      = 2_000_000
```

These values are public development inputs. They are not production selections and do not solve
permissionless derivation: withholding the key prevents byte-identical reconstruction, while
publishing it permits arbitrary transactions from the authority.

The checked-in development predeploy and historical system-transaction vectors use the retired
`5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba` binding. They are not
conformance evidence for the selectors and tuples in C.1.

## C.6 Execution and failure

Normal block admission and EVM execution rules apply. A malformed envelope, wrong sender,
incorrect nonce or chain domain, insufficient balance, invalid fee, excess intrinsic gas, or
misplaced transaction makes the candidate invalid.

After admission, an EVM revert or exceptional halt produces a valid failed transaction receipt.
The nonce and gas charge remain; call state, logs, and value effects revert. There is no implicit
retry, mint, or cross-transaction rollback.

An accepted byte-exact production system-transaction vector for `eez-evm@0.2-draft` is not yet
available. It is a release blocker.
