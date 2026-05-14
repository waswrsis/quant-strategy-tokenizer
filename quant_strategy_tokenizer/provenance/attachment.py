"""Attachment-level provenance verification."""

from __future__ import annotations

from quant_strategy_tokenizer.provenance.graph_hash import recipe_graph_template_hash
from quant_strategy_tokenizer.provenance.spec import TagSpec, VerificationStatus
from quant_strategy_tokenizer.provenance.tag import ProvenanceTag, TagAttachedBy
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry

TRUSTED_ATTACHERS = {"recipe_compiler", "trusted_generator"}


def namespace_allowed(semantic_id: str) -> bool:
    """Return whether a semantic id is allowed outside user-controlled namespace."""

    return not semantic_id.startswith("user.")


def tag_attached_by_trusted(attached_by: TagAttachedBy) -> bool:
    return attached_by.type in TRUSTED_ATTACHERS


def verify_attachment(
    tag: ProvenanceTag,
    spec: TagSpec,
    *,
    recipe_registry: RecipeRegistry | None = None,
) -> VerificationStatus:
    """Verify a tag against a TagSpec at P2a-1 attachment level."""

    expected_hash = recipe_graph_template_hash(
        spec.source_recipe,
        spec.source_recipe_version,
        recipe_registry=recipe_registry,
    )
    attached_by = tag.tag_attached_by
    if not isinstance(attached_by, TagAttachedBy):
        attached_by = TagAttachedBy(type="recipe_compiler")
    return VerificationStatus(
        tag_attached_by_trusted=(
            tag.semantic_id == spec.semantic_id
            and tag.version == spec.version
            and tag_attached_by_trusted(attached_by)
        ),
        graph_template_hash_valid=spec.graph_template_hash == expected_hash,
        namespace_allowed=namespace_allowed(spec.semantic_id),
    )


def verify_tag_spec(
    spec: TagSpec,
    *,
    recipe_registry: RecipeRegistry | None = None,
) -> TagSpec:
    """Compute the P2a-1 verification fields for a TagSpec."""

    synthetic_tag = ProvenanceTag(
        semantic_id=spec.semantic_id,
        version=spec.version,
        params={},
        tag_attached_by="recipe_compiler",
    )
    verification = verify_attachment(
        synthetic_tag,
        spec,
        recipe_registry=recipe_registry,
    )
    return spec.model_copy(update={"verification": verification})
