"""Read and write P3a-0 qst.lock artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.serialize import to_plain
from quant_strategy_tokenizer.qst_lock.canonical import canonical_lock_bytes
from quant_strategy_tokenizer.qst_lock.schema import LockFile


def write_lock(lock: LockFile, path: str | Path) -> None:
    """Write a lock file as canonical JSON bytes."""

    Path(path).write_bytes(canonical_lock_bytes(lock.model_dump(mode="json", exclude_none=True)))


def read_lock(path: str | Path) -> LockFile:
    """Read and validate a qst.lock file."""

    return LockFile.model_validate_json(Path(path).read_text(encoding="utf-8-sig"))


def write_canonical_ir(ir: StrategyIR, path: str | Path) -> None:
    """Write canonical IR as canonical JSON bytes."""

    Path(path).write_bytes(canonical_lock_bytes(to_plain(ir)))


def read_canonical_ir(path: str | Path) -> StrategyIR:
    """Read a canonical IR JSON file."""

    raw: Any = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return StrategyIR.model_validate(raw)
