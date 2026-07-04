"""Signed authority, delegation, revocation, and quorum records."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from qst.hash.common import HashString
from qst.identity import model_identity
from qst.provenance import normalize_utc

ActorKind = Literal["human", "agent", "system", "organization"]
AuthorityRole = Literal[
    "attestation_issuer",
    "customization_approver",
    "token_contract_reviewer",
    "token_implementation_reviewer",
    "token_publisher",
    "token_activation_reviewer",
    "token_activator",
    "token_builtin_nominator",
    "authority_delegator",
]
GovernanceAction = Literal[
    "attestation_issue",
    "customization_approve",
    "token_contract_approve",
    "token_implementation_approve",
    "token_publication_approve",
    "token_publish",
    "token_activation_approve",
    "token_activate",
    "token_builtin_nominate",
    "authority_delegate",
]
AuthorityMode = Literal["record_only", "advisory", "enforce"]
RevocationTarget = Literal["actor", "key", "delegation", "bundle"]

NON_DELEGABLE_ROLES: frozenset[AuthorityRole] = frozenset({"authority_delegator"})


def _sorted_unique(values: tuple[str, ...], *, field_name: str) -> tuple[str, ...]:
    result = tuple(sorted(dict.fromkeys(values)))
    if not result:
        raise ValueError(f"{field_name} must not be empty")
    return result


def _decode_base64(value: str, *, expected_length: int, field_name: str) -> bytes:
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"{field_name} must be valid base64") from exc
    if len(decoded) != expected_length:
        raise ValueError(f"{field_name} must decode to {expected_length} bytes")
    return decoded


class AuthorityKey(BaseModel):
    """One actor-bound Ed25519 verification key."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-key/1.0"] = "qst-authority-key/1.0"
    key_id: HashString | None = None
    actor_id: HashString
    algorithm: Literal["ed25519"] = "ed25519"
    public_key_b64: str
    valid_from: datetime
    valid_until: datetime | None = None

    @field_validator("public_key_b64", mode="after")
    @classmethod
    def _public_key(cls, value: str) -> str:
        _decode_base64(value, expected_length=32, field_name="public_key_b64")
        return value

    @field_validator("valid_from", "valid_until", mode="after")
    @classmethod
    def _time(cls, value: datetime | None) -> datetime | None:
        return None if value is None else normalize_utc(value)

    @model_validator(mode="after")
    def _validate_key(self) -> AuthorityKey:
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("key valid_until must follow valid_from")
        if self.key_id is not None and self.key_id != authority_key_identity(self):
            raise ValueError("key_id does not match authority key material")
        return self


class AuthorityPrincipal(BaseModel):
    """Trusted actor roles and keys included in a registry snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_id: HashString
    actor_kind: ActorKind
    roles: tuple[AuthorityRole, ...] = ()
    scopes: tuple[str, ...] = ()
    keys: tuple[AuthorityKey, ...]
    valid_from: datetime
    valid_until: datetime | None = None

    @field_validator("roles", mode="after")
    @classmethod
    def _roles(cls, value: tuple[AuthorityRole, ...]) -> tuple[AuthorityRole, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("scopes", mode="after")
    @classmethod
    def _scopes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            return ()
        return _sorted_unique(value, field_name="principal scopes")

    @field_validator("keys", mode="after")
    @classmethod
    def _keys(cls, value: tuple[AuthorityKey, ...]) -> tuple[AuthorityKey, ...]:
        return tuple(sorted(value, key=lambda item: item.key_id or ""))

    @field_validator("valid_from", "valid_until", mode="after")
    @classmethod
    def _time(cls, value: datetime | None) -> datetime | None:
        return None if value is None else normalize_utc(value)

    @model_validator(mode="after")
    def _validate_principal(self) -> AuthorityPrincipal:
        if not self.keys:
            raise ValueError("authority principal requires at least one key")
        if self.roles and not self.scopes:
            raise ValueError("authority principal with roles requires scopes")
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("principal valid_until must follow valid_from")
        key_ids: list[str] = []
        for key in self.keys:
            if key.key_id is None or key.key_id != authority_key_identity(key):
                raise ValueError("authority principal keys must be sealed")
            if key.actor_id != self.actor_id:
                raise ValueError("authority key actor_id must match principal actor_id")
            key_ids.append(key.key_id)
        if len(key_ids) != len(set(key_ids)):
            raise ValueError("authority principal key IDs must be unique")
        return self


class QuorumRule(BaseModel):
    """Action-specific role and distinct-actor threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: GovernanceAction
    required_role: AuthorityRole
    quorum: int = Field(ge=1)
    require_human: bool = False
    allowed_actor_ids: tuple[HashString, ...] = ()

    @field_validator("allowed_actor_ids", mode="after")
    @classmethod
    def _actors(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))


