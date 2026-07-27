# 9. Security and Trust Model

This chapter is normative for Rollup0 v0. It identifies trusted authorities, security claims,
non-guarantees, and release conditions. The reusable EEZ threat boundaries are in the
[EEZ security model](../eez-protocol-spec/06-security-model.md). This chapter adds the Rollup0
network choices and implementation risks.

Rollup0 is a centralized, permissioned development profile. It is not trustless. A conforming
deployment MUST publish the complete authority and deployment tuple in its activation record.

## 9.1 Views and evidence

Rollup0 distinguishes:

- **unsafe L2 state**: operator-produced state not yet accepted by canonical derivation;
- **EEZ-accepted state**: a root accepted by the selected Chiado EEZ and manager policy;
- **safe L2 state**: state reconstructed locally from canonical Chiado data and exact settlement
  evidence under §6; and
- **finalized L2 state**: safe state whose containing Chiado block is finalized.

These states provide different evidence. Operator output is equivocable. EEZ acceptance proves
only that configured contract checks and proof policy accepted the transition. Local replay can
detect inconsistency but cannot reverse an EEZ root. Chiado finality protects an accepted history
from ordinary Chiado reorganization; it does not make a malicious manager or verifier honest.

## 9.2 Trusted authorities

| Authority | Power or dependency | Failure consequence |
|---|---|---|
| **Rollup manager owner/governance** | Selects proof systems, verification keys, and threshold; the compatibility manager can replace the registered root through its administrative path. | Can weaken or remove validity policy, install an arbitrary commitment, or halt settlement. A follower can detect an underivable result but cannot stop or reverse it. |
| **Accepted proof systems and their administrators** | Decide whether each `publicInputsHash` is accepted. The ECDSA verifier administrator can rotate its signer. | A malicious threshold, non-binding verifier, compromised signer, or verifier upgrade can authorize invalid state or value movement that passes the remaining local checks. |
| **Operator/sequencer/composer** | Produces and orders unsafe blocks, constructs DA and batches, selects riders, obtains proofs, and submits bundles. | Can censor, equivocate, withhold future data, manipulate unsafe ordering within profile limits, and halt production. |
| **Relay/builder** | Provides exact-target, all-or-none, ordered inclusion for separately signed Chiado transactions. | A subset can remain on Chiado because the EVM does not roll earlier transactions back. Non-atomic submission breaks the synchronous bundle claim. |
| **Gnosis Chiado** | Supplies canonical execution, calldata availability, transaction/log ordering, receipts, and finality. | Reorganizations move the safe view. Consensus failure or finalized-history displacement is outside automatic recovery. |
| **`SYSTEM_ADDRESS` key holders** | Sign deterministic outbound-load and inbound-delivery legacy transactions from a prefunded L2 EOA. | Can forge system operations, sign arbitrary transactions from the EOA, and drain or reallocate its reserve. Key sharing extends the compromise domain to every composing/following node. |
| **Follower/deriver implementation** | Authenticates Chiado history and reconstructs the local safe/finalized chain. | A correct follower halts on invalid or ambiguous history. It cannot submit a fraud proof, revert EEZ, or provide an exit. |
| **Deployment and upgrade administrators** | Choose contract addresses/code, genesis, keys, operator, relay, and activation boundaries. | A wrong or mutable tuple can redirect every trust assumption above. |

The activation record MUST identify each authority, its current address or key, its rotation rule,
and any delay or threshold. A public source repository or profile name is not a deployment
identity.

## 9.3 Guarantees and non-guarantees

Subject to the published authority assumptions and correct clients, Rollup0 provides:

- deterministic EVM execution and header construction;
- full tag-`0x00` calldata publication for every accepted range;
- proof-policy checks over the compatibility-bound public-input digest;
- EEZ pre-state, call-order, rolling-hash, and implemented value-accounting checks;
- canonical receipt and ordered-log selection;
- byte-identical replay for full or uniquely attributable prefix settlement;
- safe/finalized labels derived from Chiado rather than the operator feed; and
- fail-closed behavior on malformed, unavailable, ambiguous, or mismatching derivation input.

Rollup0 v0 does not provide:

- permissionless sequencing or force inclusion;
- a trustless withdrawal or escape hatch;
- a fraud-proof path that can challenge an accepted root;
- protection from malicious manager governance or a malicious proof threshold;
- contract-enforced membership of separately submitted transactions in one atomic bundle;
- permissionless key-free reconstruction of cross-chain Sync blocks;
- automatic recovery from finalized Chiado displacement or an arbitrarily deep reorg;
- blob DA, an alternate DA fallback, or an L2 data-fee reimbursement mechanism; or
- a general guarantee that pooled EEZ custody remains solvent for unsupported nested value flows.

Follower disagreement is detection, not prevention or recovery. Documentation and user interfaces
MUST NOT turn “an honest follower halts” into a claim that an invalid EEZ root or value transfer
cannot occur.

