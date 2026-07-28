# Gnosis Chain Network Specification

Gnosis Chain and Rollup0 are separate EEZ networks. They have separate chain
histories and state. Neither network is an alias for the other.

This specification uses:

- the [EEZ specification](../eez-protocol-spec/index.md) for framework behavior;
- the [Rollup0 specification](../rollup0-spec/index.md) for every
  network rule that this page does not replace.

The words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** mark protocol requirements.

## Network settings

Rollup0 has open block production and permissionless candidate submission. Gnosis Chain requires
each block to be signed by an authorized sequencer. Except for this block-authorization rule,
Gnosis Chain applies the Rollup0 network rules unchanged.

Gnosis Chain settles on Ethereum in production. Rollup0 independently settles
on Ethereum. Each nominal 12-second Ethereum interval contains six 2-second
Gnosis Chain block positions.

Chiado is a development settlement network only. In that environment, each
5-second Chiado block contains five 1-second Gnosis Chain block positions.

## Block authorization

A Gnosis Chain candidate MUST:

1. be valid under the EEZ and Rollup0 rules; and
2. contain a valid authorized-sequencer signature for every block that can become canonical,
   including every terminal `B[i]` variant.

Each producer signature is carried in that block's peer-to-peer envelope. One candidate can contain
a nonterminal chain and terminal variants signed by different authorized sequencers. Gnosis Chain
validators check every required signature before attesting to the candidate. Nodes that receive an
unsafe block over peer-to-peer gossip also check its signature before following it.

The proof/settlement contract on Ethereum checks the validator attestation policy. It does not
check the sequencer signature directly. An authorized sequencer signature does not make an invalid
candidate valid.

After settlement, the producer identity is no longer needed to establish block validity. Ethereum
settlement and the Gnosis Chain validity attestations establish the canonical result.

Block authorization does not restrict relaying. Any party MAY relay a candidate. Settlement MUST
NOT require the relayer to be an authorized sequencer or composer.

!!! note "TO BE DEFINED"
    The signed block digest, peer-to-peer envelope, authorized-sequencer set, and key-rotation rules
    are not yet defined. The candidate format must also define how it carries the signatures for
    every terminal `B[i]` variant.

## Candidate selection

The settlement contract considers candidates in canonical Ethereum execution order. The first
candidate in that order that is applicable and has the required Gnosis Chain validator
attestations wins. Those attestations state that every block carried a valid authorized-sequencer
signature.

After a candidate wins, another candidate that names the previous parent is no
longer applicable.