class RevocationRecord(BaseModel):
    """Registry-owned revocation; the sealed registry is the trust anchor."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-revocation/1.0"] = (
        "qst-authority-revocation/1.0"
    )
    revocation_id: HashString | None = None
    target_type: RevocationTarget
    target_id: HashString
    effective_at: datetime
    reason_codes: tuple[str, ...]

    @field_validator("effective_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @field_validator("reason_codes", mode="after")
    @classmethod
    def _reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(value, field_name="revocation reason_codes")

    @model_validator(mode="after")
    def _validate_revocation(self) -> RevocationRecord:
        if self.revocation_id is not None and self.revocation_id != revocation_identity(self):
            raise ValueError("revocation_id does not match revocation material")
        return self


class AuthorityRegistry(BaseModel):
    """Pinned trust snapshot for actors, keys, quorum rules, and revocations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-registry/1.0"] = "qst-authority-registry/1.0"
    registry_hash: HashString | None = None
    registry_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    principals: tuple[AuthorityPrincipal, ...]
    rules: tuple[QuorumRule, ...]
    revocations: tuple[RevocationRecord, ...] = ()

    @field_validator("principals", mode="after")
    @classmethod
    def _principals(
        cls, value: tuple[AuthorityPrincipal, ...]
    ) -> tuple[AuthorityPrincipal, ...]:
        return tuple(sorted(value, key=lambda item: item.actor_id))

    @field_validator("rules", mode="after")
    @classmethod
    def _rules(cls, value: tuple[QuorumRule, ...]) -> tuple[QuorumRule, ...]:
        return tuple(sorted(value, key=lambda item: item.action))

    @field_validator("revocations", mode="after")
    @classmethod
    def _revocations(
        cls, value: tuple[RevocationRecord, ...]
    ) -> tuple[RevocationRecord, ...]:
        return tuple(
            sorted(value, key=lambda item: (item.target_type, item.target_id, item.effective_at))
        )

    @model_validator(mode="after")
    def _validate_registry(self) -> AuthorityRegistry:
        if not self.principals or not self.rules:
            raise ValueError("authority registry requires principals and quorum rules")
        actor_ids = [item.actor_id for item in self.principals]
        if len(actor_ids) != len(set(actor_ids)):
            raise ValueError("authority registry actor IDs must be unique")
        key_ids = [key.key_id for principal in self.principals for key in principal.keys]
        if len(key_ids) != len(set(key_ids)):
            raise ValueError("authority registry key IDs must be unique")
        actions = [item.action for item in self.rules]
        if len(actions) != len(set(actions)):
            raise ValueError("authority registry actions must be unique")
        revocation_targets = [(item.target_type, item.target_id) for item in self.revocations]
        if len(revocation_targets) != len(set(revocation_targets)):
            raise ValueError("authority registry revocation targets must be unique")
        for revocation in self.revocations:
            if revocation.revocation_id is None or revocation.revocation_id != revocation_identity(
                revocation
            ):
                raise ValueError("authority registry revocations must be sealed")
        if self.registry_hash is not None and self.registry_hash != authority_registry_identity(self):
            raise ValueError("registry_hash does not match authority registry material")
        return self


