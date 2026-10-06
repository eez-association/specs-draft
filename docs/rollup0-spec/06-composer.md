# 6. Composer and Candidate Competition

## 6.1 Open Composition

Rollup0 has no composer allowlist and no elected composer. Any party MAY construct a candidate from
the current Ethereum-confirmed Rollup0 cursor and submit it for validation.

A candidate does not gain Rollup0 protocol priority from:

- composer identity;
- arrival time at a validator/prover;
- proof completion time;
- a fee or side payment; or
- a validator/prover having already signed it.

Fees and side payments can affect whether an Ethereum builder includes a candidate and where the
builder places it. They do not change candidate validity. Canonical Ethereum transaction order
still determines which applicable candidate wins.

Rollup0 does not require a composer signature on a settlement candidate. It does require an
identifiable producer signature before a follower adopts a block into its unsafe view. This is the
separate unsafe-block announcement defined in Appendix D; it signs the exact block hash, not the
candidate, and is not part of settled validity. Rollup0 does not restrict the producer key. Peers
may use the recovered identity for local filtering or prioritization. A completed candidate has no
protocol owner and may be relayed unchanged by any party. Canonical Ethereum settlement determines
the safe range independently of the unsafe producer identity.

## 6.2 Candidate Lifecycle

A composer:

1. reads the current Ethereum-confirmed Rollup0 block hash from EEZ, resolves its header, and
   verifies the parent block number and EVM state root;
2. builds or adopts a valid pure-L2 chain from that cursor and collects and orders additional
   Rollup0 user transactions;
3. observes an Ethereum-to-Rollup0 intent when the candidate includes one;
4. simulates the complete Ethereum and Rollup0 interaction;
5. builds the Rollup0 blocks and every terminal Sync-block variant;
6. builds the EEZ batch and Rollup0 DA payload;
7. asks the validator/prover set to verify the complete candidate and every possible applied
   synchronous prefix;
8. obtains one required proof or signature set for the complete candidate;
9. submits the exact Ethereum prefix-bundle choices or gives them to a relayer; and
10. reconciles its unsafe blocks with canonical Ethereum settlement.

Composers may build and validators may pre-validate speculative descendants before their parent is
confirmed. A candidate submitted for final validation must nevertheless contain the complete range
from the current Ethereum-confirmed cursor. A validator/prover must not sign a candidate whose
named parent is only an unsafe or proposed Rollup0 block.

The first descendant after Sync timestamp `T` uses the `prevRandao` of the latest canonical
Ethereum block strictly before `T`. That block is known before the target slot. The header therefore
does not branch based on whether the slot is missed or whether a live or catch-up candidate lands.
An Ethereum reorganization that changes the selected preceding block still requires the normal
revalidation described in Chapter 10.

A composer may include, exclude, and order valid pure-L2 transactions and synchronous intents. It
does not have to use arrival order, fee order, or any other fairness rule. Different valid
candidates may select and order the same pending transactions differently.

The selected order must still satisfy every Rollup0 validity rule. In particular, ordinary
pure-L2 transactions precede protocol transactions in the Sync block, sender nonces and gas limits
remain valid, and every proposed Ethereum trigger must produce the corresponding ordered call in
the authenticated action manifest. A composer cannot alter a signed user transaction. A proposed
trigger cannot be an EIP-4844 blob transaction or otherwise require a blob sidecar.

A candidate is valid only in the Rollup0 manager domain defined in Appendix D and for exactly one
intended Ethereum child slot. The fixed domain identifies the protocol, chains, contracts, and
Rollup0 registration. Its settlement context contains that slot's timestamp and known parent
Ethereum block hash. The future child block hash is not known and is not part of the candidate. A
live candidate ends at that timestamp. A catch-up candidate can end at an older Sync timestamp but
is still bound to the current child slot.

If the target slot is missed or the Ethereum parent changes, the candidate expires. A live
candidate cannot reuse its synchronous variants. If its settled Rollup0 parent is still current,
its exact pure-L2 `B[0]` range may instead become a catch-up candidate. A catch-up composer may
also propose the same historical range again. In either case, it must bind the candidate to the
new settlement context and obtain a new proof or signature set. Transactions reused in a newly
built live endpoint must remain valid.

The composer MAY perform these steps with any internal architecture. The selected Rollup0 endpoint
MUST be independently reconstructible from the published candidate and canonical Ethereum. The
complete signed bytes of proposed triggers that are not included may remain private; validators
receive them before signing, but followers do not need them because they cause no Rollup0 effect.

!!! success "DECISION: composer-to-validator transport is implementation-defined"
    Candidate delivery is not a Rollup0 consensus interface. A composer may use the reference
    implementation's versioned `prove.v1` gRPC stream, another private RPC, or a local validator.
    Every route must provide the validator with the complete candidate checked in Section 6.3 and
    return a signature in the format accepted by the Rollup0 proof policy.

    A remote route carrying signed Ethereum trigger transactions must be confidential, protect
    message integrity, and authenticate the validator endpoint. Its message framing, size limits,
    errors, retries, admission controls, and multi-validator coordination are implementation and
    deployment choices. They do not change candidate validity.

## 6.3 Candidate Validity

A validator/prover checks at least:

- the candidate's parent hash equals the block-hash commitment stored by EEZ, and the parent
  header supplies the expected block number and EVM state root;
- the target timestamp and parent Ethereum block hash name the intended child slot;
- a live endpoint equals the target timestamp, or a catch-up endpoint is older and contains no
  synchronous action;
