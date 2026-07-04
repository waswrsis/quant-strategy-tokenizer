"""Mode-aware authority entrypoints for claims, proposals, and customization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from qst.attestations import Attestation, attestation_identity
from qst.claims import ClaimDecision, ClaimPolicy, evaluate_claim
from qst.customization import (
    CustomizationDeclaration,
    CustomizationResult,
    apply_customizations,
)
from qst.evidence import EvidenceEnvelope
from qst.hash.common import HashString
from qst.incubator import ProposalTransition, TokenProposal, apply_transition, seal_transition
from qst.incubator.models import ProposalStatus

from .evaluator import authority_not_evaluated, authorize_bundle
from .models import (
    AuthorityDecision,
    AuthorityMode,
    AuthorityRegistry,
    GovernanceAction,
    GovernanceBundle,
    SignedDelegation,
    authority_decision_identity,
)

TRANSITION_ACTIONS: dict[ProposalStatus, GovernanceAction] = {
    "contract_approved": "token_contract_approve",
    "implementation_reviewed": "token_implementation_approve",
    "publication_approved": "token_publication_approve",
    "published_project_local": "token_publish",
    "activation_approved": "token_activation_approve",
    "active_for_project": "token_activate",
    "builtin_candidate": "token_builtin_nominate",
}


class AuthorityBoundClaimResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: AuthorityMode
    claim_decision: ClaimDecision
    authority_decisions: tuple[AuthorityDecision, ...]
    authority_satisfied: bool
    proceed: bool
    issues: tuple[str, ...] = ()


class AuthorityBoundTransitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: AuthorityMode
    proposal: TokenProposal | None
    authority_decision: AuthorityDecision
    applied: bool
    issues: tuple[str, ...] = ()


class AuthorityBoundCustomizationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: AuthorityMode
    result: CustomizationResult | None
    authority_decisions: tuple[AuthorityDecision, ...]
    applied: bool
    issues: tuple[str, ...] = ()


def evaluate_claim_with_authority(
    policy: ClaimPolicy,
    evidence: tuple[EvidenceEnvelope, ...],
    attestations: tuple[Attestation, ...],
    *,
    subject_ref: str,
    evaluated_at: datetime,
    mode: AuthorityMode = "record_only",
    attestation_bundles: dict[HashString, GovernanceBundle] | None = None,
    registry: AuthorityRegistry | None = None,
    delegations: tuple[SignedDelegation, ...] = (),
) -> AuthorityBoundClaimResult:
    """Evaluate a claim while keeping authority facts separate from claim facts."""

    attestation_bundles = {} if attestation_bundles is None else attestation_bundles
    usable_attestations: list[Attestation] = []
    decisions: list[AuthorityDecision] = []
    issues: list[str] = []
    authority_satisfied = True
    for attestation in attestations:
        if (
            attestation.attestation_id is None
            or attestation.attestation_id != attestation_identity(attestation)
        ):
            issues.append("QST_AUTHORITY_ATTESTATION_UNSEALED_OR_TAMPERED")
            authority_satisfied = False
            continue
        adapter_id = attestation.statement.get("adapter_id")
        scope = adapter_id if isinstance(adapter_id, str) and adapter_id else "unknown.adapter"
        decision, binding_issues = _authorize_optional_bundle(
            attestation_bundles.get(attestation.attestation_id),
            registry,
            action="attestation_issue",
            subject_id=attestation.attestation_id,
            scope=scope,
            evaluated_at=evaluated_at,
            mode=mode,
            delegations=delegations,
        )
        decisions.append(decision)
        issues.extend(binding_issues)
        bound = decision.authorized is True and not binding_issues and bool(adapter_id)
        authority_satisfied = authority_satisfied and bound
        if mode != "enforce" or bound:
            usable_attestations.append(attestation)

    claim_decision = evaluate_claim(
        policy,
        evidence,
        tuple(usable_attestations),
        subject_ref=subject_ref,
        evaluated_at=evaluated_at,
    )
    return AuthorityBoundClaimResult(
        mode=mode,
        claim_decision=claim_decision,
        authority_decisions=_ordered_decisions(decisions),
        authority_satisfied=authority_satisfied,
        proceed=mode != "enforce" or authority_satisfied,
        issues=_ordered_issues(issues),
    )


def apply_transition_with_authority(
    proposal: TokenProposal,
    transition: ProposalTransition,
    *,
    evaluated_at: datetime,
    mode: AuthorityMode = "record_only",
    bundle: GovernanceBundle | None = None,
    registry: AuthorityRegistry | None = None,
    delegations: tuple[SignedDelegation, ...] = (),
) -> AuthorityBoundTransitionResult:
    """Apply a governed transition unless explicit enforcement rejects it."""

    action = TRANSITION_ACTIONS.get(transition.to_status)
    if action is None:
        raise ValueError(f"transition does not use an authority gate: {transition.to_status}")
    if transition.transition_id is None:
        transition = seal_transition(transition)
    assert transition.transition_id is not None
    decision, issues = _authorize_optional_bundle(
        bundle,
        registry,
        action=action,
        subject_id=transition.transition_id,
        scope=proposal.draft.namespace,
        evaluated_at=evaluated_at,
        mode=mode,
        delegations=delegations,
    )
    actor_bound = transition.actor_id in decision.signer_actor_ids
    if not actor_bound:
        issues.append("QST_AUTHORITY_TRANSITION_ACTOR_NOT_SIGNER")
    principal = None
    if registry is not None:
        principal = next(
            (item for item in registry.principals if item.actor_id == transition.actor_id), None
        )
    human_bound = principal is not None and principal.actor_kind == "human"
    if not human_bound:
        issues.append("QST_AUTHORITY_TRANSITION_ACTOR_NOT_REGISTERED_HUMAN")
    authority_satisfied = decision.authorized is True and actor_bound and human_bound and not issues
    if mode == "enforce" and not authority_satisfied:
        return AuthorityBoundTransitionResult(
            mode=mode,
            proposal=None,
            authority_decision=decision,
            applied=False,
            issues=_ordered_issues(issues),
        )
    return AuthorityBoundTransitionResult(
        mode=mode,
        proposal=apply_transition(proposal, transition),
        authority_decision=decision,
        applied=True,
        issues=_ordered_issues(issues),
    )


def apply_customizations_with_authority(
    base: dict[str, object],
    declarations: tuple[CustomizationDeclaration, ...],
    *,
    evaluated_at: datetime,
    mode: AuthorityMode = "record_only",
    approval_bundles: dict[HashString, GovernanceBundle] | None = None,
    registry: AuthorityRegistry | None = None,
    delegations: tuple[SignedDelegation, ...] = (),
) -> AuthorityBoundCustomizationResult:
    """Apply declared overlays, enforcing authority only in explicit enforce mode."""

    approval_bundles = {} if approval_bundles is None else approval_bundles
    approvals: dict[str, HashString] = {}
    decisions: list[AuthorityDecision] = []
    issues: list[str] = []
    authority_satisfied = True
    for declaration in declarations:
        if not declaration.approval_required:
            continue
        if declaration.customization_id is None:
            raise ValueError("customization declaration must be sealed")
        decision, binding_issues = _authorize_optional_bundle(
            approval_bundles.get(declaration.customization_id),
            registry,
            action="customization_approve",
            subject_id=declaration.customization_id,
            scope=declaration.scope,
            evaluated_at=evaluated_at,
            mode=mode,
            delegations=delegations,
        )
        decisions.append(decision)
        issues.extend(binding_issues)
        satisfied = decision.authorized is True and not binding_issues
        authority_satisfied = authority_satisfied and satisfied
        if decision.decision_id is None:
            raise ValueError("authority decision must be sealed")
        if mode != "enforce" or satisfied:
            # The referenced decision says whether authorization was actually proven.
            approvals[declaration.customization_id] = decision.decision_id

    if mode == "enforce" and not authority_satisfied:
        return AuthorityBoundCustomizationResult(
            mode=mode,
            result=None,
            authority_decisions=_ordered_decisions(decisions),
            applied=False,
            issues=_ordered_issues(issues),
        )
    result = apply_customizations(base, declarations, approvals=approvals)
    return AuthorityBoundCustomizationResult(
        mode=mode,
        result=result,
        authority_decisions=_ordered_decisions(decisions),
        applied=True,
        issues=_ordered_issues(issues),
    )


def _authorize_optional_bundle(
    bundle: GovernanceBundle | None,
    registry: AuthorityRegistry | None,
    *,
    action: GovernanceAction,
    subject_id: HashString,
    scope: str,
    evaluated_at: datetime,
    mode: AuthorityMode,
    delegations: tuple[SignedDelegation, ...],
) -> tuple[AuthorityDecision, list[str]]:
    issues: list[str] = []
    if registry is None:
        issues.append("QST_AUTHORITY_REGISTRY_NOT_PROVIDED")
    if bundle is None:
        issues.append("QST_AUTHORITY_BUNDLE_NOT_PROVIDED")
    if registry is None or bundle is None:
        return (
            authority_not_evaluated(
                action=action,
                subject_id=subject_id,
                evaluated_at=evaluated_at,
                mode=mode,
                registry=registry,
                reason_codes=tuple(issues),
            ),
            issues,
        )
    statement = bundle.statement
    if statement.action != action:
        issues.append(f"QST_AUTHORITY_ACTION_MISMATCH:{action}")
    if statement.subject_id != subject_id:
        issues.append("QST_AUTHORITY_SUBJECT_MISMATCH")
    if statement.scope != scope:
        issues.append("QST_AUTHORITY_SCOPE_MISMATCH")
    if issues:
        return (
            authority_not_evaluated(
                action=action,
                subject_id=subject_id,
                evaluated_at=evaluated_at,
                mode=mode,
                registry=registry,
                reason_codes=tuple(issues),
            ),
            issues,
        )
    decision = authorize_bundle(
        bundle,
        registry,
        evaluated_at=evaluated_at,
        mode=mode,
        delegations=delegations,
    )
    if decision.decision_id is None or decision.decision_id != authority_decision_identity(decision):
        raise ValueError("authority decision must be sealed and untampered")
    return decision, issues


def _ordered_decisions(decisions: list[AuthorityDecision]) -> tuple[AuthorityDecision, ...]:
    return tuple(sorted(decisions, key=lambda item: item.decision_id or ""))


def _ordered_issues(issues: list[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(issues)))
