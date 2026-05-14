from __future__ import annotations

from datetime import UTC, datetime

from quant_strategy_tokenizer.artifacts.backtest_evidence import BacktestEvidence
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar, SignalFrame
from quant_strategy_tokenizer.ir.model import ExternalSpec, GraphNode, StrategyIR
from quant_strategy_tokenizer.ports import BacktestConfig, run_strategy_backtest
from quant_strategy_tokenizer.runtime.signal_extraction import SignalExtractionPolicy

HASH = "sha256:" + "2" * 64


class CapturingBacktestAdapter:
    signals: SignalFrame | None = None

    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="capture", adapter_version="1.0.0")

    def run_signals_backtest(
        self,
        signals: SignalFrame,
        market: MarketFrame,
        config: BacktestConfig,
    ) -> BacktestEvidence:
        del market, config
        self.signals = signals
        return BacktestEvidence(
            strategy_instance_hash=HASH,
            stats={"total_return": 0.0, "num_trades": 0},
        )


def test_run_strategy_backtest_extracts_signals_before_adapter_call() -> None:
    market = MarketFrame(
        symbols=["BTC/USDT"],
        bars=[
            OHLCVBar(
                timestamp=datetime(2026, 5, 14, tzinfo=UTC),
                symbol="BTC/USDT",
                open="10",
                high="12",
                low="9",
                close="11",
                volume="100",
            )
        ],
    )
    strategy = StrategyIR(
        strategy="bool_signal",
        externals={"market": ExternalSpec(type="Frame[OHLCV]", required=True)},
        graph=[
            GraphNode(
                id="signal",
                token="compare.gt",
                inputs={"a": "$externals.market.close", "b": "$externals.market.open"},
            )
        ],
        outputs={"signal": "signal.value"},
    )
    adapter = CapturingBacktestAdapter()

    result = run_strategy_backtest(
        strategy,
        market,
        BacktestConfig(),
        adapter=adapter,
        signal_policy=SignalExtractionPolicy(output_node_name="signal"),
    )

    assert result.strategy_instance_hash == HASH
    assert adapter.signals is not None
    assert adapter.signals.rows[0].signal == "long"
