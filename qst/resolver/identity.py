"""Domain-separated identity helpers for resolver inputs and decisions."""

from __future__ import annotations

import hashlib
from typing import Any

from qst.canonical_json import stable_json_bytes


def resolver_hash(domain: str, payload: Any) -> str:
    """Hash canonical payload under an explicit QST resolver domain."""

    material = {"domain": domain, "payload": payload}
    return f"sha256:{hashlib.sha256(stable_json_bytes(material)).hexdigest()}"

