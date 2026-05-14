"""Deterministic mock backtest adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from quant_strategy_tokenizer.adapters.mocks.common import adapter_identity, with_artifact_id
from quant_strategy_tokenizer.artifacts.backtest_evidence import BacktestEvidence, BacktestStats
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import MarketFrame, SignalFrame, compute_frame_hash
from quant_strategy_tokenizer.ports import BacktestConfig


class MockBacktestAdapter:
    """Deterministic signal-level backtest adapter for P4b-1 smoke workflows."""

    capabilities: ClassVar[list[str]] = ["backtest"]

    def get_identity(self) -> AdapterIdentity:
        return adapter_identity("mock-backtest")

    def run_signals_backtest(
        self,
        signals: SignalFrame,
        market: MarketFrame,
        config: BacktestConfig,
    ) -> BacktestEvidence:
        active_rows = [row for row in signals.rows if row.signal != "flat"]
        signed_size = sum(
            Decimal(row.size) if row.signal == "long" else -Decimal(row.size)
            for row in active_rows
        )
        total_return = float(signed_size * Decimal("0.001"))
        strategy_hash = config.metadata.get("strategy_instance_hash")
        if not isinstance(strategy_hash, str) or not strategy_hash.startswith("sha256:"):
            strategy_hash = compute_frame_hash(signals)

        evidence = BacktestEvidence(
            strategy_instance_hash=strategy_hash,
            market_frame_hash=compute_frame_hash(market),
            stats=BacktestStats(
                total_return=total_return,
                num_trades=len(active_rows),
                win_rate=1.0 if signed_size > 0 else 0.0 if active_rows else None,
            ),
            metadata={
                "adapter_id": self.get_identity().adapter_id,
                "base_currency": config.base_currency,
                "initial_cash": config.initial_cash,
                **config.metadata,
            },
        )
        return with_artifact_id(evidence)
