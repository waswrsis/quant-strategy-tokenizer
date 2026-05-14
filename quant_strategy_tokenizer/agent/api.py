"""Agent-facing API wrappers."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.agent.fork import fork as _fork
from quant_strategy_tokenizer.agent.promote import PromoteResult
from quant_strategy_tokenizer.agent.promote import promote as _promote
from quant_strategy_tokenizer.agent.search import SearchResult
from quant_strategy_tokenizer.agent.search import search as _search
from quant_strategy_tokenizer.composition import expand_builtin_recipe, upgrade_verification
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as _explain_ir
from quant_strategy_tokenizer.detokenize.trace_explainer import explain_trace as _explain_trace
from quant_strategy_tokenizer.execution.fingerprint import compute_all_fingerprints
from quant_strategy_tokenizer.execution.kernel import KernelPlanReport, make_kernel_plan_report
from quant_strategy_tokenizer.execution.plan import make_execution_plan
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope, ProfileLiteral
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validate import ValidationResult
from quant_strategy_tokenizer.ir.validate import validate as _validate
from quant_strategy_tokenizer.mutation import (
    MutationResult,
    diff_strategies,
    mutate_strategy,
    parse_mutation_op,
)
from quant_strategy_tokenizer.package import (
    PackageBuildResult,
    UnpackedPackage,
)
from quant_strategy_tokenizer.package import (
    package_strategy as _package_strategy,
)
from quant_strategy_tokenizer.package import (
    unpack_package as _unpack_package,
)
from quant_strategy_tokenizer.package import (
    verify_package as _verify_package,
)
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.provenance.spec import TagSpec
from quant_strategy_tokenizer.qst_lock import (
    BuiltLock,
    LockFile,
    VerifyResult,
)
from quant_strategy_tokenizer.qst_lock import (
    build_lock as _build_lock,
)
from quant_strategy_tokenizer.qst_lock import (
    verify_lock as _verify_lock,
)
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.recipes.schema import RecipeSpec
from quant_strategy_tokenizer.runtime.executor import ExecutionResult, execute_strategy
from quant_strategy_tokenizer.runtime.trace import Trace
from quant_strategy_tokenizer.tokens.registry import get_registry


def vocabulary(layer: str | None = None) -> list[dict[str, Any]]:
    """Return serializable token specs."""

    registry = get_registry()
    specs = registry.list_tokens(layer=layer)  # type: ignore[arg-type]
    return [spec.model_dump(mode="json") for spec in specs]


def recipes(category: str | None = None) -> list[dict[str, Any]]:
    """Return serializable recipe specs."""

    registry = get_recipe_registry()
    return [spec.model_dump(mode="json") for spec in registry.list_recipes(category=category)]


def tagspec_get(semantic_id: str, version: int = 1) -> TagSpec | None:
    """Return a TagSpec by semantic id and version."""

    try:
        return get_tagspec_registry().get(semantic_id, version)
    except KeyError:
        return None


def tagspec_verify(semantic_id: str, version: int = 1, level: str = "attachment") -> TagSpec | None:
    """Return a TagSpec with attachment or full P2a-3 verification."""

    spec = tagspec_get(semantic_id, version)
    if spec is None:
        return None
    if level == "attachment":
        return spec
    if level == "full":
        return upgrade_verification(spec)
    raise ValueError(f"Unsupported TagSpec verification level: {level}")


def recipe_expand(semantic_id: str, params: dict[str, Any] | None = None, version: int = 1) -> RecipeSpec:
    """Expand a built-in P2a-2 recipe generator."""

    return expand_builtin_recipe(semantic_id, params or {}, version=version)


def diff(strategy_a: StrategyIR | dict[str, Any], strategy_b: StrategyIR | dict[str, Any]) -> dict[str, Any]:
    """Return a P2b-0 diff report for two strategies."""

    left = strategy_a if isinstance(strategy_a, StrategyIR) else StrategyIR.model_validate(strategy_a)
    right = strategy_b if isinstance(strategy_b, StrategyIR) else StrategyIR.model_validate(strategy_b)
    return diff_strategies(left, right).model_dump(mode="json")


def mutate(ir: StrategyIR | dict[str, Any], op: dict[str, Any]) -> MutationResult:
    """Apply one P2b mutation op."""

    parsed_ir = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    parsed_op = parse_mutation_op(op)
    return mutate_strategy(parsed_ir, parsed_op)


def fingerprint(ir: StrategyIR | dict[str, Any]) -> dict[str, Any]:
    """Return P2c-core Merkle fingerprints and execution-plan debug data."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    canonical = canonicalize(parsed)
    hashes = compute_hashes(canonical)
    fingerprints = compute_all_fingerprints(canonical.graph)
    plan = make_execution_plan(canonical)
    return {
        "hashes": hashes.as_dict(),
        "fingerprints": [
            {"node_id": node.id, "fingerprint": fingerprints[node.id]}
            for node in canonical.graph
        ],
        "plan": [node.model_dump(mode="json", exclude_none=True) for node in plan.nodes],
        "reuse_pairs": [
            {
                "node_id": node.node_id,
                "reused_from": node.reused_from,
                "fingerprint": node.fingerprint,
            }
            for node in plan.nodes
            if node.action == "reuse"
        ],
    }


