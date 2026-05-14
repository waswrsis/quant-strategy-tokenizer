from __future__ import annotations

from quant_strategy_tokenizer.provenance.spec import VerificationStatus


def test_minimally_attached_requires_attachment_hash_and_namespace() -> None:
    status = VerificationStatus(
        tag_attached_by_trusted=True,
        graph_template_hash_valid=True,
        namespace_allowed=True,
    )

    assert status.minimally_attached is True
    assert status.fully_verified is False


def test_fully_verified_requires_p2a3_checks() -> None:
    status = VerificationStatus(
        tag_attached_by_trusted=True,
        graph_template_hash_valid=True,
        namespace_allowed=True,
        contracts_pass=True,
        fuzzing_at_ci_standard=True,
        metamorphic_pass=True,
    )

    assert status.minimally_attached is True
    assert status.fully_verified is True
