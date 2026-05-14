"""P2a-3 composition verification upgrader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from quant_strategy_tokenizer.composition.contract import contracts_pass
from quant_strategy_tokenizer.composition.fuzzing import check_fuzzing_meets_threshold
from quant_strategy_tokenizer.composition.metamorphic import metamorphic_pass
from quant_strategy_tokenizer.provenance.attachment import verify_tag_spec
from quant_strategy_tokenizer.provenance.spec import TagSpec, VerificationStatus
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.tokens.registry import get_registry

_UNSAFE_WINDOW_MODES = {"centered", "full_sample", "mixed", "unknown"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_path(path: str | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else _repo_root() / candidate


def _sample_param(schema: dict[str, Any]) -> Any:
    if "default" in schema:
        return schema["default"]
    if "oneOf" in schema:
        for option in schema["oneOf"]:
            if isinstance(option, dict):
                return _sample_param(option)
    kind = schema.get("type")
    if kind == "integer":
        return int(schema.get("minimum", 1))
    if kind == "number":
        return float(schema.get("minimum", 1.0))
    if kind == "string" and "enum" in schema:
        return schema["enum"][0]
    if kind == "string":
        return "sample"
    return None


def _sample_params(params_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _sample_param(schema)
        for key, schema in params_schema.items()
        if isinstance(schema, dict)
    }


def check_temporal_safety_compatibility(spec: TagSpec) -> bool:
    """Return whether a TagSpec source recipe is safe under P1-extended-a metadata."""

    compiled = compile_recipe(
        recipe_id=spec.source_recipe,
        recipe_version=spec.source_recipe_version,
        instance_params=_sample_params(spec.params_schema),
        instance_inputs={"series": pd.Series([1.0, 2.0, 3.0], dtype=float)},
        instance_id="temporal_check",
    )
    registry = get_registry()
    for node in compiled.nodes:
        token_spec = registry.get(node.token, node.version).spec
        temporal = token_spec.temporal
        if temporal.uses_future_data or temporal.window_mode in _UNSAFE_WINDOW_MODES:
            return False
    return True


def upgrade_verification(spec: TagSpec) -> TagSpec:
    """Run P2a-3 checks and return a TagSpec with full verification fields."""

    attached = verify_tag_spec(spec)
    contract_path = _resolve_repo_path(attached.contract_suite)
    fuzzing_path = _resolve_repo_path(attached.fuzzing_report)
    contracts_ok = contract_path is not None and contracts_pass(contract_path)
    fuzzing_ok = fuzzing_path is not None and check_fuzzing_meets_threshold(fuzzing_path, "ci_standard")
    metamorphic_ok = metamorphic_pass(attached.metamorphic_properties)
    temporal_ok = check_temporal_safety_compatibility(attached)
    verification = VerificationStatus(
        tag_attached_by_trusted=attached.verification.tag_attached_by_trusted,
        graph_template_hash_valid=attached.verification.graph_template_hash_valid,
        namespace_allowed=attached.verification.namespace_allowed,
        contracts_pass=contracts_ok and temporal_ok,
        fuzzing_at_ci_standard=fuzzing_ok,
        metamorphic_pass=metamorphic_ok,
    )
    return attached.model_copy(update={"verification": verification})
