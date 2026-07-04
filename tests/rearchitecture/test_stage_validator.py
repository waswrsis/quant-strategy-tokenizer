from __future__ import annotations

from pathlib import Path

import yaml

from tools.validate_rearchitecture_stages import validate


def test_stage_validator_orders_two_digit_stage_ids_numerically(tmp_path: Path) -> None:
    for stage_id in range(11):
        status = "candidate" if stage_id == 10 else "frozen"
        manifest = {
            "schema_version": "qst-rearchitecture-stage/1",
            "stage_id": stage_id,
            "status": status,
            "freeze_tag": f"stage-{stage_id}-frozen",
            "frozen_contracts": [f"contract-{stage_id}"],
            "gates": [
                {
                    "command": "test",
                    "result": "not_run" if status == "candidate" else "pass",
                }
            ],
        }
        path = tmp_path / f"stage-{stage_id}-fixture.yaml"
        path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    report = validate(tmp_path)
    assert report["stage_manifest_validation"]["result"] == "pass"
    assert report["stage_manifest_validation"]["manifest_count"] == 11
