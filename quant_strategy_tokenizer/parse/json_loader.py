"""JSON loader for Strategy Content IR."""

from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.model import StrategyIR


def load_strategy_json(json_text: str) -> StrategyIR:
    """Load Strategy IR from JSON text."""

    return StrategyIR.model_validate_json(json_text)


def load_strategy_json_file(path: str | Path) -> StrategyIR:
    """Load a Strategy IR JSON file from disk."""

    return load_strategy_json(Path(path).read_text(encoding="utf-8"))
