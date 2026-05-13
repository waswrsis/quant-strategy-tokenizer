"""Three-layer Strategy IR hashing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.tokens.registry import get_registry


@dataclass(frozen=True)
class IRHashes:
    """P0 graph, param, and instance hashes."""

    graph_hash: str
    param_hash: str
    instance_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "graph_hash": self.graph_hash,
            "param_hash": self.param_hash,
            "instance_hash": self.instance_hash,
        }


def _stable_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def compute_hashes(ir: StrategyIR) -> IRHashes:
    """Compute graph_hash, param_hash, and instance_hash from canonical IR."""

    canonical = canonicalize(ir)
    plain = to_plain(canonical)
    graph_payload = {
        "canonical_version": canonical.canonical_version,
        "externals": plain["externals"],
        "outputs": plain["outputs"],
        "nodes": [
            {
                "id": node["id"],
                "token": node["token"],
                "v": node["v"],
                "inputs": node["inputs"],
            }
            for node in plain["graph"]
        ],
    }
    param_payload = {
        "nodes": [{"id": node["id"], "params": node["params"]} for node in plain["graph"]]
    }

    graph_hash = _sha256(graph_payload)
    param_hash = _sha256(param_payload)
    registry = get_registry()
    behavior_versions = [
        {
            "id": node["id"],
            "token": node["token"],
            "behavior_version": registry.get(node["token"], node["v"]).spec.behavior_version,
        }
        for node in plain["graph"]
    ]
    instance_hash = _sha256(
        {
            "graph_hash": graph_hash,
            "param_hash": param_hash,
            "behavior_versions": behavior_versions,
        }
    )
    return IRHashes(graph_hash=graph_hash, param_hash=param_hash, instance_hash=instance_hash)
