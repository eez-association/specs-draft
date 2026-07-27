//! Signed legacy system-transaction vector for Appendix C.
//!
//! Reproduce from an isolated checkout of
//! `eez-rollup0@00b3e75872fcc0c374d3b12a01933d732d317e4c`:
//!
//! ```text
//! cp docs/rollup0-network-spec/fixtures/system-tx-vector.rs \
//!   crates/eez-evm/examples/system_tx_vector.rs
//! cargo run -p eez-evm --example system_tx_vector
//! ```

use alloy_primitives::{B256, Bytes, I256, U256, address, hex, keccak256};
use alloy_signer_local::PrivateKeySigner;
use eez_evm::system_tx::{SystemTxContext, build_inbound_system_txs};
use eez_evm::types::{ExecutionEntrySol, L2ToL1CallSol, StateDeltaSol};

fn main() {
    let context = SystemTxContext {
        system_signer: PrivateKeySigner::from_bytes(&B256::with_last_byte(1))
            .expect("fixed private key is valid"),
        ccm_l2_address: address!("4200000000000000000000000000000000000007"),
        l2_chain_id: 1,
        l2_gas_price: 1_000_000_000,
        l2_gas_limit: 2_000_000,
        this_rollup_id: 1,
    };

    let entry = ExecutionEntrySol {
        stateDeltas: vec![StateDeltaSol {
            rollupId: U256::from(1),
            currentState: B256::ZERO,
            newState: B256::repeat_byte(0x11),
            etherDelta: I256::ZERO,
        }],
        proxyEntryHash: B256::repeat_byte(0xab),
        destinationRollupId: U256::from(1),
        l2ToL1Calls: vec![L2ToL1CallSol {
            targetAddress: address!("00000000000000000000000000000000000000aa"),
            value: U256::from(1),
            data: Bytes::from(vec![0x01, 0x02, 0x03]),
            sourceAddress: address!("00000000000000000000000000000000000000bb"),
            sourceRollupId: U256::ZERO,
            revertSpan: U256::ZERO,
        }],
        expectedL1ToL2Calls: Vec::new(),
        expectedLookups: Vec::new(),
        callCount: U256::from(1),
        returnData: Bytes::new(),
        rollingHash: B256::ZERO,
    };

    // This is the inbound half of Appendix E Vector 9. Nonce 7 belongs to
    // the preceding outbound load, so this delivery uses nonce 8.
    let raw = build_inbound_system_txs(&[entry], &context, 8)
        .expect("vector transaction builds")
        .pop()
        .expect("one matching entry emits one transaction");
    let tx_hash = keccak256(&raw);

    assert_eq!(raw.len(), 1_133);
    assert_eq!(
        tx_hash,
        "f22f620d60f898285607a2a52f80beb4f07f6dc4a408afb231c97bf979e02632"
            .parse::<B256>()
            .expect("expected hash is valid")
    );

    println!("rawTransaction = 0x{}", hex::encode(&raw));
    println!("length         = {} bytes", raw.len());
    println!("transactionHash = {tx_hash}");
}
