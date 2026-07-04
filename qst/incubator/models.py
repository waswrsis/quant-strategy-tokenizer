"""Governed token-gap and project-local token proposal records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance import normalize_utc

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
ActorKind = Literal["human", "agent", "system"]
ReviewKind = Literal["contract", "implementation", "publication", "activation"]


class TokenGapEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-token-gap-evidence/1.0"] = "qst-token-gap-evidence/1.0"
    gap_id: HashString | None = None
    resolution_hash: HashString
    intent_hash: HashString
    detected_by_actor_id: HashString
    concept: str
    reason_codes: tuple[str, ...]
    missing_builtin_surface: tuple[str, ...]
    input_ports: dict[str, Any]
    output_ports: dict[str, Any]
    detected_at: datetime

    @field_validator("reason_codes", "missing_builtin_surface", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("gap evidence requires non-empty reasons and missing surface")
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("input_ports", "output_ports", mode="after")
    @classmethod
    def _validate_ports(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value

    @field_validator("detected_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _identity(self) -> TokenGapEvidence:
        if self.gap_id is not None and self.gap_id != token_gap_identity(self):
            raise ValueError("gap_id does not match gap material")
        return self


class TokenDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-token-draft/1.0"] = "qst-token-draft/1.0"
    token_id: str
    namespace: str
    authored_by_actor_id: HashString
    requested_by_actor_id: HashString
    contract: dict[str, Any]
    maturity: Literal["experimental"] = "experimental"
    execution_support: Literal["metadata_only", "reference_helper"] = "metadata_only"

    @field_validator("contract", mode="after")
    @classmethod
    def _contract(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value

    @model_validator(mode="after")
    def _local_namespace(self) -> TokenDraft:
        if self.namespace == "core" or not self.namespace.startswith("project."):
            raise ValueError("draft namespace must start with project. and cannot be core")
        if not self.token_id.startswith(f"{self.namespace}."):
            raise ValueError("token_id must be qualified by draft namespace")
        return self


class ActivationDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    token_spec_hash: HashString
    token_pack_lock_hash: HashString
    profile: str
    namespace: str
    implementation_ref_hash: HashString | None = None
    execution_support: Literal["metadata_only", "reference_helper"] = "metadata_only"


class ProposalTransition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transition_id: HashString | None = None
    from_status: ProposalStatus
    to_status: ProposalStatus
    actor_id: HashString
    actor_kind: ActorKind
    review_kind: ReviewKind | None = None
    approved: bool | None = None
    evidence_ids: tuple[HashString, ...] = ()
    checklist: tuple[str, ...]
    reason_codes: tuple[str, ...]
    occurred_at: datetime
    activation: ActivationDescriptor | None = None

    @field_validator("evidence_ids", "checklist", "reason_codes", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("occurred_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_transition(self) -> ProposalTransition:
        _validate_transition_gate(self)
        if self.transition_id is not None and self.transition_id != transition_identity(self):
            raise ValueError("transition_id does not match transition material")
        return self


class TokenProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-token-proposal/1.0"] = "qst-token-proposal/1.0"
    proposal_id: HashString | None = None
    gap_id: HashString
    draft: TokenDraft
    status: ProposalStatus = "detected"
    transitions: tuple[ProposalTransition, ...] = ()

    @model_validator(mode="after")
    def _validate_history(self) -> TokenProposal:
        current: ProposalStatus = "detected"
        for transition in self.transitions:
            if transition.transition_id is None:
                raise ValueError("proposal transitions must be sealed")
            if transition.transition_id != transition_identity(transition):
                raise ValueError("transition_id does not match transition material")
            if transition.from_status != current:
                raise ValueError("proposal transition history is discontinuous")
            current = transition.to_status
        if current != self.status:
            raise ValueError("proposal status does not match transition history")
        if self.proposal_id is not None and self.proposal_id != token_proposal_identity(self):
            raise ValueError("proposal_id does not match proposal material")
        return self


ALLOWED_NEXT: dict[ProposalStatus, frozenset[ProposalStatus]] = {
    "detected": frozenset({"agent_draft", "rejected"}),
    "agent_draft": frozenset({"statically_validated", "rejected"}),
    "statically_validated": frozenset({"contract_approved", "rejected"}),
    "contract_approved": frozenset({"implementation_reviewed", "rejected"}),
    "implementation_reviewed": frozenset({"conformance_passed", "rejected"}),
    "conformance_passed": frozenset({"publication_approved", "rejected"}),
    "publication_approved": frozenset({"published_project_local", "rejected"}),
    "published_project_local": frozenset({"explicit_activation_requested", "builtin_candidate"}),
    "explicit_activation_requested": frozenset({"activation_approved", "rejected"}),
    "activation_approved": frozenset({"active_for_project", "rejected"}),
    "active_for_project": frozenset({"builtin_candidate"}),
    "builtin_candidate": frozenset(),
    "rejected": frozenset(),
}

HUMAN_REVIEW_TARGETS: dict[ProposalStatus, ReviewKind] = {
    "contract_approved": "contract",
    "implementation_reviewed": "implementation",
    "publication_approved": "publication",
    "activation_approved": "activation",
}
HUMAN_ACTION_TARGETS = {
    "published_project_local",
    "explicit_activation_requested",
    "active_for_project",
    "builtin_candidate",
}
SYSTEM_TARGETS = {"statically_validated", "conformance_passed"}
EVIDENCE_TARGETS = {
    "statically_validated",
    "contract_approved",
    "implementation_reviewed",
    "conformance_passed",
    "publication_approved",
    "activation_approved",
    "active_for_project",
}
REQUIRED_CHECKS: dict[ProposalStatus, frozenset[str]] = {
    "statically_validated": frozenset({"schema", "namespace", "ports", "params", "boundary"}),
    "contract_approved": frozenset({"semantics", "failure_modes", "numeric", "temporal"}),
    "implementation_reviewed": frozenset({"source_digest", "security", "determinism"}),
    "conformance_passed": frozenset({"unit_tests", "property_tests", "edge_cases"}),
    "publication_approved": frozenset({"documentation", "versioning", "ownership"}),
    "activation_approved": frozenset({"project_scope", "profile", "lock"}),
    "active_for_project": frozenset({"token_pack_lock", "profile", "namespace"}),
}


def _validate_transition_gate(value: ProposalTransition) -> None:
    if value.to_status not in ALLOWED_NEXT[value.from_status]:
        raise ValueError(f"invalid proposal transition {value.from_status} -> {value.to_status}")
    if not value.checklist or not value.reason_codes:
        raise ValueError("transition requires checklist and reason_codes")
    required_checks = REQUIRED_CHECKS.get(value.to_status, frozenset())
    missing_checks = sorted(required_checks - set(value.checklist))
    if missing_checks:
        raise ValueError(f"{value.to_status} missing checks: {', '.join(missing_checks)}")
    if value.to_status in SYSTEM_TARGETS and value.actor_kind != "system":
        raise ValueError(f"{value.to_status} requires system validation evidence")
    if value.to_status in EVIDENCE_TARGETS and not value.evidence_ids:
        raise ValueError(f"{value.to_status} requires evidence_ids")
    review_kind = HUMAN_REVIEW_TARGETS.get(value.to_status)
    if review_kind is not None:
        if value.actor_kind != "human" or value.review_kind != review_kind or value.approved is not True:
            raise ValueError(f"{value.to_status} requires approved human {review_kind} review")
    if value.to_status in HUMAN_ACTION_TARGETS and value.actor_kind != "human":
        raise ValueError(f"{value.to_status} requires explicit human action")
    if value.to_status == "active_for_project" and value.activation is None:
        raise ValueError("active_for_project requires activation descriptor")
    if value.to_status != "active_for_project" and value.activation is not None:
        raise ValueError("activation descriptor is only valid for active_for_project")


def token_gap_identity(value: TokenGapEvidence) -> str:
    return model_identity(value, domain="qst:token-gap:v1", identity_field="gap_id")


def transition_identity(value: ProposalTransition) -> str:
    return model_identity(value, domain="qst:proposal-transition:v1", identity_field="transition_id")


def token_proposal_identity(value: TokenProposal) -> str:
    return model_identity(value, domain="qst:token-proposal:v1", identity_field="proposal_id")


def seal_gap(value: TokenGapEvidence) -> TokenGapEvidence:
    return TokenGapEvidence.model_validate(
        {**value.model_dump(mode="json", exclude={"gap_id"}), "gap_id": token_gap_identity(value)}
    )


def seal_transition(value: ProposalTransition) -> ProposalTransition:
    return ProposalTransition.model_validate(
        {
            **value.model_dump(mode="json", exclude={"transition_id"}),
            "transition_id": transition_identity(value),
        }
    )


def create_proposal(gap: TokenGapEvidence, draft: TokenDraft) -> TokenProposal:
    if gap.gap_id is None:
        raise ValueError("gap must be sealed")
    if gap.gap_id != token_gap_identity(gap):
        raise ValueError("gap_id does not match gap material")
    value = TokenProposal(gap_id=gap.gap_id, draft=draft)
    return TokenProposal.model_validate(
        {
            **value.model_dump(mode="json", exclude={"proposal_id"}),
            "proposal_id": token_proposal_identity(value),
        }
    )


def apply_transition(value: TokenProposal, transition: ProposalTransition) -> TokenProposal:
    if value.proposal_id is None:
        raise ValueError("current proposal must be sealed")
    if value.proposal_id != token_proposal_identity(value):
        raise ValueError("proposal_id does not match proposal material")
    if transition.transition_id is None:
        transition = seal_transition(transition)
    elif transition.transition_id != transition_identity(transition):
        raise ValueError("transition_id does not match transition material")
    if transition.from_status != value.status:
        raise ValueError("transition does not start at current proposal status")
    updated = TokenProposal(
        gap_id=value.gap_id,
        draft=value.draft,
        status=transition.to_status,
        transitions=(*value.transitions, transition),
    )
    return TokenProposal.model_validate(
        {
            **updated.model_dump(mode="json", exclude={"proposal_id"}),
            "proposal_id": token_proposal_identity(updated),
        }
    )