## 9.4 Manager and proof-policy risk

The proof-policy gate verifies the proof systems selected by the manager. Security requires:

1. the manager configuration is authentic and not malicious;
2. at least the configured threshold of accepted proof systems binds its proof to the exact
   compatibility `publicInputsHash`;
3. verifier contracts and signer/admin keys are uncompromised;
4. validators independently reconstruct the batch, DA, proof context, and intended raw bundle
   before signing; and
5. the mock proof system is forbidden for any value-bearing or production deployment.

The remaining EEZ checks do not execute the L2 STF, decode `callData`, prove correspondence to a
real host-chain deposit, or turn a non-binding verifier into a binding one. They can reject local
inconsistency but cannot validate an arbitrary self-consistent root.

The manager's root-replacement authority is a direct validity authority. A deployment MUST treat
that key or governance threshold as capable of changing accepted state. Production SHOULD separate
manager, verifier, system-key, operator, and upgrade compromise domains and SHOULD apply an
observable delay to policy or root changes. Any emergency exception MUST be published.

### 9.4.1 Unhashed transient routing counts

In the `5c51e02` binding, `transientExecutionEntryCount` and
`transientLookupCallCount` affect immediate/transient execution routing, dropping, and published
table state. The `publicInputsHash` commits to the entry and lookup hashes but does not include
either count. A valid proof for one pair of count values can therefore remain cryptographically
valid after a submitter changes those fields, subject to contract range checks, while the
execution/publication path changes.

Validator software MUST inspect and approve the complete raw `postAndVerifyBatch` calldata and
MUST reject any count that differs from the value used during simulation. The operator MUST NOT
reuse a proof across count variants. Activation records MUST pin the allowed construction rule and
test it end to end.

These operational checks do not repair the missing cryptographic commitment. Production use of
the generic count flexibility remains an unresolved proof-routing risk. A binding protocol fix
must add both counts to the committed digest or remove submitter choice under a new compatibility
binding and protocol version. Documentation MUST NOT claim that the current proof authenticates
the counts.

## 9.5 Operator censorship, equivocation, and liveness

The operator controls the unsafe view and can omit, delay, or reorder user transactions within the
ordinary validity rules. There is no Rollup0 v0 force-inclusion inbox. If the operator, proof
threshold, relay, or system signer stops, cross-chain settlement can stop indefinitely.

Users with funds dependent on operator-mediated transitions have no protocol-defined trustless
exit. A safe/finalized follower can refuse an invalid head, but refusal does not return funds.
Applications MUST treat unsafe state as reversible and MUST NOT represent it as safe settlement.

The one-rich-attempt rule, deterministic rollback, and canonical derivation limit accidental
equivocation. They do not prevent deliberate censorship or an operator from ceasing publication.

## 9.6 Relay and receipt risk

The ordered transaction list in §4.4 consists of separately signed Chiado transactions. EEZ does
not bind their hashes into the proof digest and Chiado does not make them one EVM transaction.
Synchronous atomicity therefore depends on a relay that includes all transactions, in order, in
one exact target block, or none.

A production deployment MUST:

- name and authenticate the relay/builder;
- validate its all-or-none, no-droppable-transaction behavior;
- disable sequential mempool fallback;
- pin the exact target number and timestamp;
- validate canonical inclusion number, block hash, timestamp, transaction hashes, and indices;
  and
- derive settlement only from exact receipts and ordered EEZ log occurrences.

`BatchPosted` alone does not mean the intended batch applied. Immediate entries can be skipped and
deferred entries can remain unconsumed. A later immediate execution can follow a skipped index,
and multiple entries can emit the same Sync root. Root-set membership and a bare event count are
therefore not valid attribution. A follower MUST combine the indexed `ImmediateEntrySkipped`
outcomes in the post receipt with each rider's `ExecutionConsumed` and
`L2ExecutionPerformed` pair as specified in §4.5. It accepts a partial result only when that
receipt-bound evidence identifies one unique entry prefix and deterministic replay reaches its
last actual root. Otherwise it halts at the preceding safe head.

A non-atomic relay can leave earlier state or value effects on Chiado. Follower repair cannot undo
them.

## 9.7 DA and derivation risk

Rollup0 v0 requires complete tag-`0x00` calldata and `blobIndices == []`. Calldata prevents
operator data withholding after canonical publication, but it does not guarantee timely
publication. An operator can stop posting.

The EEZ contract treats `callData` as opaque. Validators and followers must enforce strict RLP,
full transaction/entry consumption, count cardinality, reserved-sender rules, and execution
validity. A contract-accepted but malformed payload can therefore halt derivation.

Live and catch-up paths MUST apply identical channel, codec, receipt, and replay rules. A client
must not accept nonempty `blobIndices`, trailing RLP, an empty count list, or ambiguous settlement
because one path omits a check.

