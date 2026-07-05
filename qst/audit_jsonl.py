"""Hash-chained JSONL export for audit-friendly record references."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.identity import identity_hash

MAX_AUDIT_LINE_BYTES = 64 * 1024
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


class AuditExportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_type: str = Field(min_length=1)
    record_ref: HashString
    artifact_refs: tuple[HashString, ...] = ()
    summary: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("artifact_refs", mode="after")
    @classmethod
    def _sort_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("summary", mode="after")
    @classmethod
    def _safe_summary(
        cls, value: dict[str, str | int | float | bool | None]
    ) -> dict[str, str | int | float | bool | None]:
        _reject_secrets(value)
        return dict(sorted(value.items()))


class AuditChainLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-audit-jsonl/1.0"] = "qst-audit-jsonl/1.0"
    sequence: int = Field(ge=1)
    previous_hash: HashString | None = None
    record: AuditExportRecord
    line_hash: HashString | None = None


class AuditVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    line_count: int
    last_hash: HashString | None = None
    issue_codes: tuple[str, ...] = ()


def audit_line_identity(value: AuditChainLine) -> str:
    return identity_hash(
        "qst:audit-jsonl-line:v1",
        value.model_dump(mode="json", exclude={"line_hash"}),
    )


def append_audit_record(path: Path, record: AuditExportRecord) -> AuditChainLine:
    """Append one canonical line while enforcing a single local writer."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError("audit JSONL already has an active writer") from exc
    os.close(descriptor)
    try:
        verification = verify_audit_jsonl(path)
        if not verification.valid:
            raise ValueError("cannot append to an invalid audit JSONL chain")
        line = AuditChainLine(
            sequence=verification.line_count + 1,
            previous_hash=verification.last_hash,
            record=record,
        )
        line = line.model_copy(update={"line_hash": audit_line_identity(line)})
        payload = stable_json_bytes(line.model_dump(mode="json")) + b"\n"
        if len(payload) > MAX_AUDIT_LINE_BYTES:
            raise ValueError("audit JSONL line exceeds 64 KiB")
        with path.open("ab") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return line
    finally:
        lock.unlink(missing_ok=True)


def verify_audit_jsonl(path: Path) -> AuditVerification:
    if not path.exists():
        return AuditVerification(valid=True, line_count=0)
    issues: list[str] = []
    previous: str | None = None
    count = 0
    try:
        raw_lines = path.read_bytes().splitlines(keepends=True)
    except OSError:
        return AuditVerification(valid=False, line_count=0, issue_codes=("QST_AUDIT_READ_FAILED",))
    for expected_sequence, raw in enumerate(raw_lines, start=1):
        if not raw.endswith(b"\n"):
            issues.append("QST_AUDIT_TRUNCATED_LINE")
            break
        if len(raw) > MAX_AUDIT_LINE_BYTES:
            issues.append("QST_AUDIT_LINE_TOO_LARGE")
            break
        try:
            value = AuditChainLine.model_validate(json.loads(raw))
        except (ValueError, json.JSONDecodeError):
            issues.append("QST_AUDIT_INVALID_LINE")
            break
        if value.sequence != expected_sequence:
            issues.append("QST_AUDIT_SEQUENCE_MISMATCH")
        if value.previous_hash != previous:
            issues.append("QST_AUDIT_PREVIOUS_HASH_MISMATCH")
        if value.line_hash != audit_line_identity(value):
            issues.append("QST_AUDIT_LINE_HASH_MISMATCH")
        count += 1
        previous = value.line_hash
    return AuditVerification(
        valid=not issues,
        line_count=count,
        last_hash=previous,
        issue_codes=tuple(sorted(dict.fromkeys(issues))),
    )


def _reject_secrets(value: dict[str, Any]) -> None:
    for key, item in value.items():
        lowered = key.lower().replace("-", "_")
        if lowered in SECRET_KEYS or lowered.endswith(("_password", "_secret")):
            raise ValueError("audit summaries must not contain secret-bearing keys")
        if isinstance(item, str) and item.startswith(("sk-", "ghp_", "github_pat_")):
            raise ValueError("audit summaries must not contain credential-like values")
