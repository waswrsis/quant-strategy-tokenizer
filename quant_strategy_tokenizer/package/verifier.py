"""Verify P3a-1 qstpkg directories."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from quant_strategy_tokenizer.artifacts.backtest_evidence import (
    ArtifactRef,
    BacktestEvidence,
)
from quant_strategy_tokenizer.artifacts.base import QSTArtifact
from quant_strategy_tokenizer.artifacts.execution_report import ExecutionReport
from quant_strategy_tokenizer.artifacts.portfolio_snapshot import PortfolioSnapshot
from quant_strategy_tokenizer.custom_runtime_v2 import (
    TokenRuntimeContext,
    load_token_pack,
    verify_integrity,
)
from quant_strategy_tokenizer.package.manifest import PackageFile, UnpackedPackage
from quant_strategy_tokenizer.package.paths import safe_join
from quant_strategy_tokenizer.package.reader import read_package
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.qst_lock import sha256_bytes, verify_lock
from quant_strategy_tokenizer.qst_lock.builder import trace_semantic_hash
from quant_strategy_tokenizer.qst_lock.io import read_canonical_ir, read_lock
from quant_strategy_tokenizer.qst_lock.verify_result import (
    VerificationLevel,
    VerifyFailure,
    VerifyResult,
)
from quant_strategy_tokenizer.tokens_v2 import (
    TokenPackManifestV2,
    verify_token_pack_package_section,
)


def _failure(
    kind: str,
    message: str,
    *,
    path: str | None = None,
    expected: object | None = None,
    actual: object | None = None,
) -> VerifyFailure:
    return VerifyFailure(
        kind=kind,
        message=message,
        path=path,
        expected=expected,
        actual=actual,
    )


def _file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _manifest_file_by_path(package: UnpackedPackage) -> dict[str, PackageFile]:
    return {entry.path: entry for entry in package.manifest.files}


def _check_manifest_file(package: UnpackedPackage, entry: PackageFile) -> VerifyFailure | None:
    path = safe_join(package.root, entry.path)
    if not path.exists():
        return _failure(
            "package_file_missing",
            f"Package file is missing: {entry.path}",
            path=entry.path,
            expected=entry.sha256,
            actual=None,
        )
    actual = _file_hash(path)
    if actual != entry.sha256:
        return _failure(
            "package_file_hash_mismatch",
            f"Package file hash mismatch: {entry.path}",
            path=entry.path,
            expected=entry.sha256,
            actual=actual,
        )
    return None


def _check_artifact_file_by_hash(
    package: UnpackedPackage,
    *,
    path: str,
    expected_hash: str,
    missing_kind: str = "artifact_file_missing",
    mismatch_kind: str = "artifact_file_hash_mismatch",
) -> list[VerifyFailure]:
    try:
        resolved = safe_join(package.root, path)
    except ValueError as exc:
        return [
            _failure(
                "artifact_path_unsafe",
                str(exc),
                path=path,
            )
        ]
    if not resolved.exists():
        return [
            _failure(
                missing_kind,
                f"Artifact file is missing: {path}",
                path=path,
                expected=expected_hash,
                actual=None,
            )
        ]
    actual = _file_hash(resolved)
    if actual != expected_hash:
        return [
            _failure(
                mismatch_kind,
                f"Artifact file hash mismatch: {path}",
                path=path,
                expected=expected_hash,
                actual=actual,
            )
        ]
    return []


def _check_manifest_tracked_artifact(
    package: UnpackedPackage,
    manifest_files: dict[str, PackageFile],
    path: str,
) -> list[VerifyFailure]:
    entry = manifest_files.get(path)
    if entry is None:
        return [
            _failure(
                "artifact_file_untracked",
                f"Artifact file is not tracked in package manifest files: {path}",
                path=path,
            )
        ]
    return _check_artifact_file_by_hash(
        package,
        path=entry.path,
        expected_hash=entry.sha256,
    )


def _load_artifact_model(path: Path, model: type[BaseModel]) -> BaseModel:
    loaded = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(loaded, dict):
        raise TypeError(f"Artifact JSON must be an object: {path}")
    return model.model_validate(loaded)


def _check_artifact_ref(package: UnpackedPackage, ref: ArtifactRef) -> list[VerifyFailure]:
    return _check_artifact_file_by_hash(
        package,
        path=ref.path,
        expected_hash=ref.hash,
        missing_kind="artifact_ref_missing",
        mismatch_kind="artifact_ref_hash_mismatch",
    )


def _check_raw_payload(package: UnpackedPackage, artifact: QSTArtifact, artifact_path: str) -> list[VerifyFailure]:
    if artifact.raw_payload_ref is None:
        return []
    if artifact.raw_payload_hash is None:
        return [
            _failure(
                "artifact_raw_payload_hash_missing",
                f"Artifact raw_payload_ref has no raw_payload_hash: {artifact_path}",
                path=artifact_path,
            )
        ]
    return _check_artifact_file_by_hash(
        package,
        path=artifact.raw_payload_ref,
        expected_hash=artifact.raw_payload_hash,
        missing_kind="artifact_raw_payload_missing",
        mismatch_kind="artifact_raw_payload_hash_mismatch",
    )


def _check_execution_report(package: UnpackedPackage, report_path: str) -> list[VerifyFailure]:
    try:
        resolved = safe_join(package.root, report_path)
        report = _load_artifact_model(resolved, ExecutionReport)
    except Exception as exc:
        return [
            _failure(
                "artifact_json_invalid",
                f"Could not read execution report artifact: {type(exc).__name__}: {exc}",
                path=report_path,
            )
        ]
    assert isinstance(report, ExecutionReport)
    return _check_raw_payload(package, report, report_path)


def _check_portfolio_snapshot(package: UnpackedPackage, snapshot_path: str) -> list[VerifyFailure]:
    try:
        resolved = safe_join(package.root, snapshot_path)
        snapshot = _load_artifact_model(resolved, PortfolioSnapshot)
    except Exception as exc:
        return [
            _failure(
                "artifact_json_invalid",
                f"Could not read portfolio snapshot artifact: {type(exc).__name__}: {exc}",
                path=snapshot_path,
            )
        ]
    assert isinstance(snapshot, PortfolioSnapshot)
    return _check_raw_payload(package, snapshot, snapshot_path)


def _check_backtest_evidence(package: UnpackedPackage, evidence_path: str) -> list[VerifyFailure]:
    try:
        resolved = safe_join(package.root, evidence_path)
        evidence = _load_artifact_model(resolved, BacktestEvidence)
    except Exception as exc:
        return [
            _failure(
                "artifact_json_invalid",
                f"Could not read backtest evidence artifact: {type(exc).__name__}: {exc}",
                path=evidence_path,
            )
        ]
    assert isinstance(evidence, BacktestEvidence)
    failures = _check_raw_payload(package, evidence, evidence_path)
    if evidence.equity_curve is not None:
        failures.extend(_check_artifact_ref(package, evidence.equity_curve))
    for ref in [*evidence.execution_reports, *evidence.portfolio_snapshots]:
        failures.extend(_check_artifact_ref(package, ref))
    return failures


def _check_artifacts(package: UnpackedPackage) -> list[VerifyFailure]:
    artifacts = package.manifest.artifacts
    if artifacts is None:
        return []

    failures: list[VerifyFailure] = []
    manifest_files = _manifest_file_by_path(package)

    if artifacts.backtest.evidence is not None:
        failures.extend(_check_manifest_tracked_artifact(package, manifest_files, artifacts.backtest.evidence))
        failures.extend(_check_backtest_evidence(package, artifacts.backtest.evidence))
    for artifact_file in artifacts.backtest.files:
        failures.extend(
            _check_artifact_file_by_hash(
                package,
                path=artifact_file.path,
                expected_hash=artifact_file.hash,
            )
        )

    for report_path in artifacts.execution.reports:
        failures.extend(_check_manifest_tracked_artifact(package, manifest_files, report_path))
        failures.extend(_check_execution_report(package, report_path))
    for raw_payload in artifacts.execution.raw_payloads:
        failures.extend(
            _check_artifact_file_by_hash(
                package,
                path=raw_payload.path,
                expected_hash=raw_payload.hash,
            )
        )

    for snapshot_path in artifacts.portfolio.snapshots:
        failures.extend(_check_manifest_tracked_artifact(package, manifest_files, snapshot_path))
        failures.extend(_check_portfolio_snapshot(package, snapshot_path))

    return failures


def _check_fixture_manifest_consistency(package: UnpackedPackage) -> list[VerifyFailure]:
    failures: list[VerifyFailure] = []
    if package.market_path is not None and package.fixtures_manifest.market_csv_hash is not None:
        if not package.market_path.exists():
            failures.append(
                _failure(
                    "market_csv_hash_mismatch",
                    "Market CSV fixture is missing",
                    path="fixtures.market_csv_hash",
                    expected=package.fixtures_manifest.market_csv_hash,
                    actual=None,
                )
            )
            return failures
        actual = _file_hash(package.market_path)
        if actual != package.fixtures_manifest.market_csv_hash:
            failures.append(
                _failure(
                    "market_csv_hash_mismatch",
                    "Market CSV fixture hash differs from fixtures manifest",
                    path="fixtures.market_csv_hash",
                    expected=package.fixtures_manifest.market_csv_hash,
                    actual=actual,
                )
            )
    if (
        package.expected_trace_path is not None
        and package.fixtures_manifest.expected_trace_full_hash is not None
    ):
        if not package.expected_trace_path.exists():
            failures.append(
                _failure(
                    "expected_trace_hash_mismatch",
                    "Expected trace fixture is missing",
                    path="fixtures.expected_trace_full_hash",
                    expected=package.fixtures_manifest.expected_trace_full_hash,
                    actual=None,
                )
            )
            return failures
        actual = _file_hash(package.expected_trace_path)
        if actual != package.fixtures_manifest.expected_trace_full_hash:
            failures.append(
                _failure(
                    "expected_trace_hash_mismatch",
                    "Expected trace full hash differs from fixtures manifest",
                    path="fixtures.expected_trace_full_hash",
                    expected=package.fixtures_manifest.expected_trace_full_hash,
                    actual=actual,
                )
            )
    if (
        package.expected_trace_path is not None
        and package.fixtures_manifest.expected_trace_semantic_hash is not None
    ):
        loaded = json.loads(package.expected_trace_path.read_text(encoding="utf-8-sig"))
        if isinstance(loaded, dict):
            actual = trace_semantic_hash(loaded)
            if actual != package.fixtures_manifest.expected_trace_semantic_hash:
                failures.append(
                    _failure(
                        "trace_semantic_hash_mismatch",
                        "Expected trace semantic hash differs from fixtures manifest",
                        path="fixtures.expected_trace_semantic_hash",
                        expected=package.fixtures_manifest.expected_trace_semantic_hash,
                        actual=actual,
                    )
                )
        else:
            failures.append(
                _failure(
                    "trace_semantic_hash_mismatch",
                    "Expected trace must be a JSON object",
                    path="fixtures.expected_trace_semantic_hash",
                    expected=package.fixtures_manifest.expected_trace_semantic_hash,
                    actual=None,
                )
            )
    return failures


def _load_embedded_token_packs(package: UnpackedPackage) -> list[tuple[TokenPackManifestV2, Path]]:
    if package.manifest.token_packs is None:
        return []
    packs: list[tuple[TokenPackManifestV2, Path]] = []
    for entry in package.manifest.token_packs.packs:
        candidates = [
            package.root / "deps" / "tokenpacks" / entry.pack_id,
            package.root / "tokenpacks" / entry.pack_id,
        ]
        for candidate in candidates:
            if candidate.exists():
                packs.append((load_token_pack(candidate), candidate))
                break
    return packs


def _check_token_packs(package: UnpackedPackage) -> list[VerifyFailure]:
    section = package.manifest.token_packs
    if section is None:
        return []

    embedded = _load_embedded_token_packs(package)
    packs = [pack for pack, _ in embedded]
    result = verify_token_pack_package_section(section, packs)
    failures = [
        _failure(
            diagnostic.code,
            diagnostic.message,
            path="manifest.token_packs",
        )
        for diagnostic in result.errors
    ]
    for pack, pack_path in embedded:
        context = TokenRuntimeContext(base_path=pack_path)
        for spec in pack.tokens:
            integrity = verify_integrity(pack, spec.token_ref, context=context)
            failures.extend(
                _failure(
                    diagnostic.code,
                    diagnostic.message,
                    path=f"manifest.token_packs.{pack.pack_id}.{spec.token_id}",
                )
                for diagnostic in integrity.diagnostics
                if diagnostic.severity == "error"
            )
    return failures


def verify_package(package_dir: str | Path) -> VerifyResult:
    """Verify a qstpkg directory."""

    try:
        package = read_package(package_dir)
    except Exception as exc:
        return VerifyResult.from_failures(
            [
                _failure(
                    "package_manifest_invalid",
                    f"Could not read package manifests: {type(exc).__name__}: {exc}",
                )
            ]
        )

    failures: list[VerifyFailure] = []
    required_paths = [
        package.source_path,
        package.canonical_path,
        package.lock_path,
        package.root / package.manifest.fixtures_manifest_path,
    ]
    for path in required_paths:
        if not path.exists():
            failures.append(
                _failure(
                    "package_file_missing",
                    f"Required package file is missing: {path.relative_to(package.root).as_posix()}",
                    path=path.relative_to(package.root).as_posix(),
                )
            )

    for entry in package.manifest.files:
        failure = _check_manifest_file(package, entry)
        if failure is not None:
            failures.append(failure)

    failures.extend(_check_fixture_manifest_consistency(package))
    failures.extend(_check_artifacts(package))
    failures.extend(_check_token_packs(package))

    can_verify_lock = package.source_path.exists() and package.canonical_path.exists() and package.lock_path.exists()
    if can_verify_lock:
        lock_result = verify_lock(
            load_strategy_file(package.source_path),
            read_lock(package.lock_path),
            canonical_ir=read_canonical_ir(package.canonical_path),
            market_path=package.market_path,
            expected_trace_path=package.expected_trace_path,
        )
        failures.extend(lock_result.failures)

    level = (
        VerificationLevel.SEMANTIC_TRACE
        if package.expected_trace_path is not None
        else VerificationLevel.STRUCTURAL
    )
    return VerifyResult.from_failures(failures, verification_level=level)
