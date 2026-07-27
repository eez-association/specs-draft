// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {EEZ} from "../src/EEZ.sol";
import {CrossChainProxy} from "../src/base/CrossChainProxy.sol";
import {
    ExecutionEntry,
    StateDelta,
    L2ToL1Call,
    ExpectedL1ToL2Call,
    LookupCall
} from "../src/interfaces/IEEZ.sol";

/// @title WireVectors
/// @notice Computes byte-exact conformance vectors for Appendix D of the Rollup0 spec.
/// @dev Every value here is computed by the SAME code paths the deployed `EEZ` /
///      `EEZBase` / `CrossChainProxy` contracts use, so the vectors are authoritative.
///      Run: forge script script/WireVectors.s.sol -vvv
contract WireVectors is Script {
    // Mirror the EEZBase rolling-hash domain tags.
    uint8 constant CALL_BEGIN = 1;
    uint8 constant CALL_END = 2;
    uint8 constant NESTED_BEGIN = 3;
    uint8 constant NESTED_END = 4;

    function run() external {
        // A fixed EEZ deployer/registry address so the proxy CREATE2 vector is reproducible.
        // We `vm.etch` real EEZ code at this address so computeCrossChainProxyAddress runs
        // with `address(this) == FIXED_EEZ`.
        address FIXED_EEZ = address(uint160(0x0ee200));
        EEZ impl = new EEZ();
        vm.etch(FIXED_EEZ, address(impl).code);
        EEZ eez = EEZ(FIXED_EEZ);

        console.log("================ EEZ deployed (etched) at ================");
        console.logAddress(address(eez));

        // ---------------------------------------------------------------
        // VECTOR 1: crossChainCallHash
        //   keccak256(abi.encode(targetRollupId, targetAddress, value, data,
        //                        sourceAddress, sourceRollupId))
        // ---------------------------------------------------------------
        uint256 targetRollupId = 1;
        address targetAddress = address(uint160(0xDeaDBeef));
        uint256 value = 1 ether;
        bytes memory data = hex"deadbeef";
        address sourceAddress = address(uint160(0xC0FFEE));
        uint256 sourceRollupId = 0; // MAINNET_ROLLUP_ID

        bytes32 cchash =
            eez.computeCrossChainCallHash(targetRollupId, targetAddress, value, data, sourceAddress, sourceRollupId);
        console.log("================ VECTOR 1: crossChainCallHash ================");
        console.log("targetRollupId = 1");
        console.log("targetAddress  = 0x00000000000000000000000000000000deadbeef");
        console.log("value          = 1000000000000000000 (1 ether)");
        console.log("data           = 0xdeadbeef");
        console.log("sourceAddress  = 0x0000000000000000000000000000000000c0ffee");
        console.log("sourceRollupId = 0");
        console.log("abi.encode preimage:");
        console.logBytes(abi.encode(targetRollupId, targetAddress, value, data, sourceAddress, sourceRollupId));
        console.log("crossChainCallHash:");
        console.logBytes32(cchash);

        // ---------------------------------------------------------------
        // VECTOR 2: cross-chain proxy CREATE2 address
        //   salt         = keccak256(abi.encodePacked(originalRollupId, originalAddress))
        //   bytecodeHash = keccak256(creationCode || abi.encode(eez, originalAddress, originalRollupId))
        //   addr         = last20( keccak256(0xff || eez || salt || bytecodeHash) )
        // ---------------------------------------------------------------
        address originalAddress = address(uint160(0xC0FFEE));
        uint256 originalRollupId = 1;

        address proxy = eez.computeCrossChainProxyAddress(originalAddress, originalRollupId);
        bytes32 salt = keccak256(abi.encodePacked(originalRollupId, originalAddress));
        bytes32 bytecodeHash = keccak256(
            abi.encodePacked(
                type(CrossChainProxy).creationCode, abi.encode(address(eez), originalAddress, originalRollupId)
            )
        );
        console.log("================ VECTOR 2: crossChainProxyAddress ================");
        console.log("eez (deployer)   = 0x00000000000000000000000000000000000ee200");
        console.log("originalAddress  = 0x0000000000000000000000000000000000c0ffee");
        console.log("originalRollupId = 1");
        console.log("salt = keccak256(abi.encodePacked(uint256 rollupId, address addr)):");
        console.logBytes32(salt);
        console.log("creationCode length (bytes):");
        console.log(type(CrossChainProxy).creationCode.length);
        console.log("keccak256(creationCode) [no ctor args]:");
        console.logBytes32(keccak256(type(CrossChainProxy).creationCode));
        console.log("init-code constructor-arg tail abi.encode(eez,addr,rollupId):");
        console.logBytes(abi.encode(address(eez), originalAddress, originalRollupId));
        console.log("bytecodeHash = keccak256(creationCode || ctorArgs):");
        console.logBytes32(bytecodeHash);
        console.log("proxy address:");
        console.logAddress(proxy);

        // ---------------------------------------------------------------
        // VECTOR 3: rolling hash after CALL_BEGIN(1) + CALL_END(1)
        //   _rollingHash starts at bytes32(0)
        //   CALL_BEGIN: keccak256(abi.encodePacked(prev, uint8(1), uint256 callNumber))
        //   CALL_END:   keccak256(abi.encodePacked(prev, uint8(2), uint256 callNumber,
        //                                          bool success, bytes retData))
        // ---------------------------------------------------------------
        uint256 callNumber = 1;
        bool success = true;
        bytes memory retData = hex"01"; // sample 1-byte success return

        bytes32 rh = bytes32(0);
        bytes32 afterBegin = keccak256(abi.encodePacked(rh, CALL_BEGIN, callNumber));
        bytes32 afterEnd = keccak256(abi.encodePacked(afterBegin, CALL_END, callNumber, success, retData));
        console.log("================ VECTOR 3: rolling hash CALL_BEGIN+CALL_END ================");
        console.log("start _rollingHash = 0x00..00");
        console.log("callNumber = 1, success = true, retData = 0x01");
        console.log("after CALL_BEGIN(1):");
        console.logBytes32(afterBegin);
        console.log("after CALL_END(1,true,0x01):");
        console.logBytes32(afterEnd);

        // ---------------------------------------------------------------
        // VECTOR 4: abi.encode(ExecutionEntry) and its keccak (entryHash)
        //   entryHash = keccak256(abi.encode(entry))  (exactly as _verifyProofSystemBatch)
        //   Minimal entry: one StateDelta, proxyEntryHash = cchash above,
        //   destinationRollupId = 1, one L2ToL1Call, no nested, callCount = 1,
        //   returnData = 0x, rollingHash = afterEnd (the VECTOR 3 result)
        // ---------------------------------------------------------------
        StateDelta[] memory deltas = new StateDelta[](1);
        deltas[0] = StateDelta({
            rollupId: 1,
            currentState: bytes32(uint256(0xaa)),
            newState: bytes32(uint256(0xbb)),
            etherDelta: int256(0)
        });

        L2ToL1Call[] memory calls = new L2ToL1Call[](1);
        calls[0] = L2ToL1Call({
            targetAddress: targetAddress,
            value: 0,
            data: hex"deadbeef",
            sourceAddress: sourceAddress,
            sourceRollupId: 0,
            revertSpan: 0
        });

        ExpectedL1ToL2Call[] memory nested = new ExpectedL1ToL2Call[](0);

        ExecutionEntry memory entry = ExecutionEntry({
            stateDeltas: deltas,
            proxyEntryHash: cchash,
            destinationRollupId: 1,
            L2ToL1Calls: calls,
            expectedL1ToL2Calls: nested,
            callCount: 1,
            returnData: hex"",
            rollingHash: afterEnd
        });

        bytes memory entryEnc = abi.encode(entry);
        bytes32 entryHash = keccak256(entryEnc);
        console.log("================ VECTOR 4: abi.encode(ExecutionEntry) + entryHash ================");
        console.log("abi.encode(entry):");
        console.logBytes(entryEnc);
        console.log("entryHash = keccak256(abi.encode(entry)):");
        console.logBytes32(entryHash);

        // ---------------------------------------------------------------
        // VECTOR 5: full publicInputsHash for a minimal single-rollup
        //           single-proof-system batch.
        //
        //   entryHashes      = [entryHash]                         (1 entry above)
        //   lookupCallHashes = []                                  (no lookup calls)
        //   blobHashes       = []                                  (no blobs)
        //   callData         = 0x  =>  keccak256("") = ec...85a470
        //   crossProofSystemInteractions = bytes32(0)
        //
        //   sharedPublicInput = keccak256(abi.encodePacked(
        //       abi.encode(entryHashes),
        //       abi.encode(lookupCallHashes),
        //       abi.encode(blobHashes),
        //       keccak256(callData),
        //       crossProofSystemInteractions))
        //
        //   For the single rollup (rollupId=1) attesting via the single PS (k=0):
        //   acc = keccak256(abi.encode(bytes32(0), rollupId, vkey, blockHash, timestamp))
        //   with blockNumber = 0 => (timestamp, blockHash) = (0, bytes32(0))
        //
        //   publicInputsHash[0] = keccak256(abi.encodePacked(sharedPublicInput, acc))
        // ---------------------------------------------------------------
        bytes32[] memory entryHashes = new bytes32[](1);
        entryHashes[0] = entryHash;
        bytes32[] memory lookupCallHashes = new bytes32[](0);
        bytes32[] memory blobHashes = new bytes32[](0);
        bytes memory callData = hex"";
        bytes32 crossProofSystemInteractions = bytes32(0);

        bytes32 sharedPublicInput = keccak256(
            abi.encodePacked(
                abi.encode(entryHashes),
                abi.encode(lookupCallHashes),
                abi.encode(blobHashes),
                keccak256(callData),
                crossProofSystemInteractions
            )
        );

        uint256 rollupId = 1;
        bytes32 vkey = bytes32(uint256(0x100));
        bytes32 blockHash = bytes32(0); // blockNumber == 0 sentinel
        uint256 timestamp = 0;
        bytes32 acc = bytes32(0);
        acc = keccak256(abi.encode(acc, rollupId, vkey, blockHash, timestamp));
        bytes32 publicInputsHash = keccak256(abi.encodePacked(sharedPublicInput, acc));

        console.log("================ VECTOR 5: publicInputsHash (1 rollup, 1 PS) ================");
        console.log("keccak256(callData=0x) [keccak of empty bytes]:");
        console.logBytes32(keccak256(callData));
        console.log("sharedPublicInput:");
        console.logBytes32(sharedPublicInput);
        console.log("rollupId=1, vkey=0x100, blockHash=0x0, timestamp=0");
        console.log("acc (after folding the single rollup):");
        console.logBytes32(acc);
        console.log("publicInputsHash[0]:");
        console.logBytes32(publicInputsHash);

        _vector6_multiRollupMultiPS(entryHash);
        _vector7_nonEmptyCallDataAndLookup(entryHash);
    }

    // ---------------------------------------------------------------
    // VECTOR 6: publicInputsHash with 2 rollups x 2 proof systems,
    //           overlapping/disjoint proofSystemIndex subsets.
    //
    //   proofSystems = [PS0, PS1]  (k = 0, 1)
    //   rollup 1: proofSystemIndex = [0, 1]   (attests via BOTH PS)
    //   rollup 2: proofSystemIndex = [1]      (attests via PS1 ONLY)
    //   => PS0 (k=0) is folded only by rollup 1.
    //      PS1 (k=1) is folded by rollup 1 THEN rollup 2 (ascending rollupId).
    //
    //   vkMatrix[r][j] is rollup r's vkey for the j-th PS in ITS subset:
    //      rollup1: subset [PS0,PS1] -> vk = [0x100, 0x101]
    //      rollup2: subset [PS1]     -> vk = [0x201]
    //   blockNumber = 0 => (timestamp, blockHash) = (0,0) for both rollups.
    //
    //   sharedPublicInput reused from the single-entry batch (same entries/
    //   callData/blobs/crossProofSystemInteractions as VECTOR 5).
    // ---------------------------------------------------------------
    function _vector6_multiRollupMultiPS(bytes32 entryHash) internal {
        bytes32[] memory entryHashes = new bytes32[](1);
        entryHashes[0] = entryHash;
        bytes32[] memory lookupCallHashes = new bytes32[](0);
        bytes32[] memory blobHashes = new bytes32[](0);
        bytes memory callData = hex"";
        bytes32 crossProofSystemInteractions = bytes32(0);

        bytes32 sharedPublicInput = keccak256(
            abi.encodePacked(
                abi.encode(entryHashes),
                abi.encode(lookupCallHashes),
                abi.encode(blobHashes),
                keccak256(callData),
                crossProofSystemInteractions
            )
        );

        // (timestamp, blockHash) per rollup, blockNumber == 0 sentinel.
        // rollup1 = id 1, rollup2 = id 2 (ascending order is the fold order).
        uint256 r1 = 1;
        uint256 r2 = 2;

        // PS0 (k=0): only rollup 1 lists index 0, at subset position j=0 -> vk 0x100.
        bytes32 acc0 = bytes32(0);
        acc0 = keccak256(abi.encode(acc0, r1, bytes32(uint256(0x100)), bytes32(0), uint256(0)));
        bytes32 pih0 = keccak256(abi.encodePacked(sharedPublicInput, acc0));

        // PS1 (k=1): rollup1 lists index 1 at subset position j=1 -> vk 0x101,
        //            rollup2 lists index 1 at subset position j=0 -> vk 0x201.
        bytes32 acc1 = bytes32(0);
        acc1 = keccak256(abi.encode(acc1, r1, bytes32(uint256(0x101)), bytes32(0), uint256(0)));
        acc1 = keccak256(abi.encode(acc1, r2, bytes32(uint256(0x201)), bytes32(0), uint256(0)));
        bytes32 pih1 = keccak256(abi.encodePacked(sharedPublicInput, acc1));

        console.log("================ VECTOR 6: publicInputsHash (2 rollups x 2 PS) ================");
        console.log("rollup1 subset [PS0,PS1] vk=[0x100,0x101]; rollup2 subset [PS1] vk=[0x201]");
        console.log("sharedPublicInput (same shape as VECTOR 5):");
        console.logBytes32(sharedPublicInput);
        console.log("acc for PS0 (k=0) folded by {rollup1}:");
        console.logBytes32(acc0);
        console.log("publicInputsHash[0] (PS0):");
        console.logBytes32(pih0);
        console.log("acc for PS1 (k=1) folded by {rollup1, rollup2}:");
        console.logBytes32(acc1);
        console.log("publicInputsHash[1] (PS1):");
        console.logBytes32(pih1);
    }

    // ---------------------------------------------------------------
    // VECTOR 7: sharedPublicInput / publicInputsHash with NON-EMPTY
    //           callData and ONE lookup call (exercises the non-empty
    //           abi.encode(bytes32[]) packing for lookupCallHashes).
    //
    //   entries          = [the VECTOR 4 entry]            (1 entry)
    //   l1ToL2lookupCalls = [one LookupCall]               (1 lookup call)
    //   blobHashes       = []
    //   callData         = 0xcafebabe                       (non-empty)
    //   crossProofSystemInteractions = keccak256("xpsi")    (non-zero)
    //
    //   single rollup id 1, single PS k=0, vk=0x100, blockNumber=0.
    // ---------------------------------------------------------------
    function _vector7_nonEmptyCallDataAndLookup(bytes32 entryHash) internal {
        // Build one concrete LookupCall and hash it exactly as the contract does.
        L2ToL1Call[] memory noCalls = new L2ToL1Call[](0);
        LookupCall memory lc = LookupCall({
            crossChainCallHash: bytes32(uint256(0x1234)),
            destinationRollupId: 1,
            returnData: hex"abcd",
            failed: true,
            callNumber: 0,
            lastNestedActionConsumed: 0,
            calls: noCalls,
            rollingHash: bytes32(0)
        });
        bytes32 lookupCallHash = keccak256(abi.encode(lc));

        bytes32[] memory entryHashes = new bytes32[](1);
        entryHashes[0] = entryHash;
        bytes32[] memory lookupCallHashes = new bytes32[](1);
        lookupCallHashes[0] = lookupCallHash;
        bytes32[] memory blobHashes = new bytes32[](0);
        bytes memory callData = hex"cafebabe";
        bytes32 crossProofSystemInteractions = keccak256("xpsi");

        bytes32 sharedPublicInput = keccak256(
            abi.encodePacked(
                abi.encode(entryHashes),
                abi.encode(lookupCallHashes),
                abi.encode(blobHashes),
                keccak256(callData),
                crossProofSystemInteractions
            )
        );

        bytes32 acc = bytes32(0);
        acc = keccak256(abi.encode(acc, uint256(1), bytes32(uint256(0x100)), bytes32(0), uint256(0)));
        bytes32 publicInputsHash = keccak256(abi.encodePacked(sharedPublicInput, acc));

        console.log("================ VECTOR 7: non-empty callData + 1 lookup call ================");
        console.log("abi.encode(LookupCall):");
        console.logBytes(abi.encode(lc));
        console.log("lookupCallHash = keccak256(abi.encode(lookupCall)):");
        console.logBytes32(lookupCallHash);
        console.log("callData = 0xcafebabe ; keccak256(callData):");
        console.logBytes32(keccak256(callData));
        console.log("crossProofSystemInteractions = keccak256('xpsi'):");
        console.logBytes32(crossProofSystemInteractions);
        console.log("sharedPublicInput:");
        console.logBytes32(sharedPublicInput);
        console.log("acc (rollup1, vk 0x100):");
        console.logBytes32(acc);
        console.log("publicInputsHash[0]:");
        console.logBytes32(publicInputsHash);
    }
}
