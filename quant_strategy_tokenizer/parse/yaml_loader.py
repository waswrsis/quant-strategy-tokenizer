"""YAML loader for Strategy Content IR."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from quant_strategy_tokenizer.ir.envelope import DeploymentEnvelope
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import StrategyIR


def _normalize_external_refs(raw: dict[str, Any]) -> dict[str, Any]:
    externals = set((raw.get("externals") or {}).keys())

    def normalize(value: Any) -> Any:
        if isinstance(value, str):
            head = value.split(".", 1)[0]
            if head in externals and not value.startswith("$"):
                return f"$externals.{value}"
            return value
        if isinstance(value, list):
            return [normalize(item) for item in value]
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items()}
        return value

    normalized = normalize(raw)
    if not isinstance(normalized, dict):
        raise TypeError("Strategy YAML must contain a mapping")
    return normalized


def load_strategy(yaml_text: str) -> StrategyIR:
    """Load surface IR from YAML text."""

    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise TypeError("Strategy YAML must contain a mapping")
    raw_ir = dict(raw)
    raw_ir.pop("_envelope", None)
    return StrategyIR.model_validate(_normalize_external_refs(raw_ir))


def load_strategy_with_envelope(yaml_text: str) -> tuple[StrategyIR, DeploymentEnvelope]:
    """Load Strategy Content IR and a DeploymentEnvelope from YAML text."""

    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise TypeError("Strategy YAML must contain a mapping")
    raw_ir = dict(raw)
    raw_envelope = raw_ir.pop("_envelope", {}) or {}
    if not isinstance(raw_envelope, dict):
        raise TypeError("_envelope must contain a mapping")
    ir = StrategyIR.model_validate(_normalize_external_refs(raw_ir))
    instance_hash = compute_hashes(ir).instance_hash
    envelope = DeploymentEnvelope.model_validate(
        {"strategy_instance_hash": instance_hash, **raw_envelope}
    )
    return ir, envelope


def load_strategy_file(path: str | Path) -> StrategyIR:
    """Load a Strategy IR file from disk."""

    return load_strategy(Path(path).read_text(encoding="utf-8"))


def load_strategy_file_with_envelope(path: str | Path) -> tuple[StrategyIR, DeploymentEnvelope]:
    """Load a Strategy IR file and DeploymentEnvelope from disk."""

    return load_strategy_with_envelope(Path(path).read_text(encoding="utf-8"))
