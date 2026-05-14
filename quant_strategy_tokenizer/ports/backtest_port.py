"""Backtest port protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.artifacts.backtest_evidence import BacktestEvidence
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import MarketFrame, SignalFrame
from quant_strategy_tokenizer.runtime.signal_extraction import (
    SignalExtractionPolicy,
    execute_to_signals,
)


class BacktestConfig(BaseModel):
    """Adapter-neutral backtest configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_cash: str = "100000"
    base_currency: str = "USD"
    metadata: dict[str, object] = Field(default_factory=dict)


@runtime_checkable
class BacktestPort(Protocol):
    """Adapter protocol for running a backtest from SignalFrame input only."""

    def get_identity(self) -> AdapterIdentity: ...

    def run_signals_backtest(
        self,
        signals: SignalFrame,
        market: MarketFrame,
        config: BacktestConfig,
    ) -> BacktestEvidence: ...


def run_strategy_backtest(
    strategy_ir: Any,
    market: MarketFrame,
    config: BacktestConfig,
    *,
    adapter: BacktestPort,
    signal_policy: SignalExtractionPolicy | None = None,
    externals: dict[str, Any] | None = None,
) -> BacktestEvidence:
    """Run a QST strategy through signal extraction, then hand signals to an adapter."""

    signals = execute_to_signals(
        strategy_ir,
        market,
        policy=signal_policy,
        externals=externals,
    )
    return adapter.run_signals_backtest(signals, market, config)
