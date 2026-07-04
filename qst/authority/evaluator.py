"""Deterministic authority, delegation, revocation, and quorum evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from qst.hash.common import HashString
from qst.provenance import normalize_utc

from .crypto import verify_governance_signature
from .models import (
    AuthorityDecision,
    AuthorityKey,
    AuthorityMode,
    AuthorityPrincipal,
    AuthorityRegistry,
    AuthorityRole,
    GovernanceAction,
    GovernanceBundle,
    QuorumRule,
    SignedDelegation,
    authority_registry_identity,
    delegation_identity,
    governance_bundle_identity,
    governance_statement_identity,
    seal_authority_decision,
)


@dataclass(frozen=True)
class _DelegatedRole:
    role: AuthorityRole
    scopes: frozenset[str]
    valid_from: datetime
    valid_until: datetime


def authorize_bundle(
    bundle: GovernanceBundle,
    registry: AuthorityRegistry,
    *,
    evaluated_at: datetime,
    mode: AuthorityMode = "record_only",
    delegations: tuple[SignedDelegation, ...] = (),
    consumed_bundle_ids: frozenset[HashString] = frozenset(),
) -> AuthorityDecision:
    """Verify a governance bundle against a pinned registry and optional delegations."""

    evaluated_at = normalize_utc(evaluated_at)
    _require_registry_integrity(registry)
    _require_bundle_integrity(bundle)
    delegated_roles = _validated_delegations(
        delegations, registry, evaluated_at=evaluated_at
    )
    return _authorize_bundle_core(
        bundle,
        registry,
        evaluated_at=evaluated_at,
        delegated_roles=delegated_roles,
        consumed_bundle_ids=consumed_bundle_ids,
        mode=mode,
    )


def authority_not_evaluated(
    *,
    action: GovernanceAction,
    subject_id: HashString,
    evaluated_at: datetime,
    mode: AuthorityMode = "record_only",
    registry: AuthorityRegistry | None = None,
    reason_codes: tuple[str, ...] = ("QST_AUTHORITY_EVIDENCE_NOT_PROVIDED",),
) -> AuthorityDecision:
    """Record missing authority evidence without overstating authorization."""

    evaluated_at = normalize_utc(evaluated_at)
    if registry is not None:
        _require_registry_integrity(registry)
    reasons = list(reason_codes)
    if mode == "record_only":
        reasons.append("QST_AUTHORITY_RECORD_ONLY_NOT_ENFORCED")
    elif mode == "advisory":
        reasons.append("QST_AUTHORITY_ADVISORY_NOT_ENFORCED")
    return seal_authority_decision(
        AuthorityDecision(
            registry_hash=None if registry is None else registry.registry_hash,
            bundle_id=None,
            action=action,
            subject_id=subject_id,
            mode=mode,
            authorized=None,
            proceed=mode != "enforce",
            reason_codes=tuple(reasons),
            evaluated_at=evaluated_at,
        )
    )


def _authorize_bundle_core(
    bundle: GovernanceBundle,
    registry: AuthorityRegistry,
    *,
    evaluated_at: datetime,
    delegated_roles: dict[str, tuple[_DelegatedRole, ...]],
    consumed_bundle_ids: frozenset[str] = frozenset(),
    mode: AuthorityMode = "record_only",
) -> AuthorityDecision:
    assert registry.registry_hash is not None
    assert bundle.bundle_id is not None
    assert bundle.statement.statement_id is not None
    statement = bundle.statement
    reasons: list[str] = []
    if bundle.bundle_id in consumed_bundle_ids:
        reasons.append("QST_AUTHORITY_BUNDLE_REPLAYED")
    if _is_revoked(registry, "bundle", bundle.bundle_id, evaluated_at):
        reasons.append("QST_AUTHORITY_BUNDLE_REVOKED")
    if evaluated_at < statement.issued_at:
        reasons.append("QST_AUTHORITY_STATEMENT_NOT_YET_VALID")
    if evaluated_at > statement.expires_at:
        reasons.append("QST_AUTHORITY_STATEMENT_EXPIRED")
    rule = next((item for item in registry.rules if item.action == statement.action), None)
    if rule is None:
        reasons.append("QST_AUTHORITY_RULE_MISSING")
        return _decision(bundle, registry, evaluated_at, (), (), reasons, mode=mode)

    valid_signers: dict[str, str] = {}
    valid_signature_ids: set[str] = set()
    for signature in bundle.signatures:
        principal = _principal(registry, signature.signer_actor_id)
        key = _key(principal, signature.key_id) if principal is not None else None
        if principal is None or key is None:
            continue
        if not _signature_time_valid(signature.signed_at, statement.issued_at, statement.expires_at):
            continue
        if signature.signed_at > evaluated_at:
            continue
        if not _principal_valid(principal, signature.signed_at, evaluated_at):
            continue
        if not _key_valid(key, signature.signed_at, evaluated_at):
            continue
        if _is_revoked(registry, "actor", principal.actor_id, evaluated_at):
            continue
        if key.key_id is None or _is_revoked(registry, "key", key.key_id, evaluated_at):
            continue
        if rule.allowed_actor_ids and principal.actor_id not in rule.allowed_actor_ids:
            continue
        if rule.require_human and principal.actor_kind != "human":
            continue
        if not _has_role_and_scope(
            principal,
            rule,
            statement.scope,
            delegated_roles.get(principal.actor_id, ()),
            evaluated_at,
        ):
            continue
        if not verify_governance_signature(signature, key=key):
            continue
        if signature.signature_id is None:
            continue
        valid_signers[principal.actor_id] = signature.signature_id
        valid_signature_ids.add(signature.signature_id)

    if len(valid_signers) < rule.quorum:
        reasons.append("QST_AUTHORITY_QUORUM_NOT_MET")
    if statement.decision != "approve":
        reasons.append("QST_AUTHORITY_STATEMENT_REJECTED")
    authorized = not reasons
    if authorized:
        reasons.append("QST_AUTHORITY_ALLOWED")
    elif mode == "record_only":
        reasons.append("QST_AUTHORITY_RECORD_ONLY_NOT_ENFORCED")
    elif mode == "advisory":
        reasons.append("QST_AUTHORITY_ADVISORY_NOT_ENFORCED")
    return _decision(
        bundle,
        registry,
        evaluated_at,
        tuple(valid_signers),
        tuple(valid_signature_ids),
        reasons,
        authorized=authorized,
        mode=mode,
    )


def _validated_delegations(
    delegations: tuple[SignedDelegation, ...],
    registry: AuthorityRegistry,
    *,
    evaluated_at: datetime,
) -> dict[str, tuple[_DelegatedRole, ...]]:
    result: dict[str, list[_DelegatedRole]] = {}
    seen: set[str] = set()
    for signed in sorted(delegations, key=lambda item: item.grant.delegation_id or ""):
        grant = signed.grant
        if grant.delegation_id is None or grant.delegation_id != delegation_identity(grant):
            continue
        if grant.delegation_id in seen:
            continue
        seen.add(grant.delegation_id)
        if _is_revoked(registry, "delegation", grant.delegation_id, evaluated_at):
            continue
        if not (grant.valid_from <= evaluated_at <= grant.valid_until):
            continue
        statement = signed.authorization.statement
        if (
            statement.action != "authority_delegate"
            or statement.subject_id != grant.delegation_id
            or statement.scope != "authority.registry"
        ):
            continue
        try:
            _require_bundle_integrity(signed.authorization)
        except ValueError:
            continue
        authorization = _authorize_bundle_core(
            signed.authorization,
            registry,
            evaluated_at=evaluated_at,
            delegated_roles={},
            consumed_bundle_ids=frozenset(),
            mode="enforce",
        )
        if not authorization.allowed or grant.delegator_actor_id not in authorization.signer_actor_ids:
            continue
        delegator = _principal(registry, grant.delegator_actor_id)
        delegate = _principal(registry, grant.delegate_actor_id)
        if delegator is None or delegate is None:
            continue
        if grant.role not in delegator.roles:
            continue
        if not all(_scope_allowed(scope, delegator.scopes) for scope in grant.scopes):
            continue
        result.setdefault(grant.delegate_actor_id, []).append(
            _DelegatedRole(
                role=grant.role,
                scopes=frozenset(grant.scopes),
                valid_from=grant.valid_from,
                valid_until=grant.valid_until,
            )
        )
    return {
        actor_id: tuple(
            sorted(items, key=lambda item: (item.role, tuple(sorted(item.scopes))))
        )
        for actor_id, items in result.items()
    }


def _has_role_and_scope(
    principal: AuthorityPrincipal,
    rule: QuorumRule,
    scope: str,
    delegated_roles: tuple[_DelegatedRole, ...],
    evaluated_at: datetime,
) -> bool:
    if rule.required_role in principal.roles and _scope_allowed(scope, principal.scopes):
        return True
    return any(
        item.role == rule.required_role
        and item.valid_from <= evaluated_at <= item.valid_until
        and _scope_allowed(scope, item.scopes)
        for item in delegated_roles
    )


def _scope_allowed(scope: str, granted_scopes: tuple[str, ...] | frozenset[str]) -> bool:
    return "*" in granted_scopes or scope in granted_scopes


def _principal(registry: AuthorityRegistry, actor_id: str) -> AuthorityPrincipal | None:
    return next((item for item in registry.principals if item.actor_id == actor_id), None)


def _key(principal: AuthorityPrincipal | None, key_id: str) -> AuthorityKey | None:
    if principal is None:
        return None
    return next((item for item in principal.keys if item.key_id == key_id), None)


def _principal_valid(
    principal: AuthorityPrincipal, signed_at: datetime, evaluated_at: datetime
) -> bool:
    return principal.valid_from <= signed_at <= evaluated_at and (
        principal.valid_until is None or evaluated_at <= principal.valid_until
    )


def _key_valid(key: AuthorityKey, signed_at: datetime, evaluated_at: datetime) -> bool:
    return key.valid_from <= signed_at <= evaluated_at and (
        key.valid_until is None or evaluated_at <= key.valid_until
    )


def _signature_time_valid(signed_at: datetime, issued_at: datetime, expires_at: datetime) -> bool:
    return issued_at <= signed_at <= expires_at


def _is_revoked(
    registry: AuthorityRegistry,
    target_type: str,
    target_id: str,
    evaluated_at: datetime,
) -> bool:
    return any(
        item.target_type == target_type
        and item.target_id == target_id
        and item.effective_at <= evaluated_at
        for item in registry.revocations
    )


def _require_registry_integrity(registry: AuthorityRegistry) -> None:
    if (
        registry.registry_hash is None
        or registry.registry_hash != authority_registry_identity(registry)
    ):
        raise ValueError("authority registry must be sealed and untampered")


def _require_bundle_integrity(bundle: GovernanceBundle) -> None:
    if bundle.bundle_id is None or bundle.bundle_id != governance_bundle_identity(bundle):
        raise ValueError("governance bundle must be sealed and untampered")
    statement = bundle.statement
    if (
        statement.statement_id is None
        or statement.statement_id != governance_statement_identity(statement)
    ):
        raise ValueError("governance statement must be sealed and untampered")


def _decision(
    bundle: GovernanceBundle,
    registry: AuthorityRegistry,
    evaluated_at: datetime,
    signer_actor_ids: tuple[str, ...],
    signature_ids: tuple[str, ...],
    reasons: list[str],
    *,
    authorized: bool = False,
    mode: AuthorityMode,
) -> AuthorityDecision:
    assert registry.registry_hash is not None
    assert bundle.bundle_id is not None
    if not authorized and mode == "record_only":
        reasons.append("QST_AUTHORITY_RECORD_ONLY_NOT_ENFORCED")
    elif not authorized and mode == "advisory":
        reasons.append("QST_AUTHORITY_ADVISORY_NOT_ENFORCED")
    return seal_authority_decision(
        AuthorityDecision(
            registry_hash=registry.registry_hash,
            bundle_id=bundle.bundle_id,
            action=bundle.statement.action,
            subject_id=bundle.statement.subject_id,
            mode=mode,
            authorized=authorized,
            proceed=authorized if mode == "enforce" else True,
            signer_actor_ids=signer_actor_ids,
            signature_ids=signature_ids,
            reason_codes=tuple(reasons or ["QST_AUTHORITY_DENIED"]),
            evaluated_at=evaluated_at,
        )
    )
