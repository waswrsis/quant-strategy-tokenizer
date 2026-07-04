from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from qst.incubator import (
    ActivationDescriptor,
    ProposalTransition,
    TokenDraft,
    TokenGapEvidence,
    apply_transition,
    create_proposal,
    seal_gap,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


def _proposal():
    gap = seal_gap(
        TokenGapEvidence(
            resolution_hash=HASH_A,
            intent_hash=HASH_B,
            detected_by_actor_id=HASH_C,
            concept="kdj",
            reason_codes=("QST_RESOLVER_NEW_TOKEN_GAP",),
            missing_builtin_surface=("indicator.kdj",),
            input_ports={"series": "TimeSeries[float]"},
            output_ports={"value": "TimeSeries[float]"},
            detected_at=NOW,
        )
    )
    draft = TokenDraft(
        token_id="project.alpha.indicator.kdj",
        namespace="project.alpha",
        authored_by_actor_id=HASH_A,
        requested_by_actor_id=HASH_B,
        contract={"numeric": "semantic_float64"},
    )
    return create_proposal(gap, draft)


def _advance(value, to_status, *, actor_kind="human", review_kind=None, checks=(), activation=None):
    transition = ProposalTransition(
        from_status=value.status,
        to_status=to_status,
        actor_id=HASH_C,
        actor_kind=actor_kind,
        review_kind=review_kind,
        approved=True if review_kind else None,
        evidence_ids=(HASH_A,) if to_status not in {"agent_draft", "published_project_local", "explicit_activation_requested", "builtin_candidate"} else (),
        checklist=checks or ("recorded",),
        reason_codes=("QST_PROPOSAL_GATE_PASSED",),
        occurred_at=NOW,
        activation=activation,
    )
    return apply_transition(value, transition)


def test_complete_lifecycle_separates_publication_and_activation() -> None:
    value = _proposal()
    assert value.proposal_id
    value = _advance(value, "agent_draft", actor_kind="agent")
    value = _advance(
        value,
        "statically_validated",
        actor_kind="system",
        checks=("schema", "namespace", "ports", "params", "boundary"),
    )
    value = _advance(
        value,
        "contract_approved",
        review_kind="contract",
        checks=("semantics", "failure_modes", "numeric", "temporal"),
    )
    value = _advance(
        value,
        "implementation_reviewed",
        review_kind="implementation",
        checks=("source_digest", "security", "determinism"),
    )
    value = _advance(
        value,
        "conformance_passed",
        actor_kind="system",
        checks=("unit_tests", "property_tests", "edge_cases"),
    )
    value = _advance(
        value,
        "publication_approved",
        review_kind="publication",
        checks=("documentation", "versioning", "ownership"),
    )
    value = _advance(value, "published_project_local")
    assert value.status == "published_project_local"
    value = _advance(value, "explicit_activation_requested")
    value = _advance(
        value,
        "activation_approved",
        review_kind="activation",
        checks=("project_scope", "profile", "lock"),
    )
    value = _advance(
        value,
        "active_for_project",
        checks=("token_pack_lock", "profile", "namespace"),
        activation=ActivationDescriptor(
            token_spec_hash=HASH_A,
            token_pack_lock_hash=HASH_B,
            profile="research",
            namespace="project.alpha",
        ),
    )
    assert value.status == "active_for_project"
    assert len(value.transitions) == 10


def test_agent_cannot_approve_publish_or_activate() -> None:
    value = _advance(_proposal(), "agent_draft", actor_kind="agent")
    value = _advance(
        value,
        "statically_validated",
        actor_kind="system",
        checks=("schema", "namespace", "ports", "params", "boundary"),
    )
    with pytest.raises(ValidationError, match="approved human contract review"):
        _advance(
            value,
            "contract_approved",
            actor_kind="agent",
            review_kind="contract",
            checks=("semantics", "failure_modes", "numeric", "temporal"),
        )


def test_static_and_conformance_gates_require_system_and_complete_checklists() -> None:
    value = _advance(_proposal(), "agent_draft", actor_kind="agent")
    with pytest.raises(ValidationError, match="missing checks"):
        _advance(value, "statically_validated", actor_kind="system", checks=("schema",))
    with pytest.raises(ValidationError, match="system validation"):
        _advance(
            value,
            "statically_validated",
            actor_kind="agent",
            checks=("schema", "namespace", "ports", "params", "boundary"),
        )


def test_draft_cannot_use_core_namespace_or_runtime_executor() -> None:
    with pytest.raises(ValidationError, match="cannot be core"):
        TokenDraft(
            token_id="core.indicator.kdj",
            namespace="core",
            authored_by_actor_id=HASH_A,
            requested_by_actor_id=HASH_B,
            contract={},
        )
    with pytest.raises(ValidationError):
        TokenDraft(
            token_id="project.alpha.indicator.kdj",
            namespace="project.alpha",
            authored_by_actor_id=HASH_A,
            requested_by_actor_id=HASH_B,
            contract={},
            execution_support="runtime_executor",
        )


def test_transition_cannot_skip_states() -> None:
    with pytest.raises(ValidationError, match="invalid proposal transition"):
        _advance(_proposal(), "contract_approved", review_kind="contract")


def test_transition_requires_a_sealed_current_proposal() -> None:
    proposal = _proposal().model_copy(update={"proposal_id": None})
    transition = ProposalTransition(
        from_status="detected",
        to_status="agent_draft",
        actor_id=HASH_C,
        actor_kind="agent",
        checklist=("recorded",),
        reason_codes=("QST_PROPOSAL_DRAFTED",),
        occurred_at=NOW,
    )
    with pytest.raises(ValueError, match="current proposal must be sealed"):
        apply_transition(proposal, transition)


def test_proposal_history_rejects_unsealed_transitions() -> None:
    proposal = _proposal()
    transition = ProposalTransition(
        from_status="detected",
        to_status="agent_draft",
        actor_id=HASH_C,
        actor_kind="agent",
        checklist=("recorded",),
        reason_codes=("QST_PROPOSAL_DRAFTED",),
        occurred_at=NOW,
    )
    with pytest.raises(ValidationError, match="proposal transitions must be sealed"):
        proposal.__class__(
            gap_id=proposal.gap_id,
            draft=proposal.draft,
            status="agent_draft",
            transitions=(transition,),
        )
