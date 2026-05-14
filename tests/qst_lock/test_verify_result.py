from __future__ import annotations

from quant_strategy_tokenizer.qst_lock.verify_result import (
    P3A0_LIMITATION_NOTE,
    VerificationLevel,
    VerifyFailure,
    VerifyResult,
)


def test_verify_result_is_structured_and_not_numerical() -> None:
    result = VerifyResult.from_failures(
        [VerifyFailure(kind="instance_hash_mismatch", message="bad")]
    )

    assert not result.ok
    assert result.verification_level.value == "STRUCTURAL"
    assert VerificationLevel.NUMERICAL.value == "NUMERICAL"
    assert result.limitation_note == P3A0_LIMITATION_NOTE
    assert result.failures[0].kind == "instance_hash_mismatch"
