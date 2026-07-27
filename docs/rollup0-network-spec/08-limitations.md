# 8. Open Issues and Limitations

This chapter separates behavior that `rollup0-v0` deliberately accepts from missing production
parameters and known client conformance defects.

## 8.1 Accepted v0 limitations

- **Centralized sequencing.** One permissioned operator controls inclusion and ordering. There is
  no force-inclusion inbox or trustless exit; operator failure can halt the network.
- **Trusted management and proof policy.** The selected manager controls the proof-system policy
  and retains state-root authority defined by the compatibility contracts.
- **Flat calls only.** Rollup0 supports one L1-to-L2 or L2-to-L1 call. It does not support nested,
  reentrant, or multiple cross-chain calls in one interaction.
- **Key-gated derivation.** Followers need the shared `SYSTEM_ADDRESS` private key to reproduce
  signed legacy system transactions byte for byte.
- **Prefunded value delivery.** Inbound value debits the system account. There is no mint, native
  reserve replenishment, or protocol-enforced backing mechanism.
- **Constant randomness field.** Every L2 header has `prev_randao = bytes32(0)`;
  `PREVRANDAO` is not a randomness source.
- **Relay dependency.** Inbound atomicity needs a relay or builder that includes the complete,
  ordered bundle at the exact Chiado block and timestamp.
- **Optimistic unsafe state.** A rich endpoint is committed before its bundle resolves and can be
  rolled back with all unsafe descendants.
- **Manual deep-reorg response.** A reorg deeper than finalized Gnosis history has no automatic
  recovery rule.
- **No v0 blob codec or data-fee mechanism.** The only protocol DA format is tag-`0x00` calldata,
  paid by the operator.
- **Immediate governance authority.** Manager and verifier administrators can change accepted
  proof policy or roots under the selected contracts; follower detection cannot reverse those
  effects.

## 8.2 Production activation blockers

No production activation record currently satisfies §0.4. At minimum, it MUST pin:

- a unique EIP-155 chain ID, EEZ rollup ID, native asset, production genesis commitment, and
  activation point;
- Chiado deployment addresses, runtime bytecode hashes, manager, proof-system contracts,
  verification keys, validator membership, and threshold;
- a versioned proof binding that commits both transient routing counts, or removes submitter choice
  over them; complete-calldata validator checks do not repair the `5c51e02` digest;
- the operator identity and rotation/emergency procedure;
- a non-public system key, signer address, initial reserve, custody/backing relationship, and
  top-up policy;
- the complete production fork schedule and operator/Chiado funding plan;
- relay atomicity and exact-target support, including canonical receipt/event observation;
- upgrade and compatibility-change governance; and
- capacity limits derived from measured Chiado gas and relay behavior.

The development genesis in Appendix D uses chain ID `1`, a public test key, and test allocations.
It MUST NOT be presented as a production identity.

## 8.3 Current client conformance blockers

- Multi-block derivation is not transactional; a late failure can leave a replayed prefix.
- The local-block fast path does not compare every intermediate sealed header and body.
- Receipt observation does not fully enforce the exact target block number, canonical hash, and
  timestamp.
- Settlement attribution reduces applied roots to per-Chiado-block set membership, losing exact
  transaction/log order and duplicate multiplicity.
- Live and catch-up followers do not independently reject nonempty `blobIndices`.
- The public-mempool fallback cannot guarantee bundle atomicity or exact targeting.
- Rich composition leaves `batch.blockNumber = 0` instead of binding the observed pre-target
  Chiado block.
- A permanently unavailable target-tip RPC can hold the one-in-flight gate indefinitely.
- Boundary additions and timestamp arithmetic do not consistently use checked errors.
- A zero-length `blockTxCounts` range can be treated as a no-op instead of being rejected.
- The deriver can fall back from a missing sidecar to call-empty on-chain entries and does not
  enforce the one-to-one sidecar transformation; that path cannot reconstruct inbound calls.
- An inbound sidecar value above `type(int256).max` can be omitted from the composer's value map
  and recorded as zero instead of causing the required rejection.
- The configured public development system key and absence of a production reserve policy are not
  suitable for production activation.

These are implementation defects relative to §§2-7 and §9, not alternative protocol behavior.

## 8.4 Future variants

Changing the proof budget changes the Live/Future/Sync partition and requires a new timing
activation. Open sequencing, overlapping batches, state-root chaining, a typed key-free system
envelope, blob DA, fee vaults, or L1-derived `prev_randao` each require their own versioned rules.
Appendix C describes type `0x7E` only as an informative design direction.

---

*Next: [§9 Security and Trust Model](09-security-trust-model.md).*
