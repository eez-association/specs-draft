#!/usr/bin/env python3
"""Validate EEZ network profiles and immutable binding artifacts.

This script uses only the Python standard library. It implements the JSON Schema
keywords used by network-profile.schema.json and the semantic checks that JSON
Schema cannot express.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SPEC_DIR = Path(__file__).resolve().parent
DOCS_DIR = SPEC_DIR.parent
SCHEMA_PATH = SPEC_DIR / "network-profile.schema.json"
ARTIFACT_PATH = SPEC_DIR / "fixtures" / "cross-chain-proxy-creation-code.json"
CORPUS_PATH = SPEC_DIR / "fixtures" / "eez-evm-0.2-conformance.json"
DEFAULT_PROFILES = (
    DOCS_DIR / "rollup0-network-spec" / "network-profile.json",
    DOCS_DIR / "gnosis-chain-eez-spec" / "network-profile.json",
    DOCS_DIR / "gnosis-chain-eez-spec" / "network-profile-rollup0.json",
)

EXPECTED_PROXY_LENGTH = 1111
EXPECTED_PROXY_KECCAK = (
    "0xb1687b0fbd90a4baf5ab2f1e1bb3b2c64d571f33a6e9c3fa1748cfdf500abcc8"
)
EXPECTED_DEPLOYED_ABI_SHA256 = (
    "0x642b81e32d3f8cca5510097278bb9753e8ea090a93b591803b1971db3d2820da"
)
MAX_PROFILE_INTEGER = (1 << 53) - 1
FORKS_AT_OR_AFTER_CANCUN = {
    "cancun",
    "dencun",
    "dencun/cancun",
    "prague",
    "pectra",
    "prague/pectra",
    "osaka",
}
REQUIRED_OPCODE_SEMANTICS = {
    "transient_storage": "EIP-1153",
    "blobhash": "EIP-4844",
    "mcopy": "EIP-5656",
}
REQUIRED_ROUTING_FIELDS = {
    "0.1-rollup0": {
        "transientExecutionEntryCount",
        "transientLookupCallCount",
    },
    "0.2-draft": {
        "transientExecutionEntryCount",
        "transientLookupCallCount",
    },
}
SUPPORTED_BINDINGS = {
    "0.1-rollup0": "rollup0-network-spec/E-compatibility-binding.md",
    "0.2-draft": "eez-protocol-spec/index.md",
}
EXPECTED_ERROR_SIGNATURES = {
    "shared": {
        "UnauthorizedProxy()",
        "NotSelf()",
        "ExecutionNotFound()",
        "RollingHashMismatch()",
        "ContextResult(bytes32,uint256,uint256,bool)",
        "UnexpectedContextRevert(bytes)",
        "LookupCallProxyNotDeployed(address)",
        "StaticCallWithValue()",
        "SameNetworkProxy(uint256)",
    },
    "l1": {
        "InvalidProof()",
        "PostBatchReentry()",
        "NotRollupContract()",
        "RollupBatchActiveThisBlock(uint256)",
        "InvalidRollupContract()",
        "InsufficientRollupBalance()",
        "EtherDeltaMismatch()",
        "ResidualEntryEtherIn()",
        "StateRootMismatch(uint256)",
        "ExecutionNotInCurrentBlock(uint256)",
        "L2TXNotAllowedDuringExecution()",
        "SetStateRootNotAllowedDuringExecution()",
        "TransientCountExceedsEntries()",
        "TransientLookupCallCountExceedsLookupCalls()",
        "TransientLookupCallsWithoutTransientEntries()",
        "InvalidProofSystemConfig()",
        "DuplicateProofSystem(address)",
        "RollupNotInBatch(uint256)",
        "UnconsumedL2ToL1Calls()",
        "UnconsumedL1ToL2Calls()",
        "EntryDestinationNotInStateDeltas(uint256)",
        "LookupDestinationNotPinned(uint256)",
        "CallSourceNotVerified(uint256)",
        "ReentrantDestinationNotVerified(uint256)",
        "ReentrantDestinationMismatch(uint256,uint256)",
        "StateDeltasNotStrictlyIncreasing(uint256)",
        "ExpectedStateRootsNotStrictlyIncreasing(uint256)",
    },
    "l2": {
        "Unauthorized()",
        "InvalidRollupId()",
        "ExecutionNotInCurrentBlock()",
        "EtherTransferFailed()",
        "EmptyEntries()",
        "ValueMismatch()",
        "EntryHashMismatch()",
        "UnconsumedIncomingCalls()",
        "UnconsumedOutgoingCalls()",
    },
}
EXPECTED_ABI_FUNCTION_COUNTS = {
    "EEZ": 20,
    "EEZL2": 15,
    "CrossChainProxy": 2,
}
EXPECTED_COLLABORATOR_SIGNATURES = {
    "rollupContractRegistered": "rollupContractRegistered(uint256)",
    "checkProofSystemsAndGetVkeys": "checkProofSystemsAndGetVkeys(address[])",
    "getCustomData": "getCustomData(uint64)",
    "verify": "verify(bytes,bytes32)",
    "executeMetaCrossChainTransactions": "executeMetaCrossChainTransactions()",
}
ROLE_OWNED_SELECTIONS = {
    "rollup": (
        ("chain_identity", "eip155_chain_id"),
        ("chain_identity", "eez_rollup_id"),
        ("chain_identity", "native_asset"),
        ("chain_identity", "genesis_commitment"),
        ("chain_identity", "evm_fork"),
        ("settlement_binding", "host_profile"),
        ("settlement_binding", "host_network"),
        ("settlement_binding", "host_chain_id"),
        ("settlement_binding", "manager_contract"),
        ("settlement_binding", "proof_system_contracts"),
        ("settlement_binding", "settlement_rule"),
        ("settlement_binding", "finality_rule"),
        ("execution_binding", "block_time_ms"),
        ("execution_binding", "block_gas_limit"),
        ("execution_binding", "fee_market"),
        ("execution_binding", "fee_recipient"),
        ("execution_binding", "eez_predeploys"),
        ("execution_binding", "system_address"),
        ("execution_binding", "system_transaction_envelope"),
        ("operation", "sequencing_model"),
        ("operation", "sequencing_authority"),
        ("operation", "slot_construction"),
        ("operation", "atomic_inclusion"),
        ("operation", "max_user_transactions_per_bundle"),
        ("operation", "proof_routing_mitigation"),
        ("proof_policy", "model"),
        ("proof_policy", "allowed_proof_systems_and_vkeys"),
        ("proof_policy", "threshold"),
        ("data_availability", "requirement"),
        ("data_availability", "channel"),
        ("data_availability", "codec"),
        ("data_availability", "derivation_rule"),
        ("governance_recovery", "manager_authority"),
        ("governance_recovery", "upgrade_policy"),
        ("governance_recovery", "reorg_and_emergency_rule"),
    ),
    "settlement-host": (
        ("chain_identity", "eip155_chain_id"),
        ("chain_identity", "native_asset"),
        ("chain_identity", "genesis_commitment"),
        ("chain_identity", "evm_fork"),
        ("settlement_binding", "eez_contract"),
        ("settlement_binding", "deployment_block"),
        ("settlement_binding", "settlement_rule"),
        ("settlement_binding", "finality_rule"),
        ("execution_binding", "block_time_ms"),
        ("execution_binding", "block_gas_limit"),
        ("execution_binding", "fee_market"),
        ("operation", "sequencing_model"),
        ("operation", "sequencing_authority"),
        ("operation", "slot_construction"),
        ("operation", "atomic_inclusion"),
        ("governance_recovery", "upgrade_policy"),
        ("governance_recovery", "reorg_and_emergency_rule"),
    ),
}
ROLE_EXCLUDED_SELECTIONS = {
    "rollup": (
        ("settlement_binding", "eez_contract"),
        ("settlement_binding", "deployment_block"),
    ),
    "settlement-host": (
        ("chain_identity", "eez_rollup_id"),
        ("settlement_binding", "host_profile"),
        ("settlement_binding", "host_network"),
        ("settlement_binding", "host_chain_id"),
        ("settlement_binding", "manager_contract"),
        ("settlement_binding", "proof_system_contracts"),
        ("execution_binding", "fee_recipient"),
        ("execution_binding", "eez_predeploys"),
        ("execution_binding", "system_address"),
        ("execution_binding", "system_transaction_envelope"),
        ("operation", "max_user_transactions_per_bundle"),
        ("operation", "proof_routing_mitigation"),
        ("proof_policy", "model"),
        ("proof_policy", "allowed_proof_systems_and_vkeys"),
        ("proof_policy", "threshold"),
        ("data_availability", "requirement"),
        ("data_availability", "channel"),
        ("data_availability", "codec"),
        ("data_availability", "derivation_rule"),
        ("governance_recovery", "manager_authority"),
    ),
}


class ValidationError(ValueError):
    """A profile, schema, or artifact is non-conforming."""


def load_json(path: Path) -> Any:
    def reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, child in pairs:
            if key in value:
                raise ValidationError(f"{path}: duplicate JSON object member {key!r}")
            value[key] = child
        return value

    def reject_non_json_number(token: str) -> Any:
        raise ValidationError(f"{path}: non-JSON numeric token {token!r}")

    try:
        with path.open("r", encoding="utf-8") as source:
            return json.load(
                source,
                object_pairs_hook=reject_duplicate_members,
                parse_constant=reject_non_json_number,
            )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


class SchemaValidator:
    """Validate the JSON Schema subset used by the EEZ profile schema."""

    def __init__(self, root_schema: dict[str, Any]) -> None:
        self.root_schema = root_schema

    def resolve(self, reference: str) -> Any:
        if not reference.startswith("#/"):
            raise ValidationError(f"unsupported non-local $ref: {reference}")
        value: Any = self.root_schema
        for raw_part in reference[2:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            try:
                value = value[part]
            except (KeyError, TypeError) as exc:
                raise ValidationError(f"unresolved $ref: {reference}") from exc
        return value

    @staticmethod
    def is_type(instance: Any, expected: str) -> bool:
        if expected == "null":
            return instance is None
        if expected == "boolean":
            return isinstance(instance, bool)
        if expected == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        if expected == "number":
            return isinstance(instance, (int, float)) and not isinstance(instance, bool)
        if expected == "string":
            return isinstance(instance, str)
        if expected == "array":
            return isinstance(instance, list)
        if expected == "object":
            return isinstance(instance, dict)
        raise ValidationError(f"unsupported schema type: {expected}")

    def matches(self, instance: Any, schema: Any, path: str) -> bool:
        try:
            self.validate(instance, schema, path)
        except ValidationError:
            return False
        return True

    def validate(self, instance: Any, schema: Any, path: str = "$") -> None:
        if schema is True:
            return
        if schema is False:
            raise ValidationError(f"{path}: rejected by false schema")
        if not isinstance(schema, dict):
            raise ValidationError(f"{path}: invalid schema node")

        reference = schema.get("$ref")
        if reference is not None:
            self.validate(instance, self.resolve(reference), path)

        expected_type = schema.get("type")
        if isinstance(expected_type, str) and not self.is_type(instance, expected_type):
            raise ValidationError(f"{path}: expected {expected_type}")
        if isinstance(expected_type, list) and not any(
            self.is_type(instance, item) for item in expected_type
        ):
            raise ValidationError(f"{path}: expected one of {expected_type}")

        if "const" in schema and not json_equal(instance, schema["const"]):
            raise ValidationError(f"{path}: expected constant {schema['const']!r}")
        if "enum" in schema and not any(json_equal(instance, item) for item in schema["enum"]):
            raise ValidationError(f"{path}: value is not in the allowed enum")

        if "allOf" in schema:
            for subschema in schema["allOf"]:
                self.validate(instance, subschema, path)
        if "anyOf" in schema and not any(
            self.matches(instance, subschema, path) for subschema in schema["anyOf"]
        ):
            raise ValidationError(f"{path}: no anyOf branch matched")
        if "oneOf" in schema:
            match_count = sum(
                self.matches(instance, subschema, path) for subschema in schema["oneOf"]
            )
            if match_count != 1:
                raise ValidationError(f"{path}: expected one oneOf match, got {match_count}")
        if "not" in schema and self.matches(instance, schema["not"], path):
            raise ValidationError(f"{path}: matched a forbidden schema")

        if isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0):
                raise ValidationError(f"{path}: string is too short")
            pattern = schema.get("pattern")
            if pattern is not None:
                match = re.search(pattern, instance)
                anchored_mismatch = (
                    match is not None
                    and pattern.startswith("^")
                    and pattern.endswith("$")
                    and match.span() != (0, len(instance))
                )
                if match is None or anchored_mismatch:
                    raise ValidationError(f"{path}: does not match {pattern!r}")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                raise ValidationError(f"{path}: value is below minimum {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                raise ValidationError(f"{path}: value is above maximum {schema['maximum']}")

        if isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                raise ValidationError(f"{path}: array has too few items")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                raise ValidationError(f"{path}: array has too many items")
            if schema.get("uniqueItems"):
                encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
                if len(encoded) != len(set(encoded)):
                    raise ValidationError(f"{path}: array items are not unique")
            item_schema = schema.get("items")
            if item_schema is not None:
                for index, value in enumerate(instance):
                    self.validate(value, item_schema, f"{path}[{index}]")

        if isinstance(instance, dict):
            if len(instance) < schema.get("minProperties", 0):
                raise ValidationError(f"{path}: object has too few properties")
            for key in schema.get("required", []):
                if key not in instance:
                    raise ValidationError(f"{path}: missing required property {key!r}")
            properties = schema.get("properties", {})
            for key, subschema in properties.items():
                if key in instance:
                    self.validate(instance[key], subschema, f"{path}.{key}")
            additional = schema.get("additionalProperties", True)
            unknown = set(instance) - set(properties)
            if additional is False and unknown:
                raise ValidationError(
                    f"{path}: undeclared properties: {', '.join(sorted(unknown))}"
                )
            if isinstance(additional, dict):
                for key in unknown:
                    self.validate(instance[key], additional, f"{path}.{key}")

        if "if" in schema:
            branch = "then" if self.matches(instance, schema["if"], path) else "else"
            if branch in schema:
                self.validate(instance, schema[branch], path)


def collect_release_blockers(value: Any, path: str = "$") -> list[tuple[str, str]]:
    blockers: list[tuple[str, str]] = []
    if isinstance(value, dict):
        if value.get("status") == "release-blocker":
            blocker_id = value.get("id")
            if not isinstance(blocker_id, str):
                raise ValidationError(f"{path}: release blocker has no string id")
            blockers.append((blocker_id, path))
        for key, child in value.items():
            if path == "$" and key == "release_blockers":
                continue
            blockers.extend(collect_release_blockers(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            blockers.extend(collect_release_blockers(child, f"{path}[{index}]"))
    return blockers


def validate_integer_domain(value: Any, source: Path, path: str = "$") -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < 0 or value > MAX_PROFILE_INTEGER:
            raise ValidationError(
                f"{source}: {path} integer is outside the exact interoperable JSON domain"
            )
        return
    if isinstance(value, dict):
        for key, child in value.items():
            validate_integer_domain(child, source, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_integer_domain(child, source, f"{path}[{index}]")


def validate_binding_specification(profile: dict[str, Any], path: Path) -> None:
    binding = profile["eez_dependency"]["evm_binding"]
    version = binding["version"]
    expected_specification = SUPPORTED_BINDINGS.get(version)
    if expected_specification is None:
        supported = ", ".join(sorted(SUPPORTED_BINDINGS))
        raise ValidationError(
            f"{path}: unregistered EVM binding version {version!r}; supported: {supported}"
        )
    specification = binding.get("specification")
    if specification != expected_specification:
        raise ValidationError(
            f"{path}: {version} must cite binding specification "
            f"{expected_specification!r}, got {specification!r}"
        )
    specification_path = (DOCS_DIR / specification).resolve()
    try:
        specification_path.relative_to(DOCS_DIR.resolve())
    except ValueError as exc:
        raise ValidationError(
            f"{path}: binding specification escapes the documentation root"
        ) from exc
    if not specification_path.is_file():
        raise ValidationError(
            f"{path}: binding specification does not exist: {specification}"
        )


def validate_deployment_sets(profile: dict[str, Any], path: Path) -> None:
    selection = profile["settlement_binding"]["proof_system_contracts"]
    if selection.get("status") != "fixed":
        return
    deployments = selection.get("value")
    if not isinstance(deployments, list):
        raise ValidationError(f"{path}: fixed proof_system_contracts must be an array")
    seen: set[str] = set()
    for index, deployment in enumerate(deployments):
        if not isinstance(deployment, dict) or not isinstance(deployment.get("address"), str):
            raise ValidationError(
                f"{path}: proof_system_contracts[{index}] has no deployment address"
            )
        address = deployment["address"].lower()
        if address in seen:
            raise ValidationError(
                f"{path}: duplicate proof-system deployment address {address}"
            )
        seen.add(address)


def require_cancun_compatible_fork(profile: dict[str, Any], path: Path) -> None:
    selection = profile["chain_identity"]["evm_fork"]
    if selection.get("status") != "fixed":
        raise ValidationError(f"{path}: chain_identity.evm_fork must be fixed")
    value = selection["value"]
    if not isinstance(value, dict):
        raise ValidationError(
            f"{path}: chain_identity.evm_fork.value must be an object with an explicit "
            "minimum_execution_fork"
        )
    minimum = value.get("minimum_execution_fork")
    if not isinstance(minimum, str) or minimum.strip().lower() not in FORKS_AT_OR_AFTER_CANCUN:
        allowed = ", ".join(sorted(FORKS_AT_OR_AFTER_CANCUN))
        raise ValidationError(
            f"{path}: minimum_execution_fork must be one of: {allowed}"
        )
    activation = value.get("activation")
    if not isinstance(activation, dict):
        raise ValidationError(f"{path}: evm_fork activation must be an object")
    kind = activation.get("kind")
    if kind == "genesis":
        if set(activation) != {"kind"}:
            raise ValidationError(
                f"{path}: a genesis fork activation must contain only kind"
            )
    elif kind in ("block", "timestamp"):
        activation_value = activation.get("value")
        if (
            set(activation) != {"kind", "value"}
            or not isinstance(activation_value, int)
            or isinstance(activation_value, bool)
            or activation_value < 0
        ):
            raise ValidationError(
                f"{path}: a {kind} fork activation requires one non-negative integer value"
            )
    else:
        raise ValidationError(
            f"{path}: evm_fork activation kind must be genesis, block, or timestamp"
        )
    if value.get("opcode_semantics") != REQUIRED_OPCODE_SEMANTICS:
        raise ValidationError(
            f"{path}: evm_fork must affirm the exact EIP-1153, EIP-4844, and "
            "EIP-5656 opcode semantics"
        )
    validation_rule = value.get("validation")
    if not isinstance(validation_rule, str) or not validation_rule.strip():
        raise ValidationError(f"{path}: evm_fork requires a non-empty validation rule")


def validate_proof_routing(profile: dict[str, Any], path: Path) -> None:
    metadata = profile["profile"]
    if metadata["role"] != "rollup":
        return

    selection = profile["operation"].get("proof_routing_mitigation")
    if not isinstance(selection, dict):
        raise ValidationError(
            f"{path}: rollup requires operation.proof_routing_mitigation"
        )
    status = selection.get("status")
    if status not in ("fixed", "release-blocker"):
        raise ValidationError(
            f"{path}: proof_routing_mitigation must be fixed or a release blocker"
        )
    if metadata["status"] == "production" and status != "fixed":
        raise ValidationError(
            f"{path}: production proof_routing_mitigation must be fixed"
        )
    if status == "fixed":
        value = selection.get("value")
        if not isinstance(value, dict):
            raise ValidationError(
                f"{path}: fixed proof_routing_mitigation value must be an object"
            )
        for field in (
            "authenticates_caller",
            "prevents_replay",
            "prevents_front_running",
        ):
            if value.get(field) is not True:
                raise ValidationError(
                    f"{path}: fixed proof_routing_mitigation must set {field} to true"
                )
        for field in ("mechanism", "binding_evidence", "failure_rule"):
            if not isinstance(value.get(field), str) or not value[field].strip():
                raise ValidationError(
                    f"{path}: fixed proof_routing_mitigation requires non-empty {field}"
                )
        authenticated_fields = value.get("authenticated_calldata_fields")
        if not isinstance(authenticated_fields, list) or any(
            not isinstance(field, str) or not field
            for field in authenticated_fields
        ):
            raise ValidationError(
                f"{path}: authenticated_calldata_fields must be an array of non-empty strings"
            )
        binding_version = profile["eez_dependency"]["evm_binding"]["version"]
        required_fields = REQUIRED_ROUTING_FIELDS.get(binding_version)
        if required_fields is not None and set(authenticated_fields) != required_fields:
            expected = ", ".join(sorted(required_fields))
            raise ValidationError(
                f"{path}: {binding_version} proof routing must authenticate exactly: "
                f"{expected}"
            )


def validate_role_owned_selections(profile: dict[str, Any], path: Path) -> None:
    role = profile["profile"]["role"]
    for group, field in ROLE_OWNED_SELECTIONS[role]:
        status = profile[group][field].get("status")
        if status not in ("fixed", "release-blocker"):
            raise ValidationError(
                f"{path}: {role}-owned {group}.{field} must be fixed or a release blocker"
            )
    for group, field in ROLE_EXCLUDED_SELECTIONS[role]:
        status = profile[group][field].get("status")
        if status != "not-applicable":
            raise ValidationError(
                f"{path}: {role}-excluded {group}.{field} must be not-applicable"
            )


def validate_profile_semantics(profile: dict[str, Any], path: Path) -> None:
    validate_integer_domain(profile, path)
    nested = collect_release_blockers(profile)
    nested_ids = {blocker_id for blocker_id, _ in nested}
    root_ids = profile["release_blockers"]
    root_set = set(root_ids)

    if len(root_ids) != len(root_set):
        raise ValidationError(f"{path}: release_blockers contains duplicate IDs")
    if nested_ids != root_set:
        missing = sorted(nested_ids - root_set)
        stale = sorted(root_set - nested_ids)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if stale:
            details.append(f"stale {stale}")
        raise ValidationError(f"{path}: release_blockers set mismatch ({'; '.join(details)})")
    if profile["profile"]["status"] == "production" and nested:
        first_id, first_path = nested[0]
        raise ValidationError(
            f"{path}: production profile contains blocker {first_id} at {first_path}"
        )

    validate_binding_specification(profile, path)
    validate_deployment_sets(profile, path)
    validate_role_owned_selections(profile, path)
    require_cancun_compatible_fork(profile, path)
    validate_proof_routing(profile, path)


def validate_profile_references(
    profiles: list[tuple[Path, dict[str, Any]]],
) -> None:
    """Resolve fixed rollup host references within the validated profile set."""

    by_identity: dict[tuple[str, str], tuple[Path, dict[str, Any]]] = {}
    for path, profile in profiles:
        metadata = profile["profile"]
        identity = (metadata["id"], metadata["version"])
        previous = by_identity.get(identity)
        if previous is not None:
            raise ValidationError(
                f"{path}: duplicate profile identity "
                f"{identity[0]}@{identity[1]} also loaded from {previous[0]}"
            )
        by_identity[identity] = (path, profile)

    for path, profile in profiles:
        if profile["profile"]["role"] != "rollup":
            continue

        host_selection = profile["settlement_binding"]["host_profile"]
        if host_selection.get("status") != "fixed":
            continue
        reference = host_selection["value"]
        identity = (reference["profile_id"], reference["profile_version"])
        resolved = by_identity.get(identity)
        if resolved is None:
            raise ValidationError(
                f"{path}: referenced host profile {identity[0]}@{identity[1]} "
                "is not in the validated profile set"
            )

        host_path, host = resolved
        if host["profile"]["role"] != "settlement-host":
            raise ValidationError(
                f"{path}: referenced profile {identity[0]}@{identity[1]} "
                f"from {host_path} is not a settlement host"
            )
        if profile["profile"]["status"] == "production":
            if host["profile"]["status"] != "production":
                raise ValidationError(
                    f"{path}: a production rollup must reference a production host profile"
                )
            if host["release_blockers"]:
                raise ValidationError(
                    f"{path}: a production rollup cannot reference a host profile with "
                    "release blockers"
                )

        for dependency_name in ("framework", "evm_binding"):
            rollup_dependency = profile["eez_dependency"][dependency_name]
            host_dependency = host["eez_dependency"][dependency_name]
            if rollup_dependency != host_dependency:
                raise ValidationError(
                    f"{path}: {dependency_name} dependency "
                    f"{rollup_dependency['id']}@{rollup_dependency['version']} disagrees with "
                    f"host profile {host_dependency['id']}@{host_dependency['version']}"
                )

        rollup_chain = profile["settlement_binding"]["host_chain_id"]
        host_chain = host["chain_identity"]["eip155_chain_id"]
        if rollup_chain.get("status") != "fixed" or host_chain.get("status") != "fixed":
            raise ValidationError(
                f"{path}: a fixed host_profile reference requires fixed host_chain_id "
                "in both profiles"
            )
        if not json_equal(rollup_chain["value"], host_chain["value"]):
            raise ValidationError(
                f"{path}: host_chain_id {rollup_chain['value']!r} disagrees with "
                f"{identity[0]}@{identity[1]} chain ID {host_chain['value']!r}"
            )

        rollup_network = profile["settlement_binding"]["host_network"]
        if rollup_network.get("status") != "fixed":
            raise ValidationError(
                f"{path}: a fixed host_profile reference requires fixed host_network"
            )
        if rollup_network["value"] != host["profile"]["network_name"]:
            raise ValidationError(
                f"{path}: host_network {rollup_network['value']!r} disagrees with "
                f"{identity[0]}@{identity[1]} network name "
                f"{host['profile']['network_name']!r}"
            )


ROTATION = (
    0, 1, 62, 28, 27,
    36, 44, 6, 55, 20,
    3, 10, 43, 25, 39,
    41, 45, 15, 21, 8,
    18, 2, 61, 56, 14,
)
ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)
MASK64 = (1 << 64) - 1


def rotate_left(value: int, shift: int) -> int:
    if shift == 0:
        return value
    return ((value << shift) | (value >> (64 - shift))) & MASK64


def keccak_f1600(state: list[int]) -> None:
    for round_constant in ROUND_CONSTANTS:
        columns = [
            state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
            for x in range(5)
        ]
        deltas = [
            columns[(x - 1) % 5] ^ rotate_left(columns[(x + 1) % 5], 1)
            for x in range(5)
        ]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= deltas[x]

        lanes = [0] * 25
        for x in range(5):
            for y in range(5):
                lanes[y + 5 * ((2 * x + 3 * y) % 5)] = rotate_left(
                    state[x + 5 * y], ROTATION[x + 5 * y]
                )

        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = (
                    lanes[x + 5 * y]
                    ^ ((~lanes[(x + 1) % 5 + 5 * y]) & lanes[(x + 2) % 5 + 5 * y])
                ) & MASK64
        state[0] ^= round_constant


def keccak256(payload: bytes) -> bytes:
    rate = 136
    padded = bytearray(payload)
    padded.append(0x01)
    padded.extend(b"\x00" * ((rate - len(padded) % rate) % rate))
    padded[-1] ^= 0x80

    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for lane in range(rate // 8):
            start = lane * 8
            state[lane] ^= int.from_bytes(block[start : start + 8], "little")
        keccak_f1600(state)

    output = b"".join(lane.to_bytes(8, "little") for lane in state[: rate // 8])
    return output[:32]


def validate_proxy_artifact() -> None:
    artifact = load_json(ARTIFACT_PATH)
    if artifact.get("schema") != "eez-evm-immutable-creation-code/1":
        raise ValidationError(f"{ARTIFACT_PATH}: unexpected artifact schema")
    if artifact.get("binding") != {"id": "eez-evm", "version": "0.2-draft"}:
        raise ValidationError(f"{ARTIFACT_PATH}: unexpected binding identity")

    encoded = artifact.get("creation_code")
    if not isinstance(encoded, str) or not encoded.startswith("0x"):
        raise ValidationError(f"{ARTIFACT_PATH}: creation_code must be 0x-prefixed hex")
    try:
        creation_code = bytes.fromhex(encoded[2:])
    except ValueError as exc:
        raise ValidationError(f"{ARTIFACT_PATH}: invalid creation_code hex") from exc

    declared_length = artifact.get("byte_length")
    declared_hash = artifact.get("keccak256")
    actual_hash = "0x" + keccak256(creation_code).hex()
    if len(creation_code) != EXPECTED_PROXY_LENGTH or declared_length != EXPECTED_PROXY_LENGTH:
        raise ValidationError(
            f"{ARTIFACT_PATH}: expected {EXPECTED_PROXY_LENGTH} bytes, got "
            f"{len(creation_code)} with declaration {declared_length!r}"
        )
    if actual_hash != EXPECTED_PROXY_KECCAK or declared_hash != EXPECTED_PROXY_KECCAK:
        raise ValidationError(
            f"{ARTIFACT_PATH}: expected {EXPECTED_PROXY_KECCAK}, got "
            f"{actual_hash} with declaration {declared_hash!r}"
        )

    corpus = load_json(CORPUS_PATH)
    if corpus.get("normative_proxy_creation_code_artifact") != ARTIFACT_PATH.name:
        raise ValidationError(f"{CORPUS_PATH}: proxy artifact reference is missing or stale")
    proxy_vector = corpus.get("vectors", {}).get("proxy_create2", {})
    if proxy_vector.get("creation_code_length") != EXPECTED_PROXY_LENGTH:
        raise ValidationError(f"{CORPUS_PATH}: proxy vector length does not match artifact")
    if proxy_vector.get("creation_code_hash") != EXPECTED_PROXY_KECCAK:
        raise ValidationError(f"{CORPUS_PATH}: proxy vector hash does not match artifact")


def validate_error_selectors() -> None:
    corpus = load_json(CORPUS_PATH)
    selectors = corpus.get("error_selectors")
    if not isinstance(selectors, dict) or set(selectors) != set(EXPECTED_ERROR_SIGNATURES):
        raise ValidationError(f"{CORPUS_PATH}: custom-error ownership groups are incomplete")

    selector_owners: dict[str, tuple[str, str]] = {}
    for owner, expected_signatures in EXPECTED_ERROR_SIGNATURES.items():
        owner_selectors = selectors.get(owner)
        if not isinstance(owner_selectors, dict):
            raise ValidationError(f"{CORPUS_PATH}: error_selectors.{owner} must be an object")
        if set(owner_selectors) != expected_signatures:
            missing = sorted(expected_signatures - set(owner_selectors))
            extra = sorted(set(owner_selectors) - expected_signatures)
            raise ValidationError(
                f"{CORPUS_PATH}: error_selectors.{owner} signature mismatch "
                f"(missing {missing}; extra {extra})"
            )
        for signature, declared_selector in owner_selectors.items():
            expected_selector = "0x" + keccak256(signature.encode("ascii"))[:4].hex()
            if declared_selector != expected_selector:
                raise ValidationError(
                    f"{CORPUS_PATH}: {owner} {signature} selector must be "
                    f"{expected_selector}, got {declared_selector!r}"
                )
            previous = selector_owners.get(declared_selector)
            if previous is not None:
                raise ValidationError(
                    f"{CORPUS_PATH}: selector collision {declared_selector} between "
                    f"{previous[0]} {previous[1]} and {owner} {signature}"
                )
            selector_owners[declared_selector] = (owner, signature)


def validate_deployed_abi() -> None:
    corpus = load_json(CORPUS_PATH)
    manifest = corpus.get("deployed_abi")
    if not isinstance(manifest, dict) or set(manifest) != set(EXPECTED_ABI_FUNCTION_COUNTS):
        raise ValidationError(f"{CORPUS_PATH}: deployed ABI contract set is incomplete")

    canonical_manifest = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    actual_hash = "0x" + hashlib.sha256(canonical_manifest).hexdigest()
    declared_hash = corpus.get("deployed_abi_sha256")
    if actual_hash != EXPECTED_DEPLOYED_ABI_SHA256 or declared_hash != actual_hash:
        raise ValidationError(
            f"{CORPUS_PATH}: deployed ABI manifest hash must be "
            f"{EXPECTED_DEPLOYED_ABI_SHA256}, got {actual_hash} with declaration "
            f"{declared_hash!r}"
        )

    flat_selectors = corpus.get("selectors")
    if not isinstance(flat_selectors, dict):
        raise ValidationError(f"{CORPUS_PATH}: selectors must be an object")

    expected_names = set(EXPECTED_COLLABORATOR_SIGNATURES)
    selector_signatures: dict[str, str] = {}
    for contract, expected_count in EXPECTED_ABI_FUNCTION_COUNTS.items():
        functions = manifest[contract].get("functions")
        if not isinstance(functions, list) or len(functions) != expected_count:
            raise ValidationError(
                f"{CORPUS_PATH}: {contract} must contain {expected_count} ABI functions"
            )
        contract_signatures: set[str] = set()
        for index, entry in enumerate(functions):
            if not isinstance(entry, dict):
                raise ValidationError(
                    f"{CORPUS_PATH}: {contract} ABI function {index} must be an object"
                )
            signature = entry.get("signature")
            declared_selector = entry.get("selector")
            if not isinstance(signature, str) or "(" not in signature:
                raise ValidationError(
                    f"{CORPUS_PATH}: {contract} ABI function {index} has no signature"
                )
            if signature in contract_signatures:
                raise ValidationError(
                    f"{CORPUS_PATH}: {contract} repeats ABI signature {signature}"
                )
            contract_signatures.add(signature)
            expected_selector = "0x" + keccak256(signature.encode("ascii"))[:4].hex()
            if declared_selector != expected_selector:
                raise ValidationError(
                    f"{CORPUS_PATH}: {contract} {signature} selector must be "
                    f"{expected_selector}, got {declared_selector!r}"
                )
            name = signature.split("(", 1)[0]
            expected_names.add(name)
            if flat_selectors.get(name) != expected_selector:
                raise ValidationError(
                    f"{CORPUS_PATH}: flat selector for {name} disagrees with {contract}"
                )
            previous = selector_signatures.get(expected_selector)
            if previous is not None and previous != signature:
                raise ValidationError(
                    f"{CORPUS_PATH}: function-selector collision {expected_selector} "
                    f"between {previous} and {signature}"
                )
            selector_signatures[expected_selector] = signature

    for name, signature in EXPECTED_COLLABORATOR_SIGNATURES.items():
        expected_selector = "0x" + keccak256(signature.encode("ascii"))[:4].hex()
        if flat_selectors.get(name) != expected_selector:
            raise ValidationError(
                f"{CORPUS_PATH}: collaborator {signature} selector must be "
                f"{expected_selector}"
            )
    if set(flat_selectors) != expected_names:
        missing = sorted(expected_names - set(flat_selectors))
        extra = sorted(set(flat_selectors) - expected_names)
        raise ValidationError(
            f"{CORPUS_PATH}: flat selector set mismatch (missing {missing}; extra {extra})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate EEZ network profiles and the immutable proxy artifact."
    )
    parser.add_argument(
        "profiles",
        nargs="*",
        type=Path,
        help="Profile JSON paths. Defaults to Rollup0 and both Gnosis Chain host profiles.",
    )
    arguments = parser.parse_args()

    schema = load_json(SCHEMA_PATH)
    validator = SchemaValidator(schema)
    profiles = arguments.profiles or list(DEFAULT_PROFILES)

    failures: list[str] = []
    validated_profiles: list[tuple[Path, dict[str, Any]]] = []
    for profile_path in profiles:
        path = profile_path.resolve()
        try:
            profile = load_json(path)
            validator.validate(profile, schema)
            validate_profile_semantics(profile, path)
        except ValidationError as exc:
            failures.append(str(exc))
        else:
            validated_profiles.append((path, profile))
            print(f"OK profile schema and semantics: {path}")

    try:
        validate_profile_references(validated_profiles)
    except ValidationError as exc:
        failures.append(str(exc))
    else:
        print("OK cross-profile references")

    try:
        if keccak256(b"").hex() != (
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        ):
            raise ValidationError("internal Keccak-256 self-test failed")
        validate_proxy_artifact()
        validate_deployed_abi()
        validate_error_selectors()
    except ValidationError as exc:
        failures.append(str(exc))
    else:
        print(f"OK immutable binding artifacts and selectors: {ARTIFACT_PATH}")

    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
