from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from qst.attestations import Attestation, seal_attestation
from qst.authority import (
    AuthorityDecision,
    AuthorityPrincipal,
    AuthorityRegistry,
    DelegationGrant,
    GovernanceStatement,
    QuorumRule,
    RevocationRecord,
    SignedDelegation,
    apply_customizations_with_authority,
    apply_transition_with_authority,
    authority_key_from_public_key,
    authorize_bundle,
    build_governance_bundle,
    evaluate_claim_with_authority,
    seal_authority_registry,
    seal_delegation,
    seal_governance_statement,
    seal_revocation,
    seal_signature,
    sign_governance_statement,
)
from qst.claims import ClaimPolicy, EvidenceRequirement, seal_claim_policy
from qst.customization import (
    CustomizationDeclaration,
    CustomizationOperation,
    seal_customization,
)
from qst.evidence import EvidenceEnvelope, ResultEvidencePayload, seal_evidence
from qst.identity import identity_hash
from qst.incubator import (
    ProposalTransition,
    TokenDraft,
    TokenGapEvidence,
    apply_transition,
    create_proposal,
    seal_gap,
    seal_transition,
)

NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)
EXPIRES = NOW + timedelta(hours=1)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64


def _authority_fixture() -> tuple[AuthorityRegistry, dict[str, Ed25519PrivateKey]]:
    actors = {
        "alice": HASH_A,
        "bob": HASH_B,
        "carol": HASH_C,
        "agent": HASH_D,
    }
    private_keys = {name: Ed25519PrivateKey.generate() for name in actors}
    keys = {
        name: authority_key_from_public_key(
            actor_id=actor_id,
            public_key=private_keys[name].public_key(),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        )
        for name, actor_id in actors.items()
    }
    principals = (
        AuthorityPrincipal(
            actor_id=HASH_A,
            actor_kind="human",
            roles=(
                "attestation_issuer",
                "authority_delegator",
                "customization_approver",
                "token_contract_reviewer",
                "token_publisher",
            ),
            scopes=(
                "authority.registry",
                "project.alpha",
                "qst.ai4finance.finrobot",
                "strategy.parameters",
            ),
            keys=(keys["alice"],),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
        AuthorityPrincipal(
            actor_id=HASH_B,
            actor_kind="human",
            roles=("token_publisher",),
            scopes=("project.alpha",),
            keys=(keys["bob"],),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
        AuthorityPrincipal(
            actor_id=HASH_C,
            actor_kind="human",
            keys=(keys["carol"],),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
        AuthorityPrincipal(
            actor_id=HASH_D,
            actor_kind="agent",
            roles=("token_publisher",),
            scopes=("project.alpha",),
            keys=(keys["agent"],),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
    )
    rules = (
        QuorumRule(
            action="attestation_issue",
            required_role="attestation_issuer",
            quorum=1,
        ),
        QuorumRule(
            action="authority_delegate",
            required_role="authority_delegator",
            quorum=1,
            require_human=True,
        ),
        QuorumRule(
            action="customization_approve",
            required_role="customization_approver",
            quorum=1,
            require_human=True,
        ),
        QuorumRule(
            action="token_contract_approve",
            required_role="token_contract_reviewer",
            quorum=1,
            require_human=True,
        ),
        QuorumRule(
            action="token_publication_approve",
            required_role="token_publisher",
            quorum=2,
            require_human=True,
        ),
    )
    registry = seal_authority_registry(
        AuthorityRegistry(
            registry_id="project-alpha-authorities",
            version=1,
            principals=principals,
            rules=rules,
        )
    )
    return registry, private_keys


def _key(registry: AuthorityRegistry, actor_id: str):
    principal = next(item for item in registry.principals if item.actor_id == actor_id)
    return principal.keys[0]


def _statement(
    *, action: str, subject_id: str = HASH_C, scope: str = "project.alpha"
) -> GovernanceStatement:
    return seal_governance_statement(
        GovernanceStatement(
            action=action,
            subject_id=subject_id,
            scope=scope,
            decision="approve",
            reason_codes=("QST_GOVERNANCE_REVIEWED",),
            issued_at=NOW,
            expires_at=EXPIRES,
            nonce="0123456789abcdef",
        )
    )


def _bundle(
    statement: GovernanceStatement,
    registry: AuthorityRegistry,
    private_keys: dict[str, Ed25519PrivateKey],
    signers: tuple[tuple[str, str], ...],
):
    signatures = tuple(
        sign_governance_statement(
            statement,
            key=_key(registry, actor_id),
            private_key=private_keys[name],
            signed_at=LATER,
        )
        for name, actor_id in signers
    )
    return build_governance_bundle(statement, signatures)


def test_ed25519_quorum_requires_distinct_registered_humans() -> None:
    registry, private_keys = _authority_fixture()
    statement = _statement(action="token_publication_approve")
    one = _bundle(statement, registry, private_keys, (("alice", HASH_A),))
    two = _bundle(
        statement,
        registry,
        private_keys,
        (("alice", HASH_A), ("bob", HASH_B)),
    )
    agent = _bundle(
        statement,
        registry,
        private_keys,
        (("alice", HASH_A), ("agent", HASH_D)),
    )
    assert not authorize_bundle(one, registry, evaluated_at=LATER).allowed
    allowed = authorize_bundle(two, registry, evaluated_at=LATER)
    assert allowed.allowed
    assert allowed.signer_actor_ids == (HASH_A, HASH_B)
    assert not authorize_bundle(agent, registry, evaluated_at=LATER).allowed


def test_authority_modes_separate_authorization_from_record_progression() -> None:
    registry, private_keys = _authority_fixture()
    statement = _statement(action="token_publication_approve")
    one = _bundle(statement, registry, private_keys, (("alice", HASH_A),))

    record_only = authorize_bundle(one, registry, evaluated_at=LATER)
    advisory = authorize_bundle(one, registry, evaluated_at=LATER, mode="advisory")
    enforce = authorize_bundle(one, registry, evaluated_at=LATER, mode="enforce")

    assert record_only.authorized is False
    assert record_only.proceed
    assert record_only.mode == "record_only"
    assert advisory.authorized is False
    assert advisory.proceed
    assert "QST_AUTHORITY_ADVISORY_NOT_ENFORCED" in advisory.reason_codes
    assert enforce.authorized is False
    assert not enforce.proceed
    with pytest.raises(ValidationError, match="requires registry and bundle"):
        AuthorityDecision(
            action="token_publication_approve",
            subject_id=HASH_A,
            mode="record_only",
            authorized=True,
            proceed=True,
            reason_codes=("QST_AUTHORITY_ALLOWED",),
            evaluated_at=LATER,
        )


def test_signature_tamper_expiry_replay_and_registry_tamper_are_rejected() -> None:
    registry, private_keys = _authority_fixture()
    statement = _statement(action="token_publication_approve")
    bundle = _bundle(
        statement,
        registry,
        private_keys,
        (("alice", HASH_A), ("bob", HASH_B)),
    )
    first_signature = bundle.signatures[0]
    raw = bytearray(__import__("base64").b64decode(first_signature.signature_b64))
    raw[0] ^= 1
    tampered_signature = seal_signature(
        first_signature.model_copy(
            update={
                "signature_id": None,
                "signature_b64": __import__("base64").b64encode(bytes(raw)).decode("ascii"),
            }
        )
    )
    tampered = build_governance_bundle(
        statement, (tampered_signature, bundle.signatures[1])
    )
    assert not authorize_bundle(tampered, registry, evaluated_at=LATER).allowed
    assert not authorize_bundle(
        bundle, registry, evaluated_at=EXPIRES + timedelta(seconds=1)
    ).allowed
    replay = authorize_bundle(
        bundle,
        registry,
        evaluated_at=LATER,
        consumed_bundle_ids=frozenset({bundle.bundle_id}),
    )
    assert not replay.allowed
    assert "QST_AUTHORITY_BUNDLE_REPLAYED" in replay.reason_codes
    with pytest.raises(ValueError, match="sealed and untampered"):
        authorize_bundle(
            bundle,
            registry.model_copy(update={"version": 2}),
            evaluated_at=LATER,
        )


def test_key_revocation_reduces_quorum() -> None:
    registry, private_keys = _authority_fixture()
    statement = _statement(action="token_publication_approve")
    bundle = _bundle(
        statement,
        registry,
        private_keys,
        (("alice", HASH_A), ("bob", HASH_B)),
    )
    bob_key = _key(registry, HASH_B)
    assert bob_key.key_id is not None
    revocation = seal_revocation(
        RevocationRecord(
            target_type="key",
            target_id=bob_key.key_id,
            effective_at=NOW,
            reason_codes=("QST_AUTHORITY_KEY_COMPROMISED",),
        )
    )
    revoked_registry = seal_authority_registry(
        registry.model_copy(
            update={
                "registry_hash": None,
                "version": 2,
                "revocations": (revocation,),
            }
        )
    )
    assert not authorize_bundle(bundle, revoked_registry, evaluated_at=LATER).allowed


def _signed_delegation(
    registry: AuthorityRegistry,
    private_keys: dict[str, Ed25519PrivateKey],
) -> SignedDelegation:
    grant = seal_delegation(
        DelegationGrant(
            delegator_actor_id=HASH_A,
            delegate_actor_id=HASH_C,
            role="token_contract_reviewer",
            scopes=("project.alpha",),
            valid_from=NOW,
            valid_until=EXPIRES,
            nonce="delegation-00001",
        )
    )
    assert grant.delegation_id is not None
    statement = _statement(
        action="authority_delegate",
        subject_id=grant.delegation_id,
        scope="authority.registry",
    )
    return SignedDelegation(
        grant=grant,
        authorization=_bundle(statement, registry, private_keys, (("alice", HASH_A),)),
    )


def test_non_transitive_delegation_grants_role_and_can_be_revoked() -> None:
    registry, private_keys = _authority_fixture()
    delegation = _signed_delegation(registry, private_keys)
    statement = _statement(action="token_contract_approve")
    bundle = _bundle(statement, registry, private_keys, (("carol", HASH_C),))
    assert not authorize_bundle(bundle, registry, evaluated_at=LATER).allowed
    assert authorize_bundle(
        bundle, registry, evaluated_at=LATER, delegations=(delegation,)
    ).allowed

    assert delegation.grant.delegation_id is not None
    revocation = seal_revocation(
        RevocationRecord(
            target_type="delegation",
            target_id=delegation.grant.delegation_id,
            effective_at=NOW,
            reason_codes=("QST_AUTHORITY_DELEGATION_REVOKED",),
        )
    )
    revoked_registry = seal_authority_registry(
        registry.model_copy(
            update={
                "registry_hash": None,
                "version": 2,
                "revocations": (revocation,),
            }
        )
    )
    assert not authorize_bundle(
        bundle,
        revoked_registry,
        evaluated_at=LATER,
        delegations=(delegation,),
    ).allowed
    with pytest.raises(ValidationError, match="cannot be delegated"):
        DelegationGrant(
            delegator_actor_id=HASH_A,
            delegate_actor_id=HASH_C,
            role="authority_delegator",
            scopes=("authority.registry",),
            valid_from=NOW,
            valid_until=EXPIRES,
            nonce="delegation-00002",
        )


def _proposal_at_static_validation():
    gap = seal_gap(
        TokenGapEvidence(
            resolution_hash=HASH_A,
            intent_hash=HASH_B,
            detected_by_actor_id=HASH_D,
            concept="project indicator",
            reason_codes=("QST_RESOLVER_NEW_TOKEN_GAP",),
            missing_builtin_surface=("project.alpha.indicator",),
            input_ports={"series": "TimeSeries[float]"},
            output_ports={"value": "TimeSeries[float]"},
            detected_at=NOW,
        )
    )
    proposal = create_proposal(
        gap,
        TokenDraft(
            token_id="project.alpha.indicator.custom",
            namespace="project.alpha",
            authored_by_actor_id=HASH_D,
            requested_by_actor_id=HASH_A,
            contract={"numeric": "semantic_float64"},
        ),
    )
    proposal = apply_transition(
        proposal,
        ProposalTransition(
            from_status="detected",
            to_status="agent_draft",
            actor_id=HASH_D,
            actor_kind="agent",
            checklist=("recorded",),
            reason_codes=("QST_PROPOSAL_DRAFTED",),
            occurred_at=NOW,
        ),
    )
    return apply_transition(
        proposal,
        ProposalTransition(
            from_status="agent_draft",
            to_status="statically_validated",
            actor_id=HASH_D,
            actor_kind="system",
            evidence_ids=(HASH_A,),
            checklist=("schema", "namespace", "ports", "params", "boundary"),
            reason_codes=("QST_PROPOSAL_STATIC_VALID",),
            occurred_at=NOW,
        ),
    )


def test_token_transition_binds_human_actor_subject_scope_and_signature() -> None:
    registry, private_keys = _authority_fixture()
    proposal = _proposal_at_static_validation()
    transition = seal_transition(
        ProposalTransition(
            from_status="statically_validated",
            to_status="contract_approved",
            actor_id=HASH_A,
            actor_kind="human",
            review_kind="contract",
            approved=True,
            evidence_ids=(HASH_B,),
            checklist=("semantics", "failure_modes", "numeric", "temporal"),
            reason_codes=("QST_PROPOSAL_CONTRACT_APPROVED",),
            occurred_at=LATER,
        )
    )
    assert transition.transition_id is not None
    statement = _statement(
        action="token_contract_approve",
        subject_id=transition.transition_id,
        scope="project.alpha",
    )
    bundle = _bundle(statement, registry, private_keys, (("alice", HASH_A),))
    result = apply_transition_with_authority(
        proposal,
        transition,
        bundle=bundle,
        registry=registry,
        evaluated_at=LATER,
        mode="enforce",
    )
    assert result.applied
    assert result.proposal is not None
    assert result.proposal.status == "contract_approved"
    assert result.authority_decision.allowed

    recorded = apply_transition_with_authority(
        proposal,
        transition,
        evaluated_at=LATER,
    )
    assert recorded.applied
    assert recorded.proposal is not None
    assert recorded.authority_decision.authorized is None
    assert recorded.authority_decision.proceed

    blocked = apply_transition_with_authority(
        proposal,
        transition,
        evaluated_at=LATER,
        mode="enforce",
    )
    assert not blocked.applied
    assert blocked.proposal is None
    assert not blocked.authority_decision.proceed


def test_customization_and_claim_use_authority_bound_entrypoints() -> None:
    registry, private_keys = _authority_fixture()
    base = {"params": {"threshold": 1}}
    declaration = seal_customization(
        CustomizationDeclaration(
            requested_by_actor_id=HASH_D,
            authored_by_actor_id=HASH_D,
            scope="strategy.parameters",
            rationale="Agent-declared project override",
            base_identity=identity_hash("qst:customization-base:v1", base),
            operations=(CustomizationOperation(path="/params/threshold", value=2),),
            identity_impact="derived_identity_changes",
            risk="medium",
            approval_required=True,
            declared_at=NOW,
        )
    )
    assert declaration.customization_id is not None
    customization_statement = _statement(
        action="customization_approve",
        subject_id=declaration.customization_id,
        scope="strategy.parameters",
    )
    customization_bundle = _bundle(
        customization_statement, registry, private_keys, (("alice", HASH_A),)
    )
    customization_result = apply_customizations_with_authority(
        base,
        (declaration,),
        approval_bundles={declaration.customization_id: customization_bundle},
        registry=registry,
        evaluated_at=LATER,
        mode="enforce",
    )
    assert customization_result.applied
    assert customization_result.result is not None
    assert customization_result.result.value["params"]["threshold"] == 2
    assert (
        customization_result.authority_decisions[0].decision_id
        in customization_result.result.approval_ids
    )

    recorded_customization = apply_customizations_with_authority(
        base,
        (declaration,),
        evaluated_at=LATER,
    )
    assert recorded_customization.applied
    assert recorded_customization.result is not None
    assert recorded_customization.authority_decisions[0].authorized is None

    evidence = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:authority",
            observed_at=NOW,
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="verified",
                artifact_ids=(HASH_B,),
            ),
        )
    )
    attestation = seal_attestation(
        Attestation(
            issuer_actor_id=HASH_A,
            subject_evidence_ids=(evidence.evidence_id,),
            predicate_type="qst.adapter-verification/1.0",
            statement={
                "adapter_id": "qst.ai4finance.finrobot",
                "maturity": "L3",
                "verified": True,
            },
            issued_at=NOW,
        )
    )
    assert attestation.attestation_id is not None
    attestation_statement = _statement(
        action="attestation_issue",
        subject_id=attestation.attestation_id,
        scope="qst.ai4finance.finrobot",
    )
    attestation_bundle = _bundle(
        attestation_statement, registry, private_keys, (("alice", HASH_A),)
    )
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="authority-bound-l3",
            policy_version=1,
            claim_type="experiment_completed",
            requirements=(
                EvidenceRequirement(
                    payload_kind="result",
                    require_verified_result=True,
                    minimum_adapter_maturity="L3",
                ),
            ),
        )
    )
    authorized = evaluate_claim_with_authority(
        policy,
        (evidence,),
        (attestation,),
        attestation_bundles={attestation.attestation_id: attestation_bundle},
        registry=registry,
        subject_ref="experiment:authority",
        evaluated_at=LATER,
        mode="enforce",
    )
    unauthorized = evaluate_claim_with_authority(
        policy,
        (evidence,),
        (attestation,),
        attestation_bundles={},
        registry=registry,
        subject_ref="experiment:authority",
        evaluated_at=LATER,
        mode="enforce",
    )
    assert authorized.claim_decision.allowed
    assert authorized.authority_satisfied
    assert authorized.proceed
    assert not unauthorized.claim_decision.allowed
    assert not unauthorized.authority_satisfied
    assert not unauthorized.proceed

    recorded_claim = evaluate_claim_with_authority(
        policy,
        (evidence,),
        (attestation,),
        subject_ref="experiment:authority",
        evaluated_at=LATER,
    )
    assert recorded_claim.claim_decision.allowed
    assert not recorded_claim.authority_satisfied
    assert recorded_claim.proceed


def test_enforce_claim_without_attestations_does_not_invent_an_authority_gate() -> None:
    policy = seal_claim_policy(
        ClaimPolicy(
            policy_id="evidence-only",
            policy_version=1,
            claim_type="experiment_completed",
            requirements=(EvidenceRequirement(payload_kind="result"),),
        )
    )
    evidence = seal_evidence(
        EvidenceEnvelope(
            subject_ref="experiment:evidence-only",
            observed_at=NOW,
            payload=ResultEvidencePayload(
                activity_id=HASH_A,
                collection_status="verified",
                artifact_ids=(HASH_B,),
            ),
        )
    )
    result = evaluate_claim_with_authority(
        policy,
        (evidence,),
        (),
        subject_ref="experiment:evidence-only",
        evaluated_at=LATER,
        mode="enforce",
    )
    assert result.claim_decision.allowed
    assert result.authority_satisfied
    assert result.proceed
