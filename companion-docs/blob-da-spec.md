# EEZ Blob Data-Availability Format

> **Status: placeholder.** This companion document specifies the EIP-4844 blob encoding that all EEZ
> chains conform to. The Rollup0 protocol spec (§7.1) references this format abstractly and posts the
> v0 payload as L1 calldata by default; blobs are the intended production channel, chosen per batch by
> a submit-time cost comparison (§11.4, Appendix B §B.2).

## Scope

Defines, for an EIP-4844 blob carrying an EEZ DA payload:

- field-element packing (the 31-usable-bytes-per-32 constraint) and the byte→field-element map;
- how the §7.1 payload grammar (`0x00 ‖ rlp([...])`) is laid across one or more blobs;
- multi-blob spanning and ordering when a payload exceeds one blob's `4096 × 31` bytes;
- the versioned-hash commitment binding (`blobHashes` in the public-inputs fold, §8.3);
- padding and the canonical-encoding rules a deriver checks on the reverse path.

## To specify

- [ ] Field-element encoding map and reserved bytes.
- [ ] Blob count derivation from payload length.
- [ ] Cross-blob ordering and the boundary between `transactions[]` and `l2_entries[]`.
- [ ] KZG commitment / versioned-hash linkage to `postAndVerifyBatch`.
- [ ] Conformance vectors (encode/decode round-trip fixtures).

*This document is intentionally out of the normative protocol spec; it is a shared encoding referenced
by it.*
