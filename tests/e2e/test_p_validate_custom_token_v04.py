from __future__ import annotations

import json
from pathlib import Path

from quant_strategy_tokenizer.custom_runtime_v2.p_validate import (
    diagnostics_custom_pv_d_v04,
    load_custom_pv_d_fixture,
    trace_custom_pv_d_v04,
)
from quant_strategy_tokenizer.hash_v2 import expected_artifact_hash_v2
from quant_strategy_tokenizer.ir_v04.loader import load_ir_v04_file
from quant_strategy_tokenizer.ir_v04.validator import validate_ir_v04

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "v04" / "p_validate" / "custom_token_kalman.qst.yaml"
FIXTURE_DIR = ROOT / "fixtures" / "v04" / "p_validate" / "custom_token"
TRACE_DIR = ROOT / "expected_traces" / "v04" / "p_validate" / "custom_token"
DIAG_DIR = ROOT / "expected_diagnostics" / "v04" / "p_validate" / "custom_token"
CASES = ("research", "pretrade_default", "pretrade_approved")


def test_pv_d_custom_token_expected_artifacts() -> None:
    ir = load_ir_v04_file(STRATEGY)

    assert validate_ir_v04(ir).ok

    for case in CASES:
        fixture = load_custom_pv_d_fixture(FIXTURE_DIR / f"custom_token_kalman.{case}.json")
        actual_trace = trace_custom_pv_d_v04(ir, fixture, base_path=ROOT).model_dump(mode="json")
        actual_diagnostics = diagnostics_custom_pv_d_v04(ir, fixture, base_path=ROOT)
        expected_trace = _load_json(TRACE_DIR / f"custom_token_kalman.{case}.json")
        expected_diagnostics = _load_json(DIAG_DIR / f"custom_token_kalman.{case}.json")

        assert actual_trace == expected_trace
        assert actual_diagnostics == expected_diagnostics
        assert _recompute_hash(expected_trace) == expected_trace["expected_artifact_hash"]
        assert _recompute_hash(expected_diagnostics) == expected_diagnostics["expected_artifact_hash"]


def test_pv_d_pretrade_default_integrity_passes_authorization_fails() -> None:
    ir = load_ir_v04_file(STRATEGY)
    fixture = load_custom_pv_d_fixture(FIXTURE_DIR / "custom_token_kalman.pretrade_default.json")

    trace = trace_custom_pv_d_v04(ir, fixture, base_path=ROOT)

    assert trace.integrity["ok"] is True
    assert trace.authorization["status"] == "requires_approval"
    assert trace.output is None


def test_pv_d_approved_paths_execute_and_write_audit() -> None:
    ir = load_ir_v04_file(STRATEGY)
    for case in ("research", "pretrade_approved"):
        fixture = load_custom_pv_d_fixture(FIXTURE_DIR / f"custom_token_kalman.{case}.json")
        trace = trace_custom_pv_d_v04(ir, fixture, base_path=ROOT)

        assert trace.output == {"filtered": [1.0, 1.5, 2.25, 2.125]}
        assert trace.audit_records


def test_expected_artifact_hash_excludes_itself() -> None:
    expected_trace = _load_json(TRACE_DIR / "custom_token_kalman.research.json")
    changed = dict(expected_trace)
    changed["expected_artifact_hash"] = "sha256:" + "0" * 64

    assert _recompute_hash(expected_trace) == _recompute_hash(changed)


def _load_json(path: Path) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _recompute_hash(payload: dict[str, object]) -> str:
    return expected_artifact_hash_v2(
        {key: value for key, value in payload.items() if key != "expected_artifact_hash"}
    )
