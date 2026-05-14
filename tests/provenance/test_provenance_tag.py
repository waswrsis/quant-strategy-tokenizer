from __future__ import annotations

import math

import pytest

from quant_strategy_tokenizer.provenance import ProvenanceTag, TagAttachedBy


def test_provenance_tag_params_are_canonical_and_immutable() -> None:
    raw_params = {
        "span": 9,
        "nested": {"z": True, "a": [1, 2.1234567890123456789]},
    }

    tag = ProvenanceTag(
        semantic_id="indicator.ewm",
        version=1,
        params=raw_params,
        role="ewm",
        tag_attached_by="recipe_compiler",
    )
    raw_params["nested"]["z"] = False

    assert list(tag.params) == ["nested", "span"]
    assert tag.params["nested"]["a"] == (1, 2.12345678901235)  # type: ignore[index]
    assert tag.params["nested"]["z"] is True  # type: ignore[index]
    assert isinstance(tag.tag_attached_by, TagAttachedBy)
    assert tag.tag_attached_by.type == "recipe_compiler"

    with pytest.raises(TypeError):
        tag.params["mutated"] = 1  # type: ignore[index]


def test_legacy_spike_manual_attacher_migrates_to_recipe_compiler() -> None:
    tag = ProvenanceTag("indicator.ewm", 1, tag_attached_by="spike_manual")

    assert isinstance(tag.tag_attached_by, TagAttachedBy)
    assert tag.tag_attached_by.type == "recipe_compiler"


def test_tag_attached_by_accepts_structured_mapping() -> None:
    tag = ProvenanceTag(
        "indicator.ewm",
        1,
        tag_attached_by={"type": "trusted_generator", "signed_by": "ci"},
    )

    assert isinstance(tag.tag_attached_by, TagAttachedBy)
    assert tag.tag_attached_by.type == "trusted_generator"
    assert tag.tag_attached_by.signed_by == "ci"


@pytest.mark.parametrize(
    "params",
    [
        {"x": math.nan},
        {"x": math.inf},
        {"x": b"bytes"},
        {"x": (1, 2)},
        {1: "non-string-key"},
        {"x": object()},
        {"x": [[[[[[[[["too_deep"]]]]]]]]]},
    ],
)
def test_provenance_tag_rejects_non_canonical_params(params: dict[object, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        ProvenanceTag("indicator.ewm", 1, params)
