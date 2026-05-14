"""Build deterministic P3a-0 qst.lock files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.composition import upgrade_verification
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.provenance.spec import TagSpec
from quant_strategy_tokenizer.provenance.verification_order import verification_state
from quant_strategy_tokenizer.qst_lock.canonical import (
    canonical_lock_bytes,
    hash_json_value,
    sha256_bytes,
)
from quant_strategy_tokenizer.qst_lock.schema import (
    ExternalsSnapshot,
    FixtureHashes,
    LockFile,
    RecipeDependency,
    StrategyHashSnapshot,
    TagSpecDependency,
    TokenDependency,
)
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry


@dataclass(frozen=True)
class BuiltLock:
    """Lock build output with the canonical IR bytes used for verification."""

    lock: LockFile
    canonical_ir: StrategyIR
    canonical_ir_bytes: bytes


def _file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compute_externals_schema_hash(ir: StrategyIR) -> str:
    """Compute the deterministic schema hash for Strategy IR externals."""

    payload = {
        name: spec.model_dump(mode="json")
        for name, spec in sorted(ir.externals.items())
    }
    return hash_json_value(payload)


def trace_semantic_hash(trace: dict[str, Any]) -> str:
    """Hash trace semantics without numeric runtime output values."""

    def scrub(value: Any) -> Any:
        if isinstance(value, bool) or value is None or isinstance(value, str):
            return value
        if isinstance(value, int | float):
            return "<number>"
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, dict):
            return {str(key): scrub(item) for key, item in sorted(value.items())}
        return str(type(value).__name__)

    payload = {
        "strategy_instance_hash": trace.get("strategy_instance_hash"),
        "ir_version": trace.get("ir_version"),
        "canonical_version": trace.get("canonical_version"),
        "nodes": [
            {
                "id": node.get("id"),
                "token": node.get("token"),
                "token_version": node.get("token_version"),
                "behavior_version": node.get("behavior_version"),
                "status": node.get("status"),
                "output_summary": scrub(node.get("output_summary", {})),
                "warnings": node.get("warnings", []),
                "unknown_reason": node.get("unknown_reason"),
                "error_kind": node.get("error_kind"),
                "cache_hit": node.get("cache_hit", False),
                "reused_from": node.get("reused_from"),
                "fingerprint": node.get("fingerprint"),
                "kernel_substituted": node.get("kernel_substituted", False),
                "kernel_id": node.get("kernel_id"),
                "semantic_id": node.get("semantic_id"),
            }
            for node in trace.get("nodes", [])
        ],
        "unknown_count": trace.get("unknown_count", 0),
        "error_count": trace.get("error_count", 0),
    }
    return hash_json_value(payload)


def _verification_upgraded(spec: TagSpec) -> TagSpec:
    try:
        return upgrade_verification(spec)
    except Exception:
        return spec


def _collect_token_dependencies(canonical_ir: StrategyIR) -> list[TokenDependency]:
    registry = get_registry()
    dependencies: dict[tuple[str, int], TokenDependency] = {}
    for node in canonical_ir.graph:
        registered = registry.get(node.token, node.v)
        dependencies[(node.token, node.v)] = TokenDependency(
            id=node.token,
            version=node.v,
            behavior_version=registered.spec.behavior_version,
        )
    return [dependencies[key] for key in sorted(dependencies)]


def _collect_recipe_dependencies(ir: StrategyIR) -> list[RecipeDependency]:
    registry = get_recipe_registry()
    dependencies: dict[tuple[str, int], RecipeDependency] = {}
    for recipe in ir.recipes:
        registry.get(recipe.recipe, recipe.version)
        dependencies[(recipe.recipe, recipe.version)] = RecipeDependency(
            recipe=recipe.recipe,
            version=recipe.version,
        )
    return [dependencies[key] for key in sorted(dependencies)]


def _collect_tagspec_dependencies(canonical_ir: StrategyIR) -> list[TagSpecDependency]:
    registry = get_tagspec_registry()
    dependencies: dict[tuple[str, int], TagSpecDependency] = {}
    for node in canonical_ir.graph:
        for tag in node.provenance:
            key = (tag.semantic_id, tag.version)
            if key in dependencies:
                continue
            spec = _verification_upgraded(registry.get(tag.semantic_id, tag.version))
            dependencies[key] = TagSpecDependency(
                semantic_id=spec.semantic_id,
                version=spec.version,
                graph_template_hash=spec.graph_template_hash,
                verification_state=verification_state(spec.verification),
                allowed_kernels=[
                    str(kernel["kernel_id"])
                    for kernel in spec.allowed_kernels
                    if "kernel_id" in kernel
                ],
            )
    return [dependencies[key] for key in sorted(dependencies)]


def _build_fixture_hashes(
    *,
    market_path: Path | None,
    expected_trace_path: Path | None,
) -> FixtureHashes:
    expected_trace_hash: str | None = None
    semantic_hash: str | None = None
    if expected_trace_path is not None:
        expected_trace_hash = _file_hash(expected_trace_path)
        raw_trace = json.loads(expected_trace_path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw_trace, dict):
            raise TypeError("expected trace fixture must contain a JSON object")
        semantic_hash = trace_semantic_hash(raw_trace)

    return FixtureHashes(
        market_csv_hash=_file_hash(market_path) if market_path is not None else None,
        expected_trace_hash=expected_trace_hash,
        trace_semantic_hash=semantic_hash,
    )


def build_lock(
    ir: StrategyIR,
    *,
    qst_version_policy: str = "strict",
    market_path: str | Path | None = None,
    expected_trace_path: str | Path | None = None,
) -> BuiltLock:
    """Build a deterministic qst.lock for a Strategy IR."""

    canonical_ir = canonicalize(ir)
    canonical_ir_bytes = canonical_lock_bytes(to_plain(canonical_ir))
    hashes = compute_hashes(canonical_ir)
    market = Path(market_path) if market_path is not None else None
    expected_trace = Path(expected_trace_path) if expected_trace_path is not None else None
    lock = LockFile(
        qst_version=__version__,
        qst_version_policy=qst_version_policy,  # type: ignore[arg-type]
        ir_version=canonical_ir.ir_version,
        canonical_version=canonical_ir.canonical_version,
        strategy=canonical_ir.strategy,
        strategy_version=canonical_ir.strategy_version,
        strategy_hashes=StrategyHashSnapshot(**hashes.as_dict()),
        canonical_ir_hash=sha256_bytes(canonical_ir_bytes),
        externals=ExternalsSnapshot(schema_hash=compute_externals_schema_hash(canonical_ir)),
        tokens=_collect_token_dependencies(canonical_ir),
        recipes=_collect_recipe_dependencies(ir),
        tagspecs=_collect_tagspec_dependencies(canonical_ir),
        fixtures=_build_fixture_hashes(market_path=market, expected_trace_path=expected_trace),
    )
    return BuiltLock(lock=lock, canonical_ir=canonical_ir, canonical_ir_bytes=canonical_ir_bytes)
