"""Domain-separated identities for QST 1.0 records."""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel

from qst.canonical_json import stable_json_bytes


def identity_hash(domain: str, payload: BaseModel | dict[str, Any]) -> str:
    """Return a SHA-256 identity bound to a non-empty versioned domain."""

    if not domain.startswith("qst:") or ":v" not in domain:
        raise ValueError("identity domain must be a versioned qst:*:v* name")
    value = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    material = {"domain": domain, "payload": value}
    return f"sha256:{hashlib.sha256(stable_json_bytes(material)).hexdigest()}"


def model_identity(model: BaseModel, *, domain: str, identity_field: str) -> str:
    """Hash a model after excluding its self-referential identity field."""

    material = model.model_dump(mode="json", exclude={identity_field})
    return identity_hash(domain, material)

