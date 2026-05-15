"""Read-only legacy boundary helpers for Token System v2."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from quant_strategy_tokenizer.ir.model import SUPPORTED_IR_VERSIONS, StrategyIR
from quant_strategy_tokenizer.qst_lock.schema import LockFile


def load_legacy_strategy(value: Mapping[str, Any] | str) -> StrategyIR:
    """Load a qst-ir/0.3 or qst-ir/0.3.1 strategy without upgrading it."""

    if isinstance(value, str):
        raw = yaml.safe_load(value)
        if not isinstance(raw, Mapping):
            raise ValueError("legacy strategy document must be a mapping")
        version = raw.get("ir_version")
        if version not in SUPPORTED_IR_VERSIONS:
            raise ValueError(f"unsupported legacy ir_version: {version!r}")
        strategy = StrategyIR.model_validate(raw)
    else:
        version = value.get("ir_version")
        if version not in SUPPORTED_IR_VERSIONS:
            raise ValueError(f"unsupported legacy ir_version: {version!r}")
        strategy = StrategyIR.model_validate(value)

    return strategy


def load_legacy_strategy_file(path: str | Path) -> StrategyIR:
    """Load a legacy strategy from disk without migration."""

    return load_legacy_strategy(Path(path).read_text(encoding="utf-8"))


def load_legacy_lock(value: Mapping[str, Any] | str) -> LockFile:
    """Load a P3 qst.lock without requiring v0.4-only fields."""

    if isinstance(value, str):
        raw = json.loads(value)
        if not isinstance(raw, Mapping):
            raise ValueError("legacy qst.lock must be a JSON object")
        return LockFile.model_validate(raw)

    return LockFile.model_validate(value)


def load_legacy_lock_file(path: str | Path) -> LockFile:
    """Load a P3 qst.lock from canonical JSON bytes."""

    return load_legacy_lock(Path(path).read_text(encoding="utf-8"))
