# 3. Security and Trust Model

## 3.1 Validity and Authorization

Gnosis candidate admission has two independent gates:

1. full deterministic validity; and
2. authorization by the active sequencer/composer set.

The authorization set can censor, delay, or equivocate by signing several competing valid
candidates. It cannot make an invalid candidate conforming. That guarantee depends on validators,
provers, the Ethereum proof contract, and the EEZ settlement path enforcing the same complete
validity statement.

Users MUST NOT treat an authorization signature as a proof of execution validity, data
availability, settlement, safety, or finality.

## 3.2 Permissioned Liveness

Only an authorized signer can make a candidate admissible. The active signers can halt the network
by refusing to sign. There is no permissionless fallback, force-inclusion path, or automatic change
to Rollup0 admission.

Relaying is permissionless. Once an admissible candidate and its required data are available, an
authorized signer cannot reserve submission for a preferred relayer. Permissionless relaying does
not remove the signers' censorship power over candidate authorization.

## 3.3 Proof and Routing Integrity

The selected proof policy is trusted to reject every invalid state transition. The Ethereum proof
contract is also trusted to:

- validate the exact activated authorization scheme and active signer set;
- bind authorization and validity to the same candidate;
- bind the exact parent cursor and every selectable endpoint identity;
- bind every execution, DA, range, value, and routing input that affects settlement;
- prevent cross-network, cross-contract, cross-parent, cross-epoch, and modified-calldata replay;
  and
- reject stale, malformed, unauthorized, or incompletely proven candidates.

`eez-evm@0.2-draft` does not by itself bind `msg.sender` or both transient prefix counts into its
shared proof public input. Because any relayer may submit, the activated Gnosis candidate digest and
proof-contract call path MUST authenticate the complete effective batch and both counts without
requiring the relayer to be the signer. Otherwise a copied proof or signature could be front-run
with different routing behavior.

The exact mechanism is unresolved. A generic relay promise or a check of `msg.sender` alone does
not satisfy this requirement.

## 3.4 Settlement, Data Availability, and Reorgs

Production safety and finality derive from the authenticated canonical Ethereum settlement view.
An unsafe Gnosis block can be replaced before its candidate is selected, and an Ethereum reorg can
remove or reorder a selected candidate before finality.

Followers MUST identify the exact successful settlement call and ordered event occurrence from the
activated contracts. Matching only a state root, proof, signature, or event topic elsewhere is
insufficient. On a reorg, followers rewind every removed Gnosis endpoint and replay the new
canonical Ethereum order.

The activated cursor guard MUST compare a candidate's exact parent height, block hash, and state
root with the current settled cursor and atomically commit the selected endpoint identity. The
current EEZ binding's root-only state check does not reject an old-parent sibling after an
equal-root transition. Gnosis production is blocked until an external settlement mechanism closes
that gap.

The activated applied-prefix mechanism MUST prevent a later effect from committing after a
non-applied anchor or earlier effect, including when adjacent effect roots are equal. Follower
detection after canonical inclusion is not prevention. Gnosis production is blocked until this
mechanism is selected and enforced by the Ethereum settlement operation.

The imported DA and derivation rules remain mandatory. Authorization does not cure missing,
malformed, withheld, or unreplayable data. A signer can censor DA publication; it cannot make
unavailable data conforming.

Development uses Chiado consensus and finality but provides no production security claim.

## 3.5 Governance and Upgrades

The Gnosis governance authority can select signer rotations, proof policy, deployments, upgrades,
emergency actions, and recovery activations only through the published mechanisms of an activated
profile. These powers are separate from candidate-signing authority unless the activation record
explicitly combines them.

A production profile MUST identify every authority, operation, threshold, delay, and activation
boundary. Contract code or authority changes require authenticated versioned records and MUST
preserve historical verification. An emergency action MUST NOT silently reinterpret finalized
history.

All production governance and authority values are unresolved blockers.

## 3.6 Trust Summary

Gnosis users rely on:

- Ethereum consensus, execution, data access, and finality for settlement;
- the correctness and soundness of the selected EEZ and proof-contract deployments;
- complete independent validation by validators and provers;
- the active signer set for authorization availability and censorship resistance;
- the selected DA mechanism for reconstructability;
- governance for controlled activation and recovery; and
- deterministic follower implementation of canonical selection and reorg handling.

The permissioned signature intentionally adds authority risk. It does not remove any validity,
proof, DA, settlement, or derivation requirement.

---

*Next: [§4 Implementation and Conformance Status](04-implementation-conformance-status.md).*
