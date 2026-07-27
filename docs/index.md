# EEZ Specifications

This site contains one framework specification and two network specifications.
They are versioned separately because they answer different questions.

| Specification | What it defines |
|---|---|
| [EEZ Framework Specification](eez-protocol-spec/index.md) | The reusable execution, wire-format, proving, settlement, and conformance rules for an EEZ network. |
| [Rollup0 Network Specification](rollup0-network-spec/index.md) | The choices that make an EEZ network Rollup0, including block production, open candidate admission, data availability, derivation, and Ethereum settlement. |
| [Gnosis Chain EEZ Network Specification](gnosis-chain-eez-spec/index.md) | The choices that make a separate EEZ network Gnosis Chain, including authorized-composer admission and Ethereum settlement. |

Rollup0 and Gnosis Chain are different execution networks. Neither network
settles on the other. Both settle on Ethereum.

```text
EEZ Framework Specification
          ▲
          │ implements
          ├──────────────────────────┐
          │                          │
Rollup0 Network Specification   Gnosis Chain EEZ Network Specification
          │                          │
          └──────── settle on Ethereum ────────┘
```

The network specifications make similar execution choices and can share an
exactly versioned common ruleset. They differ at candidate admission:

- Rollup0 accepts a candidate from any composer when the candidate is valid.
  More than one valid candidate can compete. The first applicable settlement
  transaction in canonical Ethereum order wins.
- Gnosis Chain accepts a valid candidate only when an authorized composer
  signed it. The Ethereum proof contract checks that authorization. Relaying a
  signed candidate to Ethereum is permissionless.

Authorization never replaces validity checking.

## Production and development

The production settlement target for both networks is Ethereum. A nominal
12-second Ethereum settlement interval corresponds to six 2-second
execution-network timestamp positions. A missing or delayed Ethereum slot does
not change this ratio.

Chiado is a development environment, not the settlement network for either
production network. In the Chiado development profile, a nominal 5-second
interval corresponds to five 1-second execution-network timestamp positions.

Development deployments, mock proof systems, test keys, and fixture chain IDs
are not production parameters. A field marked `release-blocker` has no
authoritative production value in the reviewed repositories. An implementation
MUST NOT claim production conformance until every such field has an exact value.

## Version selection

The specifications in this edition select:

- `eez-framework@0.1-draft`;
- `eez-evm@0.2-draft`; and
- the conformance source
  `eez-core-protocol@3a6ca65c4858792fc3a143d34c5484877ef8f68c`.

Repository branches and unversioned names such as `latest` are not protocol
selectors. Each conforming deployment MUST select an exact network profile.
That profile pins its framework, EVM binding, settlement chain, contract
deployments, proof policy, admission rule, and activation point.

The reviewed Rollup0 implementation is
`eez-rollup0@0e07e97945ad7d33d7c52545207887b952333e2d`. Its recorded EEZ contract
submodule is
`5c51e02b0f965ee8c94e9ed2c7e0e9f924d41fba`, which predates the selected
`eez-evm@0.2-draft` conformance source. The implementation is evidence for
network behavior, but this binding difference is a release blocker. It is not
permission to combine the two ABIs or wire formats.

## Reading order

To implement any EEZ network:

1. Read the [EEZ overview](eez-protocol-spec/index.md), scope, architecture,
   execution model, proving and settlement rules, and network-profile contract.
2. Implement and pass the `eez-evm@0.2-draft` wire-format and conformance
   vectors selected by the framework.
3. Select exactly one network specification and one exact network profile.
4. Apply that network's block, data-availability, admission, competition,
   derivation, and settlement rules.
5. Refuse production startup while any selected profile value is unresolved or
   any required deployment identity cannot be authenticated.

The EEZ specification does not supply network policy. A network specification
does not redefine framework ABI layouts, hash preimages, or settlement state
machines. A contradiction between selected specifications is a release blocker;
an implementation MUST NOT resolve it by choosing whichever document or source
checkout is newer.
