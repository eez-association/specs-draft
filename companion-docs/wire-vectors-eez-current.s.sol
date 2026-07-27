// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console} from "forge-std/Script.sol";
import {EEZ} from "../src/EEZ.sol";
import {EEZL2} from "../src/L2/EEZL2.sol";
import {CrossChainProxy} from "../src/base/CrossChainProxy.sol";
import {
    ExecutionEntry as L1ExecutionEntry,
    ExpectedL1ToL2Call,
    ExpectedLookup as L1ExpectedLookup,
    ExpectedStateRootPerRollup,
    L2ToL1Call,
    LookupCall as L1LookupCall,
    StateDelta
} from "../src/interfaces/IEEZ.sol";
import {
    CrossChainCall,
    ExecutionEntry as L2ExecutionEntry,
    ExpectedLookup as L2ExpectedLookup,
    ExpectedOutgoingCrossChainCall,
    LookupCall as L2LookupCall
} from "../src/interfaces/IEEZL2.sol";

/// @title WireVectors
/// @notice Executable conformance vectors for EEZ Framework Appendix B.
/// @dev Copy this file to eez-core-protocol@3a6ca65 as script/WireVectors.s.sol,
///      then run `forge script script/WireVectors.s.sol --offline -vv`.
contract WireVectors is Script {
    uint8 internal constant CALL_BEGIN = 1;
    uint8 internal constant CALL_END = 2;
    uint8 internal constant NESTED_BEGIN = 3;
    uint8 internal constant NESTED_END = 4;

    address internal constant TARGET = address(uint160(0xDeaDBeef));
    address internal constant SOURCE = address(uint160(0xC0FFEE));
    address internal constant FIXED_MANAGER = address(uint160(0x0EE200));

    bytes32 internal constant ACTION =
        0x6254f201d3301530dd7b10596ae0cfbc81512ae249819956824df2260cb8c2a2;
    bytes32 internal constant AFTER_BEGIN =
        0xa578faae9568ec79d80e92f83b4d08a4537677b5145aef1ab04b0c67dd76c63f;
    bytes32 internal constant AFTER_END =
        0x696336455de0a48486231a12058b65434a928dc21e0d6ce8b8e80179ac480e7d;
    bytes32 internal constant L1_ENTRY_HASH =
        0x51e1632383c7841fd9e2a174163aed36834896ede9a3d2f4936e1e67801bec71;
    bytes32 internal constant L1_LOOKUP_HASH =
        0x85be8606cad0ae3cb989136c5b255fe107c1b93f36b086538a041f5f70185b57;
    bytes32 internal constant L2_ENTRY_HASH =
        0x3308472f724b8141fe223e74d2ab939d2e0bd8668aaa25c21c8b611af0dec0fa;

    function run() external view {
        bytes32 action = _actionVector();
        bytes32 rollingHash = _rollingVectors();
        bytes32 l1EntryHash = _l1EntryVector(action, rollingHash);
        _l1LookupVector();
        _publicInputVector(l1EntryHash);
        _l2EntryVector(action, rollingHash);
        _proxyVector();
        _selectorVectors();

        console.log("All eez-core-protocol@3a6ca65 wire vectors passed.");
    }

    function _actionVector() internal pure returns (bytes32 action) {
        action = keccak256(abi.encode(uint256(1), TARGET, uint256(1 ether), hex"deadbeef", SOURCE, uint256(0)));
        require(action == ACTION, "action hash");
        console.log("action:");
        console.logBytes32(action);
    }

    function _rollingVectors() internal pure returns (bytes32 afterEnd) {
        bytes32 afterBegin = keccak256(abi.encodePacked(bytes32(0), CALL_BEGIN, uint256(1)));
        afterEnd = keccak256(abi.encodePacked(afterBegin, CALL_END, uint256(1), true, hex"01"));
        require(afterBegin == AFTER_BEGIN, "call begin");
        require(afterEnd == AFTER_END, "call end");

        bytes32 h = afterBegin;
        h = keccak256(abi.encodePacked(h, NESTED_BEGIN, uint256(1)));
        require(h == 0x3d834e314673d097a9dce11f90f7ebf82cde953e278c09167ce2a42b395b4cec, "nested begin");
        h = keccak256(abi.encodePacked(h, CALL_BEGIN, uint256(2)));
        require(h == 0x510b8848f50072c10d20af2e942be40a28b5ab71dc59658a053fa3645e6b2b2b, "child begin");
        h = keccak256(abi.encodePacked(h, CALL_END, uint256(2), true, hex"02"));
        require(h == 0x911db8ecc073330d76f92ed44c532d42128c630d888bf985e8b23e54a84aa824, "child end");
        h = keccak256(abi.encodePacked(h, NESTED_END, uint256(1)));
        require(h == 0xa4579cf4c504625737acdc1efb0a7a424e18c733de251ff23951746cf9e6d36b, "nested end");
        h = keccak256(abi.encodePacked(h, CALL_END, uint256(2), true, hex"01"));
        require(h == 0x34d9159317893ed5b9711a8212ff385c11c99bf74124608d0d219c85c429e151, "parent live cursor");

        bytes32 staticHash = keccak256(abi.encodePacked(bytes32(0), true, hex"abcd"));
        require(staticHash == 0xcadce27f539c1a651c804a271c7011fd8529acc643c3f6369a60adaa4aae1177, "static");

        console.log("direct rolling hash:");
        console.logBytes32(afterEnd);
        console.log("nested rolling hash:");
        console.logBytes32(h);
        console.log("static lookup hash:");
        console.logBytes32(staticHash);
    }

    function _l1EntryVector(bytes32 action, bytes32 rollingHash) internal pure returns (bytes32 entryHash) {
        StateDelta[] memory deltas = new StateDelta[](1);
        deltas[0] = StateDelta({
            rollupId: 1,
            currentState: bytes32(uint256(0xaa)),
            newState: bytes32(uint256(0xbb)),
            etherDelta: int256(1 ether)
        });

        L2ToL1Call[] memory calls = new L2ToL1Call[](1);
        calls[0] = L2ToL1Call({
            isStatic: false,
            targetAddress: TARGET,
            value: 0,
            data: hex"deadbeef",
            sourceAddress: SOURCE,
            sourceRollupId: 1,
            revertSpan: 0
        });

        ExpectedL1ToL2Call[] memory expectedCalls = new ExpectedL1ToL2Call[](0);
        L1ExpectedLookup[] memory expectedLookups = new L1ExpectedLookup[](0);

        L1ExecutionEntry memory entry = L1ExecutionEntry({
            stateDeltas: deltas,
            proxyEntryHash: action,
            destinationRollupId: 1,
            returnData: hex"",
            l2ToL1Calls: calls,
            expectedL1ToL2Calls: expectedCalls,
            expectedLookups: expectedLookups,
            callCount: 1,
            rollingHash: rollingHash
        });

        bytes memory encoded = abi.encode(entry);
        entryHash = keccak256(encoded);
        require(encoded.length == 928, "L1 entry length");
        require(entryHash == L1_ENTRY_HASH, "L1 entry hash");

        console.log("L1 entry hash:");
        console.logBytes32(entryHash);
    }

    function _l1LookupVector() internal pure {
        L2ToL1Call[] memory calls = new L2ToL1Call[](0);
        ExpectedL1ToL2Call[] memory expectedCalls = new ExpectedL1ToL2Call[](0);
        L1ExpectedLookup[] memory expectedLookups = new L1ExpectedLookup[](0);
        ExpectedStateRootPerRollup[] memory pins = new ExpectedStateRootPerRollup[](1);
        pins[0] = ExpectedStateRootPerRollup({rollupId: 1, stateRoot: bytes32(uint256(0xaa))});

        L1LookupCall memory lookup = L1LookupCall({
            crossChainCallHash: bytes32(uint256(0x1234)),
            destinationRollupId: 1,
            returnData: hex"abcd",
            failed: true,
            l2ToL1Calls: calls,
            expectedL1ToL2Calls: expectedCalls,
            expectedLookups: expectedLookups,
            callCount: 0,
            rollingHash: bytes32(0),
            expectedStateRoots: pins
        });

        bytes memory encoded = abi.encode(lookup);
        require(encoded.length == 608, "L1 lookup length");
        require(keccak256(encoded) == L1_LOOKUP_HASH, "L1 lookup hash");

        console.log("L1 lookup hash:");
        console.logBytes32(keccak256(encoded));
    }

    function _publicInputVector(bytes32 entryHash) internal pure {
        bytes32[] memory entryHashes = new bytes32[](1);
        entryHashes[0] = entryHash;
        bytes32[] memory lookupHashes = new bytes32[](0);
        bytes32[] memory blobHashes = new bytes32[](0);

        bytes32 customDataAcc = keccak256(abi.encode(bytes32(0), uint256(1), bytes("")));
        bytes32 sharedPublicInput = keccak256(
            abi.encodePacked(
                abi.encode(entryHashes),
                abi.encode(lookupHashes),
                abi.encode(blobHashes),
                keccak256(bytes("")),
                customDataAcc
            )
        );
        bytes32 proofSystemAcc =
            keccak256(abi.encode(bytes32(0), uint256(1), bytes32(uint256(0x100))));
        bytes32 publicInputsHash = keccak256(abi.encodePacked(sharedPublicInput, proofSystemAcc));

        require(
            customDataAcc == 0xc0dc72cf9435ef1cd9a5e872346bf9ca5cf6306d8f62305d089f6a9d582792b8,
            "custom data"
        );
        require(
            sharedPublicInput == 0x53641eba159eb8caf003dccc161151497535a7b559ac5333ae663a596dfe4c79,
            "shared input"
        );
        require(
            proofSystemAcc == 0xf648b9fec533a721da003a85b25ec87bb231f0b8d429fb3b2099729a589a48a5,
            "proof system acc"
        );
        require(
            publicInputsHash == 0xe265e1c1fbc52c560558b76be4ede800269f90a65b7065c3e0ffc9baadb83076,
            "public input"
        );

        console.log("public inputs hash:");
        console.logBytes32(publicInputsHash);
    }

    function _l2EntryVector(bytes32 action, bytes32 rollingHash) internal pure {
        CrossChainCall[] memory calls = new CrossChainCall[](1);
        calls[0] = CrossChainCall({
            isStatic: false,
            targetAddress: TARGET,
            value: 1 ether,
            data: hex"deadbeef",
            sourceAddress: SOURCE,
            sourceRollupId: 0,
            revertSpan: 0
        });
        ExpectedOutgoingCrossChainCall[] memory expectedCalls =
            new ExpectedOutgoingCrossChainCall[](0);
        L2ExpectedLookup[] memory expectedLookups = new L2ExpectedLookup[](0);

        L2ExecutionEntry memory entry = L2ExecutionEntry({
            proxyEntryHash: action,
            incomingCalls: calls,
            expectedOutgoingCalls: expectedCalls,
            expectedLookups: expectedLookups,
            callCount: 1,
            returnData: hex"",
            rollingHash: rollingHash
        });

        bytes memory encoded = abi.encode(entry);
        require(encoded.length == 704, "L2 entry length");
        require(keccak256(encoded) == L2_ENTRY_HASH, "L2 entry hash");

        // Reference the top-level L2 lookup type so ABI drift in that import is compiled too.
        L2LookupCall[] memory emptyLookups = new L2LookupCall[](0);
        require(emptyLookups.length == 0, "empty L2 lookups");

        console.log("L2 entry checksum:");
        console.logBytes32(keccak256(encoded));
    }

    function _proxyVector() internal pure {
        bytes memory creationCode = type(CrossChainProxy).creationCode;
        bytes32 creationHash = keccak256(creationCode);
        bytes32 salt = keccak256(abi.encodePacked(uint256(1), SOURCE));
        bytes32 initHash =
            keccak256(abi.encodePacked(creationCode, abi.encode(FIXED_MANAGER, SOURCE, uint256(1))));
        address proxy = address(
            uint160(uint256(keccak256(abi.encodePacked(hex"ff", FIXED_MANAGER, salt, initHash))))
        );

        require(creationCode.length == 1111, "creation length");
        require(
            creationHash == 0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8,
            "creation hash"
        );
        require(salt == 0x9b795495c996503b00c5938a264389c4df5c002802eae27e9463f48ea7aafdd5, "salt");
        require(initHash == 0x7045969eb5c85c24a087914cfde032ebaa277996f1a2ea343a2b7d92af3e7c4b, "init hash");
        require(proxy == 0xC5dc78B57986585780Dc0c44b99a94888522E50c, "proxy");

        console.log("proxy:");
        console.logAddress(proxy);
    }

    function _selectorVectors() internal pure {
        require(EEZ.postAndVerifyBatch.selector == bytes4(0xd1fc6b5a), "post selector");
        require(EEZ.executeL2TX.selector == bytes4(0xccdcf581), "L2 tx selector");
        require(EEZL2.loadExecutionTable.selector == bytes4(0xc1b4427c), "load selector");
        require(
            EEZL2.executeIncomingCrossChainCall.selector == bytes4(0xf882a0ad),
            "incoming selector"
        );
    }
}
