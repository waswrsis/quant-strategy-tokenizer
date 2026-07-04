"""Deterministic use-case policy profiles for authority mode selection."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.hash.common import HashString
from qst.identity import model_identity

from .models import AuthorityMode

AuthorityUseCase = Literal[
    "record_ingestion",
    "migration_import",
    "claim_evaluation",
    "token_review",
    "token_publication",
    "token_activation",
    "customization",
]

AUTHORITY_USE_CASES: tuple[AuthorityUseCase, ...] = (
    "claim_evaluation",
    "customization",
    "migration_import",
    "record_ingestion",
    "token_activation",
    "token_publication",
    "token_review",
)


class AuthorityPolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    use_case: AuthorityUseCase
    mode: AuthorityMode


class AuthorityPolicyProfile(BaseModel):
    """Complete, identity-bearing mapping from use cases to authority modes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-policy-profile/1.0"] = (
        "qst-authority-policy-profile/1.0"
    )
    profile_hash: HashString | None = None
    profile_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    description: str = Field(min_length=1)
    rules: tuple[AuthorityPolicyRule, ...]

    @field_validator("rules", mode="after")
    @classmethod
    def _rules(cls, value: tuple[AuthorityPolicyRule, ...]) -> tuple[AuthorityPolicyRule, ...]:
        return tuple(sorted(value, key=lambda item: item.use_case))

    @model_validator(mode="after")
    def _validate_profile(self) -> AuthorityPolicyProfile:
        use_cases = tuple(item.use_case for item in self.rules)
        if use_cases != AUTHORITY_USE_CASES:
            raise ValueError("authority profile must define every use case exactly once")
        if self.profile_hash is not None and self.profile_hash != authority_policy_profile_identity(
            self
        ):
            raise ValueError("profile_hash does not match authority policy profile material")
        return self

    def mode_for(self, use_case: AuthorityUseCase) -> AuthorityMode:
        return next(item.mode for item in self.rules if item.use_case == use_case)


class AuthorityModeSelection(BaseModel):
    """Auditable effective-mode selection, including any declared override."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-mode-selection/1.0"] = (
        "qst-authority-mode-selection/1.0"
    )
    selection_id: HashString | None = None
    profile_hash: HashString
    profile_id: str
    use_case: AuthorityUseCase
    configured_mode: AuthorityMode
    effective_mode: AuthorityMode
    override_applied: bool
    override_reason: str | None = None

    @model_validator(mode="after")
    def _validate_selection(self) -> AuthorityModeSelection:
        differs = self.configured_mode != self.effective_mode
        if self.override_applied != differs:
            raise ValueError("override_applied must match configured/effective mode difference")
        if differs and (self.override_reason is None or not self.override_reason.strip()):
            raise ValueError("authority mode override requires a reason")
        if not differs and self.override_reason is not None:
            raise ValueError("override_reason is only valid for an applied override")
        if self.selection_id is not None and self.selection_id != authority_mode_selection_identity(
            self
        ):
            raise ValueError("selection_id does not match authority mode selection material")
        return self


def authority_policy_profile_identity(value: AuthorityPolicyProfile) -> str:
    return model_identity(
        value,
        domain="qst:authority-policy-profile:v1",
        identity_field="profile_hash",
    )


def authority_mode_selection_identity(value: AuthorityModeSelection) -> str:
    return model_identity(
        value,
        domain="qst:authority-mode-selection:v1",
        identity_field="selection_id",
    )


def seal_authority_policy_profile(value: AuthorityPolicyProfile) -> AuthorityPolicyProfile:
    return AuthorityPolicyProfile.model_validate(
        {
            **value.model_dump(mode="json", exclude={"profile_hash"}),
            "profile_hash": authority_policy_profile_identity(value),
        }
    )


def seal_authority_mode_selection(value: AuthorityModeSelection) -> AuthorityModeSelection:
    return AuthorityModeSelection.model_validate(
        {
            **value.model_dump(mode="json", exclude={"selection_id"}),
            "selection_id": authority_mode_selection_identity(value),
        }
    )


def select_authority_mode(
    use_case: AuthorityUseCase,
    *,
    profile: AuthorityPolicyProfile | None = None,
    mode_override: AuthorityMode | None = None,
    override_reason: str | None = None,
) -> AuthorityModeSelection:
    """Resolve a profile deterministically and retain any explicit override rationale."""

    profile = record_capture_profile() if profile is None else profile
    if (
        profile.profile_hash is None
        or profile.profile_hash != authority_policy_profile_identity(profile)
    ):
        raise ValueError("authority policy profile must be sealed and untampered")
    configured = profile.mode_for(use_case)
    effective = configured if mode_override is None else mode_override
    reason = override_reason.strip() if override_reason is not None else None
    if effective == configured:
        reason = None
    return seal_authority_mode_selection(
        AuthorityModeSelection(
            profile_hash=profile.profile_hash,
            profile_id=profile.profile_id,
            use_case=use_case,
            configured_mode=configured,
            effective_mode=effective,
            override_applied=effective != configured,
            override_reason=reason,
        )
    )


@lru_cache(maxsize=1)
def record_capture_profile() -> AuthorityPolicyProfile:
    return _profile(
        "record-capture",
        "Non-blocking ingestion and exploratory record capture.",
        {use_case: "record_only" for use_case in AUTHORITY_USE_CASES},
    )


@lru_cache(maxsize=1)
def research_advisory_profile() -> AuthorityPolicyProfile:
    return _profile(
        "research-advisory",
        "Non-blocking research checks with strict publication and activation boundaries.",
        {
            "record_ingestion": "record_only",
            "migration_import": "record_only",
            "claim_evaluation": "advisory",
            "token_review": "advisory",
            "token_publication": "enforce",
            "token_activation": "enforce",
            "customization": "advisory",
        },
    )


@lru_cache(maxsize=1)
def controlled_release_profile() -> AuthorityPolicyProfile:
    return _profile(
        "controlled-release",
        "Advisory review with enforced publication, activation, and customization.",
        {
            "record_ingestion": "record_only",
            "migration_import": "record_only",
            "claim_evaluation": "advisory",
            "token_review": "advisory",
            "token_publication": "enforce",
            "token_activation": "enforce",
            "customization": "enforce",
        },
    )


@lru_cache(maxsize=1)
def strict_governance_profile() -> AuthorityPolicyProfile:
    return _profile(
        "strict-governance",
        "Enforce authority for every governed use case.",
        {use_case: "enforce" for use_case in AUTHORITY_USE_CASES},
    )


def _profile(
    profile_id: str,
    description: str,
    modes: dict[AuthorityUseCase, AuthorityMode],
) -> AuthorityPolicyProfile:
    return seal_authority_policy_profile(
        AuthorityPolicyProfile(
            profile_id=profile_id,
            version=1,
            description=description,
            rules=tuple(
                AuthorityPolicyRule(use_case=use_case, mode=mode)
                for use_case, mode in modes.items()
            ),
        )
    )
