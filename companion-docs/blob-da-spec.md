# Future EIP-4844 Data-Availability Extension

> **Status: non-normative, incomplete design notes.** This document is not part of
> `rollup0@0.2-draft` and does not define an implementable wire format. The current draft uses
> only tag `0x00` in Ethereum
> transaction calldata and requires `blobIndices == []`
> ([Rollup0 §4](../docs/rollup0-network-spec/04-da-batches-bundles.md)). No blob tag, activation
> rule, or calldata-versus-blob selection rule is assigned.

## Candidate scope

A future, versioned EIP-4844 extension must define:

- field-element packing and the byte-to-field-element map;
- whether it reuses the logical tag `0x00` RLP body or assigns a new grammar and tag;
- multi-blob spanning, total-length recovery, ordering, and padding;
- transaction and `l2_entries` boundaries across blobs;
- the mapping from `blobIndices` to sidecars and versioned-hash commitments in the public-input
  fold ([EEZ §5](../docs/eez-protocol-spec/05-proving-settlement.md));
- canonical decoding and rejection rules; and
- a fee and channel-selection policy if a later profile activates multiple channels.

The generic settlement ABI exposes `blobIndices` and can fold `blobhash` values. That surface is
not an active mode. The current producer has no blob transaction or sidecar path, the codec
accepts only tag `0x00`, and current consumers do not derive data from blobs. The producer rejects
non-empty `blobIndices`; the follower's missing independent empty-list guard is an implementation
gap ([M-1](IMPLEMENTATION_NOTES.md#m-1-calldata-only-da-follower-still-needs-the-empty-blobindices-guard)).

## Work required

- [ ] Assign a versioned profile and unambiguous discriminator.
- [ ] Specify encoding, reserved bytes, padding, and total-length recovery.
- [ ] Specify blob-count derivation and cross-blob ordering.
- [ ] Specify `blobIndices` to sidecar/versioned-hash validation.
- [ ] Implement producer, submitter, follower, and reorg behavior end to end.
- [ ] Specify DA fees and channel selection.
- [ ] Publish byte-exact positive and negative vectors.
- [ ] Add an activation rule that rejects pre-activation blob batches.

Until all items ship together, blobs remain future design material and non-empty `blobIndices`
remain invalid under the current Rollup0 draft.
