"""Market data port protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import MarketFrame, QSTSymbol


class MarketLoadRequest(BaseModel):
    """Adapter-neutral market data load request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    symbols: list[QSTSymbol] = Field(default_factory=list)


@runtime_checkable
class MarketDataPort(Protocol):
    """Adapter protocol for loading market data into a QST MarketFrame."""

    def get_identity(self) -> AdapterIdentity: ...

    def load_market(self, request: MarketLoadRequest) -> MarketFrame: ...
