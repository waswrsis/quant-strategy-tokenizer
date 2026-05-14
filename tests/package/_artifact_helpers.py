from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HASH = "sha256:" + "1" * 64


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return path


def execution_report(qty_intended: str = "1") -> dict[str, Any]:
    return {
        "artifact_version": "qst-execution-report/1",
        "event_type": "new",
        "state": "acknowledged",
        "qty_intended": qty_intended,
        "qty_last": "0",
        "qty_filled": "0",
        "qty_remaining": qty_intended,
        "source_protocol": "test",
        "venue": "paper",
    }


def portfolio_snapshot() -> dict[str, Any]:
    return {
        "artifact_version": "qst-portfolio-snapshot/1",
        "timestamp": "2026-05-14T00:00:00Z",
        "base_currency": "USD",
        "cash": "100",
        "equity": "100",
        "positions": [],
    }


def backtest_evidence(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_version": "qst-backtest-evidence/1",
        "strategy_instance_hash": HASH,
        "stats": {
            "total_return": 0.25,
            "num_trades": 1,
        },
    }
    payload.update(overrides)
    return payload
