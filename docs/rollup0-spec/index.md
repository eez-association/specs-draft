# Rollup0 Network Specification

Rollup0 is an experimental EEZ network that settles on Ethereum. Users are strongly discouraged
from putting significant value on it.

| Item | Rollup0 choice |
|---|---|
| Status | Draft |
| Settlement network | Ethereum |
| L2 block interval | 2 seconds |
| EVM hardforks | Fusaka at genesis; later Ethereum execution forks at mainnet timestamps |
| L2 blob transactions | Not supported; blobs are used only for L1 data availability |
| Ethereum alignment | Six L2 block positions per Ethereum slot, including missed slots |
| Anchoring | For a synchronous transaction, or after a 15-minute operational target |
| Block production and candidate composition | Open; no composer or sequencer allowlist |
| Unsafe block attribution | Producer-signed; no Rollup0 signer allowlist |
| Block syncing, relay, and RPC | Open; peers may relay producer-signed blocks |
| Candidate validation | Permissioned validators provide a best-effort validation service |
| Validator threshold | Dynamic set; `floor(2M / 3) + 1` active members |
| Candidate selection | The first applicable candidate in canonical Ethereum order wins |
| Inbound execution | Unsigned protocol-derived EIP-2718 transactions |
| EEZ state commitment | Terminal Rollup0 block hash |
| Data availability | Ethereum blobs; normative raw, uncompressed, columnar V0 payload |
| Late synchronization | Standard execution-layer `eth` block sync and `snap` state sync on Rollup0 |

Composers build the continuous L2 chain. Sequencers sync and distribute those blocks. Blocks do not
have to be posted every Ethereum slot. An anchor contains the complete contiguous range from the
block after the previous settled endpoint through its new endpoint. Historical catch-up anchors
can publish a backlog over several Ethereum blocks.

This specification uses the [EEZ specification](../eez-protocol-spec/index.md) for the shared
contracts, cross-chain execution, proofs, settlement, proxies, and wire formats. This document
defines the choices made by Rollup0.

Decisions, production blockers, open interoperability work, genesis parameters, and trust
assumptions use distinct labels. Unresolved items are collected in
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
- [Appendix G: Blob Payload Design](G-blob-payload-design.md)