- the block range and terminal Sync position follow Chapter 4;
- replay reproduces every complete block and its exact block hash;
- every transaction executes from the claimed parent state;
- the transaction root, receipts, receipt root, logs bloom, gas used, state root, and all header
  fields match replay;
- the EEZ batch is the exact result of that execution;
- the DA payload reconstructs the complete range, `blobIndices` canonically selects every blob of
  the exact settlement transaction in order, every selected versioned hash is nonzero and matches
  its verified sidecar, and batch `callData` is empty;
- every protocol transaction has the required position and is byte-identical to the deterministic
  Rollup0 construction;
- every protocol transaction and typed receipt is included in the correct transaction and receipt
  root;
- every failed action has one correctly pinned L1 EEZ failed lookup, exact revert data, and no
  Rollup0 transaction;
- a failed action, when present, is the candidate's final manifest action;
- every `H[k]` and `R[k]`, including `H[0]` and `R0`, matches independent execution; and
- when the request proposes a nonzero synchronous prefix, it supplies the corresponding signed
  Ethereum triggers, and every proposed prefix bundle produces an ordered prefix of the
  authenticated action manifest in simulation.

Each validator/prover provides this work on a best-effort basis. When it completes the checks, it
signs only a candidate that passes them. It MAY sign several valid candidates with the same parent.

One proof or signature set covers the complete candidate, including the ordered action manifest and
every deterministic terminal variant `B[0]` through `B[s]`. It is not split into a separate proof
or signature set for each prefix. Validators use the privately supplied proposed triggers to check
delivery simulations. That check determines whether the validator accepts the proposed delivery
request; the resulting proof or signatures authenticate only the candidate. The exact trigger
transaction hashes are not Rollup0 action identity. Ethereum execution then selects one of the
authenticated endpoints, including when different carrier transactions realize the same ordered
calls.

!!! warning "TRUST ASSUMPTION: private Ethereum triggers"
    Every validator/prover must receive the exact signed Ethereum trigger transactions to
    reproduce the intended L1 execution and bundle. Relayers and Ethereum builders also receive
    those transactions when they handle the bundle.

    Rollup0 trusts each recipient only to keep the transactions private. Rollup0 validity must not
    depend on a recipient submitting an approved bundle unchanged: the on-chain settlement path
    must prevent a changed sequence from consuming prepared results or advancing Rollup0.

    A recipient can leak or submit a trigger by itself. A reverting standalone transaction still
    consumes the sender's nonce and gas. If its outer call catches the missing Rollup0 result, it
    can also succeed and change Ethereum state. Ordered-call prefix enforcement cannot stop Ethereum
    from including a valid signed transaction or undo its ordinary L1 effects. Users must treat
    leakage as a private-order-flow risk, even though it must not compromise Rollup0 validity.

    A different carrier can consume the prepared result first only if it produces the same
    effective source address and next ordered call, for example through the same source router or
    another valid transaction from the same EOA. The originally proposed trigger can then revert
    and spend nonce and gas, or—if the manifest's next position has the same call hash—consume that
    later position and receive its potentially different prepared result. This is an L1
    substitution consequence; the retained Rollup0 endpoint still follows the authenticated
    ordered prefix.

    Encrypted transaction delivery, threshold release, and intent-based execution are possible
    Rollup0.x designs. They are not part of the initial protocol.

!!! success "DECISION: enforce the initial transient prefixes through the settlement wrapper"
    The proof or signature set does not authenticate the batch's two transient-prefix lengths.
    These fields select which leading entries and failed lookups EEZ handles inside
    `postAndVerifyBatch`; they do not count successful triggers or Rollup0 protocol transactions.
    Initial Rollup0 requires the values `1` and `0`.

    The active Rollup0 settlement wrapper checks those values before calling EEZ. The manager
    rejects a direct EEZ call without wrapper authorization. Appendix D defines the gate and the
    versioned update path for later outbound or nested execution profiles.

## 6.4 Candidate Competition

Candidates are ordered only by canonical Ethereum transaction order. When a candidate settlement
is evaluated:

1. its named parent block hash must equal the commitment stored by EEZ, and its parent number and
   EVM state root must match that block's authenticated header;
2. all EEZ and Rollup0 validity checks must pass; and
3. its proof or validator/prover signatures must satisfy the production policy.

The first candidate that meets all three conditions advances Rollup0. A later sibling whose parent
has been superseded is stale and MUST NOT advance, even if it was valid when built or has enough
signatures.

## 6.5 Failure and Retry

A candidate that is invalid, stale, expired, or not included does not advance Rollup0. An included
prefix bundle advances Rollup0 to `B[0]` or a later `B[k]` even when the longest candidate bundle
is not selected.

A transaction that landed on canonical Ethereum or in canonical `B[k]` must not be retried. This
includes an Ethereum trigger that landed and caught a Rollup0 failure. An omitted synchronous
transaction or a transaction from a losing unsafe branch may return to a private or pure-L2 pool
only after the node revalidates it against the new canonical L1 and L2 state. Revalidation includes
its nonce, balance, gas, expiry conditions, and any state-dependent call result.

An expired or stale candidate's proof and signatures cannot be reused. A node may retain its
losing branch as noncanonical data for a possible Ethereum reorganization, but it must not keep
extending that branch as its current Rollup0 view.

A local timeout is not a settlement result. Settlement follows canonical Ethereum evidence.

---

*Next: [Chapter 7, Data Availability, Batches, and Bundles](07-da-batches-bundles.md).*
