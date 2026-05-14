"""P3b-1 strategy fork API."""

from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import (
    IR_VERSION_P3_LINEAGE,
    DerivedFrom,
    StrategyIR,
)
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file


def fork(
    parent: StrategyIR | str | Path,
    new_id: str,
    *,
    parent_package: str | None = None,
    parent_package_version: str | None = None,
) -> StrategyIR:
    """Fork a strategy with inert lineage metadata.

    The parent IR is not modified. The fork output is the only P3 command path
    that intentionally emits qst-ir/0.3.1.
    """

    parent_ir = load_strategy_file(parent) if isinstance(parent, (str, Path)) else parent
    parent_hashes = compute_hashes(parent_ir)
    return parent_ir.model_copy(
        update={
            "ir_version": IR_VERSION_P3_LINEAGE,
            "strategy": new_id,
            "strategy_version": 1,
            "form": "surface",
            "derived_from": DerivedFrom(
                parent_instance_hash=parent_hashes.instance_hash,
                parent_strategy=parent_ir.strategy,
                parent_package=parent_package,
                parent_package_version=parent_package_version,
                mutation_chain=[],
            ),
        },
        deep=True,
    )
