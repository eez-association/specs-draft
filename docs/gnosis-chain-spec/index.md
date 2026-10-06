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
the fork-transition rules below, and other differences stated on this page, Gnosis Chain applies
the Rollup0 network rules unchanged.

Gnosis Chain settles on Ethereum in production. Rollup0 independently settles
on Ethereum. Each nominal 12-second Ethereum interval contains six 2-second
Gnosis Chain block positions.

Chiado is a development settlement network only. In that environment, each
5-second Chiado block contains five 1-second Gnosis Chain block positions.

## Operational funding and fees

At launch, Gnosis funds the authorized sequencer/composer as an operational service. That operator
sets the block `beneficiary` to the Gnosis-designated fee recipient, so ordinary Gnosis Chain
transaction priority fees accrue to Gnosis and can offset sequencing, composition, validation, DA,
and settlement costs. Base fees remain burned under the inherited Rollup0 fee rules.

This funding and cost-recovery arrangement is deployment policy, not a protocol reimbursement or
profitability guarantee. Gnosis Chain does not mint an additional protocol fee for the operator and
does not guarantee that priority-fee revenue covers its costs. The Rollup0 type-`0x45`
protocol-transaction rule is inherited unchanged: these transactions consume and report gas but
pay no execution fee unless a later Gnosis Chain specification explicitly replaces that rule.

## Fork transition

The EEZ version of Gnosis Chain continues from a designated canonical block of the existing Gnosis
Chain. It does not start from an empty state. The fork configuration identifies that block by
number and hash and defines the first block governed by this specification.

Gnosis Chain keeps xDAI as its native currency. The fork preserves the existing account state,
including all native xDAI balances. Rollup0's empty native-balance genesis rule does not apply.

The initial RANDAO value is copied directly from the `prevRandao` in the designated finalized
Gnosis Chain fork block. After the transition, Gnosis Chain follows Rollup0's interval rule: every
interval copies `prevRandao` from the latest canonical Ethereum execution block strictly before
the interval's starting Sync timestamp, independently of anchor inclusion.

Gnosis Chain does not reset its base fee at the fork. The first EEZ-era block derives
`baseFeePerGas` from the designated Gnosis Chain parent using Rollup0's elasticity `2` and
base-fee-change denominator `50`. Every later block continues that rule.

!!! success "DECISION: native xDAI delivery at launch"
    Initial Gnosis Chain supports synchronous Ethereum-to-Gnosis-Chain delivery of native xDAI. It
    uses a Gnosis-specific DAI/xDAI adapter and system action, not Rollup0's ETH `etherBalance`
    path.

    On Ethereum, the adapter locks the backing DAI and enters EEZ through a zero-`msg.value` call.
    On Gnosis Chain, the matching protocol action credits or releases the same amount of native
    xDAI and delivers it to the selected destination. The amount, recipient, DAI custody change,
    native xDAI change, and application result are part of the authenticated candidate and are
    checked by every validator.

    Other generic EEZ calls involving Gnosis Chain use `value = 0`. They must not interpret an ETH
    `msg.value` amount as xDAI.

    Gnosis Chain requires an asynchronous withdrawal path that records the native-xDAI debit and
    permits a later DAI claim on Ethereum. It also targets a user-selectable synchronous path at
    launch. That path remains under discussion because a direct bridge call would conflict with
    the inherited Ethereum-to-Gnosis-Chain-only profile. Gnosis Chain may instead use an
    Ethereum-initiated authorization if the native-xDAI debit can be defined safely.

!!! danger "PRODUCTION BLOCKER: DAI/xDAI adapter design"
    The exact Ethereum adapter, Gnosis Chain system action, custody invariant, mint or release
    authority, failure handling, asynchronous claim proof, synchronous withdrawal design, and wire
    encoding are not yet defined. The design must work with the fixed EEZ contracts, bind each DAI
    deposit to exactly one native-xDAI delivery, and prevent replay or double issuance. Native-xDAI
    delivery and withdrawal cannot launch until these rules and contracts are complete.

!!! note "FORK PARAMETERS"
    The exact Gnosis Chain fork block and first EEZ-era block are selected in the final network
    configuration.

## Block authorization

A Gnosis Chain candidate MUST:

1. be valid under the EEZ and Rollup0 rules; and
2. contain a valid authorized-sequencer signature for every block that can become canonical,
   including every terminal `B[k]` variant through the candidate's successful-action count `s`.

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
    Gnosis Chain reuses Appendix D's Rollup0 unsafe-block digest and peer-to-peer announcement
    envelope. Its authorized-sequencer set and key-rotation rules are not yet defined. The candidate
    format must also define how it authenticates and carries the authorized signatures for every
    terminal `B[k]` variant through `B[s]`; Rollup0's ordinary unsafe announcement alone is not a
    settlement-authorization mechanism.

## Candidate selection

The settlement contract considers candidates in canonical Ethereum execution order. The first
candidate in that order that is applicable and has the required Gnosis Chain validator
attestations wins. Those attestations state that every block carried a valid authorized-sequencer
signature.

After a candidate wins, another candidate that names the previous parent is no
longer applicable.
