"""IndexRecord: unified middle structure for P3 search."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.composition import upgrade_verification
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.validators.profile_policy import (
    PROFILE_MAX_PURITY,
    PURITY_ORDER,
    STRICT_TEMPORAL_PROFILES,
    UNSAFE_STRICT_WINDOW_MODES,
)
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.recipes.schema import RecipeSpec
from quant_strategy_tokenizer.tokens.registry import get_registry
from quant_strategy_tokenizer.tokens.spec import TokenSpec

IndexKind = Literal["token", "recipe", "tagspec"]
SearchProfile = Literal["research", "paper", "pretrade", "production_guarded"]


class IndexRecord(BaseModel):
    """Unified searchable metadata for tokens, recipes, and TagSpecs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: IndexKind
    id: str
    version: int
    domain: str | None = None
    input_types: tuple[str, ...] = ()
    output_type: str | None = None
    state_tag: str | None = None
    profile_allowed: tuple[str, ...] = ()
    uses_tokens: tuple[str, ...] = ()
    fully_verified: bool | None = None
    lifecycle: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)

    def matches(
        self,
        *,
        domain: str | None = None,
        output_type: str | None = None,
        input_types: list[str] | None = None,
        state_tag: str | None = None,
        profile_allowed: str | None = None,
        uses_token: str | None = None,
        fully_verified_only: bool = False,
        lifecycle: list[str] | None = None,
    ) -> bool:
        """Return whether this record matches all supplied filters."""

        if domain is not None and self.domain != domain:
            return False
        if output_type is not None and self.output_type != output_type:
            return False
        if input_types is not None and not set(input_types).issubset(self.input_types):
            return False
        if state_tag is not None and self.state_tag != state_tag:
            return False
        if profile_allowed is not None and profile_allowed not in self.profile_allowed:
            return False
        if uses_token is not None and uses_token not in self.uses_tokens:
            return False
        if fully_verified_only and self.fully_verified is not True:
            return False
        if lifecycle is not None and self.lifecycle not in set(lifecycle):
            return False
        return True


def _domain_from_id(identifier: str) -> str | None:
    if "." not in identifier:
        return None
    return identifier.split(".", 1)[0]


def _primary_output_type(outputs: dict[str, str]) -> str | None:
    if not outputs:
        return None
    if "value" in outputs:
        return outputs["value"]
    if "series" in outputs:
        return outputs["series"]
    first_key = sorted(outputs)[0]
    return outputs[first_key]


def _recipe_output_type(spec: RecipeSpec) -> str | None:
    output_ref = _primary_output_type(spec.outputs)
    if output_ref is None:
        return None
    if "." not in output_ref:
        return None
    node_id, output_port = output_ref.split(".", 1)
    for node in spec.graph:
        if node.id != node_id or node.token is None:
            continue
        token_spec = get_registry().get(node.token, node.v).spec
        return token_spec.outputs.get(output_port)
    return None


def _profile_allowed_for_token(spec: TokenSpec) -> tuple[ProfileLiteral, ...]:
    allowed: list[ProfileLiteral] = []
    for profile, max_purity in PROFILE_MAX_PURITY.items():
        if spec.purity in {"external_write", "forbidden"}:
            continue
        if PURITY_ORDER[spec.purity] > PURITY_ORDER[max_purity]:
            continue
        if profile in STRICT_TEMPORAL_PROFILES and (
            spec.temporal.uses_future_data
            or spec.temporal.window_mode in UNSAFE_STRICT_WINDOW_MODES
        ):
            continue
        allowed.append(profile)
    return tuple(allowed)


def _token_records() -> list[IndexRecord]:
    records: list[IndexRecord] = []
    for spec in get_registry().list_tokens():
        records.append(
            IndexRecord(
                kind="token",
                id=spec.id,
                version=spec.version,
                domain=_domain_from_id(spec.id),
                input_types=tuple(sorted(spec.inputs.values())),
                output_type=_primary_output_type(spec.outputs),
                state_tag=spec.state_tag,
                profile_allowed=_profile_allowed_for_token(spec),
                uses_tokens=(),
                fully_verified=None,
                lifecycle=spec.lifecycle,
                raw_metadata={
                    "behavior_version": spec.behavior_version,
                    "category": spec.category,
                    "layer": spec.layer,
                    "purity": spec.purity,
                    "description": spec.description,
                },
            )
        )
    return records


def _recipe_records() -> list[IndexRecord]:
    records: list[IndexRecord] = []
    for spec in get_recipe_registry().list_recipes():
        used_tokens = tuple(sorted({node.token for node in spec.graph if node.token is not None}))
        records.append(
            IndexRecord(
                kind="recipe",
                id=spec.recipe,
                version=spec.version,
                domain=_domain_from_id(spec.recipe),
                input_types=tuple(sorted(spec.inputs.values())),
                output_type=_recipe_output_type(spec),
                state_tag=None,
                profile_allowed=(),
                uses_tokens=used_tokens,
                fully_verified=None,
                lifecycle=None,
                raw_metadata={
                    "description": spec.description,
                    "node_count": len(spec.graph),
                },
            )
        )
    return records


def _verification_state(spec_fully_verified: bool, minimally_attached: bool) -> str:
    if spec_fully_verified:
        return "fully_verified"
    if minimally_attached:
        return "minimally_attached"
    return "unverified"


def _tagspec_records() -> list[IndexRecord]:
    records: list[IndexRecord] = []
    for raw_spec in get_tagspec_registry().list_specs():
        spec = upgrade_verification(raw_spec)
        records.append(
            IndexRecord(
                kind="tagspec",
                id=spec.semantic_id,
                version=spec.version,
                domain=spec.domain,
                input_types=(),
                output_type=None,
                state_tag=None,
                profile_allowed=(),
                uses_tokens=(),
                fully_verified=spec.verification.fully_verified,
                lifecycle=spec.lifecycle,
                raw_metadata={
                    "source_recipe": spec.source_recipe,
                    "source_recipe_version": spec.source_recipe_version,
                    "graph_template_hash": spec.graph_template_hash,
                    "verification_state": _verification_state(
                        spec.verification.fully_verified,
                        spec.verification.minimally_attached,
                    ),
                },
            )
        )
    return records


def build_index(kind: IndexKind) -> list[IndexRecord]:
    """Build P3b-0 index records on demand from public registries."""

    if kind == "token":
        return _token_records()
    if kind == "recipe":
        return _recipe_records()
    if kind == "tagspec":
        return _tagspec_records()
    raise ValueError(f"Unsupported index kind: {kind!r}")
