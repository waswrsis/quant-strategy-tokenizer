"""TagSpec and progressive verification models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VerificationStatus(BaseModel):
    """Progressive provenance verification state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tag_attached_by_trusted: bool
    graph_template_hash_valid: bool
    namespace_allowed: bool
    contracts_pass: bool | None = None
    fuzzing_at_ci_standard: bool | None = None
    metamorphic_pass: bool | None = None

    @property
    def minimally_attached(self) -> bool:
        return (
            self.tag_attached_by_trusted
            and self.graph_template_hash_valid
            and self.namespace_allowed
        )

    @property
    def fully_verified(self) -> bool:
        return self.minimally_attached and all(
            item is True
            for item in (
                self.contracts_pass,
                self.fuzzing_at_ci_standard,
                self.metamorphic_pass,
            )
        )


def default_verification() -> VerificationStatus:
    return VerificationStatus(
        tag_attached_by_trusted=False,
        graph_template_hash_valid=False,
        namespace_allowed=False,
    )


class TagSpec(BaseModel):
    """Serializable semantic tag specification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    semantic_id: str
    version: int = 1
    domain: str
    params_schema: dict[str, Any] = Field(default_factory=dict)
    source_recipe: str
    source_recipe_version: int = 1
    graph_template_hash: str
    verification: VerificationStatus = Field(default_factory=default_verification)
    reference_impl: str | None = None
    contract_suite: str | None = None
    fuzzing_report: str | None = None
    metamorphic_properties: list[str] = Field(default_factory=list)
    allowed_kernels: list[dict[str, Any]] = Field(default_factory=list)
    lifecycle: Literal["experimental", "core_candidate", "core_stable", "deprecated"] = (
        "experimental"
    )
    owner: str | None = None
