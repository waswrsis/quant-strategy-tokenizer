"""Feature port protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import FeatureFrame, QSTSymbol


class FeatureLoadRequest(BaseModel):
    """Adapter-neutral feature load request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    symbols: list[QSTSymbol] = Field(default_factory=list)
    feature_names: list[str] = Field(default_factory=list)


@runtime_checkable
class FeaturePort(Protocol):
    """Adapter protocol for loading feature data into a QST FeatureFrame."""

    def get_identity(self) -> AdapterIdentity: ...

    def load_features(self, request: FeatureLoadRequest) -> FeatureFrame: ...
