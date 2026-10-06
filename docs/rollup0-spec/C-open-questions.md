# Appendix C. Remaining Production Work

The main protocol choices reviewed through Chapter 12 are fixed. The following work still needs a
normative specification, implementation, deployment selection, or measurement before production.
It is not left to incompatible client convention.

## C.1 Conformance and Contract Work

- Select and pin the EEZ Core revision, import its exact `getCustomData` public-input fold and
  physical blob-message stream into the normative EEZ chapters, and add an end-to-end
  `publicInputsHash` vector.
- Add transaction, receipt, execution, JSON-RPC, and invalid-input conformance vectors for the
  fixed type-`0x45` envelope and RPC schema.
- Add comprehensive canonical and invalid-input vectors for Appendix D's normative V0 payload.
- Add canonical and invalid-signature vectors and a P2P message mapping for Appendix D's
  unsafe-block announcement.
- Implement and test Chapter 7's required L1 EEZ transaction-scoped guard, including its transient
  successful-consumption latch, per-rollup carrier-policy flag, nonzero-`BLOBHASH(0)` rejection,
  revert behavior, and failed-lookup behavior.
- Define deterministic failed-lookup construction and lowering from an authenticated candidate to
  every type-`0x45` transaction.

## C.2 Asynchronous Withdrawals

- What proves or authorizes an asynchronous Rollup0 withdrawal?
- How long must a request wait before Ethereum releases ETH?
- How does the payout path atomically reduce Rollup0's EEZ backing and prevent replay?
- Which fields and domain form the unique withdrawal identifier?

## C.3 Deployment and Capacity Validation

- Which builders and relays support the selected blob-sidecar and prefix-bundle delivery strategy?
- What exact API, fee policy, and request limits will the initial operator use?
- Will the composer construct payloads in process, or which versioned Rollup0-specific execution-
  client extension will insert deterministic type-`0x45` transactions during payload building?
- Can synchronous inbound execution consume enough of the common Rollup0 block gas pool to make
  useful action prefixes operationally impractical?
- Which settled-lag, pending-range, publication-rate, and estimated-catch-up-time metrics should
  clients expose?

---

*Next: [Appendix D, Rollup0 Wire Format](D-wire-formats.md).*
