"""Typer CLI for QST P0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
import typer
import yaml

from quant_strategy_tokenizer.agent.promote import promote as promote_strategy
from quant_strategy_tokenizer.composition import expand_builtin_recipe, upgrade_verification
from quant_strategy_tokenizer.core.output import jsonable_value
from quant_strategy_tokenizer.detokenize.explain_emitter import explain_ir as explain_text
from quant_strategy_tokenizer.detokenize.trace_explainer import explain_trace as explain_trace_text
from quant_strategy_tokenizer.execution.fingerprint import compute_all_fingerprints
from quant_strategy_tokenizer.execution.kernel import make_kernel_plan_report
from quant_strategy_tokenizer.execution.plan import make_execution_plan
from quant_strategy_tokenizer.ir.canonicalize import canonicalize as canonicalize_ir
from quant_strategy_tokenizer.ir.compare import compare_ir
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.serialize import to_json, to_plain
from quant_strategy_tokenizer.ir.validate import validate as validate_ir
from quant_strategy_tokenizer.mutation import diff_strategies, mutate_strategy, parse_mutation_op
from quant_strategy_tokenizer.mutation.repair import mutation_from_repair_hint
from quant_strategy_tokenizer.package import (
    package_strategy,
    unpack_package,
    verify_package,
)
from quant_strategy_tokenizer.parse.yaml_loader import (
    load_strategy_file,
    load_strategy_file_with_envelope,
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

app = typer.Typer(no_args_is_help=True)
tag_app = typer.Typer(no_args_is_help=True)
recipe_app = typer.Typer(no_args_is_help=True)
kernel_app = typer.Typer(no_args_is_help=True)
app.add_typer(tag_app, name="tag")
app.add_typer(recipe_app, name="recipe")
app.add_typer(kernel_app, name="kernel")

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
