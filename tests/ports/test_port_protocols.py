from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.artifacts.backtest_evidence import BacktestEvidence
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import FeatureFrame, MarketFrame
from quant_strategy_tokenizer.package import UnpackedPackage
from quant_strategy_tokenizer.ports import (
    BacktestConfig,
    BacktestPort,
    ExperimentPort,
    ExperimentRunConfig,
    FeatureLoadRequest,
    FeaturePort,
    MarketDataPort,
    MarketLoadRequest,
    RLPort,
    StrategyPackagePort,
)

HASH = "sha256:" + "1" * 64


class FakeMarketPort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-market", adapter_version="1.0.0")

    def load_market(self, request: MarketLoadRequest) -> MarketFrame:
        return MarketFrame(symbols=request.symbols, bars=[])


class FakeFeaturePort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-feature", adapter_version="1.0.0")

    def load_features(self, request: FeatureLoadRequest) -> FeatureFrame:
        return FeatureFrame(symbols=request.symbols, rows=[])


class FakeBacktestPort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-backtest", adapter_version="1.0.0")

    def run_signals_backtest(
        self,
        signals: object,
        market: object,
        config: BacktestConfig,
    ) -> BacktestEvidence:
        del signals, market, config
        return BacktestEvidence(
            strategy_instance_hash=HASH,
            stats={"total_return": 0.0, "num_trades": 0},
        )


class FakeExperimentPort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-experiment", adapter_version="1.0.0")

    def track_package(self, package_dir: Path, config: ExperimentRunConfig) -> object:
        del package_dir, config
        return {"path": "artifacts/backtest/evidence.json", "hash": HASH}


class FakePackagePort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-package", adapter_version="1.0.0")

    def put_package(self, package_dir: Path) -> str:
        del package_dir
        return "pkg-1"

    def get_package(self, package_id: str, output_dir: Path) -> UnpackedPackage:
        del package_id, output_dir
        raise NotImplementedError


class FakeRLPort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-rl", adapter_version="1.0.0")


def test_port_protocols_are_runtime_checkable() -> None:
    assert isinstance(FakeMarketPort(), MarketDataPort)
    assert isinstance(FakeFeaturePort(), FeaturePort)
    assert isinstance(FakeBacktestPort(), BacktestPort)
    assert isinstance(FakeExperimentPort(), ExperimentPort)
    assert isinstance(FakePackagePort(), StrategyPackagePort)
    assert isinstance(FakeRLPort(), RLPort)


def test_backtest_port_protocol_has_signal_frame_boundary() -> None:
    annotations = BacktestPort.run_signals_backtest.__annotations__

    assert annotations["signals"] == "SignalFrame"
    assert annotations["market"] == "MarketFrame"
    assert "StrategyIR" not in annotations.values()
