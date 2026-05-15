"""Deterministic target core registry hash for WP10 migration."""

from __future__ import annotations

import hashlib
import json

from quant_strategy_tokenizer.decision_v2 import decision_algebra_token_pack_v2
from quant_strategy_tokenizer.hash_v2 import hash_v2_payload, token_pack_hash_for_pack_v2
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.panel_v2 import (
    panel_ops_token_pack_v2,
    panel_weights_token_pack_v2,
)
from quant_strategy_tokenizer.state_v2 import (
    state_basic_token_pack_v2,
    state_fsm_token_pack_v2,
)
from quant_strategy_tokenizer.tokens.registry import get_registry


def target_core_registry_hash() -> str:
    """Return the registry hash binding legacy migration to the accepted core set."""

    legacy_specs = [
        {
            "id": spec.id,
            "version": spec.version,
            "behavior_version": spec.behavior_version,
            "spec_hash": _legacy_spec_hash(to_plain(spec)),
        }
        for spec in get_registry().list_tokens()
    ]
    packs = [
        state_basic_token_pack_v2(),
        state_fsm_token_pack_v2(),
        decision_algebra_token_pack_v2(),
        panel_ops_token_pack_v2(),
        panel_weights_token_pack_v2(),
    ]
    payload = {
        "schema_version": "qst-target-core-registry/0.4",
        "legacy_tokens": legacy_specs,
        "v2_core_token_packs": [
            {
                "pack_id": pack.pack_id,
                "version": pack.version,
                "token_pack_hash": token_pack_hash_for_pack_v2(pack),
            }
            for pack in sorted(packs, key=lambda item: item.pack_id)
        ],
    }
    return hash_v2_payload("target_core_registry", payload)


def _legacy_spec_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
