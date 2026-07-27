# Gnosis Chain Network Specification

Gnosis Chain and Rollup0 are separate EEZ networks. They have separate chain
histories and state. Neither network is an alias for the other.

This specification uses:

- the [EEZ specification](../eez-protocol-spec/index.md) for framework behavior;
- the [Rollup0 specification](../rollup0-spec/index.md) for every
  network rule that this page does not replace.

The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## Network settings

Rollup0 is an open-composer network with permissionless candidate submission.
Gnosis Chain is a permissioned-composer network. Except for the candidate
authorization rule below, Gnosis Chain applies the Rollup0 network rules
unchanged.

Gnosis Chain settles on Ethereum in production. Rollup0 independently settles
on Ethereum. Each nominal 12-second Ethereum interval contains six 2-second
Gnosis Chain block positions.

Chiado is a development settlement network only. In that environment, each
5-second Chiado block contains five 1-second Gnosis Chain block positions.

## Candidate authorization

A Gnosis Chain candidate MUST:

1. be valid under the EEZ and Rollup0 rules; and
2. carry a valid signature from an authorized Gnosis Chain
   sequencer/composer.

The Gnosis Chain proof/settlement contract on Ethereum MUST check both
conditions. An authorized signature does not make an invalid candidate valid.

Authorization applies to the candidate, not to its relayer. Any party MAY relay
a candidate. Settlement MUST NOT require the relayer to be an authorized
sequencer or composer.

## Candidate selection

The settlement contract MUST consider candidates in canonical Ethereum
execution order. The first candidate in that order that is applicable, valid,
and authorized wins.

After a candidate wins, another candidate that names the previous parent is no
longer applicable.
