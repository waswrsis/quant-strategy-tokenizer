"""Typer CLI for QST P0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
import typer
import yaml

from quant_strategy_tokenizer.adapters import discover_adapters, get_adapter
from quant_strategy_tokenizer.agent.fork import fork as fork_strategy
from quant_strategy_tokenizer.agent.promote import promote as promote_strategy
from quant_strategy_tokenizer.agent.search import search as search_index
from quant_strategy_tokenizer.canonical_json import stable_json_bytes
from quant_strategy_tokenizer.composition import expand_builtin_recipe, upgrade_verification
from quant_strategy_tokenizer.core.output import jsonable_value
from quant_strategy_tokenizer.custom_runtime_v2 import (
    ApprovalRequest,
    ApprovalStore,
    TokenRuntimeContext,
    TokenRuntimeService,
    approval_record_hash,
    load_token_pack,
)
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as explain_text
from quant_strategy_tokenizer.detokenize.trace_explainer import explain_trace as explain_trace_text
from quant_strategy_tokenizer.execution.fingerprint import compute_all_fingerprints
from quant_strategy_tokenizer.execution.kernel import make_kernel_plan_report
from quant_strategy_tokenizer.execution.plan import make_execution_plan
from quant_strategy_tokenizer.frames import MarketFrame, compute_frame_hash
from quant_strategy_tokenizer.frames.io.csv_io import read_csv_frame
from quant_strategy_tokenizer.frames.io.json_io import Frame, read_json_frame, write_json_frame
from quant_strategy_tokenizer.frames.io.parquet_io import read_parquet_frame
from quant_strategy_tokenizer.ir.canonicalize import canonicalize as canonicalize_ir
from quant_strategy_tokenizer.ir.compare import compare_ir
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json, to_plain
from quant_strategy_tokenizer.ir.validate import validate as validate_ir
from quant_strategy_tokenizer.ir_v04 import TokenRefV04, canonical_bytes_v04
from quant_strategy_tokenizer.migration_v2 import (
    build_migration_lock_v04,
    migrate_strategy_file,
)
from quant_strategy_tokenizer.migration_v2 import (
    migrate_package as migrate_package_v2,
)
from quant_strategy_tokenizer.mutation import diff_strategies, mutate_strategy, parse_mutation_op
from quant_strategy_tokenizer.mutation.repair import mutation_from_repair_hint
from quant_strategy_tokenizer.package import (
    add_artifact_to_package,
    package_strategy,
    unpack_package,
    verify_package,
)
from quant_strategy_tokenizer.parse.yaml_loader import (
    load_strategy_file,
    load_strategy_file_with_envelope,
)
from quant_strategy_tokenizer.ports import (
    BacktestConfig,
    BacktestPort,
    ExecutionPort,
    ExperimentPort,
    ExperimentRunConfig,
    MarketDataPort,
    MarketLoadRequest,
    run_strategy_backtest,
)
from quant_strategy_tokenizer.provenance.registry import load_tagspec_file
from quant_strategy_tokenizer.qst_lock import build_lock, verify_lock
from quant_strategy_tokenizer.qst_lock.io import (
    read_canonical_ir,
    read_lock,
    write_canonical_ir,
    write_lock,
)
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from quant_strategy_tokenizer.runtime.trace import Trace
from quant_strategy_tokenizer.tokens._contract_runner import run_contract
from quant_strategy_tokenizer.tokens.registry import get_registry
from quant_strategy_tokenizer.types.plan import parse_plan

app = typer.Typer(no_args_is_help=True)
tag_app = typer.Typer(no_args_is_help=True)
recipe_app = typer.Typer(no_args_is_help=True)
kernel_app = typer.Typer(no_args_is_help=True)
pkg_app = typer.Typer(no_args_is_help=True)
load_app = typer.Typer(no_args_is_help=True)
adapter_app = typer.Typer(no_args_is_help=True)
token_app = typer.Typer(no_args_is_help=True)
token_approvals_app = typer.Typer(no_args_is_help=True)
app.add_typer(tag_app, name="tag")
app.add_typer(recipe_app, name="recipe")
app.add_typer(kernel_app, name="kernel")
app.add_typer(pkg_app, name="pkg")
app.add_typer(load_app, name="load")
app.add_typer(adapter_app, name="adapter")
app.add_typer(token_app, name="token")
token_app.add_typer(token_approvals_app, name="approvals")

P0_TOKEN_TRIPLES: tuple[tuple[str, int, int], ...] = (
    ("data.column", 1, 1),
    ("data.shift", 1, 1),
    ("window.max", 1, 1),
    ("window.min", 1, 1),
    ("smooth.linear_recursive", 1, 1),
    ("math.add", 1, 1),
    ("math.sub", 1, 1),
    ("math.mul", 1, 1),
    ("math.div", 1, 1),
    ("math.linear_combination", 1, 1),
    ("compare.gt", 1, 1),
    ("compare.le", 1, 1),
    ("logic.and", 1, 1),
    ("norm.range_position", 1, 1),
    ("decision.lift_bool", 1, 1),
    ("decision.reduce", 1, 1),
    ("plan.noop", 1, 1),
)
P0_RECIPE_PAIRS: tuple[tuple[str, int], ...] = (
    ("indicator.ewm", 1),
    ("indicator.rma", 1),
    ("indicator.kdj", 1),
    ("event.cross_above", 1),
)
PROFILE_VALUES = {"research", "paper", "pretrade", "production_guarded"}


def _echo_json(value: Any) -> None:
    typer.echo(json.dumps(jsonable_value(value), ensure_ascii=False, indent=2, default=str))


def _write_canonical_json(path: Path, value: Any) -> None:
    path.write_bytes(stable_json_bytes(jsonable_value(value)))


def _parse_token_ref(value: str) -> TokenRefV04:
    try:
        token_part, version_part, behavior_part = value.split("/")
        namespace, name = token_part.split(".", 1)
        version = int(version_part.removeprefix("v"))
        behavior_version = int(behavior_part.removeprefix("bv"))
    except Exception as exc:
        raise typer.BadParameter(
            "token ref must be formatted as namespace.name/v1/bv1"
        ) from exc
    return TokenRefV04(
        namespace=namespace,
        name=name,
        version=version,
        behavior_version=behavior_version,
    )


def _approval_store_path(path: Path | None) -> Path:
    return path or Path(".qst") / "approvals.json"


def _load_approval_store(path: Path | None) -> tuple[Path, ApprovalStore]:
    resolved = _approval_store_path(path)
    return resolved, ApprovalStore.load(resolved)


def _load_inputs(inputs_json: str | None, inputs_file: Path | None) -> dict[str, Any]:
    if inputs_file is not None:
        raw = json.loads(inputs_file.read_text(encoding="utf-8-sig"))
    elif inputs_json is not None:
        raw = json.loads(inputs_json)
    else:
        raw = {}
    if not isinstance(raw, dict):
        raise typer.BadParameter("custom token inputs must be a JSON object")
    return raw


def _write_v04_strategy_yaml(path: Path, value: Any) -> None:
    path.write_text(
        yaml.safe_dump(
            value.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


@app.command("migrate-ir")
def migrate_ir_cmd(
    strategy: Path,
    to: Annotated[str, typer.Option("--to")] = "qst-ir/0.4",
    output: Annotated[Path | None, typer.Option("--output")] = None,
    canonical_output: Annotated[Path | None, typer.Option("--canonical-output")] = None,
    lock_output: Annotated[Path | None, typer.Option("--lock-output")] = None,
    report_output: Annotated[Path | None, typer.Option("--report-output")] = None,
) -> None:
    """Migrate a legacy qst-ir/0.3 or 0.3.1 strategy to qst-ir/0.4."""

    if to != "qst-ir/0.4":
        raise typer.BadParameter("WP10 only supports --to qst-ir/0.4")
    result = migrate_strategy_file(strategy)
    if report_output is not None:
        _write_canonical_json(report_output, result.model_dump(mode="json"))
    if not result.ok or result.strategy is None:
        _echo_json(result.model_dump(mode="json"))
        raise typer.Exit(1)

    if output is not None:
        _write_v04_strategy_yaml(output, result.strategy)
    if canonical_output is not None:
        canonical_output.write_bytes(canonical_bytes_v04(result.strategy))
    if lock_output is not None:
        _write_canonical_json(lock_output, build_migration_lock_v04(result))

    _echo_json(
        {
            "ok": True,
            "output": str(output) if output is not None else None,
            "canonical_output": str(canonical_output) if canonical_output is not None else None,
            "lock_output": str(lock_output) if lock_output is not None else None,
            "source_instance_hash": result.source_hashes["instance_hash"],
            "target_instance_hash": result.target_hashes["instance_hash"] if result.target_hashes else None,
            "target_core_registry_hash": result.target_core_registry_hash,
            "migration_tool_version": result.migration_tool_version,
            "diagnostics": [diagnostic.model_dump(mode="json") for diagnostic in result.diagnostics],
        }
    )


@app.command("migrate-package")
def migrate_package_cmd(
    package_dir: Path,
    to: Annotated[str, typer.Option("--to")] = "qst-ir/0.4",
    output: Annotated[Path, typer.Option("--output")] = Path("migrated.qstpkg"),
) -> None:
    """Migrate a legacy qstpkg directory to a qst-ir/0.4 package snapshot."""

    if to != "qst-ir/0.4":
        raise typer.BadParameter("WP10 only supports --to qst-ir/0.4")
    result = migrate_package_v2(package_dir, output)
    payload = {
        "ok": result.migration.ok,
        "output": str(result.package_dir),
        "source_instance_hash": result.migration.source_hashes.get("instance_hash"),
        "target_instance_hash": (
            result.migration.target_hashes.get("instance_hash")
            if result.migration.target_hashes is not None
            else None
        ),
        "target_core_registry_hash": result.migration.target_core_registry_hash,
        "migration_tool_version": result.migration.migration_tool_version,
        "diagnostics": [
            diagnostic.model_dump(mode="json") for diagnostic in result.migration.diagnostics
        ],
    }
    _echo_json(payload)
    if not result.migration.ok:
        raise typer.Exit(1)


def _ensure_market_frame(frame: Frame) -> MarketFrame:
    if not isinstance(frame, MarketFrame):
        raise TypeError(f"Expected qst-market-frame/1, got {frame.frame_version!r}")
    return frame


def _market_with_hash(frame: MarketFrame) -> MarketFrame:
    return frame.model_copy(update={"frame_hash": compute_frame_hash(frame)})


def _read_market_frame(path: Path) -> MarketFrame:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _ensure_market_frame(read_json_frame(path))
    if suffix == ".csv":
        return _ensure_market_frame(read_csv_frame(path, "qst-market-frame/1"))
    if suffix in {".parquet", ".pq"}:
        return _ensure_market_frame(read_parquet_frame(path, "qst-market-frame/1"))
    raise ValueError(f"Unsupported market frame file suffix: {path.suffix!r}")


def _market_adapter_id(source: Path, adapter: str) -> str:
    if adapter != "auto":
        return adapter
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return "mock-csv-market"
    if suffix in {".parquet", ".pq"}:
        return "mock-parquet-market"
    raise ValueError("auto market adapter supports only .csv, .parquet, or .pq sources")


def _load_market_adapter(adapter_id: str) -> MarketDataPort:
    adapter = get_adapter(adapter_id)
    if not isinstance(adapter, MarketDataPort):
        raise TypeError(f"Adapter {adapter_id!r} does not implement MarketDataPort")
    return adapter


def _load_backtest_adapter(adapter_id: str) -> BacktestPort:
    resolved = "mock-backtest" if adapter_id == "mock" else adapter_id
    adapter = get_adapter(resolved)
    if not isinstance(adapter, BacktestPort):
        raise TypeError(f"Adapter {resolved!r} does not implement BacktestPort")
    return adapter


def _load_execution_adapter(adapter_id: str) -> ExecutionPort:
    adapter = get_adapter(adapter_id)
    if not isinstance(adapter, ExecutionPort):
        raise TypeError(f"Adapter {adapter_id!r} does not implement ExecutionPort")
    return adapter


def _load_experiment_adapter(adapter_id: str) -> ExperimentPort:
    adapter = get_adapter(adapter_id)
    if not isinstance(adapter, ExperimentPort):
        raise TypeError(f"Adapter {adapter_id!r} does not implement ExperimentPort")
    return adapter


def _parse_tags(items: list[str] | None) -> dict[str, str]:
    tags: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Tag {item!r} must use key=value format")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError("Tag key cannot be empty")
        tags[key] = value
    return tags


def _effective_profile(override: str | None, envelope_profile: ProfileLiteral) -> ProfileLiteral:
    raw_profile = override or envelope_profile
    if raw_profile not in PROFILE_VALUES:
        typer.echo(f"unsupported profile: {raw_profile}", err=True)
        raise typer.Exit(2)
    return cast(ProfileLiteral, raw_profile)


def _compile_smoke_recipe(recipe_id: str) -> None:
    smoke: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        "indicator.ewm": ({"span": 3}, {"series": "$externals.series"}),
        "indicator.rma": ({"alpha": 0.5}, {"series": "$externals.series"}),
        "indicator.kdj": (
            {"lookback": 9, "k_alpha": 0.3333333, "d_alpha": 0.3333333, "init": 50},
            {
                "high": "$externals.market.high",
                "low": "$externals.market.low",
                "close": "$externals.market.close",
            },
        ),
        "event.cross_above": (
            {},
            {"fast": "$externals.fast", "slow": "$externals.slow"},
        ),
        "event.threshold_above": (
            {},
            {"series": "$externals.series", "threshold": "$externals.threshold"},
        ),
        "event.threshold_below": (
            {},
            {"series": "$externals.series", "threshold": "$externals.threshold"},
        ),
        "gate.elapsed_threshold": (
            {"field": "elapsed", "threshold": 10, "default": 0},
            {"state": "$externals.state"},
        ),
        "gate.cooldown": (
            {"field": "cooldown_elapsed", "threshold": 10, "default": 0},
            {"state": "$externals.state"},
        ),
        "signals.dual_ema_cross": (
            {"fast_span": 9, "slow_span": 21, "init": "first_value"},
            {"series": "$externals.series"},
        ),
    }
    params, inputs = smoke[recipe_id]
    compile_recipe(
        recipe_id=recipe_id,
        recipe_version=1,
        instance_params=params,
        instance_inputs=inputs,
        instance_id=recipe_id.replace(".", "_"),
        registry=get_registry(),
        recipe_registry=get_recipe_registry(),
    )


@app.command("vocabulary")
def vocabulary(check: bool = False, markdown: bool = False) -> None:
    """List or check built-in token and recipe vocabulary."""

    token_registry = get_registry()
    recipe_registry = get_recipe_registry()
    tokens = token_registry.list_tokens()
    recipes = recipe_registry.list_recipes()

    if check:
        if len(tokens) != 25:
            typer.echo(f"expected 25 tokens, got {len(tokens)}", err=True)
            raise typer.Exit(1)
        if len(recipes) != 9:
            typer.echo(f"expected 9 recipes, got {len(recipes)}", err=True)
            raise typer.Exit(1)
        for token_id, version, behavior_version in P0_TOKEN_TRIPLES:
            spec = token_registry.get(token_id, version).spec
            if spec.behavior_version != behavior_version:
                typer.echo(
                    f"P0 token drift: {token_id}/v{version} expected bv{behavior_version}, "
                    f"got bv{spec.behavior_version}",
                    err=True,
                )
                raise typer.Exit(1)
        for recipe_id, version in P0_RECIPE_PAIRS:
            recipe_registry.get(recipe_id, version)
        for spec in tokens:
            for contract in spec.behavior_contract:
                result = run_contract(token_registry.get(spec.id, spec.version), contract)
                if not result.passed:
                    typer.echo(f"{spec.id}:{result.name}: {result.error}", err=True)
                    raise typer.Exit(1)
        for recipe in recipes:
            _compile_smoke_recipe(recipe.recipe)
        typer.echo("P0 frozen baseline:")
        typer.echo("  tokens: 17")
        typer.echo("  recipes: 4")
        typer.echo("  status: preserved")
        typer.echo("Current vocabulary:")
        typer.echo("  tokens: 25")
        typer.echo("  recipes: 9")
        typer.echo("25 tokens registered, all behavior_contracts pass")
        typer.echo("9 recipes registered, all compile")
        return

    if markdown:
        typer.echo("| kind | id | version |")
        typer.echo("|---|---|---|")
        for spec in tokens:
            typer.echo(f"| token | {spec.id} | {spec.version} |")
        for recipe in recipes:
            typer.echo(f"| recipe | {recipe.recipe} | {recipe.version} |")
        return

    _echo_json(
        {
            "tokens": [spec.model_dump(mode="json") for spec in tokens],
            "recipes": [recipe.model_dump(mode="json") for recipe in recipes],
        }
    )


@app.command("validate")
def validate_cmd(
    path: Path,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
) -> None:
    """Validate a strategy YAML file."""

    ir, envelope = load_strategy_file_with_envelope(path)
    result = validate_ir(ir, profile=_effective_profile(profile, envelope.profile))
    if result.ok:
        typer.echo("valid")
        for warning in result.warnings:
            typer.echo(
                json.dumps(warning.model_dump(exclude_none=True), ensure_ascii=False),
                err=True,
            )
        return
    typer.echo("INVALID", err=True)
    for failure in result.failures:
        typer.echo(json.dumps(failure.model_dump(exclude_none=True), ensure_ascii=False), err=True)
    raise typer.Exit(1)


@app.command("canonicalize")
def canonicalize_cmd(path: Path) -> None:
    """Print canonical IR JSON."""

    typer.echo(to_json(canonicalize_ir(load_strategy_file(path))))


@app.command("hash")
def hash_cmd(path: Path) -> None:
    """Print P0 graph, param, and instance hashes."""

    hashes = compute_hashes(load_strategy_file(path))
    typer.echo(f"graph_hash:    {hashes.graph_hash}")
    typer.echo(f"param_hash:    {hashes.param_hash}")
    typer.echo(f"instance_hash: {hashes.instance_hash}")


@app.command("lock")
def lock_cmd(
    path: Path,
    output: Annotated[Path, typer.Option("--output")] = Path("qst.lock"),
    canonical_output: Annotated[Path | None, typer.Option("--canonical-output")] = None,
    market: Annotated[Path | None, typer.Option("--market")] = None,
    expected_trace: Annotated[Path | None, typer.Option("--expected-trace")] = None,
) -> None:
    """Build a deterministic P3a-0 qst.lock for a strategy."""

    built = build_lock(
        load_strategy_file(path),
        market_path=market,
        expected_trace_path=expected_trace,
    )
    write_lock(built.lock, output)
    if canonical_output is not None:
        write_canonical_ir(built.canonical_ir, canonical_output)
    _echo_json(
        {
            "ok": True,
            "lock": str(output),
            "canonical": str(canonical_output) if canonical_output is not None else None,
            "strategy_hashes": built.lock.strategy_hashes.model_dump(mode="json"),
            "canonical_ir_hash": built.lock.canonical_ir_hash,
            "verification_level": "STRUCTURAL",
        }
    )


@app.command("package")
def package_cmd(
    path: Path,
    output: Annotated[Path, typer.Option("--output")],
    market: Annotated[Path | None, typer.Option("--market")] = None,
    expected_trace: Annotated[Path | None, typer.Option("--expected-trace")] = None,
) -> None:
    """Build a P3a-1 directory-based .qstpkg package."""

    try:
        result = package_strategy(
            path,
            output,
            market_path=market,
            expected_trace_path=expected_trace,
        )
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json(
        {
            "ok": True,
            "package": str(result.package_dir),
            "package_version": result.manifest.package_version,
            "strategy": result.manifest.strategy.model_dump(mode="json"),
            "files": len(result.manifest.files),
            "verification_level": (
                "SEMANTIC_TRACE"
                if result.fixtures_manifest.expected_trace_path is not None
                else "STRUCTURAL"
            ),
        }
    )


@app.command("unpack")
def unpack_cmd(pkg_dir: Path, output: Annotated[Path, typer.Option("--output")]) -> None:
    """Unpack a P3a-1 .qstpkg directory to another directory."""

    try:
        unpacked = unpack_package(pkg_dir, output)
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json(
        {
            "ok": True,
            "package": str(pkg_dir),
            "output": str(output),
            "package_version": unpacked.manifest.package_version,
            "strategy": unpacked.manifest.strategy.model_dump(mode="json"),
            "files": len(unpacked.manifest.files),
        }
    )


@pkg_app.command("add-artifact")
def pkg_add_artifact_cmd(
    pkg_dir: Path,
    artifact_json: Path,
    dest: Annotated[str | None, typer.Option("--dest")] = None,
) -> None:
    """Add one P4 artifact JSON file to a qstpkg directory."""

    try:
        result = add_artifact_to_package(pkg_dir, artifact_json, dest_path=dest)
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json(
        {
            "ok": True,
            "package": str(result.package_dir),
            "artifact_path": result.artifact_path,
            "artifact_version": result.artifact_version,
            "files": len(result.manifest.files),
        }
    )


@pkg_app.command("verify-artifacts")
def pkg_verify_artifacts_cmd(pkg_dir: Path) -> None:
    """Verify qstpkg contents including optional P4 artifacts."""

    result = verify_package(pkg_dir)
    _echo_json(result.model_dump(mode="json", exclude_none=True))
    if not result.ok:
        raise typer.Exit(1)


@token_app.command("verify")
def token_verify_cmd(
    token_ref: str,
    pack: Annotated[Path, typer.Option("--pack")],
    profile: Annotated[str, typer.Option("--profile")] = "research",
    allow_token: Annotated[bool, typer.Option("--allow-token")] = False,
    ack_risk: Annotated[bool, typer.Option("--ack-risk")] = False,
    approvals: Annotated[Path | None, typer.Option("--approvals")] = None,
) -> None:
    """Verify custom token integrity and authorization without executing code."""

    ref = _parse_token_ref(token_ref)
    service = TokenRuntimeService()
    pack_manifest = load_token_pack(pack)
    _, store = _load_approval_store(approvals)
    integrity = service.verify_integrity(
        pack_manifest,
        ref,
        context=TokenRuntimeContext(base_path=pack.parent if pack.is_file() else pack),
    )
    authorization = service.check_authorization(
        integrity,
        profile=profile,  # type: ignore[arg-type]
        approval_store=store,
        allow_token=allow_token,
        ack_risk=ack_risk,
    )
    payload = {"ok": integrity.ok and authorization.ok, "integrity": integrity, "authorization": authorization}
    _echo_json(payload)
    if not integrity.ok or authorization.status == "denied_by_profile":
        raise typer.Exit(1)


@token_app.command("approve")
def token_approve_cmd(
    token_ref: str,
    pack: Annotated[Path, typer.Option("--pack")],
    profile: Annotated[str, typer.Option("--profile")],
    approved_by: Annotated[str, typer.Option("--approved-by")],
    allow_token: Annotated[bool, typer.Option("--allow-token")] = False,
    ack_risk: Annotated[bool, typer.Option("--ack-risk")] = False,
    scope: Annotated[str, typer.Option("--scope")] = "project",
    approvals: Annotated[Path | None, typer.Option("--approvals")] = None,
) -> None:
    """Write a local custom token approval record without executing code."""

    ref = _parse_token_ref(token_ref)
    service = TokenRuntimeService()
    pack_manifest = load_token_pack(pack)
    store_path, store = _load_approval_store(approvals)
    integrity = service.verify_integrity(
        pack_manifest,
        ref,
        context=TokenRuntimeContext(base_path=pack.parent if pack.is_file() else pack),
    )
    if not integrity.ok:
        _echo_json({"ok": False, "integrity": integrity})
        raise typer.Exit(1)
    request = ApprovalRequest(
        token_ref=ref,
        profile=profile,  # type: ignore[arg-type]
        scope=scope,  # type: ignore[arg-type]
        approved_by=approved_by,
        allow_token=allow_token,
        ack_risk=ack_risk,
        approved_risk_level=integrity.risk_level,
        token_spec_hash=integrity.token_spec_hash,
        token_pack_hash=integrity.token_pack_hash,
        implementation_ref_hash=integrity.implementation_ref_hash,
        runtime_environment_hash=integrity.runtime_environment_hash,
    )
    try:
        record, updated = service.approve_token_pack(request, approval_store=store)
    except ValueError as exc:
        _echo_json({"ok": False, "error": str(exc)})
        raise typer.Exit(1) from None
    updated.save(store_path)
    _echo_json(
        {
            "ok": True,
            "approval_record": record,
            "approval_record_hash": approval_record_hash(record),
            "approvals": str(store_path),
        }
    )


@token_approvals_app.command("list")
def token_approvals_list_cmd(
    approvals: Annotated[Path | None, typer.Option("--approvals")] = None,
) -> None:
    """List local custom token approvals."""

    store_path, store = _load_approval_store(approvals)
    _echo_json(
        {
            "ok": True,
            "approvals": str(store_path),
            "records": [
                {
                    **record.model_dump(mode="json"),
                    "approval_record_hash": approval_record_hash(record),
                }
                for record in store.records
            ],
        }
    )


@token_approvals_app.command("revoke")
def token_approvals_revoke_cmd(
    token_ref: str,
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    approvals: Annotated[Path | None, typer.Option("--approvals")] = None,
) -> None:
    """Revoke local custom token approvals for a token."""

    ref = _parse_token_ref(token_ref)
    store_path, store = _load_approval_store(approvals)
    updated = store.revoke(ref, profile=profile)  # type: ignore[arg-type]
    updated.save(store_path)
    _echo_json({"ok": True, "approvals": str(store_path), "records": len(updated.records)})


@token_app.command("execute")
def token_execute_cmd(
    token_ref: str,
    pack: Annotated[Path, typer.Option("--pack")],
    profile: Annotated[str, typer.Option("--profile")] = "research",
    inputs_json: Annotated[str | None, typer.Option("--inputs-json")] = None,
    inputs_file: Annotated[Path | None, typer.Option("--inputs-file")] = None,
    approvals: Annotated[Path | None, typer.Option("--approvals")] = None,
    run_id: Annotated[str, typer.Option("--run-id")] = "manual",
    current_time_utc: Annotated[str | None, typer.Option("--current-time-utc")] = None,
) -> None:
    """Execute an approved custom token python_entrypoint."""

    if current_time_utc is None:
        _echo_json({"ok": False, "error": "qst token execute requires --current-time-utc"})
        raise typer.Exit(1)
    ref = _parse_token_ref(token_ref)
    service = TokenRuntimeService()
    pack_manifest = load_token_pack(pack)
    _, store = _load_approval_store(approvals)
    context = TokenRuntimeContext(
        base_path=pack.parent if pack.is_file() else pack,
        profile=profile,  # type: ignore[arg-type]
        run_id=run_id,
        current_time_utc=current_time_utc,
    )
    integrity = service.verify_integrity(pack_manifest, ref, context=context)
    authorization = service.check_authorization(
        integrity,
        profile=profile,  # type: ignore[arg-type]
        approval_store=store,
    )
    try:
        grant = service.issue_execution_grant(
            integrity,
            authorization,
            run_id=run_id,
            issued_at_utc=current_time_utc,
        )
    except ValueError as exc:
        _echo_json({"ok": False, "integrity": integrity, "authorization": authorization, "error": str(exc)})
        raise typer.Exit(1) from None
    result = service.execute_custom_token(
        pack_manifest,
        ref,
        inputs=_load_inputs(inputs_json, inputs_file),
        grant=grant,
        context=context,
        approval_store=store,
    )
    _echo_json(result.model_dump(mode="json", exclude_none=True))
    if not result.ok:
        raise typer.Exit(1)


@app.command("verify")
def verify_cmd(
    path: Path,
    lock_path: Annotated[Path | None, typer.Option("--lock")] = None,
    canonical_path: Annotated[Path | None, typer.Option("--canonical")] = None,
    market: Annotated[Path | None, typer.Option("--market")] = None,
    expected_trace: Annotated[Path | None, typer.Option("--expected-trace")] = None,
) -> None:
    """Verify a strategy+lock pair or a P3a-1 .qstpkg directory."""

    if path.is_dir() and (path / "qst.lock").exists():
        result = verify_package(path)
    elif lock_path is not None:
        result = verify_lock(
            load_strategy_file(path),
            read_lock(lock_path),
            canonical_ir=read_canonical_ir(canonical_path) if canonical_path is not None else None,
            market_path=market,
            expected_trace_path=expected_trace,
        )
    else:
        _echo_json({"ok": False, "error": "provide a .qstpkg directory or --lock"})
        raise typer.Exit(2)
    _echo_json(result.model_dump(mode="json", exclude_none=True))
    if not result.ok:
        raise typer.Exit(1)


@load_app.command("market")
def load_market_cmd(
    source: Annotated[Path, typer.Option("--source")],
    output: Annotated[Path, typer.Option("--output")],
    symbols: Annotated[list[str] | None, typer.Option("--symbols")] = None,
    adapter: Annotated[str, typer.Option("--adapter")] = "auto",
) -> None:
    """Load a P4 MarketFrame through a local market adapter."""

    try:
        adapter_id = _market_adapter_id(source, adapter)
        market_adapter = _load_market_adapter(adapter_id)
        frame = _market_with_hash(
            market_adapter.load_market(
                MarketLoadRequest(source=str(source), symbols=symbols or [])
            )
        )
        write_json_frame(frame, output)
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json(
        {
            "ok": True,
            "adapter": adapter_id,
            "output": str(output),
            "frame_version": frame.frame_version,
            "frame_hash": frame.frame_hash,
            "symbols": frame.symbols,
            "bars": len(frame.bars),
        }
    )


@app.command("backtest")
def backtest_cmd(
    strategy: Path,
    adapter: Annotated[str, typer.Option("--adapter")] = "mock",
    market: Annotated[Path, typer.Option("--market")] = Path("market.json"),
    output: Annotated[Path, typer.Option("--output")] = Path("result.qstpkg"),
) -> None:
    """Run a strategy through signal extraction and a mock backtest adapter."""

    try:
        ir = load_strategy_file(strategy)
        market_frame = _read_market_frame(market)
        hashes = compute_hashes(ir)
        evidence = run_strategy_backtest(
            ir,
            market_frame,
            BacktestConfig(metadata={"strategy_instance_hash": hashes.instance_hash}),
            adapter=_load_backtest_adapter(adapter),
        )
        package_strategy(strategy, output)
        with tempfile.TemporaryDirectory() as tmp_dir:
            evidence_path = Path(tmp_dir) / "backtest_evidence.json"
            _write_canonical_json(evidence_path, evidence.model_dump(mode="json"))
            add_artifact_to_package(output, evidence_path)
        verification = verify_package(output)
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json(
        {
            "ok": True,
            "adapter": "mock-backtest" if adapter == "mock" else adapter,
            "package": str(output),
            "backtest_artifact_id": evidence.artifact_id,
            "strategy_instance_hash": hashes.instance_hash,
            "verification_ok": verification.ok,
        }
    )


@app.command("submit-plan")
def submit_plan_cmd(
    plan_json: Path,
    adapter: Annotated[str, typer.Option("--adapter")] = "mock-execution",
    confirm: Annotated[bool, typer.Option("--confirm")] = False,
    client_order_id: Annotated[str | None, typer.Option("--client-order-id")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Submit a venue-neutral plan through a local execution adapter."""

    try:
        plan = parse_plan(_load_json_path(plan_json))
        report = _load_execution_adapter(adapter).submit_plan(
            plan,
            confirm=confirm,
            client_order_id=client_order_id,
        )
        if output is not None:
            _write_canonical_json(output, report.model_dump(mode="json"))
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    payload = {"ok": True, "adapter": adapter, "report": report.model_dump(mode="json")}
    if output is not None:
        payload["output"] = str(output)
    _echo_json(payload)


