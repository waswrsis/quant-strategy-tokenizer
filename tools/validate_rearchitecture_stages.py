"""Validate staged QST 1.0 rearchitecture freeze manifests."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "qst-rearchitecture-stage/1"
ALLOWED_STATUSES = {"planned", "active", "candidate", "failed", "frozen"}
ALLOWED_RESULTS = {"pass", "fail", "not_run"}


def _issue(code: str, path: Path, message: str) -> dict[str, str]:
    return {"code": code, "path": path.as_posix(), "message": message}


def _load_manifests(root: Path) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, str]]]:
    manifests: list[tuple[Path, dict[str, Any]]] = []
    issues: list[dict[str, str]] = []
    for path in sorted(root.glob("stage-*.yaml")):
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            issues.append(_issue("QST_STAGE_MANIFEST_PARSE_ERROR", path, str(exc)))
            continue
        if not isinstance(value, dict):
            issues.append(
                _issue("QST_STAGE_MANIFEST_NOT_MAPPING", path, "manifest must be a mapping")
            )
            continue
        manifests.append((path, value))
    manifests.sort(
        key=lambda item: (
            item[1].get("stage_id")
            if isinstance(item[1].get("stage_id"), int)
            else float("inf"),
            item[0].name,
        )
    )
    if not manifests:
        issues.append(_issue("QST_STAGE_MANIFEST_MISSING", root, "no stage manifests found"))
    return manifests, issues


def _git_tag_exists(tag: str, *, cwd: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def validate(root: Path, *, check_git_tags: bool = False) -> dict[str, Any]:
    manifests, issues = _load_manifests(root)
    seen_ids: set[int] = set()
    frozen_prefix = True
    repo_root = root.resolve().parents[2]

    for path, manifest in manifests:
        stage_id = manifest.get("stage_id")
        status = manifest.get("status")
        if manifest.get("schema_version") != SCHEMA_VERSION:
            issues.append(_issue("QST_STAGE_SCHEMA_INVALID", path, "schema_version is invalid"))
        if not isinstance(stage_id, int) or stage_id < 0:
            issues.append(_issue("QST_STAGE_ID_INVALID", path, "stage_id must be nonnegative"))
            continue
        if stage_id in seen_ids:
            issues.append(_issue("QST_STAGE_ID_DUPLICATE", path, f"duplicate stage_id {stage_id}"))
        seen_ids.add(stage_id)
        if status not in ALLOWED_STATUSES:
            issues.append(_issue("QST_STAGE_STATUS_INVALID", path, f"invalid status {status!r}"))
        if status != "frozen":
            frozen_prefix = False
        elif not frozen_prefix:
            issues.append(
                _issue("QST_STAGE_FREEZE_ORDER_INVALID", path, "frozen stages must form a prefix")
            )

        gates = manifest.get("gates")
        if not isinstance(gates, list) or not gates:
            issues.append(_issue("QST_STAGE_GATES_MISSING", path, "gates must be non-empty"))
        else:
            for gate in gates:
                if not isinstance(gate, dict) or gate.get("result") not in ALLOWED_RESULTS:
                    issues.append(_issue("QST_STAGE_GATE_INVALID", path, "gate result is invalid"))
                elif status == "frozen" and gate["result"] != "pass":
                    issues.append(
                        _issue("QST_STAGE_FROZEN_GATE_NOT_PASS", path, "all frozen gates must pass")
                    )

        frozen_contracts = manifest.get("frozen_contracts")
        if not isinstance(frozen_contracts, list) or not frozen_contracts:
            issues.append(
                _issue("QST_STAGE_FROZEN_CONTRACTS_MISSING", path, "contracts are required")
            )

        tag = manifest.get("freeze_tag")
        if not isinstance(tag, str) or not tag:
            issues.append(_issue("QST_STAGE_FREEZE_TAG_MISSING", path, "freeze_tag is required"))
        elif check_git_tags and status == "frozen" and not _git_tag_exists(tag, cwd=repo_root):
            issues.append(_issue("QST_STAGE_FREEZE_TAG_NOT_FOUND", path, f"missing local tag {tag}"))

    expected_ids = list(range(len(seen_ids)))
    if sorted(seen_ids) != expected_ids:
        issues.append(
            _issue(
                "QST_STAGE_ID_SEQUENCE_INVALID",
                root,
                f"stage ids must be contiguous from zero; found {sorted(seen_ids)}",
            )
        )

    issues.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return {
        "stage_manifest_validation": {
            "result": "pass" if not issues else "fail",
            "manifest_count": len(manifests),
            "issue_count": len(issues),
            "issues": issues,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("docs/rearchitecture/stages"),
    )
    parser.add_argument("--check-git-tags", action="store_true")
    args = parser.parse_args()
    report = validate(args.root, check_git_tags=args.check_git_tags)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["stage_manifest_validation"]["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
