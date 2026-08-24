# Rollup0 Network Specification

Rollup0 is an experimental EEZ network that settles on Ethereum. Users are strongly discouraged
from putting significant value on it.

| Item | Rollup0 choice |
|---|---|
| Status | Draft |
| Settlement network | Ethereum |
| L2 block interval | 2 seconds |
| Ethereum alignment | Six L2 block positions per Ethereum slot, including missed slots |
| Anchoring | For a synchronous transaction, or after a maximum interval that is **to be defined** |
| Block production and composition | Open; no composer allowlist |
| Block syncing, P2P, and RPC | Open; no sequencer allowlist |
| Candidate validation | Permissioned provers provide a best-effort validation service |
| Candidate selection | The first applicable candidate in canonical Ethereum order wins |
| Inbound execution | Unsigned protocol-derived EIP-2718 transactions |
| Data availability | Ethereum blobs; the exact format is **to be defined** |

Composers build the continuous L2 chain. Sequencers sync and distribute those blocks. Blocks do not
have to be posted every Ethereum slot. An anchor contains the complete contiguous range from the
block after the previous settled endpoint through its new endpoint. Historical catch-up anchors
can publish a backlog over several Ethereum blocks.

This specification uses the [EEZ specification](../eez-protocol-spec/index.md) for the shared
contracts, cross-chain execution, proofs, settlement, proxies, and wire formats. This document
defines the choices made by Rollup0.

Unfinished parts are marked **To be defined** and collected in
[Chapter 12](12-open-issues.md).

## Reading Order

1. [Overview and Scope](01-overview.md)
2. [Architecture](02-architecture.md)
3. [EVM, Proxy, and Inbound Transactions](03-evm-proxy-systemtx.md)
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
- [Appendix E: Current Implementation Differences](E-implementation-divergences.md)
- [Appendix F: Inbound Transaction Design](F-system-transaction-design.md)
