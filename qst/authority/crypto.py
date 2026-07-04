"""Ed25519 helpers for detached governance signatures."""

from __future__ import annotations

import base64
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from qst.canonical_json import stable_json_bytes
from qst.hash.common import HashString
from qst.provenance import normalize_utc

from .models import (
    AuthorityKey,
    GovernanceBundle,
    GovernanceStatement,
    SignatureEnvelope,
    authority_key_identity,
    governance_statement_identity,
    seal_authority_key,
    seal_governance_bundle,
    seal_signature,
    signature_identity,
)


def authority_key_from_public_key(
    *,
    actor_id: HashString,
    public_key: Ed25519PublicKey,
    valid_from: datetime,
    valid_until: datetime | None = None,
) -> AuthorityKey:
    """Create a sealed public-key descriptor; private material is never recorded."""

    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return seal_authority_key(
        AuthorityKey(
            actor_id=actor_id,
            public_key_b64=base64.b64encode(raw).decode("ascii"),
            valid_from=valid_from,
            valid_until=valid_until,
        )
    )


def signature_message(
    *, statement_id: HashString, signer_actor_id: HashString, key_id: HashString, signed_at: datetime
) -> bytes:
    """Return canonical, domain-separated bytes bound to signer, key, and timestamp."""

    return stable_json_bytes(
        {
            "domain": "qst:governance-signature:v1",
            "statement_id": statement_id,
            "signer_actor_id": signer_actor_id,
            "key_id": key_id,
            "signed_at": normalize_utc(signed_at).isoformat(),
        }
    )


def sign_governance_statement(
    statement: GovernanceStatement,
    *,
    key: AuthorityKey,
    private_key: Ed25519PrivateKey,
    signed_at: datetime,
) -> SignatureEnvelope:
    """Sign a sealed statement after proving the private key matches its descriptor."""

    if statement.statement_id is None or statement.statement_id != governance_statement_identity(
        statement
    ):
        raise ValueError("governance statement must be sealed")
    if key.key_id is None or key.key_id != authority_key_identity(key):
        raise ValueError("authority key must be sealed")
    expected_public = base64.b64decode(key.public_key_b64, validate=True)
    actual_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if actual_public != expected_public:
        raise ValueError("private key does not match authority key descriptor")
    normalized_time = normalize_utc(signed_at)
    message = signature_message(
        statement_id=statement.statement_id,
        signer_actor_id=key.actor_id,
        key_id=key.key_id,
        signed_at=normalized_time,
    )
    signature = private_key.sign(message)
    return seal_signature(
        SignatureEnvelope(
            statement_id=statement.statement_id,
            signer_actor_id=key.actor_id,
            key_id=key.key_id,
            signed_at=normalized_time,
            signature_b64=base64.b64encode(signature).decode("ascii"),
        )
    )


def verify_governance_signature(
    signature: SignatureEnvelope,
    *,
    key: AuthorityKey,
) -> bool:
    """Verify envelope identity, key binding, and Ed25519 signature bytes."""

    if (
        signature.signature_id is None
        or signature.signature_id != signature_identity(signature)
        or key.key_id is None
        or key.key_id != authority_key_identity(key)
        or signature.key_id != key.key_id
        or signature.signer_actor_id != key.actor_id
    ):
        return False
    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(key.public_key_b64, validate=True)
        )
        public_key.verify(
            base64.b64decode(signature.signature_b64, validate=True),
            signature_message(
                statement_id=signature.statement_id,
                signer_actor_id=signature.signer_actor_id,
                key_id=signature.key_id,
                signed_at=signature.signed_at,
            ),
        )
    except (InvalidSignature, ValueError):
        return False
    return True


def build_governance_bundle(
    statement: GovernanceStatement, signatures: tuple[SignatureEnvelope, ...]
) -> GovernanceBundle:
    """Seal a statement/signature bundle after structural binding checks."""

    return seal_governance_bundle(
        GovernanceBundle(statement=statement, signatures=signatures)
    )