def lock(ir: StrategyIR | dict[str, Any]) -> BuiltLock:
    """Build a P3a-0 deterministic qst.lock for a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _build_lock(parsed)


def verify(
    ir: StrategyIR | dict[str, Any],
    lock_file: LockFile | dict[str, Any],
    canonical_ir: StrategyIR | dict[str, Any] | None = None,
) -> VerifyResult:
    """Verify a Strategy IR against a P3a-0 qst.lock."""

    parsed_ir = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    parsed_lock = (
        lock_file
        if isinstance(lock_file, LockFile)
        else LockFile.model_validate(lock_file)
    )
    parsed_canonical = None
    if canonical_ir is not None:
        parsed_canonical = (
            canonical_ir
            if isinstance(canonical_ir, StrategyIR)
            else StrategyIR.model_validate(canonical_ir)
        )
    return _verify_lock(parsed_ir, parsed_lock, canonical_ir=parsed_canonical)


def package(
    strategy_path: str,
    output_dir: str,
    market_path: str | None = None,
    expected_trace_path: str | None = None,
) -> PackageBuildResult:
    """Build a P3a-1 qstpkg package."""

    return _package_strategy(
        strategy_path,
        output_dir,
        market_path=market_path,
        expected_trace_path=expected_trace_path,
    )


def unpack(package_dir: str, output_dir: str) -> UnpackedPackage:
    """Unpack a P3a-1 qstpkg package."""

    return _unpack_package(package_dir, output_dir)


def verify_package(package_dir: str) -> VerifyResult:
    """Verify a P3a-1 qstpkg package."""

    return _verify_package(package_dir)


def search(
    kind: str,
    *,
    domain: str | None = None,
    output_type: str | None = None,
    input_types: list[str] | None = None,
    state_tag: str | None = None,
    profile_allowed: str | None = None,
    uses_token: str | None = None,
    fully_verified_only: bool = False,
    lifecycle: list[str] | None = None,
    limit: int = 100,
) -> list[SearchResult]:
    """Search P3 IndexRecord metadata."""

    if kind not in {"token", "recipe", "tagspec"}:
        raise ValueError(f"Unsupported search kind: {kind}")
    return _search(
        kind,  # type: ignore[arg-type]
        domain=domain,
        output_type=output_type,
        input_types=input_types,
        state_tag=state_tag,
        profile_allowed=profile_allowed,
        uses_token=uses_token,
        fully_verified_only=fully_verified_only,
        lifecycle=lifecycle,
        limit=limit,
    )


def fork(
    parent: StrategyIR | str,
    new_id: str,
    parent_package: str | None = None,
    parent_package_version: str | None = None,
) -> StrategyIR:
    """Fork a strategy with P3b-1 derived_from lineage."""

    return _fork(
        parent,
        new_id,
        parent_package=parent_package,
        parent_package_version=parent_package_version,
    )


def validate(ir: StrategyIR | dict[str, Any], profile: ProfileLiteral = "research") -> ValidationResult:
    """Validate a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _validate(parsed, profile=profile)


def execute(
    ir: StrategyIR | dict[str, Any],
    externals: dict[str, Any],
    profile: ProfileLiteral = "research",
    kernel_substitution: bool = False,
) -> ExecutionResult:
    """Execute a Strategy IR against externals."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return execute_strategy(
        parsed,
        externals,
        profile=profile,
        kernel_substitution=kernel_substitution,
    )


def kernel_plan(ir: StrategyIR | dict[str, Any]) -> KernelPlanReport:
    """Return opt-in P2c-extended kernel substitution eligibility."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return make_kernel_plan_report(canonicalize(parsed))


def explain_ir(ir: StrategyIR | dict[str, Any], level: str = "L1") -> str:
    """Explain a Strategy IR."""

    parsed = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    return _explain_ir(parsed, level=level)


def explain_trace(trace: Trace | dict[str, Any], level: str = "human") -> str:
    """Explain an execution trace."""

    parsed = trace if isinstance(trace, Trace) else Trace.model_validate(trace)
    if level not in {"human", "agent", "raw"}:
        raise ValueError(f"Unsupported trace explain level: {level}")
    return _explain_trace(parsed, level=level)  # type: ignore[arg-type]


def promote(
    ir: StrategyIR | dict[str, Any],
    envelope: DeploymentEnvelope | dict[str, Any],
    target_profile: ProfileLiteral,
    approved_by: str | None = None,
) -> PromoteResult:
    """Promote a strategy envelope to a target profile."""

    parsed_ir = ir if isinstance(ir, StrategyIR) else StrategyIR.model_validate(ir)
    parsed_envelope = (
        envelope
        if isinstance(envelope, DeploymentEnvelope)
        else DeploymentEnvelope.model_validate(envelope)
    )
    return _promote(parsed_ir, parsed_envelope, target_profile, approved_by=approved_by)
