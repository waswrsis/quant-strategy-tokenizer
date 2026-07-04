from __future__ import annotations

import pytest

from qst.resolver import (
    RecipeSpec,
    ResolverPolicy,
    TokenGapResolver,
    TokenIntent,
    TokenProposalSummary,
    vocabulary_snapshot,
)
from qst.resolver.identity import resolver_hash
from qst.tokens import TokenRegistryV2, builtin_token_packs


def _snapshot():
    return vocabulary_snapshot(TokenRegistryV2.from_packs(builtin_token_packs()))


def test_vocabulary_snapshot_is_independent_of_pack_input_order() -> None:
    packs = builtin_token_packs()
    forward = vocabulary_snapshot(TokenRegistryV2.from_packs(packs))
    reverse = vocabulary_snapshot(TokenRegistryV2.from_packs(reversed(packs)))
    assert forward == reverse


def test_exact_and_alias_matches_are_deterministic() -> None:
    snapshot = _snapshot()
    exact = TokenGapResolver(snapshot).resolve(
        TokenIntent(concept="core.math.add", requested_token_id="core.math.add")
    )
    alias = TokenGapResolver(snapshot, aliases={"sum-series": "core.math.add"}).resolve(
        TokenIntent(concept="sum-series")
    )
    assert exact.route == "direct_token_match"
    assert exact.candidates[0].status == "exact_compatible"
    assert alias.route == "direct_token_match"
    assert alias.candidates[0].status == "alias_compatible"
    assert exact.identity.alias_catalog_hash != alias.identity.alias_catalog_hash


def test_version_mismatch_is_collected_before_new_gap_route() -> None:
    result = TokenGapResolver(_snapshot()).resolve(
        TokenIntent(
            concept="core.math.add",
            requested_token_id="core.math.add",
            version=99,
            behavior_version=1,
        )
    )
    assert result.route == "new_token_gap"
    assert result.candidates[0].status == "version_incompatible"
    assert "version" in result.candidates[0].incompatibilities


def test_type_and_param_failures_are_complete_sibling_facts() -> None:
    intent = TokenIntent(
        concept="core.indicator.ema",
        requested_token_id="core.indicator.ema",
        inputs={"series": "TimeSeries[bool]"},
        params={"window": 0, "unexpected": 1},
    )
    result = TokenGapResolver(_snapshot()).resolve(intent)
    candidate = result.candidates[0]
    assert result.route == "new_token_gap"
    assert not candidate.types_compatible
    assert not candidate.params_compatible
    assert "input_type:series" in candidate.incompatibilities
    assert "param_minimum:window" in candidate.incompatibilities
    assert "param_unknown:unexpected" in candidate.incompatibilities


def test_recipe_precedes_existing_proposal_but_both_catalogs_are_hashed() -> None:
    recipe = RecipeSpec(
        recipe_id="recipe.sum",
        concepts=("combined-series",),
        token_refs=("core.math.add/v1/bv1",),
    )
    proposal = TokenProposalSummary(
        proposal_id="proposal.combined-series",
        concept="combined-series",
        status="agent_draft",
        proposed_token_id="local.combined_series",
        proposal_hash=resolver_hash("qst:token-proposal:v1", {"id": "proposal"}),
    )
    result = TokenGapResolver(_snapshot(), recipes=(recipe,), proposals=(proposal,)).resolve(
        TokenIntent(concept="combined-series")
    )
    assert result.route == "recipe_match"
    assert result.matched_recipe_id == "recipe.sum"
    assert result.identity.proposal_catalog_hash


def test_incompatible_recipe_interface_falls_through_to_existing_proposal() -> None:
    recipe = RecipeSpec(
        recipe_id="recipe.bool-only",
        concepts=("combined-series",),
        token_refs=("core.math.add/v1/bv1",),
        inputs={"series": "TimeSeries[bool]"},
    )
    proposal = TokenProposalSummary(
        proposal_id="proposal.combined-series",
        concept="combined-series",
        status="agent_draft",
        proposed_token_id="local.combined_series",
        proposal_hash=resolver_hash("qst:token-proposal:v1", {"id": "proposal"}),
    )
    result = TokenGapResolver(_snapshot(), recipes=(recipe,), proposals=(proposal,)).resolve(
        TokenIntent(concept="combined-series", inputs={"series": "TimeSeries[float]"})
    )
    assert result.route == "existing_proposal"


def test_existing_proposal_prevents_duplicate_gap() -> None:
    proposal = TokenProposalSummary(
        proposal_id="proposal.kdj",
        concept="kdj",
        status="statically_validated",
        proposed_token_id="local.indicator.kdj",
        proposal_hash=resolver_hash("qst:token-proposal:v1", {"id": "kdj"}),
    )
    result = TokenGapResolver(_snapshot(), proposals=(proposal,)).resolve(
        TokenIntent(concept="kdj")
    )
    assert result.route == "existing_proposal"
    assert result.matched_proposal_id == "proposal.kdj"


def test_non_goal_precedes_reserved_and_reserved_precedes_token_match() -> None:
    non_goal = TokenGapResolver(_snapshot()).resolve(
        TokenIntent(
            concept="core.event.filter",
            requested_token_id="core.event.filter",
            required_types=("EventStream",),
            runtime_requirements=("live_execution",),
        )
    )
    reserved = TokenGapResolver(_snapshot()).resolve(
        TokenIntent(concept="core.event.filter", requested_token_id="core.event.filter")
    )
    assert non_goal.route == "non_goal_runtime"
    assert non_goal.boundary_terms == ("live_execution",)
    assert reserved.route == "reserved_typespec"
    assert reserved.candidates[0].reserved


def test_unknown_runtime_is_non_goal_but_evidence_collection_is_not() -> None:
    unknown = TokenGapResolver(_snapshot()).resolve(
        TokenIntent(concept="new-concept", runtime_requirements=("arbitrary_executor",))
    )
    collection = TokenGapResolver(_snapshot()).resolve(
        TokenIntent(concept="new-concept", runtime_requirements=("artifact_collection",))
    )
    assert unknown.route == "non_goal_runtime"
    assert collection.route == "new_token_gap"


def test_invalid_intent_has_stable_route_and_issue() -> None:
    result = TokenGapResolver(_snapshot()).resolve({"concept": ""})
    assert result.route == "invalid_intent"
    assert result.intent is None
    assert {issue.code for issue in result.issues} == {"QST_RESOLVER_INVALID_INTENT"}


def test_policy_route_order_is_immutable_in_v1() -> None:
    data = ResolverPolicy().model_dump(mode="json")
    data["route_precedence"][1], data["route_precedence"][2] = (
        data["route_precedence"][2],
        data["route_precedence"][1],
    )
    with pytest.raises(ValueError, match="route_precedence is immutable"):
        ResolverPolicy.model_validate(data)
