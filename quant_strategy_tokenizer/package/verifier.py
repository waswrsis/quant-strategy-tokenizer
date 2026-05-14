"""Verify P3a-1 qstpkg directories."""

from __future__ import annotations

import json
from pathlib import Path

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
