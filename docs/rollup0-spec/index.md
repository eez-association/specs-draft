# Rollup0 Network Specification

Rollup0 is an EEZ execution network that settles on Ethereum.

| Item | Rollup0 choice |
|---|---|
| Status | Draft |
| Settlement network | Ethereum |
| Execution interval | 2 seconds |
| Nominal settlement interval | 12 seconds |
| Positions per nominal interval | 6: five Live positions followed by one Sync position |
| Candidate production | Open |
| Candidate validation | Permissioned validators/provers sign every valid candidate they receive |
| Candidate selection | The first applicable candidate in canonical Ethereum order wins |
| Data availability | Complete calldata payload |

This specification imports the [EEZ specification](../eez-protocol-spec/index.md). EEZ defines the
generic contracts, cross-network execution model, proof interface, settlement operations, proxy
behavior, and EVM wire formats. This document defines only Rollup0 choices.

Rollup0 is not ready for production. Several values and mechanisms are intentionally left open in
[Chapter 12](12-open-issues.md). A client can implement the draft behavior, but independent
production clients cannot interoperate until those questions have exact answers.

## Reading Order

1. [Overview and Scope](01-overview.md)
2. [Architecture](02-architecture.md)
3. [EVM, Proxy, and System Transactions](03-evm-proxy-systemtx.md)
4. [Block Production and Headers](04-block-production.md)
5. [Execution Profile](05-execution-model.md)
6. [Composer and Candidate Competition](06-composer.md)
7. [Data Availability, Batches, and Bundles](07-da-batches-bundles.md)
8. [Proving and Settlement](08-proving-settlement.md)
9. [Ethereum to Rollup0 Flow](09-l1-to-l2.md)
10. [Derivation and Following](10-derivation-following.md)
11. [Gas and Economics](11-gas-economics.md)
12. [Limitations and Open Issues](12-open-issues.md)

Appendices:

- [Appendix A: Reference](A-reference.md)
- [Appendix B: Gas and Cost Model](B-gas-cost-analysis.md)
- [Appendix C: Open Questions](C-open-questions.md)
- [Appendix D: Rollup0 Wire Format](D-wire-formats.md)
