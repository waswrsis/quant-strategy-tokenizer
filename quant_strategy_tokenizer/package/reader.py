"""Read and unpack P3a-1 qstpkg directories."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from quant_strategy_tokenizer.package.manifest import (
    FixturesManifest,
    PackageManifest,
    UnpackedPackage,
)
from quant_strategy_tokenizer.package.paths import safe_join


def _read_yaml_object(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    return raw


def read_package(package_dir: str | Path) -> UnpackedPackage:
    """Read qstpkg manifests and resolve known paths."""

    root = Path(package_dir)
    manifest = PackageManifest.model_validate(_read_yaml_object(root / "manifest.yaml"))
    fixtures_manifest_path = safe_join(root, manifest.fixtures_manifest_path)
    fixtures_manifest = FixturesManifest.model_validate(_read_yaml_object(fixtures_manifest_path))
    market_path = (
        safe_join(root, fixtures_manifest.market_csv_path)
        if fixtures_manifest.market_csv_path is not None
        else None
    )
    expected_trace_path = (
        safe_join(root, fixtures_manifest.expected_trace_path)
        if fixtures_manifest.expected_trace_path is not None
        else None
    )
    return UnpackedPackage(
        root=root,
        manifest=manifest,
        fixtures_manifest=fixtures_manifest,
        source_path=safe_join(root, manifest.strategy.source_path),
        canonical_path=safe_join(root, manifest.strategy.canonical_path),
        lock_path=safe_join(root, manifest.strategy.lock_path),
        market_path=market_path,
        expected_trace_path=expected_trace_path,
    )


def unpack_package(package_dir: str | Path, output_dir: str | Path) -> UnpackedPackage:
    """Copy a qstpkg directory to another directory and return its parsed manifests."""

    source = Path(package_dir)
    target = Path(output_dir)
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Unpack output directory is not empty: {target}")
    if target.exists():
        target.rmdir()
    shutil.copytree(source, target)
    return read_package(target)
