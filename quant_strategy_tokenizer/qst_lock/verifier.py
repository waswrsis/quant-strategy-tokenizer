"""P3a-0 qst.lock verifier."""

from __future__ import annotations

import json
from pathlib import Path

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.composition import upgrade_verification
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, IR_VERSION, StrategyIR
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.provenance.verification_order import (
    VerificationState,
    verification_satisfies,
    verification_state,
)
from quant_strategy_tokenizer.qst_lock.builder import (
    compute_externals_schema_hash,
    trace_semantic_hash,
)
from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes, sha256_bytes
from quant_strategy_tokenizer.qst_lock.schema import LockFile
from quant_strategy_tokenizer.qst_lock.verify_result import VerifyFailure, VerifyResult
from quant_strategy_tokenizer.qst_lock.version_policy import check_version_policy
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry


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


def _current_tagspec_state(semantic_id: str, version: int) -> tuple[VerificationState, str]:
    spec = get_tagspec_registry().get(semantic_id, version)
    upgraded = upgrade_verification(spec)
    return verification_state(upgraded.verification), upgraded.graph_template_hash


def _check_token_dependencies(lock: LockFile) -> list[VerifyFailure]:
    registry = get_registry()
    failures: list[VerifyFailure] = []
    for dependency in lock.tokens:
        try:
            spec = registry.get(dependency.id, dependency.version).spec
        except KeyError:
            failures.append(
                _failure(
                    "token_dependency_missing",
                    f"Token {dependency.id}/v{dependency.version} is not registered",
                    path=f"tokens.{dependency.id}",
                )
            )
            continue
        if spec.behavior_version != dependency.behavior_version:
            failures.append(
                _failure(
                    "token_behavior_version_mismatch",
                    f"Token {dependency.id}/v{dependency.version} behavior version changed",
                    path=f"tokens.{dependency.id}.behavior_version",
                    expected=dependency.behavior_version,
                    actual=spec.behavior_version,
                )
            )
    return failures


def _check_recipe_dependencies(lock: LockFile) -> list[VerifyFailure]:
    registry = get_recipe_registry()
    failures: list[VerifyFailure] = []
    for dependency in lock.recipes:
        try:
            registry.get(dependency.recipe, dependency.version)
        except KeyError:
            failures.append(
                _failure(
                    "recipe_dependency_missing",
                    f"Recipe {dependency.recipe}/v{dependency.version} is not registered",
                    path=f"recipes.{dependency.recipe}",
                )
            )
    return failures


def _check_tagspec_dependencies(lock: LockFile) -> list[VerifyFailure]:
    failures: list[VerifyFailure] = []
    for dependency in lock.tagspecs:
        try:
            current_state, graph_template_hash = _current_tagspec_state(
                dependency.semantic_id,
                dependency.version,
            )
        except KeyError:
            failures.append(
                _failure(
                    "tagspec_verification_state_insufficient",
                    f"TagSpec {dependency.semantic_id}/v{dependency.version} is not registered",
                    path=f"tagspecs.{dependency.semantic_id}",
                    expected=dependency.verification_state,
                    actual="missing",
                )
            )
            continue

        if graph_template_hash != dependency.graph_template_hash:
            failures.append(
                _failure(
                    "tagspec_graph_template_hash_mismatch",
                    f"TagSpec {dependency.semantic_id}/v{dependency.version} graph hash changed",
                    path=f"tagspecs.{dependency.semantic_id}.graph_template_hash",
                    expected=dependency.graph_template_hash,
                    actual=graph_template_hash,
                )
            )
        if not verification_satisfies(current_state, dependency.verification_state):
            failures.append(
                _failure(
                    "tagspec_verification_state_insufficient",
                    f"TagSpec {dependency.semantic_id}/v{dependency.version} verification is insufficient",
                    path=f"tagspecs.{dependency.semantic_id}.verification_state",
                    expected=dependency.verification_state,
                    actual=current_state,
                )
            )
    return failures


def _check_fixtures(
    lock: LockFile,
    *,
    market_path: Path | None,
    expected_trace_path: Path | None,
) -> list[VerifyFailure]:
    failures: list[VerifyFailure] = []
    if lock.fixtures.market_csv_hash is not None:
        if market_path is None:
            failures.append(
                _failure(
                    "market_csv_hash_mismatch",
                    "Lock requires a market CSV fixture but none was provided",
                    path="fixtures.market_csv_hash",
                    expected=lock.fixtures.market_csv_hash,
                    actual=None,
                )
            )
        else:
            actual = _file_hash(market_path)
            if actual != lock.fixtures.market_csv_hash:
                failures.append(
                    _failure(
                        "market_csv_hash_mismatch",
                        "Market CSV fixture hash mismatch",
                        path="fixtures.market_csv_hash",
                        expected=lock.fixtures.market_csv_hash,
                        actual=actual,
                    )
                )

    if lock.fixtures.expected_trace_hash is not None:
        if expected_trace_path is None:
            failures.append(
                _failure(
                    "expected_trace_hash_mismatch",
                    "Lock requires an expected trace fixture but none was provided",
                    path="fixtures.expected_trace_hash",
                    expected=lock.fixtures.expected_trace_hash,
                    actual=None,
                )
            )
        else:
            actual = _file_hash(expected_trace_path)
            if actual != lock.fixtures.expected_trace_hash:
                failures.append(
                    _failure(
                        "expected_trace_hash_mismatch",
                        "Expected trace fixture hash mismatch",
                        path="fixtures.expected_trace_hash",
                        expected=lock.fixtures.expected_trace_hash,
                        actual=actual,
                    )
                )

    if lock.fixtures.trace_semantic_hash is not None and expected_trace_path is not None:
        raw_trace = json.loads(expected_trace_path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw_trace, dict):
            failures.append(
                _failure(
                    "trace_semantic_hash_mismatch",
                    "Expected trace fixture must contain a JSON object",
                    path="fixtures.trace_semantic_hash",
                    expected=lock.fixtures.trace_semantic_hash,
                    actual=None,
                )
            )
        else:
            actual = trace_semantic_hash(raw_trace)
            if actual != lock.fixtures.trace_semantic_hash:
                failures.append(
                    _failure(
                        "trace_semantic_hash_mismatch",
                        "Trace semantic hash mismatch",
                        path="fixtures.trace_semantic_hash",
                        expected=lock.fixtures.trace_semantic_hash,
                        actual=actual,
                    )
                )
    return failures


