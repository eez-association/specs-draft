# 1. Scope & Conformance

## 1.1 Normative scope

This specification defines the reusable, implementation-independent EEZ framework and its EVM
binding. It specifies:

- the L1 `EEZ` registry/execution manager, the L2 `EEZL2` manager, cross-chain proxies, and their
  required call behavior;
- the distinct L1 and L2 execution entries, nested lookups, state deltas, replay cursors, rollback
  rules, batch verification, and settlement events;
- EVM ABI layouts and byte-exact hashing rules; and
- the reusable security boundary and schema every EEZ network profile MUST complete.

It does not choose an L1, an L2 chain ID, a block schedule, a sequencer, a proof-system policy, a
data-availability codec, fee recipients, deployment addresses, or a finality rule. Those are
network-profile fields.

## 1.2 Version identifiers

The normative identifiers of this edition are:

```text
EEZ framework: eez-framework@0.1-draft
EVM binding:   eez-evm@0.2-draft
```

A conforming network profile MUST name both identifiers and versions. Referring only to “EEZ v0,”
“latest EEZ,” a repository, a branch, or a source commit is not a version pin.

The source snapshot recorded in [Appendix B](B-wire-formats.md) is informative provenance for
reproducing this edition's conformance vectors. It is neither the framework identity nor the EVM
binding identity. Normative behavior or vector changes require a new applicable framework or
binding version; an implementation-only source change does not silently revise this specification.

## 1.3 Conformance

An EVM implementation conforms to this edition when it reproduces the normative contract behavior,
ABI encodings, hashes, ordering rules, and revert conditions in this specification and passes the
applicable conformance vectors.

A network conforms only when, in addition:

1. it publishes a profile satisfying the [required schema](07-network-profile.md) and pins the
   exact framework identifier plus an exact compatible binding edition;
2. every profile field is fixed or explicitly not applicable;
3. it has no field marked `release-blocker`; and
4. its deployed bytecode and configuration match the pinned profile.

Draft and development profiles MAY contain release blockers. Such profiles document an
implementation target but MUST NOT claim production conformance.

## 1.4 Normative language

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative. Text explicitly labelled
**Informative** is not a conformance requirement.

---

*Next: [§2 Architecture](02-architecture.md).*
