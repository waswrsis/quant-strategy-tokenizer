from __future__ import annotations

from pathlib import Path

import yaml

from qst import __version__

ROOT = Path(__file__).resolve().parents[2]
REARCHITECTURE = ROOT / "docs" / "rearchitecture"


def test_stage_zero_governance_documents_exist() -> None:
    required = {
        "README.md",
        "ADR-0001-qst-1.0-product-redefinition.md",
        "STAGE_GOVERNANCE.md",
        "V04_COMPATIBILITY_BOUNDARY.md",
        "stages/stage-0-baseline.yaml",
    }
    for relative in required:
        path = REARCHITECTURE / relative
        assert path.is_file(), relative
        assert path.read_text(encoding="utf-8").strip(), relative


def test_stage_zero_manifest_is_frozen_with_passing_gates() -> None:
    path = REARCHITECTURE / "stages" / "stage-0-baseline.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "qst-rearchitecture-stage/1"
    assert manifest["stage_id"] == 0
    assert manifest["status"] == "frozen"
    assert manifest["freeze_tag"] == "qst-1.0-stage-0-baseline-frozen"
    assert manifest["frozen_contracts"]
    assert all(gate["result"] == "pass" for gate in manifest["gates"])


def test_product_version_signals_major_alpha_redefinition() -> None:
    assert __version__ == "1.0.0a1"
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "1.0.0a1"' in pyproject


def test_product_boundary_disallows_execution_claims() -> None:
    adr = (REARCHITECTURE / "ADR-0001-qst-1.0-product-redefinition.md").read_text(
        encoding="utf-8"
    )
    for boundary in ("train models", "execute backtests", "broker", "exchange", "live trading"):
        assert boundary in adr
    assert "Adapters have no `execute` method" in adr
