"""Claim policies and immutable policy decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance.time import normalize_utc

ClaimType = Literal[
    "strategy_validated",
    "experiment_completed",
    "backtested",
    "agent_recommended",
    "token_contract_approved",
    "token_implementation_approved",
    "token_publication_approved",
    "token_activation_approved",
]


class EvidenceRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    payload_kind: str
    minimum_count: int = Field(default=1, ge=1)
    require_verified_result: bool = False
    minimum_adapter_maturity: Literal["L0", "L1", "L2", "L3", "L4"] = "L0"


class ClaimPolicy(BaseModel):
    """Hash-bearing declaration of evidence required for a claim."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-claim-policy/1.0"] = "qst-claim-policy/1.0"
    policy_hash: HashString | None = None
    policy_id: str
    policy_version: int = Field(ge=1)
    claim_type: ClaimType
    requirements: tuple[EvidenceRequirement, ...]
    allow_warnings: bool = False

    @field_validator("requirements", mode="after")
    @classmethod
    def _sort_requirements(
        cls, value: tuple[EvidenceRequirement, ...]
    ) -> tuple[EvidenceRequirement, ...]:
        return tuple(
            sorted(
                value,
                key=lambda item: (
                    item.payload_kind,
                    item.minimum_count,
                    item.require_verified_result,
                    item.minimum_adapter_maturity,
                ),
            )
        )

    @model_validator(mode="after")
    def _validate_policy(self) -> ClaimPolicy:
        if not self.requirements:
            raise ValueError("claim policy requires evidence requirements")
        if self.policy_hash is not None and self.policy_hash != claim_policy_identity(self):
            raise ValueError("policy_hash does not match policy material")
        return self


class ClaimDecision(BaseModel):
    """A policy result; it cannot serve as evidence or an approval grant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-claim-decision/1.0"] = "qst-claim-decision/1.0"
    decision_id: HashString | None = None
    claim_type: ClaimType
    subject_ref: str
    policy_hash: HashString
    allowed: bool
    evidence_ids: tuple[HashString, ...]
    attestation_ids: tuple[HashString, ...] = ()
    reason_codes: tuple[str, ...]
    evaluated_at: datetime

    @field_validator("evidence_ids", "attestation_ids", "reason_codes", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("evaluated_at", mode="after")
    @classmethod
    def _normalize_time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_decision(self) -> ClaimDecision:
        if not self.reason_codes:
            raise ValueError("claim decision requires reason_codes")
        if self.decision_id is not None and self.decision_id != claim_decision_identity(self):
            raise ValueError("decision_id does not match decision material")
        return self


def claim_policy_identity(value: ClaimPolicy) -> str:
    return model_identity(value, domain="qst:claim-policy:v1", identity_field="policy_hash")


def claim_decision_identity(value: ClaimDecision) -> str:
    return model_identity(value, domain="qst:claim-decision:v1", identity_field="decision_id")


def seal_claim_policy(value: ClaimPolicy) -> ClaimPolicy:
    return ClaimPolicy.model_validate(
        {
            **value.model_dump(mode="json", exclude={"policy_hash"}),
            "policy_hash": claim_policy_identity(value),
        }
    )


def seal_claim_decision(value: ClaimDecision) -> ClaimDecision:
    return ClaimDecision.model_validate(
        {
            **value.model_dump(mode="json", exclude={"decision_id"}),
            "decision_id": claim_decision_identity(value),
        }
    )
