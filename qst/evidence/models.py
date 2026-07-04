"""Typed evidence envelopes for QST 1.0."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance.time import normalize_utc


class PlanEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["plan"] = "plan"
    adapter_id: str
    source_ref: str
    planned_activity_types: tuple[str, ...]
    configuration_artifact_ids: tuple[HashString, ...] = ()

    @field_validator("planned_activity_types", "configuration_artifact_ids", mode="after")
    @classmethod
    def _sort_plan_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


class ResultEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["result"] = "result"
    activity_id: HashString
    collection_status: Literal["partial", "complete", "verified", "failed"]
    artifact_ids: tuple[HashString, ...] = ()
    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)

    @field_validator("artifact_ids", mode="after")
    @classmethod
    def _sort_artifacts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("metrics", mode="after")
    @classmethod
    def _validate_metrics(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value


class AgentActionEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["agent_action"] = "agent_action"
    actor_id: HashString
    action_type: str
    tool_id: str | None = None
    prompt_ref: str | None = None
    input_artifact_ids: tuple[HashString, ...] = ()
    output_artifact_ids: tuple[HashString, ...] = ()

    @field_validator("input_artifact_ids", "output_artifact_ids", mode="after")
    @classmethod
    def _sort_action_artifacts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


class ExternalRecordEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["external_record"] = "external_record"
    adapter_id: str
    record_type: str
    record_schema: str
    record: dict[str, Any]

    @field_validator("record", mode="after")
    @classmethod
    def _validate_record(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value


EvidencePayload = Annotated[
    PlanEvidencePayload
    | ResultEvidencePayload
    | AgentActionEvidencePayload
    | ExternalRecordEvidencePayload,
    Field(discriminator="kind"),
]


class EvidenceEnvelope(BaseModel):
    """An immutable observation; it does not approve a claim."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-evidence/1.0"] = "qst-evidence/1.0"
    evidence_id: HashString | None = None
    subject_ref: str
    observed_at: datetime
    source_actor_id: HashString | None = None
    source_activity_id: HashString | None = None
    parent_evidence_ids: tuple[HashString, ...] = ()
    payload: EvidencePayload

    @field_validator("observed_at", mode="after")
    @classmethod
    def _normalize_time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @field_validator("parent_evidence_ids", mode="after")
    @classmethod
    def _sort_parents(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @model_validator(mode="after")
    def _verify_identity(self) -> EvidenceEnvelope:
        if self.evidence_id is not None and self.evidence_id != evidence_identity(self):
            raise ValueError("evidence_id does not match evidence material")
        return self


def evidence_identity(value: EvidenceEnvelope) -> str:
    return model_identity(value, domain="qst:evidence:v1", identity_field="evidence_id")


def seal_evidence(value: EvidenceEnvelope) -> EvidenceEnvelope:
    return EvidenceEnvelope.model_validate(
        {
            **value.model_dump(mode="json", exclude={"evidence_id"}),
            "evidence_id": evidence_identity(value),
        }
    )
