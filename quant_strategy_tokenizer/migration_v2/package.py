"""qstpkg migration helpers for WP10."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.ir_v04 import canonical_bytes_v04, canonicalize_v04
from quant_strategy_tokenizer.migration_v2.strategy import (
    MigrationResult,
    build_migration_lock_v04,
    migrate_strategy_file,
)
from quant_strategy_tokenizer.package.manifest import (
    PackageFile,
    PackageManifest,
    PackageStrategyManifest,
)
from quant_strategy_tokenizer.package.paths import to_posix_relative
from quant_strategy_tokenizer.package.reader import read_package
from quant_strategy_tokenizer.qst_lock import sha256_bytes


@dataclass(frozen=True)
class PackageMigrationResult:
    """Result of migrating a legacy qstpkg directory."""

    package_dir: Path
    migration: MigrationResult
    manifest: PackageManifest


def migrate_package(package_dir: str | Path, output_dir: str | Path) -> PackageMigrationResult:
    """Migrate a legacy qstpkg directory to a v0.4 qstpkg snapshot."""

    source_package = read_package(package_dir)
    target = Path(output_dir)
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Package output directory is not empty: {target}")
    if target.exists():
        target.rmdir()
    shutil.copytree(source_package.root, target)

    migrated = migrate_strategy_file(source_package.source_path)
    if not migrated.ok or migrated.strategy is None:
        _write_json(target / "migration" / "report.json", migrated.model_dump(mode="json"))
        return PackageMigrationResult(
            package_dir=target,
            migration=migrated,
            manifest=read_package(target).manifest,
        )

    source_target = target / "strategies" / "source.qst.yaml"
    canonical_target = target / "strategies" / "canonical.json"
    lock_target = target / "qst.lock"
    report_target = target / "migration" / "report.json"
    report_target.parent.mkdir(parents=True, exist_ok=True)

    source_target.write_text(
        yaml.safe_dump(
            migrated.strategy.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    canonical_target.write_bytes(canonical_bytes_v04(canonicalize_v04(migrated.strategy)))
    _write_json(lock_target, build_migration_lock_v04(migrated))
    _write_json(report_target, migrated.model_dump(mode="json"))

    original_manifest = read_package(target).manifest
    tracked_files = [
        source_target,
        canonical_target,
        lock_target,
        target / original_manifest.fixtures_manifest_path,
        report_target,
    ]
    tracked_files.extend(target / path for path in original_manifest.tagspec_paths)
    tracked_files.extend(target / path for path in original_manifest.recipe_paths)
    if original_manifest.token_packs is not None:
        for entry in original_manifest.token_packs.packs:
            for candidate in (
                target / "deps" / "tokenpacks" / entry.pack_id,
                target / "tokenpacks" / entry.pack_id,
            ):
                if candidate.exists():
                    tracked_files.extend(path for path in candidate.rglob("*") if path.is_file())
                    break

    manifest = PackageManifest(
        qst_version=__version__,
        strategy=PackageStrategyManifest(
            name=migrated.strategy.strategy.id,
            version=migrated.strategy.strategy.version,
        ),
        fixtures_manifest_path=original_manifest.fixtures_manifest_path,
        files=_file_entries(target, tracked_files),
        tagspec_paths=original_manifest.tagspec_paths,
        recipe_paths=original_manifest.recipe_paths,
        artifacts=original_manifest.artifacts,
        token_packs=original_manifest.token_packs,
    )
    _write_yaml(target / "manifest.yaml", manifest.model_dump(mode="json", exclude_none=True))
    return PackageMigrationResult(package_dir=target, migration=migrated, manifest=manifest)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )


def _write_yaml(path: Path, payload: Any) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _file_entries(root: Path, paths: list[Path]) -> list[PackageFile]:
    unique = sorted({path for path in paths if path.exists() and path.is_file()}, key=lambda item: item.as_posix())
    return [
        PackageFile(
            path=to_posix_relative(path, root),
            sha256=sha256_bytes(path.read_bytes()),
        )
        for path in unique
    ]

