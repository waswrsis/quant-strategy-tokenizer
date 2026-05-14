"""Build P3a-1 qstpkg directory packages."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.package.manifest import (
    FixturesManifest,
    PackageFile,
    PackageManifest,
    PackageStrategyManifest,
)
from quant_strategy_tokenizer.package.paths import to_posix_relative
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.qst_lock import build_lock, sha256_bytes
from quant_strategy_tokenizer.qst_lock.io import write_canonical_ir, write_lock


@dataclass(frozen=True)
class PackageBuildResult:
    """Result of a qstpkg build."""

    package_dir: Path
    manifest: PackageManifest
    fixtures_manifest: FixturesManifest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _ensure_output_dir(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Package output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(
        yaml.safe_dump(to_plain(payload), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _copy_tagspecs(package_dir: Path, semantic_ids: list[str]) -> list[str]:
    paths: list[str] = []
    tagspec_dir = _repo_root() / "docs" / "tagspecs"
    target_dir = package_dir / "deps" / "tagspecs"
    target_dir.mkdir(parents=True, exist_ok=True)
    for semantic_id in sorted(set(semantic_ids)):
        source = tagspec_dir / f"{semantic_id}.tagspec.yaml"
        if not source.exists():
            continue
        target = target_dir / source.name
        shutil.copy2(source, target)
        paths.append(to_posix_relative(target, package_dir))
    return paths


def _build_file_entries(package_dir: Path, paths: list[Path]) -> list[PackageFile]:
    return [
        PackageFile(path=to_posix_relative(path, package_dir), sha256=_file_hash(path))
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]


def package_strategy(
    strategy_path: str | Path,
    output_dir: str | Path,
    *,
    market_path: str | Path | None = None,
    expected_trace_path: str | Path | None = None,
) -> PackageBuildResult:
    """Build a directory-based .qstpkg package."""

    source_strategy = Path(strategy_path)
    package_dir = Path(output_dir)
    market = Path(market_path) if market_path is not None else None
    expected_trace = Path(expected_trace_path) if expected_trace_path is not None else None
    _ensure_output_dir(package_dir)

    strategies_dir = package_dir / "strategies"
    fixtures_dir = package_dir / "fixtures"
    (package_dir / "deps" / "recipes").mkdir(parents=True, exist_ok=True)
    strategies_dir.mkdir(parents=True, exist_ok=True)
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    source_target = strategies_dir / "source.qst.yaml"
    canonical_target = strategies_dir / "canonical.json"
    lock_target = package_dir / "qst.lock"
    fixtures_manifest_target = fixtures_dir / "manifest.yaml"

    shutil.copy2(source_strategy, source_target)
    if market is not None:
        shutil.copy2(market, fixtures_dir / "market.csv")
    if expected_trace is not None:
        shutil.copy2(expected_trace, fixtures_dir / "expected_trace.json")

    ir = load_strategy_file(source_strategy)
    built = build_lock(ir, market_path=market, expected_trace_path=expected_trace)
    write_lock(built.lock, lock_target)
    write_canonical_ir(built.canonical_ir, canonical_target)

    tagspec_paths = _copy_tagspecs(
        package_dir,
        [dependency.semantic_id for dependency in built.lock.tagspecs],
    )

    copied_market = fixtures_dir / "market.csv" if market is not None else None
    copied_trace = fixtures_dir / "expected_trace.json" if expected_trace is not None else None
    fixtures_manifest = FixturesManifest(
        market_csv_path=to_posix_relative(copied_market, package_dir) if copied_market else None,
        market_csv_hash=built.lock.fixtures.market_csv_hash,
        expected_trace_path=to_posix_relative(copied_trace, package_dir) if copied_trace else None,
        expected_trace_full_hash=built.lock.fixtures.expected_trace_hash,
        expected_trace_semantic_hash=built.lock.fixtures.trace_semantic_hash,
    )
    _write_yaml(fixtures_manifest_target, fixtures_manifest)

    tracked_files = [
        source_target,
        canonical_target,
        lock_target,
        fixtures_manifest_target,
        *(package_dir / path for path in tagspec_paths),
    ]
    if copied_market is not None:
        tracked_files.append(copied_market)
    if copied_trace is not None:
        tracked_files.append(copied_trace)

    manifest = PackageManifest(
        qst_version=__version__,
        strategy=PackageStrategyManifest(
            name=built.lock.strategy,
            version=built.lock.strategy_version,
        ),
        tagspec_paths=tagspec_paths,
        recipe_paths=[],
        files=_build_file_entries(package_dir, tracked_files),
    )
    _write_yaml(package_dir / "manifest.yaml", manifest)
    return PackageBuildResult(
        package_dir=package_dir,
        manifest=manifest,
        fixtures_manifest=fixtures_manifest,
    )
