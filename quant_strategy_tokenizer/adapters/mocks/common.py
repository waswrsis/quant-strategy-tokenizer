"""Shared helpers for built-in mock adapters."""

from __future__ import annotations

import hashlib
from typing import Any, TypeVar

from pydantic import BaseModel

from quant_strategy_tokenizer.artifacts.artifact_id import compute_artifact_id
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.canonical_json import stable_json_bytes
from quant_strategy_tokenizer.qst_lock import sha256_bytes

ArtifactT = TypeVar("ArtifactT", bound=BaseModel)


def adapter_identity(adapter_id: str) -> AdapterIdentity:
    """Return deterministic identity for a built-in mock adapter."""

    return AdapterIdentity(adapter_id=adapter_id, adapter_version="0.1.0")


def content_hash(payload: dict[str, Any]) -> str:
    """Hash a JSON-compatible payload using QST canonical JSON."""

    return f"sha256:{hashlib.sha256(stable_json_bytes(payload)).hexdigest()}"


def bytes_hash(payload: bytes) -> str:
    """Hash raw bytes as a QST hash string."""

    return sha256_bytes(payload)


def with_artifact_id(model: ArtifactT) -> ArtifactT:
    """Return a frozen artifact model with its content-derived artifact_id set."""

    artifact_id = compute_artifact_id(model.model_dump(mode="json"))
    return model.model_copy(update={"artifact_id": artifact_id})