class GovernanceStatement(BaseModel):
    """Human-meaningful approval/rejection statement signed by authorities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-governance-statement/1.0"] = (
        "qst-governance-statement/1.0"
    )
    statement_id: HashString | None = None
    action: GovernanceAction
    subject_id: HashString
    scope: str = Field(min_length=1)
    decision: Literal["approve", "reject"]
    reason_codes: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    nonce: str = Field(min_length=16)

    @field_validator("reason_codes", mode="after")
    @classmethod
    def _reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(value, field_name="statement reason_codes")

    @field_validator("issued_at", "expires_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_statement(self) -> GovernanceStatement:
        if self.expires_at <= self.issued_at:
            raise ValueError("statement expires_at must follow issued_at")
        if self.statement_id is not None and self.statement_id != governance_statement_identity(
            self
        ):
            raise ValueError("statement_id does not match governance statement material")
        return self


class SignatureEnvelope(BaseModel):
    """Detached Ed25519 signature over one governance statement and signing context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-signature-envelope/1.0"] = "qst-signature-envelope/1.0"
    signature_id: HashString | None = None
    statement_id: HashString
    signer_actor_id: HashString
    key_id: HashString
    signed_at: datetime
    signature_b64: str

    @field_validator("signed_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @field_validator("signature_b64", mode="after")
    @classmethod
    def _signature(cls, value: str) -> str:
        _decode_base64(value, expected_length=64, field_name="signature_b64")
        return value

    @model_validator(mode="after")
    def _validate_signature(self) -> SignatureEnvelope:
        if self.signature_id is not None and self.signature_id != signature_identity(self):
            raise ValueError("signature_id does not match signature envelope material")
        return self


class GovernanceBundle(BaseModel):
    """One statement plus detached signatures used for quorum evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-governance-bundle/1.0"] = "qst-governance-bundle/1.0"
    bundle_id: HashString | None = None
    statement: GovernanceStatement
    signatures: tuple[SignatureEnvelope, ...]

    @field_validator("signatures", mode="after")
    @classmethod
    def _signatures(
        cls, value: tuple[SignatureEnvelope, ...]
    ) -> tuple[SignatureEnvelope, ...]:
        return tuple(sorted(value, key=lambda item: item.signature_id or ""))

    @model_validator(mode="after")
    def _validate_bundle(self) -> GovernanceBundle:
        if self.statement.statement_id is None:
            raise ValueError("governance bundle statement must be sealed")
        if not self.signatures:
            raise ValueError("governance bundle requires signatures")
        signature_ids: list[str] = []
        for signature in self.signatures:
            if signature.signature_id is None or signature.signature_id != signature_identity(
                signature
            ):
                raise ValueError("governance bundle signatures must be sealed")
            if signature.statement_id != self.statement.statement_id:
                raise ValueError("signature statement_id does not match bundle statement")
            signature_ids.append(signature.signature_id)
        if len(signature_ids) != len(set(signature_ids)):
            raise ValueError("governance bundle signatures must be unique")
        if self.bundle_id is not None and self.bundle_id != governance_bundle_identity(self):
            raise ValueError("bundle_id does not match governance bundle material")
        return self


class DelegationGrant(BaseModel):
    """Non-transitive role delegation authorized by a governance bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-delegation/1.0"] = "qst-authority-delegation/1.0"
    delegation_id: HashString | None = None
    delegator_actor_id: HashString
    delegate_actor_id: HashString
    role: AuthorityRole
    scopes: tuple[str, ...]
    valid_from: datetime
    valid_until: datetime
    nonce: str = Field(min_length=16)

    @field_validator("scopes", mode="after")
    @classmethod
    def _scopes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_unique(value, field_name="delegation scopes")

    @field_validator("valid_from", "valid_until", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_delegation(self) -> DelegationGrant:
        if self.delegator_actor_id == self.delegate_actor_id:
            raise ValueError("delegator and delegate must be distinct")
        if self.role in NON_DELEGABLE_ROLES:
            raise ValueError(f"role cannot be delegated: {self.role}")
        if self.valid_until <= self.valid_from:
            raise ValueError("delegation valid_until must follow valid_from")
        if self.delegation_id is not None and self.delegation_id != delegation_identity(self):
            raise ValueError("delegation_id does not match delegation material")
        return self


class SignedDelegation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    grant: DelegationGrant
    authorization: GovernanceBundle


class AuthorityDecision(BaseModel):
    """Sealed result of registry, signature, revocation, and quorum evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qst-authority-decision/1.0"] = "qst-authority-decision/1.0"
    decision_id: HashString | None = None
    registry_hash: HashString | None = None
    bundle_id: HashString | None = None
    action: GovernanceAction
    subject_id: HashString
    mode: AuthorityMode = "record_only"
    authorized: bool | None
    proceed: bool
    signer_actor_ids: tuple[HashString, ...] = ()
    signature_ids: tuple[HashString, ...] = ()
    reason_codes: tuple[str, ...]
    evaluated_at: datetime

    @field_validator("signer_actor_ids", "signature_ids", "reason_codes", mode="after")
    @classmethod
    def _values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(dict.fromkeys(value)))

    @field_validator("evaluated_at", mode="after")
    @classmethod
    def _time(cls, value: datetime) -> datetime:
        return normalize_utc(value)

    @model_validator(mode="after")
    def _validate_decision(self) -> AuthorityDecision:
        if not self.reason_codes:
            raise ValueError("authority decision requires reason_codes")
        if self.authorized is True and (self.registry_hash is None or self.bundle_id is None):
            raise ValueError("authorized decision requires registry and bundle identities")
        if self.mode == "enforce" and self.proceed != (self.authorized is True):
            raise ValueError("enforce mode progression must match authorization")
        if self.mode != "enforce" and not self.proceed:
            raise ValueError("record_only and advisory decisions must not block recording")
        if self.decision_id is not None and self.decision_id != authority_decision_identity(self):
            raise ValueError("decision_id does not match authority decision material")
        return self

    @property
    def allowed(self) -> bool:
        """Compatibility view of cryptographic authorization, not record progression."""

        return self.authorized is True


def authority_key_identity(value: AuthorityKey) -> str:
    return model_identity(value, domain="qst:authority-key:v1", identity_field="key_id")


def revocation_identity(value: RevocationRecord) -> str:
    return model_identity(
        value, domain="qst:authority-revocation:v1", identity_field="revocation_id"
    )


def authority_registry_identity(value: AuthorityRegistry) -> str:
    return model_identity(
        value, domain="qst:authority-registry:v1", identity_field="registry_hash"
    )


def governance_statement_identity(value: GovernanceStatement) -> str:
    return model_identity(
        value, domain="qst:governance-statement:v1", identity_field="statement_id"
    )


def signature_identity(value: SignatureEnvelope) -> str:
    return model_identity(value, domain="qst:signature-envelope:v1", identity_field="signature_id")


def governance_bundle_identity(value: GovernanceBundle) -> str:
    return model_identity(value, domain="qst:governance-bundle:v1", identity_field="bundle_id")


def delegation_identity(value: DelegationGrant) -> str:
    return model_identity(value, domain="qst:authority-delegation:v1", identity_field="delegation_id")


def authority_decision_identity(value: AuthorityDecision) -> str:
    return model_identity(value, domain="qst:authority-decision:v1", identity_field="decision_id")


def _seal(value: BaseModel, *, identity_field: str, identity: str) -> dict[str, object]:
    return {**value.model_dump(mode="json", exclude={identity_field}), identity_field: identity}


def seal_authority_key(value: AuthorityKey) -> AuthorityKey:
    return AuthorityKey.model_validate(
        _seal(value, identity_field="key_id", identity=authority_key_identity(value))
    )


def seal_revocation(value: RevocationRecord) -> RevocationRecord:
    return RevocationRecord.model_validate(
        _seal(value, identity_field="revocation_id", identity=revocation_identity(value))
    )


def seal_authority_registry(value: AuthorityRegistry) -> AuthorityRegistry:
    return AuthorityRegistry.model_validate(
        _seal(value, identity_field="registry_hash", identity=authority_registry_identity(value))
    )


def seal_governance_statement(value: GovernanceStatement) -> GovernanceStatement:
    return GovernanceStatement.model_validate(
        _seal(value, identity_field="statement_id", identity=governance_statement_identity(value))
    )


def seal_signature(value: SignatureEnvelope) -> SignatureEnvelope:
    return SignatureEnvelope.model_validate(
        _seal(value, identity_field="signature_id", identity=signature_identity(value))
    )


def seal_governance_bundle(value: GovernanceBundle) -> GovernanceBundle:
    return GovernanceBundle.model_validate(
        _seal(value, identity_field="bundle_id", identity=governance_bundle_identity(value))
    )


def seal_delegation(value: DelegationGrant) -> DelegationGrant:
    return DelegationGrant.model_validate(
        _seal(value, identity_field="delegation_id", identity=delegation_identity(value))
    )


def seal_authority_decision(value: AuthorityDecision) -> AuthorityDecision:
    return AuthorityDecision.model_validate(
        _seal(value, identity_field="decision_id", identity=authority_decision_identity(value))
    )
