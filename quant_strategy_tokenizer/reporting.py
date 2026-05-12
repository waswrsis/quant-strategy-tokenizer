"""
quant_strategy_tokenizer.reporting
==================================
Module purpose: write standard redacted module reports for humans and automation.
Core idea: Serialize ModuleResult into summary, events, and data files only when output_dir is explicitly supplied. Assumes report writing is an opt-in side effect and sensitive-looking keys/values must be redacted recursively.
Inputs: module name, ModuleResult, output directory, and optional run id.
Outputs: OutputFiles pointing to summary JSON, events JSONL, and data JSON.
Failure semantics: file-system errors are raised to the caller; modules should call this only after successful explicit output_dir configuration.
Market generalization: report format is module-agnostic and does not assume venue, account, or asset class.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
import json
import re
from typing import Any

import pandas as pd

from .contracts import ModuleResult, OutputFiles

_SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|apikey|secret|token|password|passwd|authorization|auth|cookie|session|signature|private[_-]?key|email|account)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_RE = re.compile(
    r"(ghp_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
    re.IGNORECASE,
)
_REDACTED = "[REDACTED]"


def write_module_report(module_name: str, result: ModuleResult[Any], output_dir: str, *, run_id: str = "") -> OutputFiles:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = str(module_name or "module")
    summary_path = out / f"{stem}.summary.json"
    events_path = out / f"{stem}.events.jsonl"
    data_path = out / f"{stem}.data.json"

    summary = {
        "module": stem,
        "run_id": run_id,
        "ok": result.ok,
        "warnings": list(result.warnings or []),
        "failure": _safe(result.failure),
        "event_count": len(result.events or []),
    }
    summary_path.write_text(json.dumps(_safe(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    with events_path.open("w", encoding="utf-8") as fh:
        for ev in result.events or []:
            fh.write(json.dumps(_safe(ev), ensure_ascii=False, separators=(",", ":")) + "\n")

    data_path.write_text(json.dumps(_safe(result.value), ensure_ascii=False, indent=2), encoding="utf-8")
    return OutputFiles(summary_json=str(summary_path), events_jsonl=str(events_path), data_json=str(data_path))


def _safe(value: Any) -> Any:
    if isinstance(value, str):
        return _REDACTED if _SENSITIVE_VALUE_RE.search(value) else value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if is_dataclass(value):
        return _safe(asdict(value))
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key = str(k)
            out[key] = _REDACTED if _SENSITIVE_KEY_RE.search(key) else _safe(v)
        return out
    if isinstance(value, (list, tuple, set)):
        return [_safe(v) for v in value]
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.tolist()
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    except Exception:
        pass
    return str(value)


__all__ = ["write_module_report"]
