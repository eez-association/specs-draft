# Implementations

This chapter is informative. It records how known client implementations relate to the
specifications on this site. It does not define protocol behavior. Where an implementation differs
from a specification, the specification takes precedence, and an independent implementation must
not copy the difference.

## Known Implementations

| Implementation | Checked commit | Pinned EEZ Core | Settlement networks | Scope |
|---|---|---|---|---|
| `eez-rollup0` | `6ff63ec` (2026-10-02) | `9735f53` (2026-08-14) | Chiado, Kurtosis devnet | Development client for Rollup0 |
| `rollupX` | `3b96266` (2026-10-06) | `855fe06` (2026-10-01) | Ethereum, Chiado, Kurtosis devnet | Later fork of `eez-rollup0` with native blob DA and a wider action profile |

Both clients are Rust programs built on reth. Each contains a sequencer (block-production loop),
a composer (Sync-block contents and settlement), a remote proof signer, a deriver, and a follower.
`rollupX` began as a fork of `eez-rollup0` and still shares much of its structure, but the two now
pin different EEZ Core versions and use different Rollup0 payload encodings. They cannot validate or
derive each other's chains.

Neither implementation is a conforming Rollup0 client yet. The largest gaps common to both are the
inbound protocol-transaction envelope, base-fee routing, the settlement wrapper and candidate
domain, the validator threshold, and the unsafe-block announcement. `rollupX` is closer to the
specification in block production, headers, fees, and data availability. However, it adds
consensus rules and actions that Rollup0 does not have.

The [native-format update](A-rollup0-differences.md#a61-native-format-alignment) separately
compares Rollup0 PR #235 and a later RollupX revision, checked on 2026-11-10. Their shared
transaction encoding and source identity now match Appendix F; their execution and deployment
differences remain explicit. The other implementation findings retain the October baselines above.

## Appendices

- [Appendix A: Rollup0 Specification Differences](A-rollup0-differences.md) lists every material
  difference found between each implementation and the
  [Rollup0 specification](../rollup0-spec/index.md), and the differences between the two
  implementations.
