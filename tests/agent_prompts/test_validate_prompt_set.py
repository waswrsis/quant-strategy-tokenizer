from __future__ import annotations

import shutil
from pathlib import Path

from tools.validate_prompt_set import validate_prompt_set

ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = ROOT / "docs" / "agent" / "prompts" / "qst_stage_3c_v0_3_2"


def _copy_prompt_pack(tmp_path: Path) -> Path:
    target = tmp_path / "prompt_pack"
    shutil.copytree(PROMPT_ROOT, target)
    return target


def _issue_ids(result: dict[str, object]) -> set[str]:
    payload = result["prompt_validation"]
    assert isinstance(payload, dict)
    checks = payload["checks"]
    assert isinstance(checks, list)
    return {
        str(check["id"])
        for check in checks
        if isinstance(check, dict) and check.get("result") == "fail"
    }


def test_stage3c_prompt_pack_validation_passes() -> None:
    result = validate_prompt_set(PROMPT_ROOT)

    assert result["prompt_validation"]["result"] == "pass"


def test_stage3c_prompt_validator_detects_missing_cross_reference(tmp_path: Path) -> None:
    prompt_root = _copy_prompt_pack(tmp_path)
    (prompt_root / "readers" / "READ_CLI.md").unlink()
    result = validate_prompt_set(prompt_root)

    assert result["prompt_validation"]["result"] == "fail"
    assert {"required_files", "cross_references", "load_profiles"} & _issue_ids(result)


def test_stage3c_prompt_validator_detects_stale_state_and_hash_truth(tmp_path: Path) -> None:
    prompt_root = _copy_prompt_pack(tmp_path)
    stale = prompt_root / "core" / "99_STALE.md"
    stale.write_text(
        "prompt_system_version: qst-stage-3c-v0.3.2.1\n"
        "QST_CURRENT_STATE\n"
        "graph_hash = sha256:0000000000000000000000000000000000000000000000000000000000000000\n",
        encoding="utf-8",
    )
    result = validate_prompt_set(prompt_root)

    assert result["prompt_validation"]["result"] == "fail"
    assert "stale_information" in _issue_ids(result)


def test_stage3c_prompt_validator_detects_load_profile_missing_file(tmp_path: Path) -> None:
    prompt_root = _copy_prompt_pack(tmp_path)
    profile = prompt_root / "load_profiles" / "PROFILE_MINIMAL.md"
    profile.write_text(
        profile.read_text(encoding="utf-8") + "\n- `readers/READ_NOT_REAL.md`\n",
        encoding="utf-8",
    )
    result = validate_prompt_set(prompt_root)

    assert result["prompt_validation"]["result"] == "fail"
    assert {"cross_references", "load_profiles"} <= _issue_ids(result)


def test_stage3c_prompt_validator_requires_three_complete_golden_tasks(tmp_path: Path) -> None:
    prompt_root = _copy_prompt_pack(tmp_path)
    (prompt_root / "golden" / "12_custom_token_kalman_signal.intent.yaml").unlink()
    result = validate_prompt_set(prompt_root)

    assert result["prompt_validation"]["result"] == "fail"
    assert "golden_tasks" in _issue_ids(result)
