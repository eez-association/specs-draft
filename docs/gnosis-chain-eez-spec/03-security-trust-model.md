# 3. Security & Trust Model

## 3.1 Host guarantees

Each profile relies on canonical Chiado consensus for transaction execution, receipt and log
ordering, reorg handling, and finality. A consumer MAY call an EEZ result finalized only after the
Chiado block that contains the result is finalized by the canonical consensus view.

The host guarantee is conditional on the authenticated, binding-specific deployment identity in
§2. It does not apply to a contract at an unpinned address, runtime code that does not match the
pinned hash, or a deployment selected by the other Gnosis host profile.

## 3.2 Guarantees that the host does not provide

Chiado inclusion and finality do not establish:

- that a consumer rollup's state transition is valid;
- that its manager or proof systems are honest;
- that its data-availability payload is sufficient or correctly encoded;
- that its operator, composer, or system-transaction signer is honest or available;
- that its L1 and L2 value accounting is solvent; or
- that users have a force-inclusion or exit path.

Each consumer network profile MUST specify those properties. Neither Gnosis profile inherits
Rollup0's operator, manager, validator, system-key, DA, or fee assumptions.

## 3.3 Atomic inclusion

A consumer may require an ordered group containing an EEZ settlement transaction and one or more
triggering transactions to appear in one Chiado block. That property requires the external
builder or relay selected by `GC-ATOMIC-INCLUSION` for
`gnosis-chain-eez-chiado@0.1-draft`, or by `GC-R0-ATOMIC-INCLUSION` for
`gnosis-chain-eez-chiado-rollup0@0.1-draft`.

A conforming mechanism MUST either include the complete ordered group or include none of it.
Submitting the transactions independently, or falling back to sequential public-mempool
submission, is not conforming atomic inclusion. The authenticated profile MUST identify the
mechanism, its ordering rule, its rejection behavior, and how clients detect partial inclusion.

Whole-bundle inclusion alone does not protect proof routing when the selected binding leaves
caller or calldata fields outside the proof statement. For `eez-evm@0.2-draft`, the batch proof
does not bind `msg.sender`, `transientExecutionEntryCount`, or `transientLookupCallCount`, and the
EEZ entry point is permissionless. The Rollup0 compatibility profile has its own binding-specific
routing statement and mitigation requirement.

If a consumer uses the host mechanism to mitigate such a limitation, the mechanism MUST
authenticate the exact caller and calldata before execution and prevent a copied proof from being
submitted first with altered routing inputs. The consuming rollup profile MUST select the exact
mechanism and failure rule. Each Gnosis host profile exposes the corresponding required host
capability but does not silently choose a consumer mitigation.

## 3.4 Shared deployment governance

The selected EEZ deployment owner, upgrade authority, and emergency authority are trusted until
the profile's binding-specific blocker is resolved: `GC-UPGRADES` for
`gnosis-chain-eez-chiado@0.1-draft`, or `GC-R0-UPGRADES` for
`gnosis-chain-eez-chiado-rollup0@0.1-draft`. These authorities can change behavior for every
consumer that uses that deployment. A production profile MUST publish:

- the controlling addresses and threshold rules;
- the operations each authority can perform;
- activation delays and consumer notification requirements;
- emergency actions and recovery rules; and
- the new deployment or profile identity produced by a code or authority change.

## 3.5 Reorgs and evidence

Clients MUST associate EEZ results with the exact canonical transaction receipt and ordered log
occurrence. Matching only a state-root value within a block is insufficient when values repeat or
multiple batches affect the same rollup.

Before finality, a Chiado reorg may remove or reorder those receipts. A consumer MUST rewind its
host-derived view and apply its own network-profile recovery rule. Neither host profile makes a
claim that an unsafe or merely included consumer state is final.

---

*End of the Gnosis Chain EEZ Network Specification.*
