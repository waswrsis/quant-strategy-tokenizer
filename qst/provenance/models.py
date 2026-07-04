"""Immutable provenance entities for QST 1.0 evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance.time import normalize_utc

ActorKind = Literal["human", "agent", "system", "organization"]
ActivityStatus = Literal[
    "discovered",
    "collecting",
    "partial",
    "complete",
    "verified",
    "failed",
]


def _json_mapping(value: dict[str, Any], *, field_name: str) -> dict[str, Any]:
    try:
        stable_json_bytes(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be canonical JSON-compatible") from exc
    return value


class ActorDescriptor(BaseModel):
    """A human, agent, system, or organization involved in provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-actor/1.0"] = "qst-actor/1.0"
    actor_id: HashString | None = None
    kind: ActorKind
    name: str = Field(min_length=1)
    version: str | None = None
    model_id: str | None = None
    tool_ids: tuple[str, ...] = ()
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tool_ids", mode="after")
    @classmethod
    def _sort_tools(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("attributes", mode="after")
    @classmethod
    def _validate_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _json_mapping(value, field_name="actor attributes")

    @model_validator(mode="after")
    def _verify_identity(self) -> ActorDescriptor:
        if self.actor_id is not None and self.actor_id != actor_identity(self):
            raise ValueError("actor_id does not match actor material")
        return self


class ArtifactDescriptor(BaseModel):
    """Content-addressed descriptor for an opaque external artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-artifact-descriptor/1.0"] = "qst-artifact-descriptor/1.0"
    descriptor_id: HashString | None = None
    media_type: str = Field(min_length=1)
    digest: HashString
    size: int = Field(ge=0)
    uris: tuple[str, ...] = ()
    producer_activity_id: HashString | None = None
    normalized_digest: HashString | None = None
    normalization: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("uris", mode="after")
    @classmethod
    def _sort_uris(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("attributes", mode="after")
    @classmethod
    def _validate_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _json_mapping(value, field_name="artifact attributes")

    @model_validator(mode="after")
    def _validate_descriptor(self) -> ArtifactDescriptor:
        if (self.normalized_digest is None) != (self.normalization is None):
            raise ValueError("normalized_digest and normalization must be declared together")
        if self.descriptor_id is not None and self.descriptor_id != artifact_identity(self):
            raise ValueError("descriptor_id does not match artifact material")
        return self


class ActivityRecord(BaseModel):
    """Immutable snapshot of an external or QST-side activity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-activity/1.0"] = "qst-activity/1.0"
    activity_id: HashString | None = None
    activity_type: str = Field(min_length=1)
    status: ActivityStatus
    actor_ids: tuple[HashString, ...] = ()
    input_artifact_ids: tuple[HashString, ...] = ()
    output_artifact_ids: tuple[HashString, ...] = ()
    previous_activity_id: HashString | None = None
    external_run_ref: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "actor_ids", "input_artifact_ids", "output_artifact_ids", mode="after"
    )
    @classmethod
    def _sort_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("started_at", "ended_at", mode="after")
    @classmethod
    def _normalize_time(cls, value: datetime | None) -> datetime | None:
        return None if value is None else normalize_utc(value)

    @field_validator("attributes", mode="after")
    @classmethod
    def _validate_attributes(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _json_mapping(value, field_name="activity attributes")

    @model_validator(mode="after")
    def _validate_activity(self) -> ActivityRecord:
        if self.started_at is not None and self.ended_at is not None:
            if self.ended_at < self.started_at:
                raise ValueError("ended_at cannot precede started_at")
        if self.status == "verified" and self.ended_at is None:
            raise ValueError("verified activity requires ended_at")
        if self.status == "verified" and not self.output_artifact_ids:
            raise ValueError("verified activity requires output artifacts")
        if self.activity_id is not None and self.activity_id != activity_identity(self):
            raise ValueError("activity_id does not match activity material")
        return self


def actor_identity(value: ActorDescriptor) -> str:
    return model_identity(value, domain="qst:actor:v1", identity_field="actor_id")


def artifact_identity(value: ArtifactDescriptor) -> str:
    return model_identity(value, domain="qst:artifact:v1", identity_field="descriptor_id")


def activity_identity(value: ActivityRecord) -> str:
    return model_identity(value, domain="qst:activity:v1", identity_field="activity_id")


def seal_actor(value: ActorDescriptor) -> ActorDescriptor:
    return ActorDescriptor.model_validate(
        {**value.model_dump(mode="json", exclude={"actor_id"}), "actor_id": actor_identity(value)}
    )


def seal_artifact(value: ArtifactDescriptor) -> ArtifactDescriptor:
    return ArtifactDescriptor.model_validate(
        {
            **value.model_dump(mode="json", exclude={"descriptor_id"}),
            "descriptor_id": artifact_identity(value),
        }
    )


def seal_activity(value: ActivityRecord) -> ActivityRecord:
    return ActivityRecord.model_validate(
        {
            **value.model_dump(mode="json", exclude={"activity_id"}),
            "activity_id": activity_identity(value),
        }
    )
