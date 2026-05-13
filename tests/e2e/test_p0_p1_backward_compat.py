from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_GRAPH_HASH = "sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947"
EXPECTED_PARAM_HASH = "sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28"
EXPECTED_INSTANCE_HASH = "sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d"

P0_TOKEN_TRIPLES = [
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
]

P0_RECIPE_PAIRS = [
    ("indicator.ewm", 1),
    ("indicator.rma", 1),
    ("indicator.kdj", 1),
    ("event.cross_above", 1),
]


def test_kdj_p0_hashes_unchanged_under_p1() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")

    hashes = compute_hashes(ir)

    assert hashes.graph_hash == EXPECTED_GRAPH_HASH
    assert hashes.param_hash == EXPECTED_PARAM_HASH
    assert hashes.instance_hash == EXPECTED_INSTANCE_HASH


def test_broken_no_lift_repair_hint_remains_available() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "broken_no_lift.qst.yaml")

    result = validate(ir)

    assert not result.ok
    assert any(failure.kind == "type_mismatch" for failure in result.failures)
    hints = [failure.repair_hint for failure in result.failures if failure.repair_hint is not None]
    assert hints
    assert any(
        op.get("insert_node", {}).get("token") == "decision.lift_bool"
        for hint in hints
        for op in hint.get("ops", [])
    )


def test_p0_vocabulary_triples_still_resolve() -> None:
    registry = get_registry()
    recipe_registry = get_recipe_registry()

    for token_id, version, behavior_version in P0_TOKEN_TRIPLES:
        registered = registry.get(token_id, version)
        assert registered.spec.behavior_version == behavior_version

    for recipe_id, version in P0_RECIPE_PAIRS:
        recipe = recipe_registry.get(recipe_id, version)
        assert recipe.recipe == recipe_id
        assert recipe.version == version