def verify_lock(
    ir: StrategyIR,
    lock: LockFile,
    *,
    canonical_ir: StrategyIR | None = None,
    market_path: str | Path | None = None,
    expected_trace_path: str | Path | None = None,
) -> VerifyResult:
    """Verify a surface strategy against a P3a-0 qst.lock."""

    failures: list[VerifyFailure] = []
    failures.extend(check_version_policy(lock, __version__))

    if lock.ir_version != IR_VERSION:
        failures.append(
            _failure(
                "ir_version_mismatch",
                "Lock IR version differs from the supported IR version",
                path="ir_version",
                expected=lock.ir_version,
                actual=IR_VERSION,
            )
        )
    if lock.canonical_version != CANONICAL_VERSION:
        failures.append(
            _failure(
                "canonical_version_mismatch",
                "Lock canonical version differs from the supported canonical version",
                path="canonical_version",
                expected=lock.canonical_version,
                actual=CANONICAL_VERSION,
            )
        )

    recomputed_canonical = canonicalize(ir)
    recomputed_bytes = canonical_lock_bytes(to_plain(recomputed_canonical))
    recomputed_canonical_hash = sha256_bytes(recomputed_bytes)
    hashes = compute_hashes(recomputed_canonical)

    if hashes.graph_hash != lock.strategy_hashes.graph_hash:
        failures.append(
            _failure(
                "graph_hash_mismatch",
                "graph_hash differs from the lock",
                path="strategy_hashes.graph_hash",
                expected=lock.strategy_hashes.graph_hash,
                actual=hashes.graph_hash,
            )
        )
    if hashes.param_hash != lock.strategy_hashes.param_hash:
        failures.append(
            _failure(
                "param_hash_mismatch",
                "param_hash differs from the lock",
                path="strategy_hashes.param_hash",
                expected=lock.strategy_hashes.param_hash,
                actual=hashes.param_hash,
            )
        )
    if hashes.instance_hash != lock.strategy_hashes.instance_hash:
        failures.append(
            _failure(
                "instance_hash_mismatch",
                "instance_hash differs from the lock",
                path="strategy_hashes.instance_hash",
                expected=lock.strategy_hashes.instance_hash,
                actual=hashes.instance_hash,
            )
        )

    if recomputed_canonical_hash != lock.canonical_ir_hash and canonical_ir is None:
        failures.append(
            _failure(
                "canonical_ir_tampered",
                "Recomputed canonical IR hash differs from the lock",
                path="canonical_ir_hash",
                expected=lock.canonical_ir_hash,
                actual=recomputed_canonical_hash,
            )
        )

    if canonical_ir is not None:
        provided_bytes = canonical_lock_bytes(to_plain(canonical_ir))
        provided_hash = sha256_bytes(provided_bytes)
        if provided_hash != lock.canonical_ir_hash:
            failures.append(
                _failure(
                    "canonical_ir_tampered",
                    "Provided canonical IR hash differs from the lock",
                    path="canonical_ir_hash",
                    expected=lock.canonical_ir_hash,
                    actual=provided_hash,
                )
            )
        elif provided_bytes != recomputed_bytes:
            failures.append(
                _failure(
                    "surface_canonical_inconsistent",
                    "Provided canonical IR is inconsistent with the surface strategy",
                    path="canonical_ir",
                )
            )

    externals_hash = compute_externals_schema_hash(recomputed_canonical)
    if externals_hash != lock.externals.schema_hash:
        failures.append(
            _failure(
                "externals_schema_hash_mismatch",
                "Externals schema hash differs from the lock",
                path="externals.schema_hash",
                expected=lock.externals.schema_hash,
                actual=externals_hash,
            )
        )

    failures.extend(_check_token_dependencies(lock))
    failures.extend(_check_recipe_dependencies(lock))
    failures.extend(_check_tagspec_dependencies(lock))
    failures.extend(
        _check_fixtures(
            lock,
            market_path=Path(market_path) if market_path is not None else None,
            expected_trace_path=(
                Path(expected_trace_path) if expected_trace_path is not None else None
            ),
        )
    )
    return VerifyResult.from_failures(failures)
