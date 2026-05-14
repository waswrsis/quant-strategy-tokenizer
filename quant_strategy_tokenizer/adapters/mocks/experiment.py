"""Deterministic mock experiment adapter."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from quant_strategy_tokenizer.adapters.mocks.common import adapter_identity, content_hash
from quant_strategy_tokenizer.artifacts.backtest_evidence import ArtifactRef
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.package import read_package
from quant_strategy_tokenizer.ports import ExperimentRunConfig


class MockExperimentAdapter:
    """Mock experiment tracking adapter that records package metadata only."""

    capabilities: ClassVar[list[str]] = ["experiment"]

    def get_identity(self) -> AdapterIdentity:
        return adapter_identity("mock-experiment")

    def track_package(self, package_dir: Path, config: ExperimentRunConfig) -> ArtifactRef:
        package = read_package(package_dir)
        payload = {
            "adapter_id": self.get_identity().adapter_id,
            "package_version": package.manifest.package_version,
            "qst_version": package.manifest.qst_version,
            "run_name": config.run_name,
            "strategy": package.manifest.strategy.model_dump(mode="json"),
            "tags": dict(sorted(config.tags.items())),
        }
        digest = content_hash(payload)
        return ArtifactRef(
            path=f"artifacts/experiments/{digest.removeprefix('sha256:')[:16]}.json",
            hash=digest,
        )
