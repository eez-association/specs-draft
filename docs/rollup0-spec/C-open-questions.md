# Appendix C. Open Questions

The following questions require protocol decisions. They are not left to client discretion.

## C.1 Domain Separation and Replay

The EEZ call hash and proof digest do not by themselves state every deployment property.

- What binds a signature to this Ethereum chain, EEZ deployment, and Rollup0 instance?
- Is the EEZ proof-context block hash sufficient anti-replay protection?
- What prevents a stale but otherwise valid batch from being resubmitted?
- What structure must `crossProofSystemInteractions` have for Rollup0?

## C.2 System Call

- What system caller address invokes the EIP-4788-style call?
- How are gas, logs, return data, and value handled?
- How are system-call results exposed through receipts, RPC, explorers, and indexers?
- Which block commitments include the system call and its result?

## C.3 Ethereum Inclusion

- Will Rollup0 submit one strict atomic bundle for every trigger prefix?
- Which builders support overlapping prefix bundles with one shared settlement transaction?
- Is trusting those builders not to repackage signed transactions acceptable for Rollup0?
- Is a contract-enforced progress mechanism needed instead?
- Which duplicate-call rule from Chapter 7 will Rollup0 select?
- Should duplicate rejection be enforced by Rollup0 validation or by the EEZ contract?
- Who pays inclusion fees?
- How does a relayer submit a candidate without gaining composer privileges?

## C.4 Adversarial Gas, DA, and Recovery

- Can a Rollup0 target exhaust the fixed inbound gas budget after Ethereum state has advanced?
- Which payload-size and fee rules prevent blob-cost griefing?
- Is re-inclusion safe when an Ethereum reorganization removes the trigger but leaves the candidate
  available for resubmission?
- What backs Rollup0 native value on Ethereum?
- Who pays DA and proof costs?
- How are fees distributed?
- What automatic reorganization depth is supported?
- Who can authorize recovery after a deeper reorganization or a finalized-history failure?

---

*Next: [Appendix D, Rollup0 Wire Format](D-wire-formats.md).*