The signed system envelope makes cross-chain replay permissioned. A follower without the system key
cannot reconstruct exact transaction bytes and MUST halt. Publishing the private key would remove
this availability restriction only by destroying the system-only authorization boundary.

## 9.8 System key, reserve, and value

The active system transactions are signed legacy EIP-155 transactions. Inbound envelope value is
debited from the prefunded `SYSTEM_ADDRESS`; it is not minted. The `msg.value == value` check binds
the transfer to calldata but does not prove that a corresponding value was locked on Chiado.

Production MUST pin:

- the signer address and custody/distribution policy;
- the initial system reserve and its commitment in genesis;
- the native-asset and Chiado custody/backing relationship;
- permitted top-up and recovery operations;
- minimum balance and base-fee monitoring thresholds; and
- an accounting procedure that reconciles EEZ recorded liabilities, physical custody, and system
  reserve movements.

A compromised key can forge table loads, deliveries, and ordinary EOA transfers. A depleted
reserve or block base fee above the fixed 1 gwei system gas price halts system delivery.

The selected EEZ compatibility contract accounts outer value flow, but the reviewed implementation
can discard value returned by recursively processed nested calls. A successful nested outflow can
therefore reduce physical EEZ custody without entering the checked aggregate. Rollup0 v0 disables
nested/reentrant cross-chain calls. Validators and posting paths MUST reject every such
value-bearing shape until the contract uses entry-scoped, revert-safe accounting at all nesting
depths. Deployments SHOULD monitor:

```text
address(EEZ).balance >= sum(rollups[r].etherBalance)
```

Monitoring detects a breach; it does not repair one.

## 9.9 Proof context and replay domain

A rich batch MUST use the explicit recent Chiado block N selected under §§2 and 4. N is distinct
from the future inclusion target. The operator, validators, and production manager MUST reject
zero and `uint64.max` context sentinels and MUST require a nonzero canonical `blockhash(N)` that is
still available at settlement.

The compatibility digest does not by itself include every desirable deployment-domain value,
such as the Chiado chain ID, EEZ address, protocol identifier, trigger transaction hashes, or a
batch nonce. A zero context would make replay across time or compatible deployments easier when
the remaining inputs and pre-root coincide. A binding verifier authenticates the digest it is
given; it does not add omitted domains.

If N reorgs, expires from the contract's block-hash window, or differs between validators and the
manager, the attempt MUST be discarded and rebuilt. Production remains blocked while the live
composer leaves `blockNumber = 0`.

## 9.10 Reorganizations and finality

Chiado canonical history owns safe and finalized state. On a shallow reorg, §6.7 removes orphaned
attempts, rewinds L2 to the last surviving endpoint, restores eligible source transactions only
after canonical receipt checks, and replays the replacement branch.

The implementation's automatic common-ancestor history is bounded. A deeper reorg must halt rather
than claim recovery. Finalized Chiado displacement, corrupted index/database state, or disagreement
about the recovery ancestor requires an authenticated operator/governance procedure and a published
recovery activation.

Recovery races use one reconciliation lock. A stale dropped verdict cannot roll back a Sync height
already reached by canonical derivation. An orphaned event, receipt, root, or payload has no
continuing authority.

## 9.11 Fees and economic liveness

V0 uses standard EIP-1559 parameters, a 30,000,000 block gas limit, and the zero beneficiary.
Base fees burn, priority fees are economically inaccessible, and no fee vault, oracle, or L1-data
surcharge reimburses Chiado posting cost. The operator funds DA and settlement.

This is a liveness and sustainability risk. Sustained Chiado costs can make the operator stop
posting. System delivery also depends on the prefunded account and fixed-price envelopes.
Changing the beneficiary, fee parameters, system gas rule, or L1-cost recovery changes consensus
or signed bytes and requires a new activated profile.

## 9.12 Production security checklist

A production activation is nonconforming until it publishes and verifies:

- unique L2 identity, genesis commitment, activation boundary, and complete fork schedule;
- Chiado EEZ, manager, rollup, proof-system, and verifier code/address hashes;
- manager, verifier, upgrade, operator, relay, and emergency authorities;
- validator identities, verification keys, threshold, and proof-binding tests;
- non-public system key custody plus reserve, top-up, and backing policy;
- atomic relay behavior and exact-target canonical receipt validation;
- tag-`0x00`/empty-`blobIndices` enforcement on every producer and follower path;
- transactional range replay, complete header/body comparison, and exact log attribution;
- shallow and deep reorg operating procedures;
- value/custody and system-fee monitoring; and
- removal of mock proof and public development keys.

Known implementation deviations are listed in §8.3. An activation record cannot waive a normative
protocol rule while retaining the same `rollup0-v0` identifier.

---

*Next: [§10 Future Design](10-future-design.md).*
