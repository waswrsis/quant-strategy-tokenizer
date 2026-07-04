from __future__ import annotations

import json
import time
from pathlib import Path

from qst.identity import identity_hash
from qst.integrations.finrobot import FinRobotReadOnlyTools
from qst.storage import ContentAddressedStore

ROOT = Path(__file__).resolve().parents[2]


def test_alpha_package_and_document_status_are_consistent() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'version = "1.0.0a1"' in pyproject
    assert "1.0.0a1" in readme
    assert "research/qst-1.0-agent-provenance" in readme
    assert "nothing on this branch has been pushed" in readme.lower()


def test_public_demo_set_and_vocabulary_baseline_are_unchanged() -> None:
    cases = {
        path.parent.name
        for path in (ROOT / "examples" / "strategies").glob("*/strategy.gkr.yaml")
    }
    assert len(cases) == 12
    assert "01_ema_cross" in cases
    assert "12_custom_token_kalman_signal" in cases


def test_small_identity_hash_p95_is_below_measurement_target() -> None:
    durations = []
    payload = {"strategy_hash": "sha256:" + "a" * 64, "parameters": {"window": 20}}
    for _ in range(200):
        started = time.perf_counter()
        identity_hash("qst:performance-probe:v1", payload)
        durations.append(time.perf_counter() - started)
    durations.sort()
    p95 = durations[int(len(durations) * 0.95) - 1]
    assert p95 < 0.010


def test_finrobot_default_token_resolution_response_is_compact(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    response = tools.token_resolve({"concept": "core.math.add"})
    encoded = json.dumps(response, sort_keys=True).encode("utf-8")
    assert len(encoded) <= 4096
    assert response["route"] == "direct_token_match"


def test_python_sources_have_no_nul_bytes() -> None:
    assert [path for path in (ROOT / "qst").rglob("*.py") if b"\x00" in path.read_bytes()] == []
