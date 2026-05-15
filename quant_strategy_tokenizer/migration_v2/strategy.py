"""Legacy qst-ir/0.3 and 0.3.1 to qst-ir/0.4 migration."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.decision_v2 import classify_legacy_decision_reduce
from quant_strategy_tokenizer.hash_v2 import (
    audit_chain_hash_v2,
    behavior_hash_v2,
    compute_hashes_v2,
    expected_artifact_hash_v2,
    implementation_ref_hash_v2,
    runtime_environment_hash_v2,
    signature_hash_v2,
    token_pack_hash_v2,
    token_spec_hash_v2,
)
from quant_strategy_tokenizer.ir.canonicalize import canonicalize as canonicalize_legacy
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import GraphNode, StrategyIR
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.ir_v04 import (
    CANONICAL_VERSION_V04,
    IR_VERSION_V04,
    MIGRATION_TOOL_VERSION_V04,
    MigrationLineageV04,
    NodeV04,
    StrategyBodyV04,
    StrategyIRV04,
    TokenRefV04,
    validate_ir_v04,
)
from quant_strategy_tokenizer.migration_v2.core_registry import target_core_registry_hash
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.ports_v2 import InputSpec, OutputSpec, PortSignature
from quant_strategy_tokenizer.tokens.registry import get_registry
from quant_strategy_tokenizer.types_v2 import parse_type_spec
from quant_strategy_tokenizer.validation_v2 import Diagnostic

MIGRATION_TOOL_VERSION = MIGRATION_TOOL_VERSION_V04


class MigrationResult(BaseModel):
    """Structured result for WP10 strategy migration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_hashes: dict[str, str]
    target_hashes: dict[str, str] | None = None
    target_core_registry_hash: str
    migration_tool_version: str = MIGRATION_TOOL_VERSION
    strategy: StrategyIRV04 | None = None
    diagnostics: list[Diagnostic] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ok(self) -> bool:
        return not any(diagnostic.severity == "error" for diagnostic in self.diagnostics)


def migrate_strategy_file(path: str | Path) -> MigrationResult:
    """Load and migrate a legacy strategy file."""

    return migrate_strategy(load_strategy_file(path))


def migrate_strategy(ir: StrategyIR | Mapping[str, Any]) -> MigrationResult:
    """Migrate a legacy strategy into the accepted qst-ir/0.4 shell."""

    legacy = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    source_hashes = compute_hashes(legacy)
    registry_hash = target_core_registry_hash()
    canonical = canonicalize_legacy(legacy)
    diagnostics: list[Diagnostic] = []

    nodes: list[NodeV04] = []
    for node in canonical.graph:
        migrated_node = _migrate_node(node, diagnostics)
        if migrated_node is not None:
            nodes.append(migrated_node)

    if any(diagnostic.severity == "error" for diagnostic in diagnostics):
        return MigrationResult(
            source_hashes=source_hashes.as_dict(),
            target_core_registry_hash=registry_hash,
            diagnostics=diagnostics,
        )

    migrated = StrategyIRV04(
        capabilities=["core"],
        strategy=StrategyBodyV04(
            id=canonical.strategy,
            version=canonical.strategy_version,
            nodes=nodes,
            outputs=canonical.outputs,
        ),
        metadata={
            "legacy_externals": {
                key: value.model_dump(mode="json")
                for key, value in sorted(canonical.externals.items())
            },
            "migration": {
                "migration_tool_version": MIGRATION_TOOL_VERSION,
                "target_core_registry_hash": registry_hash,
            },
        },
        derived_from=MigrationLineageV04(
            source_ir_version=legacy.ir_version,  # type: ignore[arg-type]
            source_instance_hash=source_hashes.instance_hash,
            source_strategy=legacy.strategy,
            source_strategy_version=legacy.strategy_version,
            target_core_registry_hash=registry_hash,
        ),
    )

    validation = validate_ir_v04(migrated)
    diagnostics.extend(validation.diagnostics)
    if any(diagnostic.severity == "error" for diagnostic in diagnostics):
        return MigrationResult(
            source_hashes=source_hashes.as_dict(),
            target_core_registry_hash=registry_hash,
            strategy=migrated,
            diagnostics=diagnostics,
        )

    target_hashes = compute_hashes_v2(migrated)
    return MigrationResult(
        source_hashes=source_hashes.as_dict(),
        target_hashes={
            "graph_hash": target_hashes.graph_hash,
            "param_hash": target_hashes.param_hash,
            "instance_hash": target_hashes.instance_hash,
        },
        target_core_registry_hash=registry_hash,
        strategy=migrated,
        diagnostics=diagnostics,
    )


