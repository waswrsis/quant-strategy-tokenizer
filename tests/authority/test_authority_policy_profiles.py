from __future__ import annotations

import pytest
from pydantic import ValidationError

from qst.authority import (
    AUTHORITY_USE_CASES,
    AuthorityPolicyProfile,
    AuthorityPolicyRule,
    authority_mode_selection_identity,
    authority_policy_profile_identity,
    controlled_release_profile,
    record_capture_profile,
    research_advisory_profile,
    select_authority_mode,
    strict_governance_profile,
)


def test_builtin_profiles_are_complete_sealed_and_deterministic() -> None:
    profiles = (
        record_capture_profile(),
        research_advisory_profile(),
        controlled_release_profile(),
        strict_governance_profile(),
    )
    assert len({item.profile_hash for item in profiles}) == len(profiles)
    for profile in profiles:
        assert tuple(item.use_case for item in profile.rules) == AUTHORITY_USE_CASES
        assert profile.profile_hash == authority_policy_profile_identity(profile)
    assert record_capture_profile() == record_capture_profile()


def test_profiles_map_use_cases_without_hidden_strictness() -> None:
    research = research_advisory_profile()
    controlled = controlled_release_profile()
    strict = strict_governance_profile()

    assert research.mode_for("record_ingestion") == "record_only"
    assert research.mode_for("token_review") == "advisory"
    assert research.mode_for("token_publication") == "enforce"
    assert research.mode_for("token_activation") == "enforce"
    assert research.mode_for("customization") == "advisory"
    assert controlled.mode_for("customization") == "enforce"
    assert all(strict.mode_for(use_case) == "enforce" for use_case in AUTHORITY_USE_CASES)


def test_mode_override_is_identity_bearing_and_requires_reason() -> None:
    profile = research_advisory_profile()
    with pytest.raises(ValidationError, match="override requires a reason"):
        select_authority_mode(
            "token_review",
            profile=profile,
            mode_override="enforce",
        )

    selection = select_authority_mode(
        "token_review",
        profile=profile,
        mode_override="enforce",
        override_reason="Release review requires a strict gate.",
    )
    assert selection.configured_mode == "advisory"
    assert selection.effective_mode == "enforce"
    assert selection.override_applied
    assert selection.selection_id == authority_mode_selection_identity(selection)


def test_unsealed_or_incomplete_profile_is_rejected() -> None:
    with pytest.raises(ValidationError, match="every use case"):
        AuthorityPolicyProfile(
            profile_id="incomplete",
            version=1,
            description="Missing most use cases.",
            rules=(AuthorityPolicyRule(use_case="record_ingestion", mode="record_only"),),
        )

    profile = research_advisory_profile()
    tampered = profile.model_copy(update={"description": "Changed after sealing."})
    with pytest.raises(ValueError, match="sealed and untampered"):
        select_authority_mode("claim_evaluation", profile=tampered)
