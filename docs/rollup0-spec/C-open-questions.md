# Appendix C. Open Questions

The following questions require protocol decisions. They are not left to client discretion.

## C.1 Domain Separation and Replay

The EEZ call hash and proof digest do not by themselves state every deployment property.

- What binds a signature to this Ethereum chain, EEZ deployment, and Rollup0 instance?
- Is the EEZ proof-context block hash sufficient anti-replay protection?
- What prevents a stale but otherwise valid batch from being resubmitted?
- What structure must `crossProofSystemInteractions` have for Rollup0?

## C.2 System Transaction

- What is the byte-exact type-`0x7e` envelope?
- How are nonce, gas, fees, and value derived?
- Which execution rule authorizes the unsigned envelope from `SYSTEM_ADDRESS`?
- How are arbitrary transactions from `SYSTEM_ADDRESS` prevented?

## C.3 Ethereum Inclusion

- Which builder or protocol provides ordered all-or-none inclusion?
- What happens when the trigger reverts or the builder drops one transaction?
- Who pays inclusion fees?
- How does a relayer submit a candidate without gaining composer privileges?

## C.4 Adversarial Gas, DA, and Recovery

- Can a Rollup0 target exhaust the fixed inbound gas budget after Ethereum state has advanced?
- Which payload-size and fee rules prevent calldata-cost griefing?
- Is re-inclusion safe when an Ethereum reorganization removes the trigger but leaves the candidate
  available for resubmission?
- What backs Rollup0 native value on Ethereum?
- Who pays DA and proof costs?
- How are fees distributed?
- What automatic reorganization depth is supported?
- Who can authorize recovery after a deeper reorganization or a finalized-history failure?

---

*Next: [Appendix D, Rollup0 Wire Format](D-wire-formats.md).*