def build_migration_lock_v04(result: MigrationResult) -> dict[str, Any]:
    """Build a minimal qst-lock/0.4 snapshot for a successful migration."""

    if result.strategy is None or result.target_hashes is None:
        raise ValueError("cannot build a v0.4 lock for an unsuccessful migration")
    migrated = result.strategy
    signature_material = [
        {
            "id": node.id,
            "token_ref": node.token_ref.model_dump(mode="json") if node.token_ref else None,
            "signature": node.signature.model_dump(mode="json", exclude_none=True),
        }
        for node in migrated.strategy.nodes
    ]
    behavior_material = [
        {
            "id": node.id,
            "token_ref": node.token_ref.model_dump(mode="json") if node.token_ref else None,
            "legacy_behavior_version": node.metadata.get("legacy_behavior_version"),
        }
        for node in migrated.strategy.nodes
    ]
    return {
        "lock_version": "qst-lock/0.4",
        "qst_version": __version__,
        "qst_version_policy": "strict",
        "ir_version": IR_VERSION_V04,
        "canonical_version": CANONICAL_VERSION_V04,
        "strategy": migrated.strategy.id,
        "strategy_version": migrated.strategy.version,
        "hashes": {
            **result.target_hashes,
            "signature_hash": signature_hash_v2(signature_material),
            "behavior_hash": behavior_hash_v2(behavior_material),
            "token_spec_hash": token_spec_hash_v2(signature_material),
            "token_pack_hash": token_pack_hash_v2(
                {"target_core_registry_hash": result.target_core_registry_hash}
            ),
            "implementation_ref_hash": implementation_ref_hash_v2(
                {"kind": "core_registry", "target_core_registry_hash": result.target_core_registry_hash}
            ),
            "audit_chain_hash": audit_chain_hash_v2([]),
            "runtime_environment_hash": runtime_environment_hash_v2(
                {"kind": "migration_tool", "version": MIGRATION_TOOL_VERSION}
            ),
            "expected_artifact_hash": expected_artifact_hash_v2(
                {
                    "kind": "migration_lock",
                    "source_instance_hash": migrated.derived_from.source_instance_hash
                    if migrated.derived_from
                    else None,
                    "target_instance_hash": result.target_hashes["instance_hash"],
                }
            ),
        },
        "legacy_source": {
            "source_ir_version": migrated.derived_from.source_ir_version if migrated.derived_from else None,
            "source_instance_hash": (
                migrated.derived_from.source_instance_hash if migrated.derived_from else None
            ),
            "target_core_registry_hash": result.target_core_registry_hash,
            "migration_lineage": [
                migrated.derived_from.model_dump(mode="json") if migrated.derived_from else {}
            ],
        },
        "tokens": [],
        "token_pack_dependencies": [],
    }


def _migrate_node(node: GraphNode, diagnostics: list[Diagnostic]) -> NodeV04 | None:
    registry = get_registry()
    try:
        legacy_spec = registry.get(node.token, node.v).spec
    except KeyError:
        diagnostics.append(
            _diagnostic(
                "QST_V2_MIGRATION_TOKEN_NOT_FOUND",
                f"Legacy token {node.token}/v{node.v} is not in the accepted registry.",
            )
        )
        return None

    target_token = legacy_spec.id
    target_version = legacy_spec.version
    target_behavior_version = legacy_spec.behavior_version
    metadata: dict[str, Any] = {
        "legacy_token": legacy_spec.id,
        "legacy_version": legacy_spec.version,
        "legacy_behavior_version": legacy_spec.behavior_version,
    }
    params = dict(node.params)

    if node.token == "decision.reduce":
        classification = classify_legacy_decision_reduce(
            policy=str(node.params.get("policy", "all_accept")),
            unknown_handling=str(node.params.get("unknown_handling", "treat_as_reject")),
            block_handling=str(node.params.get("block_handling", "forward")),
            abstain_handling=str(node.params.get("abstain_handling", "skip")),
            error_handling=str(node.params.get("error_handling", "keep_as_diagnostic")),
        )
        metadata["legacy_decision_reduce"] = classification.model_dump(mode="json")
        if not classification.result.ok or classification.target_id is None:
            diagnostics.extend(classification.result.diagnostics)
            return None
        target_token = classification.target_id
        target_version = 1
        target_behavior_version = 1
        params = {}

    if node.provenance:
        metadata["legacy_provenance"] = [to_plain(tag) for tag in node.provenance]

    return NodeV04(
        id=node.id,
        token=target_token,
        version=target_version,
        token_ref=TokenRefV04(
            namespace="core",
            name=target_token,
            version=target_version,
            behavior_version=target_behavior_version,
        ),
        inputs=node.inputs,
        params=params,
        signature=_legacy_signature_for(node.token, node.v),
        metadata=metadata,
    )


def _legacy_signature_for(token_id: str, version: int) -> PortSignature:
    spec = get_registry().get(token_id, version).spec
    return PortSignature(
        inputs={
            name: InputSpec(type=parse_type_spec(_legacy_type_to_v04(type_name)))
            for name, type_name in sorted(spec.inputs.items())
        },
        outputs={
            name: OutputSpec(type=parse_type_spec(_legacy_type_to_v04(type_name)))
            for name, type_name in sorted(spec.outputs.items())
        },
    )


def _legacy_type_to_v04(type_name: str) -> str:
    if type_name.endswith("[]"):
        return "EventStream[object]"
    if type_name in {"Decision", "Plan"}:
        return type_name
    if type_name == "State":
        return "State[object]"
    if type_name == "Number":
        return "Scalar[float]"
    if type_name == "Frame" or type_name.startswith("Frame["):
        return "Scalar[object]"
    return type_name


def _diagnostic(code: str, message: str, severity: str = "error") -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        phase="schema",
        message=message,
    )
