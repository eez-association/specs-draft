# Appendix D. Rollup0 Wire Format and Vector

[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines EEZ ABI tuples, selectors,
hashes, events, proof inputs, and proxy bytecode. This appendix defines only the Rollup0 DA
envelope, inbound protocol transaction, and ECDSA proof policy.

## D.1 ECDSA Attestation

Rollup0 realizes an `N`-of-`M` attestation with `M` independently configured instances of the
single-signer `ECDSAProofSystem`, one per prover. A candidate supplies signatures for at least `N`
accepted instances.

For proof system `k`:

```text
proofs[k] = r || s || v
message   = publicInputsHash[k]
signer    = ecrecover(message, v, r, s)
```

The proof is exactly 65 bytes:

```text
r: bytes32
s: bytes32, low-s
v: uint8, either 27 or 28
```

The signer signs the raw 32-byte EEZ public-input hash. The signer MUST NOT add an EIP-191
`Ethereum Signed Message` prefix or an EIP-712 domain. Verification succeeds only when the
recovered address equals the signer configured for that proof system.

`proofSystems` is strictly increasing by address and contains one proof per element. Rollup0's
proof-system index list is strictly increasing. The Rollup0 manager accepts only configured proof
systems and rejects a submitted subset with fewer than the selected threshold `N`.

## D.2 Blob Format

Rollup0 uses Ethereum blobs for anchored chain data. The format must encode or commit to:

1. a format version;
2. the exact settled Rollup0 parent;
3. every block boundary in the anchored range;
4. every pure-L2 and protocol-derived transaction in exact block order;
5. all non-derived header inputs;
6. the EEZ objects and Ethereum origin data for every synchronous effect; and
7. the ordered Ethereum trigger manifest; and
8. every non-derived input needed to reconstruct terminal variants `B[0]` through `B[n]`.

The manifest must end at its first failed action.

The terminal block timestamp and authenticated current Ethereum settlement context determine
whether an anchor is live or catch-up. The format does not need a separate anchor-mode flag. A
catch-up payload has no synchronous effect and an empty trigger manifest.

!!! note "TO BE DEFINED"
    The byte-exact encoding, field limits, multi-blob rules, and conformance vectors are not yet
    defined. The previous calldata RLP draft is not the Rollup0 blob format and must not be used by
    an independent implementation. The format must also define the authenticated candidate domain,
    including the Ethereum chain, EEZ deployment, Rollup0 ID, protocol and format versions, parent,
    and settlement context. It may place a field in the blob, EEZ batch, or manager `customData`,
    but must not rely on unauthenticated side data.

## D.3 Inbound Protocol Transaction

Rollup0 represents each successful inbound action as an unsigned EIP-2718 transaction in the normal
transaction list. Its typed receipt occupies the matching receipt index. The receipt payload
contains the standard status, cumulative gas used, log bloom, and logs fields. A failed action has
an L1 EEZ failed lookup but no Rollup0 transaction or receipt.

The transaction is derived rather than signed. Its sender is `SYSTEM_ADDRESS`, its recipient is
`EEZL2`, and its calldata follows the selected `EEZL2` inbound delivery ABI. Its access list,
blob-hash list, and authorization list are empty. Its gas limit is the lower of the block gas
remaining before it starts and the Fusaka per-transaction cap of `16,777,216`.

The transaction root commits the exact input and order. The receipt root commits status, gas use,
and logs. The state root commits persistent execution effects. Exact return data is checked against
the EEZ execution data during replay and is not added to the receipt.

For a value-bearing successful transaction, the state checkpoint starts before the temporary
protocol credit and the `EEZL2` call. A failed action opens no checkpoint and creates no L2 value.
Any outer failure in a protocol transaction that was expected to succeed invalidates the candidate.

!!! note "TO BE DEFINED: byte-exact envelope"
    The transaction type, payload encoding, source-identifier calculation, fee fields, transaction
    hash vectors, JSON-RPC extensions, and protocol-credit encoding are not yet defined. The blob
    format must carry the exact serialized transaction bytes and the authenticated origin data
    needed to verify their derivation. No complete conformance vector can be produced until these
    rules are fixed.

    [Appendix F](F-system-transaction-design.md) compares an OP-compatible `0x7e` envelope with a
    Rollup0-specific transaction type.

---

*Next: [Appendix E, Current Implementation Differences](E-implementation-divergences.md).*
