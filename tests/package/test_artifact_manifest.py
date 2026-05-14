from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from quant_strategy_tokenizer.package import PackageManifest, package_strategy, verify_package

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
SCHEMA = ROOT / "docs" / "JSON_SCHEMAS" / "qst_package_manifest.schema.json"


def _manifest_payload(path: Path) -> dict[str, object]:
    raw = yaml.safe_load((path / "manifest.yaml").read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _schema() -> dict[str, object]:
    raw = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    Draft202012Validator.check_schema(raw)
    return raw


def test_legacy_package_without_artifacts_parse_and_verify(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    raw = _manifest_payload(package_dir)

    assert "artifacts" not in raw
    Draft202012Validator(_schema()).validate(raw)
    assert PackageManifest.model_validate(raw).artifacts is None

    result = verify_package(package_dir)
    assert result.ok, result.failures


def test_manifest_schema_accepts_artifacts_section(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    raw = _manifest_payload(package_dir)
    raw["artifacts"] = {
        "backtest": {"evidence": None, "files": []},
        "execution": {"reports": [], "raw_payloads": []},
        "portfolio": {"snapshots": []},
    }

    Draft202012Validator(_schema()).validate(raw)
    manifest = PackageManifest.model_validate(raw)

    assert manifest.artifacts is not None
    assert manifest.artifacts.execution.reports == []


@pytest.mark.parametrize("bad_path", ["/abs/report.json", "../report.json", "artifacts\\report.json"])
def test_unsafe_artifact_paths_are_rejected(tmp_path: Path, bad_path: str) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    raw = _manifest_payload(package_dir)
    raw["artifacts"] = {
        "backtest": {"evidence": None, "files": []},
        "execution": {"reports": [bad_path], "raw_payloads": []},
        "portfolio": {"snapshots": []},
    }

    with pytest.raises(ValidationError):
        PackageManifest.model_validate(raw)
