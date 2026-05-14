"""Experiment tracking port protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.artifacts.backtest_evidence import ArtifactRef
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity


class ExperimentRunConfig(BaseModel):
    """Adapter-neutral experiment tracking request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_name: str
    tags: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class ExperimentPort(Protocol):
    """Adapter protocol for tracking qstpkg experiment outputs."""

    def get_identity(self) -> AdapterIdentity: ...

    def track_package(self, package_dir: Path, config: ExperimentRunConfig) -> ArtifactRef: ...
