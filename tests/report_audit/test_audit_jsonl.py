from __future__ import annotations

from pathlib import Path

import pytest

from qst.audit_jsonl import (
    AuditExportRecord,
    append_audit_record,
    verify_audit_jsonl,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def test_jsonl_export_is_append_only_and_hash_chained(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    first = append_audit_record(
        path,
        AuditExportRecord(record_type="strategy_receipt", record_ref=HASH_A),
    )
    second = append_audit_record(
        path,
        AuditExportRecord(
            record_type="experiment_receipt",
            record_ref=HASH_B,
            artifact_refs=(HASH_A,),
            summary={"status": "verified"},
        ),
    )
    result = verify_audit_jsonl(path)
    assert result.valid
    assert result.line_count == 2
    assert second.previous_hash == first.line_hash


@pytest.mark.parametrize("mutation", ["tamper", "truncate", "reorder"])
def test_jsonl_verifier_rejects_chain_corruption(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "audit.jsonl"
    append_audit_record(path, AuditExportRecord(record_type="first", record_ref=HASH_A))
    append_audit_record(path, AuditExportRecord(record_type="second", record_ref=HASH_B))
    lines = path.read_bytes().splitlines(keepends=True)
    if mutation == "tamper":
        lines[0] = lines[0].replace(b'"first"', b'"other"')
    elif mutation == "truncate":
        lines[-1] = lines[-1][:-1]
    else:
        lines.reverse()
    path.write_bytes(b"".join(lines))
    assert not verify_audit_jsonl(path).valid


def test_jsonl_export_rejects_secret_bearing_summary() -> None:
    with pytest.raises(ValueError, match="secret-bearing"):
        AuditExportRecord(
            record_type="unsafe",
            record_ref=HASH_A,
            summary={"api_key": "redacted"},
        )
    record = AuditExportRecord(
        record_type="token_resolution",
        record_ref=HASH_A,
        summary={"token_ref": "core.math.add/v1/bv1"},
    )
    assert record.summary["token_ref"] == "core.math.add/v1/bv1"
