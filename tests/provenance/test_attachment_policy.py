from __future__ import annotations

from quant_strategy_tokenizer.provenance.attachment import (
    namespace_allowed,
    verify_attachment,
)
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.provenance.spec import TagSpec
from quant_strategy_tokenizer.provenance.tag import ProvenanceTag


def test_recipe_compiler_attachment_is_trusted_for_indicator_ewm() -> None:
    spec = get_tagspec_registry().get("indicator.ewm", 1)
    tag = ProvenanceTag(
        semantic_id="indicator.ewm",
        version=1,
        tag_attached_by="recipe_compiler",
    )

    status = verify_attachment(tag, spec)

    assert status.minimally_attached is True


def test_user_authored_attachment_is_not_trusted() -> None:
    spec = get_tagspec_registry().get("indicator.ewm", 1)
    tag = ProvenanceTag(
        semantic_id="indicator.ewm",
        version=1,
        tag_attached_by="user_authored",
    )

    status = verify_attachment(tag, spec)

    assert status.tag_attached_by_trusted is False
    assert status.minimally_attached is False


def test_user_namespace_is_not_allowed_for_core_tags() -> None:
    assert namespace_allowed("indicator.ewm") is True
    assert namespace_allowed("user.custom") is False


def test_invalid_graph_template_hash_fails_attachment() -> None:
    good = get_tagspec_registry().get("indicator.ewm", 1)
    bad = TagSpec.model_validate(
        {
            **good.model_dump(mode="json"),
            "graph_template_hash": "sha256:" + ("0" * 64),
        }
    )
    tag = ProvenanceTag("indicator.ewm", 1, tag_attached_by="recipe_compiler")

    status = verify_attachment(tag, bad)

    assert status.graph_template_hash_valid is False
    assert status.minimally_attached is False