@app.command("poll-execution")
def poll_execution_cmd(
    execution_report_id: str,
    adapter: Annotated[str, typer.Option("--adapter")] = "mock-execution",
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Poll a mock execution report by id."""

    try:
        report = _load_execution_adapter(adapter).poll_report(execution_report_id)
        if output is not None:
            _write_canonical_json(output, report.model_dump(mode="json"))
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    payload = {"ok": True, "adapter": adapter, "report": report.model_dump(mode="json")}
    if output is not None:
        payload["output"] = str(output)
    _echo_json(payload)


@app.command("track")
def track_cmd(
    pkg_dir: Path,
    adapter: Annotated[str, typer.Option("--adapter")] = "mock-experiment",
    run_name: Annotated[str, typer.Option("--run-name")] = "run",
    tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
) -> None:
    """Track a qstpkg through a local experiment adapter."""

    try:
        ref = _load_experiment_adapter(adapter).track_package(
            pkg_dir,
            ExperimentRunConfig(run_name=run_name, tags=_parse_tags(tag)),
        )
    except Exception as exc:
        _echo_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    _echo_json({"ok": True, "adapter": adapter, "artifact_ref": ref.model_dump(mode="json")})


@adapter_app.command("list")
def adapter_list_cmd() -> None:
    """List locally discoverable QST adapters."""

    _echo_json([descriptor.model_dump(mode="json") for descriptor in discover_adapters()])


@adapter_app.command("verify")
def adapter_verify_cmd(adapter_id: str) -> None:
    """Load one adapter and report implemented P4 port protocols."""

    try:
        adapter = get_adapter(adapter_id)
        identity = adapter.get_identity()
    except Exception as exc:
        _echo_json({"ok": False, "adapter_id": adapter_id, "error": f"{type(exc).__name__}: {exc}"})
        raise typer.Exit(1) from None
    capabilities = {
        "market_data": isinstance(adapter, MarketDataPort),
        "backtest": isinstance(adapter, BacktestPort),
        "execution": isinstance(adapter, ExecutionPort),
        "experiment": isinstance(adapter, ExperimentPort),
    }
    _echo_json(
        {
            "ok": any(capabilities.values()),
            "adapter_id": adapter_id,
            "identity": identity.model_dump(mode="json"),
            "capabilities": capabilities,
        }
    )


@app.command("search")
def search_cmd(
    kind: str,
    domain: Annotated[str | None, typer.Option("--domain")] = None,
    output_type: Annotated[str | None, typer.Option("--output-type")] = None,
    input_type: Annotated[list[str] | None, typer.Option("--input-type")] = None,
    state_tag: Annotated[str | None, typer.Option("--state-tag")] = None,
    profile_allowed: Annotated[str | None, typer.Option("--profile-allowed")] = None,
    uses_token: Annotated[str | None, typer.Option("--uses-token")] = None,
    fully_verified: Annotated[bool, typer.Option("--fully-verified")] = False,
    lifecycle: Annotated[list[str] | None, typer.Option("--lifecycle")] = None,
    limit: Annotated[int, typer.Option("--limit")] = 100,
) -> None:
    """Search token, recipe, or TagSpec metadata."""

    if kind not in {"token", "recipe", "tagspec"}:
        typer.echo(f"unsupported search kind: {kind}", err=True)
        raise typer.Exit(2)
    try:
        results = search_index(
            kind,  # type: ignore[arg-type]
            domain=domain,
            output_type=output_type,
            input_types=input_type,
            state_tag=state_tag,
            profile_allowed=profile_allowed,
            uses_token=uses_token,
            fully_verified_only=fully_verified,
            lifecycle=lifecycle,
            limit=limit,
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from None
    _echo_json([result.model_dump(mode="json") for result in results])


@app.command("compare")
def compare_cmd(yaml_a: Path, yaml_b: Path) -> None:
    """Compare two strategy YAML files by P0 hash layers."""

    result = compare_ir(load_strategy_file(yaml_a), load_strategy_file(yaml_b))
    typer.echo("== Compare Report ==")
    typer.echo("")
    typer.echo("Structure:")
    typer.echo(f"  graph_hash {'identical' if result.graph_equal else 'different'}")
    typer.echo("")
    typer.echo("Parameters:")
    typer.echo(f"  param_hash {'identical' if result.param_equal else 'differs'}")
    if result.param_diffs:
        for diff in result.param_diffs:
            typer.echo(f"  - {diff.path}: {diff.left} -> {diff.right}")
    typer.echo("")
    typer.echo("Instance:")
    typer.echo(f"  instance_hash {'identical' if result.instance_equal else 'differs'}")


@app.command("diff")
def diff_cmd(yaml_a: Path, yaml_b: Path) -> None:
    """Print a P2b-0 JSON diff report for two strategy YAML files."""

    result = diff_strategies(load_strategy_file(yaml_a), load_strategy_file(yaml_b))
    _echo_json(result.model_dump(mode="json"))


def _load_json_path(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return raw


def _parse_mutation_input(
    op_json: str | None,
    op_file: Path | None,
    repair_hint: Path | None,
) -> Any:
    inputs = [item is not None for item in (op_json, op_file, repair_hint)]
    if sum(inputs) != 1:
        typer.echo("provide exactly one of --op, --op-file, or --repair-hint", err=True)
        raise typer.Exit(2)
    if op_json is not None:
        raw = json.loads(op_json)
        if not isinstance(raw, dict):
            raise TypeError("--op must decode to a JSON object")
        return parse_mutation_op(raw)
    if op_file is not None:
        return parse_mutation_op(_load_json_path(op_file))
    assert repair_hint is not None
    return mutation_from_repair_hint(_load_json_path(repair_hint))


@app.command("mutate")
def mutate_cmd(
    path: Path,
    op_json: Annotated[str | None, typer.Option("--op")] = None,
    op_file: Annotated[Path | None, typer.Option("--op-file")] = None,
    repair_hint: Annotated[Path | None, typer.Option("--repair-hint")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Apply one P2b mutation operation to a strategy YAML file."""

    op = _parse_mutation_input(op_json, op_file, repair_hint)
    result = mutate_strategy(load_strategy_file(path), op)
    if not result.ok:
        _echo_json(result.model_dump(mode="json", exclude={"ir"}))
        raise typer.Exit(1)

    assert result.ir is not None
    if output is not None:
        output.write_text(
            yaml.safe_dump(to_plain(result.ir), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    payload = result.model_dump(mode="json", exclude={"ir"})
    if output is not None:
        payload["output"] = str(output)
    else:
        payload["ir"] = to_plain(result.ir)
    _echo_json(payload)


def _package_version_from_manifest(parent_package: Path | None) -> str | None:
    if parent_package is None:
        return None
    manifest_path = parent_package / "manifest.yaml"
    if not manifest_path.exists():
        return None
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    package_version = raw.get("package_version")
    return package_version if isinstance(package_version, str) else None


@app.command("fork")
def fork_cmd(
    parent: Path,
    new_id: Annotated[str, typer.Option("--new-id")],
    out: Annotated[Path, typer.Option("--out")],
    parent_package: Annotated[Path | None, typer.Option("--parent-package")] = None,
) -> None:
    """Fork a strategy. This is the only CLI path that emits qst-ir/0.3.1."""

    forked = fork_strategy(
        parent,
        new_id,
        parent_package=str(parent_package) if parent_package is not None else None,
        parent_package_version=_package_version_from_manifest(parent_package),
    )
    out.write_text(
        yaml.safe_dump(to_plain(forked), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _echo_json(
        {
            "ok": True,
            "output": str(out),
            "ir_version": forked.ir_version,
            "strategy": forked.strategy,
            "derived_from": (
                forked.derived_from.model_dump(mode="json")
                if forked.derived_from is not None
                else None
            ),
        }
    )


@app.command("explain")
def explain_cmd(path: Path, level: str = "L1") -> None:
    """Print a human-readable strategy explanation."""

    typer.echo(explain_text(load_strategy_file(path), level=level))


@app.command("fingerprint")
def fingerprint_cmd(path: Path) -> None:
    """Print P2c-core Merkle fingerprints and execution plan debug data."""

    ir = load_strategy_file(path)
    canonical = canonicalize_ir(ir)
    hashes = compute_hashes(canonical)
    fingerprints = compute_all_fingerprints(canonical.graph)
    plan = make_execution_plan(canonical)
    _echo_json(
        {
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
    )


def _load_market_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in ("timestamp", "ts", "time", "date"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
            frame = frame.set_index(column)
            break
    return frame


@app.command("execute")
def execute_cmd(
    path: Path,
    market: Annotated[Path, typer.Option("--market")],
    trace_path: Annotated[Path, typer.Option("--trace-path")] = Path("trace.json"),
    profile: Annotated[str | None, typer.Option("--profile")] = None,
    kernel_substitution: Annotated[bool, typer.Option("--kernel-substitution")] = False,
) -> None:
    """Execute a strategy YAML file against sample market CSV data."""

    ir, envelope = load_strategy_file_with_envelope(path)
    execution_profile = _effective_profile(profile, envelope.profile)
    result = execute_strategy(
        ir,
        {
            "market": _load_market_csv(market),
            "state": {
                "current_symbol": 1.0,
                "current_notional": 0.0,
                "elapsed": 0.0,
                "cooldown_elapsed": 0.0,
            },
            "sizing": 1.0,
        },
        trace_path=trace_path,
        profile=execution_profile,
        kernel_substitution=kernel_substitution,
    )
    if not result.ok:
        typer.echo(result.error or "execution failed", err=True)
        if result.validation_failures:
            for failure in result.validation_failures:
                typer.echo(json.dumps(failure.model_dump(exclude_none=True), ensure_ascii=False), err=True)
            raise typer.Exit(1)
        raise typer.Exit(4)
    _echo_json({"outputs": result.outputs, "trace": str(trace_path)})

@app.command("promote")
def promote_cmd(
    path: Path,
    to_profile: Annotated[ProfileLiteral, typer.Option("--to")],
    approved_by: Annotated[str | None, typer.Option("--approved-by")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Promote a strategy deployment envelope to a target profile."""

    ir, envelope = load_strategy_file_with_envelope(path)
    result = promote_strategy(ir, envelope, to_profile, approved_by=approved_by)
    if not result.ok:
        _echo_json(
            {
                "ok": False,
                "target_profile": to_profile,
                "strategy_instance_hash": envelope.strategy_instance_hash,
                "new_envelope": None,
                "validation_failures": [
                    failure.model_dump(mode="json", exclude_none=True)
                    for failure in result.new_validation_failures
                ],
            }
        )
        raise typer.Exit(1)

    assert result.new_envelope is not None
    if output is not None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError("Strategy YAML must contain a mapping")
        raw["_envelope"] = result.new_envelope.model_dump(mode="json", exclude_none=True)
        output.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
    payload = {
        "ok": True,
        "target_profile": to_profile,
        "strategy_instance_hash": result.new_envelope.strategy_instance_hash,
        "new_envelope": result.new_envelope.model_dump(mode="json", exclude_none=True),
        "validation_failures": [],
        "diff": result.diff_from_previous,
    }
    if output is not None:
        payload["output"] = str(output)
    _echo_json(payload)


@app.command("explain-trace")
def explain_trace_cmd(
    trace_path: Path,
    level: Annotated[str, typer.Option("--level")] = "human",
) -> None:
    """Explain a trace JSON file."""

    if level not in {"human", "agent", "raw"}:
        typer.echo(f"unsupported level: {level}", err=True)
        raise typer.Exit(2)
    trace = Trace.model_validate_json(trace_path.read_text(encoding="utf-8"))
    typer.echo(explain_trace_text(trace, level=level))  # type: ignore[arg-type]


@tag_app.command("verify")
def tag_verify_cmd(
    tag_path: Path,
    level: Annotated[str, typer.Option("--level")] = "attachment",
) -> None:
    """Verify a TagSpec YAML file."""

    if level not in {"attachment", "full"}:
        typer.echo(f"unsupported verification level: {level}", err=True)
        raise typer.Exit(2)
    spec = load_tagspec_file(tag_path)
    if level == "full":
        spec = upgrade_verification(spec)
    payload = {
        "ok": spec.verification.minimally_attached,
        "level": level,
        "semantic_id": spec.semantic_id,
        "version": spec.version,
        "verification": spec.verification.model_dump(mode="json"),
        "minimally_attached": spec.verification.minimally_attached,
        "fully_verified": spec.verification.fully_verified,
    }
    _echo_json(payload)
    if (level == "attachment" and not spec.verification.minimally_attached) or (
        level == "full" and not spec.verification.fully_verified
    ):
        raise typer.Exit(1)


@recipe_app.command("expand")
def recipe_expand_cmd(
    semantic_id: str,
    params_json: Annotated[str, typer.Option("--params")] = "{}",
    output: Annotated[Path, typer.Option("--output")] = Path("recipe.json"),
) -> None:
    """Expand a P2a-2 recipe generator to a concrete recipe YAML or JSON file."""

    try:
        raw_params = json.loads(params_json)
        if not isinstance(raw_params, dict):
            raise TypeError("--params must decode to a JSON object")
        recipe = expand_builtin_recipe(semantic_id, raw_params)
    except Exception as exc:
        _echo_json({"ok": False, "semantic_id": semantic_id, "error": str(exc)})
        raise typer.Exit(1) from None

    payload = recipe.model_dump(mode="json")
    if output.suffix.lower() in {".yaml", ".yml"}:
        output.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    else:
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _echo_json(
        {
            "ok": True,
            "semantic_id": semantic_id,
            "version": recipe.version,
            "output": str(output),
            "node_count": len(recipe.graph),
            "recipe_id": recipe.recipe,
        }
    )


@kernel_app.command("plan")
def kernel_plan_cmd(path: Path) -> None:
    """Print P2c-extended opt-in kernel substitution eligibility."""

    canonical = canonicalize_ir(load_strategy_file(path))
    _echo_json(make_kernel_plan_report(canonical).model_dump(mode="json"))


if __name__ == "__main__":
    app()
