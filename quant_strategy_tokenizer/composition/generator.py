"""Deterministic YAML recipe generator for P2a-2."""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Mapping
from importlib.resources import files
from math import isfinite
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.provenance.tag import canonicalize_params
from quant_strategy_tokenizer.recipes.schema import RecipeNode, RecipeSpec

MAX_EXPANDED_NODES = 5000
MAX_STATIC_LOOP_COUNT = 1024
MAX_MACRO_DEPTH = 4

_TEMPLATE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_PARAM_RE = re.compile(r"\$params\.([A-Za-z_][A-Za-z0-9_]*)")
_NONDETERMINISTIC_KEYS = {
    "callable",
    "eval",
    "exec",
    "now",
    "python",
    "random",
    "runtime",
    "timestamp",
    "uuid",
}


class GeneratorConstraintError(ValueError):
    """Generator hard constraint failed."""


class StaticFor(BaseModel):
    """Static loop definition."""

    model_config = ConfigDict(extra="forbid")

    var: str
    range: tuple[Any, Any]


class GeneratorNode(BaseModel):
    """One generator emit item."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    token: str | None = None
    recipe: str | None = None
    v: int = 1
    version: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    role: str | None = None

    static_for: StaticFor | None = None
    body: list[GeneratorNode] = Field(default_factory=list)
    static_if: str | bool | None = None
    then: list[GeneratorNode] = Field(default_factory=list)
    else_: list[GeneratorNode] = Field(default_factory=list, alias="else")
    include: str | None = None


class GeneratorBody(BaseModel):
    """Generator body."""

    model_config = ConfigDict(extra="forbid")

    emit: list[GeneratorNode]


class RecipeGeneratorRoot(BaseModel):
    """Recipe generator root object."""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: int = 1
    params_schema: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, str]
    outputs: dict[str, str]
    generator: GeneratorBody
    description: str = ""


class RecipeGeneratorDocument(BaseModel):
    """Top-level generator YAML document."""

    model_config = ConfigDict(extra="forbid")

    recipe: RecipeGeneratorRoot


def _scan_for_nondeterminism(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in _NONDETERMINISTIC_KEYS:
                raise GeneratorConstraintError(f"nondeterministic construct is forbidden: {key}")
            _scan_for_nondeterminism(item)
        return
    if isinstance(value, list):
        for item in value:
            _scan_for_nondeterminism(item)
        return
    if isinstance(value, str) and value.startswith("$runtime."):
        raise GeneratorConstraintError(f"nondeterministic runtime reference is forbidden: {value}")


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    _scan_for_nondeterminism(raw)
    return raw


def load_generator_file(path: str | Path) -> RecipeGeneratorDocument:
    """Load and validate a generator YAML file."""

    return RecipeGeneratorDocument.model_validate(_load_yaml_mapping(Path(path)))


def _defaults_from_schema(params_schema: Mapping[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for key, schema in params_schema.items():
        if isinstance(schema, Mapping) and "default" in schema:
            defaults[str(key)] = schema["default"]
    return defaults


def _validate_single_param(name: str, value: Any, schema: Mapping[str, Any]) -> None:
    if "oneOf" in schema:
        errors = []
        for option in schema["oneOf"]:
            if not isinstance(option, Mapping):
                continue
            try:
                _validate_single_param(name, value, option)
                return
            except (TypeError, ValueError) as exc:
                errors.append(str(exc))
        raise ValueError(f"param {name!r} does not match any oneOf schema: {errors}")

    kind = schema.get("type")
    if kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
        raise TypeError(f"param {name!r} must be integer")
    if kind == "number" and (
        isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(float(value))
    ):
        raise TypeError(f"param {name!r} must be finite number")
    if kind == "string" and not isinstance(value, str):
        raise TypeError(f"param {name!r} must be string")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"param {name!r} must be one of {schema['enum']}")
    if "minimum" in schema and isinstance(value, int | float) and value < schema["minimum"]:
        raise ValueError(f"param {name!r} must be >= {schema['minimum']}")
    if "maximum" in schema and isinstance(value, int | float) and value > schema["maximum"]:
        raise ValueError(f"param {name!r} must be <= {schema['maximum']}")


def _merge_and_validate_params(
    params_schema: Mapping[str, Any],
    params: Mapping[str, Any],
) -> dict[str, Any]:
    merged = _defaults_from_schema(params_schema)
    for key in params:
        if key not in params_schema:
            raise KeyError(f"Unknown generator param {key!r}")
    merged.update(params)
    for key, schema in params_schema.items():
        if key not in merged:
            raise KeyError(f"Missing required generator param {key!r}")
        if isinstance(schema, Mapping):
            _validate_single_param(str(key), merged[str(key)], schema)
    canonicalize_params(merged)
    return merged


def _template_string(value: str, params: Mapping[str, Any], loop_vars: Mapping[str, int]) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in loop_vars:
            return str(loop_vars[name])
        if name in params:
            return str(params[name])
        raise KeyError(f"Unknown template variable {name!r}")

    return _TEMPLATE_RE.sub(replace, value)


def _resolve_value(
    value: Any,
    params: Mapping[str, Any],
    loop_vars: Mapping[str, int],
    *,
    concrete_params: bool,
) -> Any:
    if isinstance(value, str):
        if value.startswith("$params."):
            key = value.removeprefix("$params.")
            if concrete_params:
                return params[key]
            return value
        if _TEMPLATE_RE.search(value):
            return _template_string(value, params, loop_vars)
        return value
    if isinstance(value, list):
        return [
            _resolve_value(item, params, loop_vars, concrete_params=concrete_params)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            _template_string(str(key), params, loop_vars): _resolve_value(
                item,
                params,
                loop_vars,
                concrete_params=concrete_params,
            )
            for key, item in value.items()
        }
    return value


def _resolve_int(value: Any, params: Mapping[str, Any], loop_vars: Mapping[str, int]) -> int:
    resolved = _resolve_value(value, params, loop_vars, concrete_params=True)
    if isinstance(resolved, bool) or not isinstance(resolved, int):
        raise TypeError(f"static_for range bound must be integer, got {resolved!r}")
    return resolved


def _safe_eval_bool(expr: str | bool, params: Mapping[str, Any]) -> bool:
    if isinstance(expr, bool):
        return expr
    resolved = _PARAM_RE.sub(lambda match: repr(params[match.group(1)]), expr)
    tree = ast.parse(resolved, mode="eval")
    allowed = (
        ast.Expression,
        ast.BoolOp,
        ast.Compare,
        ast.Constant,
        ast.And,
        ast.Or,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.UnaryOp,
        ast.Not,
        ast.Load,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise GeneratorConstraintError(f"Unsupported static_if expression: {expr}")
    return bool(_eval_static_ast(tree))


def _eval_static_ast(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_static_ast(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_eval_static_ast(node.operand))
    if isinstance(node, ast.BoolOp):
        values = [bool(_eval_static_ast(value)) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Compare):
        left = _eval_static_ast(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            right = _eval_static_ast(comparator)
            if not _compare_static_values(left, op, right):
                return False
            left = right
        return True
    raise GeneratorConstraintError("Unsupported static_if expression")


def _compare_static_values(left: Any, op: ast.cmpop, right: Any) -> bool:
    if isinstance(op, ast.Eq):
        return bool(left == right)
    if isinstance(op, ast.NotEq):
        return bool(left != right)
    if isinstance(op, ast.Lt):
        return bool(left < right)
    if isinstance(op, ast.LtE):
        return bool(left <= right)
    if isinstance(op, ast.Gt):
        return bool(left > right)
    if isinstance(op, ast.GtE):
        return bool(left >= right)
    raise GeneratorConstraintError("Unsupported static_if comparison")


def _resolve_include_path(path: str, *, base_dir: Path) -> Path:
    if "://" in path:
        raise GeneratorConstraintError("include path must be local")
    include_path = Path(path)
    if include_path.is_absolute():
        raise GeneratorConstraintError("include path must be relative")
    resolved = (base_dir / include_path).resolve()
    root = base_dir.resolve()
    if root != resolved and root not in resolved.parents:
        raise GeneratorConstraintError("include path escapes generator directory")
    return resolved


def _load_include_items(path: Path) -> list[GeneratorNode]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _scan_for_nondeterminism(raw)
    if isinstance(raw, list):
        return [GeneratorNode.model_validate(item) for item in raw]
    if isinstance(raw, dict):
        if "emit" in raw:
            emit = raw["emit"]
            if not isinstance(emit, list):
                raise TypeError("include emit must be a list")
            return [GeneratorNode.model_validate(item) for item in emit]
        return [GeneratorNode.model_validate(raw)]
    raise TypeError(f"{path} must contain a generator item, list, or emit mapping")


def _expand_items(
    items: list[GeneratorNode],
    *,
    params: Mapping[str, Any],
    loop_vars: Mapping[str, int],
    base_dir: Path,
    include_stack: tuple[Path, ...],
    include_depth: int,
    concrete_params: bool,
) -> list[RecipeNode]:
    if include_depth > MAX_MACRO_DEPTH:
        raise GeneratorConstraintError(f"macro/include depth exceeds {MAX_MACRO_DEPTH}")

    expanded: list[RecipeNode] = []
    for item in items:
        if item.static_for is not None:
            start = _resolve_int(item.static_for.range[0], params, loop_vars)
            stop = _resolve_int(item.static_for.range[1], params, loop_vars)
            size = max(0, stop - start)
            if size > MAX_STATIC_LOOP_COUNT:
                raise GeneratorConstraintError(
                    f"static_for range {size} exceeds {MAX_STATIC_LOOP_COUNT}"
                )
            for index in range(start, stop):
                nested_loop_vars = {**loop_vars, item.static_for.var: index}
                expanded.extend(
                    _expand_items(
                        item.body,
                        params=params,
                        loop_vars=nested_loop_vars,
                        base_dir=base_dir,
                        include_stack=include_stack,
                        include_depth=include_depth,
                        concrete_params=concrete_params,
                    )
                )
            continue

        if item.static_if is not None:
            branch = item.then if _safe_eval_bool(item.static_if, params) else item.else_
            expanded.extend(
                _expand_items(
                    branch,
                    params=params,
                    loop_vars=loop_vars,
                    base_dir=base_dir,
                    include_stack=include_stack,
                    include_depth=include_depth,
                    concrete_params=concrete_params,
                )
            )
            continue

        if item.include is not None:
            include_path = _resolve_include_path(item.include, base_dir=base_dir)
            if include_path in include_stack:
                chain = " -> ".join(str(path) for path in (*include_stack, include_path))
                raise GeneratorConstraintError(f"recursive include is forbidden: {chain}")
            included_items = _load_include_items(include_path)
            include_params = _resolve_value(
                item.params,
                params,
                loop_vars,
                concrete_params=True,
            )
            if not isinstance(include_params, dict):
                raise TypeError("include params must resolve to a mapping")
            expanded.extend(
                _expand_items(
                    included_items,
                    params={**params, **include_params},
                    loop_vars=loop_vars,
                    base_dir=base_dir,
                    include_stack=(*include_stack, include_path),
                    include_depth=include_depth + 1,
                    concrete_params=concrete_params,
                )
            )
            continue

        if item.id is None or (item.token is None and item.recipe is None):
            raise GeneratorConstraintError("plain emit item must include id and token or recipe")
        node_data = {
            "id": _template_string(item.id, params, loop_vars),
            "token": item.token,
            "recipe": item.recipe,
            "v": item.v,
            "version": item.version,
            "params": _resolve_value(
                item.params,
                params,
                loop_vars,
                concrete_params=concrete_params,
            ),
            "inputs": _resolve_value(
                item.inputs,
                params,
                loop_vars,
                concrete_params=concrete_params,
            ),
            "role": item.role,
        }
        expanded.append(RecipeNode.model_validate({k: v for k, v in node_data.items() if v is not None}))
        if len(expanded) > MAX_EXPANDED_NODES:
            raise GeneratorConstraintError(
                f"expanded graph has more than {MAX_EXPANDED_NODES} nodes"
            )

    return expanded


def expand_generator(
    document: RecipeGeneratorDocument,
    params: Mapping[str, Any] | None = None,
    *,
    source_path: Path | None = None,
    concrete_params: bool = True,
) -> RecipeSpec:
    """Expand a recipe generator document into a RecipeSpec."""

    root = document.recipe
    merged_params = _merge_and_validate_params(root.params_schema, params or {})
    base_dir = (source_path.parent if source_path is not None else Path.cwd()).resolve()
    graph = _expand_items(
        root.generator.emit,
        params=merged_params,
        loop_vars={},
        base_dir=base_dir,
        include_stack=(),
        include_depth=0,
        concrete_params=concrete_params,
    )
    if len(graph) > MAX_EXPANDED_NODES:
        raise GeneratorConstraintError(f"expanded graph has more than {MAX_EXPANDED_NODES} nodes")
    return RecipeSpec(
        recipe=root.id,
        version=root.version,
        params_schema=root.params_schema,
        inputs=root.inputs,
        outputs=root.outputs,
        graph=graph,
        description=root.description,
    )


def _builtin_generator_path(semantic_id: str, version: int) -> Path:
    filename = f"{semantic_id}.v{version}.yaml"
    return Path(str(files("quant_strategy_tokenizer.composition.generators").joinpath(filename)))


def expand_builtin_recipe(
    semantic_id: str,
    params: Mapping[str, Any] | None = None,
    *,
    version: int = 1,
    concrete_params: bool = True,
) -> RecipeSpec:
    """Expand a built-in P2a-2 recipe generator."""

    path = _builtin_generator_path(semantic_id, version)
    return expand_generator(
        load_generator_file(path),
        params or {},
        source_path=path,
        concrete_params=concrete_params,
    )


def recipe_to_stable_json(recipe: RecipeSpec) -> str:
    """Serialize a generated recipe deterministically."""

    return json.dumps(
        recipe.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
