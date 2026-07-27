# The EEZ Protocol Specification

**A general protocol for synchronous cross-chain execution.**

| | |
|---|---|
| **Status** | Draft / normative intent |
| **Execution** | Cancun-equivalent Ethereum EVM; no custom opcodes or precompiles |
| **Scope** | Cross-chain contracts, execution entries, replay, proving interfaces, settlement, and byte-exact wire formats |

EEZ is a cross-chain protocol: a set of settlement and execution contracts and a settlement rule
that let a contract on one chain call a contract on another and receive the result synchronously.
It is implementation-agnostic: it defines *what* a conforming implementation does, not *how*.

The EEZ execution model supports arbitrary bidirectional, multi-call, reentrant cross-chain
interactions. An EEZ network can select a narrower subset.

EEZ does not define block cadence, sequencing or admission, data availability, fees, gas limits,
chain derivation, or a network's proof policy. Those are choices made by each EEZ network.

Key words (MUST/SHOULD/MAY) carry their usual normative meaning.

## Reading order

1. [Architecture](01-architecture.md)
2. [EVM and Cross-Chain Proxies](02-evm-and-proxies.md)
3. [Execution Model](03-execution-model.md)
4. [Proving and Settlement](04-proving-and-settlement.md)
5. [Wire Formats and Conformance Vectors](05-wire-formats.md)

