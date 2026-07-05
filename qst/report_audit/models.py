"""Typed provenance for agent-produced financial research reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance.time import normalize_utc

SECRET_KEYS = {
    "access_token",
    "api_key",
    "api_secret",
    "auth_token",
    "bearer_token",
    "password",
    "private_key",
    "refresh_token",
    "secret",
}


def _reject_secret_material(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in SECRET_KEYS or lowered.endswith(("_password", "_secret")):
                raise ValueError("report provenance must not contain secret-bearing fields")
            _reject_secret_material(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_secret_material(item)
    elif isinstance(value, str) and value.startswith(("sk-", "ghp_", "github_pat_")):
        raise ValueError("report provenance must not contain credential-like values")


class ReportSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_ref: str = Field(min_length=1)
    status: Literal["verified", "missing", "failed"]
    ticker: str | None = None
    report_period: str | None = None
    url: str | None = None
    artifact_id: HashString | None = None


class ReportToolInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(min_length=1)
    normalized_parameters: dict[str, Any]
    status: Literal["success", "failed"]
    input_artifact_ids: tuple[HashString, ...] = ()
    output_artifact_ids: tuple[HashString, ...] = ()
    output_paths: tuple[str, ...] = ()
    error_code: str | None = None
    retry_count: int = Field(default=0, ge=0)
    fallback_used: bool = False
    truncated: bool = False

    @field_validator("normalized_parameters", mode="after")
    @classmethod
    def _json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        _reject_secret_material(value)
        return dict(sorted(value.items()))

    @field_validator("input_artifact_ids", "output_artifact_ids", "output_paths", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


class ReportSectionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    section_id: str = Field(min_length=1)
    evidence_ids: tuple[HashString, ...]

    @field_validator("evidence_ids", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


class FinancialReportProvenance(BaseModel):
    """A report draft provenance record; it never publishes or approves the report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-financial-report-provenance/1.0"] = (
        "qst-financial-report-provenance/1.0"
    )
    provenance_id: HashString | None = None
    run_id: str = Field(min_length=1)
    recorded_at: datetime
    agent_name: str = Field(min_length=1)
    agent_role: str = Field(min_length=1)
    task_summary: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prompt_ref: str = Field(min_length=1)
    expected_ticker: str | None = None
    expected_report_period: str | None = None
    sources: tuple[ReportSourceRecord, ...]
    tool_invocations: tuple[ReportToolInvocation, ...]
    report_sections: tuple[ReportSectionEvidence, ...]
    output_artifact_ids: tuple[HashString, ...]
    valuation_assumptions: dict[str, Any] = Field(default_factory=dict)
    changed_assumptions: tuple[str, ...] = ()
    assumption_change_reasons: dict[str, str] = Field(default_factory=dict)
    draft_for_human_review: bool = True

    @field_validator("recorded_at", mode="after")
    @classmethod
    def _normalize_time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @field_validator("output_artifact_ids", "changed_assumptions", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("valuation_assumptions", mode="after")
    @classmethod
    def _assumptions_json(cls, value: dict[str, Any]) -> dict[str, Any]:
        stable_json_bytes(value)
        return dict(sorted(value.items()))

    @field_validator("assumption_change_reasons", mode="after")
    @classmethod
    def _reasons(cls, value: dict[str, str]) -> dict[str, str]:
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def _identity(self) -> FinancialReportProvenance:
        if self.provenance_id is not None and self.provenance_id != report_provenance_identity(self):
            raise ValueError("provenance_id does not match report provenance material")
        return self


class ReportReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-financial-report-review/1.0"] = (
        "qst-financial-report-review/1.0"
    )
    ready_for_human_review: bool
    provenance_id: HashString | None
    issue_codes: tuple[str, ...]

    @field_validator("issue_codes", mode="after")
    @classmethod
    def _sort_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


def report_provenance_identity(value: FinancialReportProvenance) -> str:
    return model_identity(
        value, domain="qst:financial-report-provenance:v1", identity_field="provenance_id"
    )


def seal_report_provenance(value: FinancialReportProvenance) -> FinancialReportProvenance:
    return FinancialReportProvenance.model_validate(
        {
            **value.model_dump(mode="json", exclude={"provenance_id"}),
            "provenance_id": report_provenance_identity(value),
        }
    )
