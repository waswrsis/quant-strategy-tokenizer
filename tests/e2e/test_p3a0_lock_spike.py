from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.qst_lock.io import read_lock

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
runner = CliRunner()


def test_qst_lock_and_verify_roundtrip(tmp_path: Path) -> None:
    lock_path = tmp_path / "qst.lock"
    canonical_path = tmp_path / "qst.canonical.json"

    first = runner.invoke(
        app,
        [
            "lock",
            str(STRATEGY),
            "--output",
            str(lock_path),
            "--canonical-output",
            str(canonical_path),
        ],
    )
    assert first.exit_code == 0, first.output
    first_bytes = lock_path.read_bytes()

    second = runner.invoke(
        app,
        [
            "lock",
            str(STRATEGY),
            "--output",
            str(lock_path),
            "--canonical-output",
            str(canonical_path),
        ],
    )
    assert second.exit_code == 0, second.output
    assert lock_path.read_bytes() == first_bytes
    assert read_lock(lock_path).canonical_ir_hash.startswith("sha256:")

    verified = runner.invoke(
        app,
        [
            "verify",
            str(STRATEGY),
            "--lock",
            str(lock_path),
            "--canonical",
            str(canonical_path),
        ],
    )
    assert verified.exit_code == 0, verified.output
    payload = json.loads(verified.output)
    assert payload["ok"] is True
    assert payload["verification_level"] == "STRUCTURAL"
    assert payload["failures"] == []


def test_qst_verify_reports_structured_failure(tmp_path: Path) -> None:
    lock_path = tmp_path / "qst.lock"
    canonical_path = tmp_path / "qst.canonical.json"
    result = runner.invoke(
        app,
        [
            "lock",
            str(STRATEGY),
            "--output",
            str(lock_path),
            "--canonical-output",
            str(canonical_path),
        ],
    )
    assert result.exit_code == 0, result.output
    raw = json.loads(lock_path.read_text(encoding="utf-8"))
    raw["strategy_hashes"]["instance_hash"] = "sha256:" + ("0" * 64)
    lock_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    verified = runner.invoke(
        app,
        [
            "verify",
            str(STRATEGY),
            "--lock",
            str(lock_path),
            "--canonical",
            str(canonical_path),
        ],
    )

    assert verified.exit_code == 1
    payload = json.loads(verified.output)
    assert payload["ok"] is False
    assert any(failure["kind"] == "instance_hash_mismatch" for failure in payload["failures"])
