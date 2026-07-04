"""Models for deterministic token-gap resolution."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.types import TypeSpec, parse_type_spec

RESOLVER_POLICY_SCHEMA_VERSION: Literal["qst-resolver-policy/1.0"] = (
    "qst-resolver-policy/1.0"
)
TOKEN_INTENT_SCHEMA_VERSION: Literal["qst-token-intent/1.0"] = "qst-token-intent/1.0"
VOCABULARY_SNAPSHOT_SCHEMA_VERSION: Literal["qst-vocabulary-snapshot/1.0"] = (
    "qst-vocabulary-snapshot/1.0"
)

ResolverRoute = Literal[
    "invalid_intent",
    "non_goal_runtime",
    "reserved_typespec",
    "direct_token_match",
    "recipe_match",
    "existing_proposal",
    "new_token_gap",
]
CandidateStatus = Literal[
    "exact_compatible",
    "alias_compatible",
    "version_compatible",
    "exact_incompatible",
    "alias_incompatible",
    "version_incompatible",
]
ProposalStatus = Literal[
    "detected",
    "agent_draft",
    "statically_validated",
    "contract_approved",
    "implementation_reviewed",
    "conformance_passed",
    "publication_approved",
    "published_project_local",
    "explicit_activation_requested",
    "activation_approved",
    "active_for_project",
    "builtin_candidate",
    "rejected",
]


def _stable_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(values)))


def _ensure_json(value: Any, *, field_name: str) -> Any:
    try:
        stable_json_bytes(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be canonical JSON-compatible") from exc
    return value


class TokenIntent(BaseModel):
    """Structured token need supplied to the deterministic resolver."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-token-intent/1.0"] = TOKEN_INTENT_SCHEMA_VERSION
    concept: str = Field(min_length=1)
    requested_token_id: str | None = None
    version: int | None = Field(default=None, ge=1)
    behavior_version: int | None = Field(default=None, ge=1)
    inputs: dict[str, TypeSpec] = Field(default_factory=dict)
    outputs: dict[str, TypeSpec] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    required_types: tuple[str, ...] = ()
    runtime_requirements: tuple[str, ...] = ()
    target_profile: str = "research"

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def _parse_types(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {str(name): parse_type_spec(type_spec) for name, type_spec in value.items()}

    @field_validator("required_types", "runtime_requirements", mode="after")
    @classmethod
    def _sort_terms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _stable_unique(value)

    @field_validator("params", mode="after")
    @classmethod
    def _validate_params(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_json(value, field_name="intent params")
        return value

    @model_validator(mode="after")
    def _version_pair(self) -> TokenIntent:
        if self.behavior_version is not None and self.version is None:
            raise ValueError("behavior_version requires version")
        return self


class ResolverPolicy(BaseModel):
    """Versioned route lattice and boundary vocabulary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-resolver-policy/1.0"] = RESOLVER_POLICY_SCHEMA_VERSION
    policy_id: str = "qst.default-resolver-policy"
    route_precedence: tuple[ResolverRoute, ...] = (
        "invalid_intent",
        "non_goal_runtime",
        "reserved_typespec",
        "direct_token_match",
        "recipe_match",
        "existing_proposal",
        "new_token_gap",
    )
    non_goal_runtime_terms: tuple[str, ...] = (
        "backtest_execution",
        "backtest_engine",
        "broker_execution",
        "custom_python_execution",
        "custody",
        "exchange_routing",
        "live_execution",
        "model_inference",
        "model_training",
        "production_execution",
        "trading_simulation",
    )
    evidence_only_runtime_terms: tuple[str, ...] = (
        "artifact_collection",
        "result_collection",
        "workflow_discovery",
    )
    reserved_type_terms: tuple[str, ...] = (
        "Calendar",
        "Distribution",
        "EventStream",
        "OrderBook",
    )
    candidate_status_rank: dict[CandidateStatus, int] = Field(
        default_factory=lambda: _default_candidate_status_rank()
    )

    @field_validator(
        "non_goal_runtime_terms",
        "evidence_only_runtime_terms",
        "reserved_type_terms",
        mode="after",
    )
    @classmethod
    def _sort_policy_terms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _stable_unique(value)

    @model_validator(mode="after")
    def _fixed_v1_lattice(self) -> ResolverPolicy:
        expected = (
            "invalid_intent",
            "non_goal_runtime",
            "reserved_typespec",
            "direct_token_match",
            "recipe_match",
            "existing_proposal",
            "new_token_gap",
        )
        if self.route_precedence != expected:
            raise ValueError("qst-resolver-policy/1.0 route_precedence is immutable")
        expected_statuses = {
            "exact_compatible",
            "alias_compatible",
            "version_compatible",
            "exact_incompatible",
            "alias_incompatible",
            "version_incompatible",
        }
        if set(self.candidate_status_rank) != expected_statuses:
            raise ValueError("candidate_status_rank must define every status exactly once")
        if len(set(self.candidate_status_rank.values())) != len(expected_statuses):
            raise ValueError("candidate status ranks must be unique")
        return self


class ResolverTokenRecord(BaseModel):
    """Hash-bearing token material used by a vocabulary snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    token_id: str
    namespace: str
    name: str
    version: int
    behavior_version: int
    token_spec_hash: HashString
    inputs: dict[str, TypeSpec]
    outputs: dict[str, TypeSpec]
    params_schema: dict[str, Any]
    maturity: str
    supported_profiles: tuple[str, ...]
    reserved_only: bool

    @field_validator("params_schema", mode="after")
    @classmethod
    def _validate_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_json(value, field_name="params_schema")
        return value


class VocabularySnapshot(BaseModel):
    """Deterministically ordered resolver view of token vocabulary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-vocabulary-snapshot/1.0"] = (
        VOCABULARY_SNAPSHOT_SCHEMA_VERSION
    )
    records: tuple[ResolverTokenRecord, ...]
    snapshot_hash: HashString


class RecipeSpec(BaseModel):
    """Declarative recipe candidate; it does not execute a graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recipe_id: str
    concepts: tuple[str, ...]
    token_refs: tuple[str, ...]
    inputs: dict[str, TypeSpec] = Field(default_factory=dict)
    outputs: dict[str, TypeSpec] = Field(default_factory=dict)
    params_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "additionalProperties": True}
    )
    supported_profiles: tuple[str, ...] = (
        "research",
        "paper",
        "pretrade",
        "production_guarded",
    )

    @field_validator("inputs", "outputs", mode="before")
    @classmethod
    def _parse_recipe_types(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {str(name): parse_type_spec(type_spec) for name, type_spec in value.items()}

    @field_validator("concepts", "token_refs", "supported_profiles", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _stable_unique(value)

    @field_validator("params_schema", mode="after")
    @classmethod
    def _validate_recipe_params_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_json(value, field_name="recipe params_schema")
        return value


class TokenProposalSummary(BaseModel):
    """Non-executable summary of an existing governed token proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str
    concept: str
    status: ProposalStatus
    proposed_token_id: str
    proposal_hash: HashString


class CandidateFacts(BaseModel):
    """Complete compatibility facts for one token candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    token_id: str
    token_spec_hash: HashString
    namespace: str
    name: str
    version: int
    behavior_version: int
    status: CandidateStatus
    identifier_match: Literal["exact", "alias", "version"]
    version_compatible: bool
    ports_compatible: bool
    types_compatible: bool
    params_compatible: bool
    profile_allowed: bool
    reserved: bool
    incompatibilities: tuple[str, ...] = ()


class ResolutionIdentity(BaseModel):
    """All independently hashable inputs to a resolver decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_hash: HashString
    vocabulary_snapshot_hash: HashString
    alias_catalog_hash: HashString
    recipe_catalog_hash: HashString
    proposal_catalog_hash: HashString
    profile_policy_hash: HashString
    resolver_policy_hash: HashString
    resolution_hash: HashString


class ResolverIssue(BaseModel):
    """Stable resolver issue independent of v0.4 validation phases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str
    path: str = ""


class ResolutionResult(BaseModel):
    """Deterministic token route and its complete evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route: ResolverRoute
    intent: TokenIntent | None
    identity: ResolutionIdentity
    candidates: tuple[CandidateFacts, ...] = ()
    matched_recipe_id: str | None = None
    matched_proposal_id: str | None = None
    boundary_terms: tuple[str, ...] = ()
    issues: tuple[ResolverIssue, ...] = ()


def _default_candidate_status_rank() -> dict[CandidateStatus, int]:
    return {
        "exact_compatible": 0,
        "alias_compatible": 1,
        "version_compatible": 2,
        "exact_incompatible": 3,
        "alias_incompatible": 4,
        "version_incompatible": 5,
    }
