"""P4a-2 qstpkg artifact helpers."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from quant_strategy_tokenizer.artifacts.backtest_evidence import BacktestEvidence
from quant_strategy_tokenizer.artifacts.execution_report import ExecutionReport
from quant_strategy_tokenizer.artifacts.portfolio_snapshot import PortfolioSnapshot
from quant_strategy_tokenizer.artifacts.safety import validate_posix_relative_path
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.package.manifest import (
    PackageArtifacts,
    PackageBacktestArtifacts,
    PackageExecutionArtifacts,
    PackageFile,
    PackageManifest,
    PackagePortfolioArtifacts,
)
from quant_strategy_tokenizer.package.paths import safe_join, to_posix_relative
from quant_strategy_tokenizer.package.reader import read_package
from quant_strategy_tokenizer.qst_lock import sha256_bytes

ArtifactModel = BacktestEvidence | ExecutionReport | PortfolioSnapshot


@dataclass(frozen=True)
class AddArtifactResult:
    """Result of adding one P4 artifact to a qstpkg."""

    package_dir: Path
    artifact_path: str
    artifact_version: str
    manifest: PackageManifest


def _file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(
        yaml.safe_dump(to_plain(payload), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _load_artifact(path: Path) -> ArtifactModel:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path} must contain a JSON object")

    artifact_version = raw.get("artifact_version")
    if artifact_version == "qst-execution-report/1":
        return ExecutionReport.model_validate(raw)
    if artifact_version == "qst-portfolio-snapshot/1":
        return PortfolioSnapshot.model_validate(raw)
    if artifact_version == "qst-backtest-evidence/1":
        return BacktestEvidence.model_validate(raw)
    raise ValueError(f"Unsupported artifact_version: {artifact_version!r}")


def _default_artifact_path(artifact: ArtifactModel, source: Path) -> str:
    if isinstance(artifact, ExecutionReport):
        return f"artifacts/execution/reports/{source.name}"
    if isinstance(artifact, PortfolioSnapshot):
        return f"artifacts/portfolio/snapshots/{source.name}"
    return "artifacts/backtest/backtest_evidence.json"


def _replace_file_entry(entries: list[PackageFile], entry: PackageFile) -> list[PackageFile]:
    retained = [item for item in entries if item.path != entry.path]
    retained.append(entry)
    return sorted(retained, key=lambda item: item.path)


def _unique_sorted(values: list[str]) -> list[str]:
    return sorted(set(values))


def _artifacts_or_default(manifest: PackageManifest) -> PackageArtifacts:
    return manifest.artifacts or PackageArtifacts()


def _update_artifact_section(
    artifacts: PackageArtifacts,
    artifact: ArtifactModel,
    artifact_path: str,
) -> PackageArtifacts:
    if isinstance(artifact, ExecutionReport):
        execution = PackageExecutionArtifacts(
            reports=_unique_sorted([*artifacts.execution.reports, artifact_path]),
            raw_payloads=artifacts.execution.raw_payloads,
        )
        return PackageArtifacts(
            backtest=artifacts.backtest,
            execution=execution,
            portfolio=artifacts.portfolio,
        )

    if isinstance(artifact, PortfolioSnapshot):
        portfolio = PackagePortfolioArtifacts(
            snapshots=_unique_sorted([*artifacts.portfolio.snapshots, artifact_path])
        )
        return PackageArtifacts(
            backtest=artifacts.backtest,
            execution=artifacts.execution,
            portfolio=portfolio,
        )

    backtest = PackageBacktestArtifacts(
        evidence=artifact_path,
        files=artifacts.backtest.files,
    )
    return PackageArtifacts(
        backtest=backtest,
        execution=artifacts.execution,
        portfolio=artifacts.portfolio,
    )


def add_artifact_to_package(
    package_dir: str | Path,
    artifact_json: str | Path,
    *,
    dest_path: str | None = None,
) -> AddArtifactResult:
    """Copy one P4 artifact JSON file into a qstpkg and update its manifest."""

    package = read_package(package_dir)
    source = Path(artifact_json)
    artifact = _load_artifact(source)
    artifact_path = validate_posix_relative_path(
        dest_path or _default_artifact_path(artifact, source)
    )
    target = safe_join(package.root, artifact_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)

    entry = PackageFile(path=artifact_path, sha256=_file_hash(target))
    artifacts = _update_artifact_section(_artifacts_or_default(package.manifest), artifact, artifact_path)
    manifest = package.manifest.model_copy(
        update={
            "files": _replace_file_entry(list(package.manifest.files), entry),
            "artifacts": artifacts,
        }
    )
    _write_yaml(package.root / "manifest.yaml", manifest)
    return AddArtifactResult(
        package_dir=package.root,
        artifact_path=to_posix_relative(target, package.root),
        artifact_version=artifact.artifact_version,
        manifest=manifest,
    )
