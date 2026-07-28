# Appendix D. Rollup0 Wire Format and Vector

[EEZ Wire Formats](../eez-protocol-spec/05-wire-formats.md) defines EEZ ABI tuples, selectors,
hashes, events, proof inputs, and proxy bytecode. This appendix defines only the Rollup0 DA
envelope and the Rollup0 ECDSA proof policy.

## D.1 ECDSA Attestation

Rollup0 realizes an `N`-of-`M` attestation with one independent single-signer ECDSA proof system
per validator/prover.

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
4. every signed pure-L2 transaction in block order;
5. all non-derived header inputs;
6. the EEZ objects and system-call inputs for every synchronous effect; and
7. the ordered Ethereum trigger manifest.

!!! note "TO BE DEFINED"
    The byte-exact encoding, field limits, multi-blob rules, and conformance vectors are not yet
    defined. The previous calldata RLP draft is not the Rollup0 blob format and must not be used by
    an independent implementation.

## D.3 Undefined System Call

Rollup0 represents an inbound action as an EIP-4788-style system call. The call is injected by
block execution and is not included in the transaction list. Its byte-exact input follows the EEZ
inbound delivery ABI.

!!! note "TO BE DEFINED"
    The exact system caller, gas rules, value source, and commitment of results and logs are not yet
    defined. No complete conformance vector can be produced until those rules are fixed. The
    recovered draft's `0x7e` unsigned-transaction proposal is not a Rollup0 protocol rule.
