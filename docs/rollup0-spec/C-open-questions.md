# Appendix C. Open Questions

The following questions require protocol decisions. They are not left to client discretion.

## C.1 Domain Separation and Replay

The EEZ call hash and proof digest do not by themselves state every deployment property.

- What binds a signature to this Ethereum chain, EEZ deployment, and Rollup0 instance?
- Is the EEZ proof-context block hash sufficient anti-replay protection?
- What prevents a stale but otherwise valid batch from being resubmitted?
- What structure must `crossProofSystemInteractions` have for Rollup0?

## C.2 Inbound Protocol Transaction

- Will Rollup0 keep one protocol transaction per successful Ethereum trigger, or select another
  grouping option from Chapter 3?
- What transaction type and byte-exact payload will Rollup0 use?
- Which fields make the source identifier unique and bind it to the Ethereum and Rollup0 domains?
- Will the typed receipt use only the standard EIP-2718 receipt fields?
- Will every protocol-level transaction failure continue to invalidate the complete candidate?
- Will `EEZL2` continue to require balance neutrality rather than an absolute zero balance?
- Will Rollup0 keep the protocol-credit value source selected in Chapter 3?
- Will protocol transactions continue to share the ordinary block gas pool?
- Who pays for protocol-transaction gas, in which asset, and who receives it?
- Who pays for simulating and proving a failed action that creates no Rollup0 transaction?
- What do `GASPRICE` and receipt `effectiveGasPrice` return?
- Which extra transaction fields, if any, are exposed through JSON-RPC?
- How does the blob format carry the exact protocol transaction and its authenticated origin data?

## C.3 Ethereum Inclusion

- Will Rollup0 submit one strict atomic bundle for every trigger prefix?
- Which builders support overlapping prefix bundles with one shared settlement transaction?
- Is trusting those builders not to repackage signed transactions acceptable for Rollup0?
- Is a contract-enforced progress mechanism needed instead?
- Will a later version permit actions after a caught failure by trusting exact builder ordering or
  by adding a unified on-chain action cursor?
- Which duplicate-call rule from Chapter 7 will Rollup0 select?
- Should duplicate rejection be enforced by Rollup0 validation or by the EEZ contract?
- Who pays inclusion fees?
- How does a relayer submit a candidate without gaining composer privileges?
- How does Rollup0 enforce its required transient execution-entry and lookup counts while
  preventing the same proof from bypassing that check through direct EEZ submission?

## C.4 Adversarial Gas, DA, and Recovery

- Can synchronous execution consume enough of the common block gas pool to make useful prefixes
  impractical?
- Which payload-size and fee rules prevent blob-cost griefing?
- Is re-inclusion safe when an Ethereum reorganization removes the trigger but leaves the candidate
  available for resubmission?
- Will a later version move backing from pooled EEZ custody to a dedicated vault, and what liquidity
  and loss rules would apply?
- Who pays DA and proof costs?
- How are fees distributed?
- What automatic reorganization depth is supported?
- Who can authorize recovery after a deeper reorganization or a finalized-history failure?

---

*Next: [Appendix D, Rollup0 Wire Format](D-wire-formats.md).*
