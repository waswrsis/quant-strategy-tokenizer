"""P3a-0 qst.lock schema models."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, IR_VERSION
from quant_strategy_tokenizer.provenance.verification_order import VerificationState

SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
HashString = Annotated[str, Field(pattern=SHA256_PATTERN)]
QstVersionPolicy = Literal["strict", "same_minor"]


class StrategyHashSnapshot(BaseModel):
    """Frozen strategy hash snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    graph_hash: HashString
    param_hash: HashString
    instance_hash: HashString


class ExternalsSnapshot(BaseModel):
    """Frozen externals schema snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_hash: HashString


class TokenDependency(BaseModel):
    """A token dependency required by a locked strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    version: int
    behavior_version: int


class RecipeDependency(BaseModel):
    """A recipe dependency required by a locked strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recipe: str
    version: int


class TagSpecDependency(BaseModel):
    """A provenance TagSpec dependency required by a locked strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    semantic_id: str
    version: int
    graph_template_hash: HashString
    verification_state: VerificationState
    allowed_kernels: list[str] = Field(default_factory=list)


class FixtureHashes(BaseModel):
    """Optional fixture hashes used for reproducibility checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    market_csv_hash: HashString | None = None
    expected_trace_hash: HashString | None = None
    trace_semantic_hash: HashString | None = None


class LockFile(BaseModel):
    """Canonical P3a-0 qst.lock model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lock_version: Literal["qst-lock/0.1"] = "qst-lock/0.1"
    qst_version: str
    qst_version_policy: QstVersionPolicy = "strict"
    ir_version: str = IR_VERSION
    canonical_version: str = CANONICAL_VERSION
    strategy: str
    strategy_version: int
    strategy_hashes: StrategyHashSnapshot
    canonical_ir_hash: HashString
    externals: ExternalsSnapshot
    tokens: list[TokenDependency]
    recipes: list[RecipeDependency] = Field(default_factory=list)
    tagspecs: list[TagSpecDependency] = Field(default_factory=list)
    fixtures: FixtureHashes = Field(default_factory=FixtureHashes)
