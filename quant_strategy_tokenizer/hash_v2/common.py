"""Common helpers for Token System v2 hashes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from quant_strategy_tokenizer.canonical_json import stable_json_bytes

HASH_V2_PREFIX = "sha256:"
HASH_V2_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def hash_v2_payload(kind: str, payload: Any) -> str:
    """Hash a canonical JSON-compatible v2 payload."""

    material = {
        "hash_namespace": "qst-hash-v2/0.1",
        "kind": kind,
        "payload": payload,
    }
    digest = hashlib.sha256(stable_json_bytes(material)).hexdigest()
    return f"{HASH_V2_PREFIX}{digest}"


@dataclass(frozen=True)
class IRHashesV2:
    """Three-layer qst-ir/0.4 strategy hash snapshot."""

    graph_hash: str
    param_hash: str
    instance_hash: str
