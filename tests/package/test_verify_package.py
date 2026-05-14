from __future__ import annotations

import json
from pathlib import Path

from quant_strategy_tokenizer.package import package_strategy, verify_package
from quant_strategy_tokenizer.qst_lock.verify_result import VerificationLevel

ROOT = Path(__file__).resolve().parents[2]
EWM_STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
EXPECTED_TRACE = ROOT / "strategies" / "examples_kdj_with_ema_filter.expected_trace.json"


def _failure_kinds(package_dir: Path) -> set[str]:
    return {failure.kind for failure in verify_package(package_dir).failures}


def test_verify_package_without_expected_trace_is_structural(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(EWM_STRATEGY, package_dir)

    result = verify_package(package_dir)

    assert result.ok, result.failures
    assert result.verification_level == VerificationLevel.STRUCTURAL


def test_verify_package_with_expected_trace_is_semantic_trace(tmp_path: Path) -> None:
    package_dir = tmp_path / "p1.qstpkg"
    package_strategy(
        P1_STRATEGY,
        package_dir,
        market_path=MARKET,
        expected_trace_path=EXPECTED_TRACE,
    )

    result = verify_package(package_dir)

    assert result.ok, result.failures
    assert result.verification_level == VerificationLevel.SEMANTIC_TRACE


def test_tamper_market_csv_reports_market_hash_mismatch(tmp_path: Path) -> None:
    package_dir = tmp_path / "p1.qstpkg"
    package_strategy(P1_STRATEGY, package_dir, market_path=MARKET)
    market = package_dir / "fixtures" / "market.csv"
    market.write_text(market.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert "market_csv_hash_mismatch" in _failure_kinds(package_dir)


def test_tamper_expected_trace_reports_trace_hash_mismatch(tmp_path: Path) -> None:
    package_dir = tmp_path / "p1.qstpkg"
    package_strategy(
        P1_STRATEGY,
        package_dir,
        market_path=MARKET,
        expected_trace_path=EXPECTED_TRACE,
    )
    trace = package_dir / "fixtures" / "expected_trace.json"
    payload = json.loads(trace.read_text(encoding="utf-8"))
    payload["nodes"] = [
        {
            "id": "tampered",
            "token": "plan.noop",
            "token_version": 1,
            "behavior_version": 1,
            "status": "error",
            "output_summary": {},
        }
    ]
    trace.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    kinds = _failure_kinds(package_dir)
    assert "expected_trace_hash_mismatch" in kinds
    assert "trace_semantic_hash_mismatch" in kinds


def test_tamper_canonical_json_reports_canonical_ir_tampered(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(EWM_STRATEGY, package_dir)
    canonical = package_dir / "strategies" / "canonical.json"
    payload = json.loads(canonical.read_text(encoding="utf-8"))
    payload["strategy_version"] = 999
    canonical.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    assert "canonical_ir_tampered" in _failure_kinds(package_dir)


def test_tamper_source_reports_surface_canonical_inconsistent(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(EWM_STRATEGY, package_dir)
    source = package_dir / "strategies" / "source.qst.yaml"
    source.write_text(
        source.read_text(encoding="utf-8").replace("span: 3", "span: 5"),
        encoding="utf-8",
    )

    assert "surface_canonical_inconsistent" in _failure_kinds(package_dir)


def test_missing_manifest_file_reports_package_failure(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(EWM_STRATEGY, package_dir)
    (package_dir / "strategies" / "source.qst.yaml").unlink()

    assert "package_file_missing" in _failure_kinds(package_dir)


def test_externals_schema_hash_is_checked_through_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(EWM_STRATEGY, package_dir)
    source = package_dir / "strategies" / "source.qst.yaml"
    source.write_text(
        source.read_text(encoding="utf-8").replace("type: Frame[OHLCV]", "type: Frame[CLOSE]"),
        encoding="utf-8",
    )

    assert "externals_schema_hash_mismatch" in _failure_kinds(package_dir)
