"""qst.lock version policy checks."""

from __future__ import annotations

from quant_strategy_tokenizer.qst_lock.schema import LockFile
from quant_strategy_tokenizer.qst_lock.verify_result import VerifyFailure


def check_version_policy(lock: LockFile, current_qst_version: str) -> list[VerifyFailure]:
    """Return failures for P3a-0 qst version policy checks."""

    if lock.qst_version_policy != "strict":
        return [
            VerifyFailure(
                kind="qst_version_policy_unsupported",
                message=(
                    f"qst_version_policy={lock.qst_version_policy!r} is unsupported "
                    "in P3a-0"
                ),
                path="qst_version_policy",
                expected="strict",
                actual=lock.qst_version_policy,
            )
        ]

    if lock.qst_version != current_qst_version:
        return [
            VerifyFailure(
                kind="qst_version_mismatch",
                message="qst_version differs from the installed QST version",
                path="qst_version",
                expected=lock.qst_version,
                actual=current_qst_version,
            )
        ]

    return []
