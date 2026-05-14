"""Interface-only reinforcement-learning port."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity


@runtime_checkable
class RLPort(Protocol):
    """Marker protocol for future RL adapters."""

    def get_identity(self) -> AdapterIdentity: ...
