from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.model import RecipeInstance
from quant_strategy_tokenizer.ir.serialize import to_json, to_plain
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
P0_STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"


def test_indicator_ewm_expansion_carries_provenance_through_rename_and_sort() -> None:
    canonical = canonicalize(load_strategy_file(P1_STRATEGY))

    tagged_nodes = [node for node in canonical.graph if node.provenance]

    assert len(tagged_nodes) == 1
    tagged = tagged_nodes[0]
    assert tagged.id.startswith("n")
    assert tagged.token == "smooth.linear_recursive"
    assert all(node.id != "ema.ewm" for node in canonical.graph)

    tag = tagged.provenance[0]
    assert tag.semantic_id == "indicator.ewm"
    assert tag.version == 1
    assert tag.params["span"] == 9
    assert tag.params["init"] == "first_value"
    assert tag.role == "ewm"
    assert tag.tag_attached_by.type == "recipe_compiler"


def test_non_ewm_recipes_do_not_get_p2a0_provenance() -> None:
    canonical = canonicalize(load_strategy_file(P0_STRATEGY))

    assert canonical.graph
    assert all(not node.provenance for node in canonical.graph)


def test_dce_removes_unreachable_provenance() -> None:
    ir = load_strategy_file(P1_STRATEGY)
    with_dead_ewm = ir.model_copy(
        update={
            "recipes": [
                *ir.recipes,
                RecipeInstance(
                    id="dead_ewm",
                    recipe="indicator.ewm",
                    version=1,
                    params={"span": 5},
                    inputs={"series": "market.close"},
                ),
            ]
        },
        deep=True,
    )

    canonical = canonicalize(with_dead_ewm)
    tagged_nodes = [node for node in canonical.graph if node.provenance]

    assert len(tagged_nodes) == 1
    assert tagged_nodes[0].provenance[0].params["span"] == 9


def test_empty_provenance_is_omitted_from_canonical_serialization() -> None:
    canonical = canonicalize(load_strategy_file(P0_STRATEGY))

    plain = to_plain(canonical)

    assert all("provenance" not in node for node in plain["graph"])
    assert "provenance" not in to_json(canonical)


def test_non_empty_provenance_is_serialized() -> None:
    canonical = canonicalize(load_strategy_file(P1_STRATEGY))

    tagged_nodes = [
        node for node in to_plain(canonical)["graph"]
        if "provenance" in node
    ]

    assert len(tagged_nodes) == 1
    assert tagged_nodes[0]["provenance"][0]["semantic_id"] == "indicator.ewm"
