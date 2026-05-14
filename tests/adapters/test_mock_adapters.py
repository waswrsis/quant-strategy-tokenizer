from __future__ import annotations

from pathlib import Path

import pytest

from quant_strategy_tokenizer.adapters import discover_adapters, get_adapter
from quant_strategy_tokenizer.adapters.mocks import (
    CsvMarketAdapter,
    MockBacktestAdapter,
    MockExecutionAdapter,
    MockExperimentAdapter,
    ParquetMarketAdapter,
)
from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar, SignalFrame, SignalRow
from quant_strategy_tokenizer.frames.io.csv_io import write_csv_frame
from quant_strategy_tokenizer.frames.io.parquet_io import write_parquet_frame
from quant_strategy_tokenizer.package import package_strategy
from quant_strategy_tokenizer.ports import BacktestConfig, ExperimentRunConfig, MarketLoadRequest
from quant_strategy_tokenizer.types.plan import OrderIntentPlan

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def _market_frame() -> MarketFrame:
    return MarketFrame(
        bars=[
            OHLCVBar(
                timestamp="2026-05-14T00:00:00Z",
                symbol="BTC/USDT",
                open="100",
                high="101",
                low="99",
                close="100",
                volume="1",
            ),
            OHLCVBar(
                timestamp="2026-05-14T00:01:00Z",
                symbol="BTC/USDT",
                open="100",
                high="102",
                low="100",
                close="101",
                volume="2",
            ),
        ]
    )


def _signal_frame() -> SignalFrame:
    return SignalFrame(
        rows=[
            SignalRow(
                timestamp="2026-05-14T00:00:00Z",
                symbol="BTC/USDT",
                signal="long",
                size="1",
            )
        ]
    )


def test_builtin_mock_adapters_are_discoverable_and_loadable() -> None:
    ids = [descriptor.adapter_id for descriptor in discover_adapters()]

    assert ids == sorted(ids)
    assert {
        "mock-backtest",
        "mock-csv-market",
        "mock-execution",
        "mock-experiment",
        "mock-parquet-market",
    }.issubset(ids)
    assert isinstance(get_adapter("mock-csv-market"), CsvMarketAdapter)
    assert isinstance(get_adapter("mock-parquet-market"), ParquetMarketAdapter)
    assert isinstance(get_adapter("mock-backtest"), MockBacktestAdapter)
    assert isinstance(get_adapter("mock-execution"), MockExecutionAdapter)
    assert isinstance(get_adapter("mock-experiment"), MockExperimentAdapter)


def test_csv_market_adapter_filters_symbols(tmp_path: Path) -> None:
    market = MarketFrame(
        bars=[
            *_market_frame().bars,
            OHLCVBar(
                timestamp="2026-05-14T00:00:00Z",
                symbol="ETH/USDT",
                open="10",
                high="11",
                low="9",
                close="10",
                volume="1",
            ),
            OHLCVBar(
                timestamp="2026-05-14T00:01:00Z",
                symbol="ETH/USDT",
                open="10",
                high="12",
                low="10",
                close="11",
                volume="1",
            ),
        ]
    )
    path = tmp_path / "market.csv"
    write_csv_frame(market, path)

    loaded = CsvMarketAdapter().load_market(
        MarketLoadRequest(source=str(path), symbols=["BTC/USDT"])
    )

    assert loaded.symbols == ["BTC/USDT"]
    assert all(bar.symbol == "BTC/USDT" for bar in loaded.bars)


def test_parquet_market_adapter_round_trips(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    path = tmp_path / "market.parquet"
    write_parquet_frame(_market_frame(), path)

    loaded = ParquetMarketAdapter().load_market(MarketLoadRequest(source=str(path)))

    assert loaded == _market_frame()


def test_mock_backtest_adapter_is_deterministic() -> None:
    adapter = MockBacktestAdapter()
    market = _market_frame()
    signals = _signal_frame()
    config = BacktestConfig(metadata={"strategy_instance_hash": "sha256:" + "1" * 64})

    first = adapter.run_signals_backtest(signals, market, config)
    second = adapter.run_signals_backtest(signals, market, config)

    assert first.artifact_id == second.artifact_id
    assert first.stats.num_trades == 1
    assert first.market_frame_hash is not None


def test_mock_execution_submit_and_poll_are_immutable() -> None:
    adapter = MockExecutionAdapter()
    plan = OrderIntentPlan(
        decision={"kind": "accept", "reason": "test"},
        side="long",
        sizing=1.0,
    )

    submitted = adapter.submit_plan(plan, confirm=True, client_order_id="cid-1")
    polled = adapter.poll_report(submitted.artifact_id or "missing")

    assert submitted.artifact_id
    assert polled.artifact_id
    assert submitted.artifact_id != polled.artifact_id
    assert polled.event_type == "trade"


def test_mock_experiment_adapter_tracks_package_deterministically(tmp_path: Path) -> None:
    package_dir = tmp_path / "strategy.qstpkg"
    package_strategy(STRATEGY, package_dir)
    adapter = MockExperimentAdapter()
    config = ExperimentRunConfig(run_name="test", tags={"stage": "p4b-1"})

    first = adapter.track_package(package_dir, config)
    second = adapter.track_package(package_dir, config)

    assert first == second
    assert first.path.startswith("artifacts/experiments/")
