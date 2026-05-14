"""Strategy package port protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.package import UnpackedPackage


@runtime_checkable
class StrategyPackagePort(Protocol):
    """Adapter protocol for storing and retrieving qstpkg directories."""

    def get_identity(self) -> AdapterIdentity: ...

    def put_package(self, package_dir: Path) -> str: ...

    def get_package(self, package_id: str, output_dir: Path) -> UnpackedPackage: ...
