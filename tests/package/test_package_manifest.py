from __future__ import annotations

import json
from pathlib import Path

import yaml

from quant_strategy_tokenizer.package import FixturesManifest, PackageManifest, package_strategy
from quant_strategy_tokenizer.package.reader import read_package
from quant_strategy_tokenizer.qst_lock.io import read_lock

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
SCHEMA = ROOT / "docs" / "JSON_SCHEMAS" / "qst_package_manifest.schema.json"


def test_package_manifest_schema_and_roundtrip(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"

    built = package_strategy(STRATEGY, package_dir)
    manifest = read_package(package_dir).manifest

    assert built.manifest == manifest
    assert PackageManifest.model_validate(manifest.model_dump(mode="json")) == manifest
    assert FixturesManifest.model_validate(
        read_package(package_dir).fixtures_manifest.model_dump(mode="json")
    )
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["files"]["items"]["properties"]["sha256"]["pattern"] == (
        "^sha256:[0-9a-f]{64}$"
    )


def test_package_contains_canonical_json_lock(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"

    package_strategy(STRATEGY, package_dir)

    raw_lock = (package_dir / "qst.lock").read_bytes()
    assert raw_lock.startswith(b"{")
    assert b"\n" not in raw_lock
    assert read_lock(package_dir / "qst.lock").lock_version == "qst-lock/0.1"
    manifest_raw = yaml.safe_load((package_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest_raw["strategy"]["source_path"] == "strategies/source.qst.yaml"
