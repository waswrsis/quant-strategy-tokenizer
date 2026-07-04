"""Attestations bind an issuer statement to existing evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance.time import normalize_utc


class Attestation(BaseModel):
    """An issuer statement, not a claim-policy decision or execution grant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-attestation/1.0"] = "qst-attestation/1.0"
    attestation_id: HashString | None = None
    issuer_actor_id: HashString
    subject_evidence_ids: tuple[HashString, ...]
    predicate_type: str = Field(min_length=1)
    statement: dict[str, Any]
    issued_at: datetime
    signature_artifact_id: HashString | None = None

    @field_validator("subject_evidence_ids", mode="after")
    @classmethod
    def _sort_subjects(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("attestation requires at least one evidence subject")
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("statement", mode="after")
    @classmethod
    def _validate_statement(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return value

    @field_validator("issued_at", mode="after")
    @classmethod
    def _normalize_time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _verify_identity(self) -> Attestation:
        if self.attestation_id is not None and self.attestation_id != attestation_identity(self):
            raise ValueError("attestation_id does not match attestation material")
        return self


def attestation_identity(value: Attestation) -> str:
    return model_identity(
        value,
        domain="qst:attestation:v1",
        identity_field="attestation_id",
    )


def seal_attestation(value: Attestation) -> Attestation:
    return Attestation.model_validate(
        {
            **value.model_dump(mode="json", exclude={"attestation_id"}),
            "attestation_id": attestation_identity(value),
        }
    )
