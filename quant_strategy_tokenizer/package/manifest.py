"""P3a-1 package manifest models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.qst_lock.schema import HashString


class PackageFile(BaseModel):
    """One file entry recorded in a qstpkg manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sha256: HashString


class PackageStrategyManifest(BaseModel):
    """Strategy file locations inside a qstpkg."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    version: int
    source_path: str = "strategies/source.qst.yaml"
    canonical_path: str = "strategies/canonical.json"
    lock_path: str = "qst.lock"


class PackageManifest(BaseModel):
    """Top-level qstpkg manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    package_version: Literal["qstpkg/0.1"] = "qstpkg/0.1"
    qst_version: str
    strategy: PackageStrategyManifest
    fixtures_manifest_path: str = "fixtures/manifest.yaml"
    files: list[PackageFile] = Field(default_factory=list)
    tagspec_paths: list[str] = Field(default_factory=list)
    recipe_paths: list[str] = Field(default_factory=list)


class FixturesManifest(BaseModel):
    """Optional fixture file locations and hashes inside a qstpkg."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    market_csv_path: str | None = None
    market_csv_hash: HashString | None = None
    expected_trace_path: str | None = None
    expected_trace_full_hash: HashString | None = None
    expected_trace_semantic_hash: HashString | None = None


class UnpackedPackage(BaseModel):
    """Resolved qstpkg paths and parsed manifests."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    root: Path
    manifest: PackageManifest
    fixtures_manifest: FixturesManifest
    source_path: Path
    canonical_path: Path
    lock_path: Path
    market_path: Path | None = None
    expected_trace_path: Path | None = None
