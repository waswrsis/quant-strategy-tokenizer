from __future__ import annotations

from pathlib import Path

import yaml

from qst.integrations.finrobot import FinRobotReadOnlyTools, finrobot_toolkit_config
from qst.provenance import ArtifactDescriptor
from qst.storage import ContentAddressedStore

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "examples" / "strategies" / "01_ema_cross" / "strategy.gkr.yaml"


def test_finrobot_returns_canonical_record_and_three_hashes(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    identity = tools.strategy_identity(STRATEGY)
    assert identity["strategy_hash"].startswith("sha256:")
    assert identity["graph_hash"].startswith("sha256:")
    assert identity["param_hash"].startswith("sha256:")
    assert identity["instance_hash"].startswith("sha256:")
    assert identity["canonical"]["delivery"] == "inline"
    assert identity["canonical"]["value"]["ir_version"] == "qst-ir/0.4"

    validation = tools.strategy_validate(STRATEGY)
    assert validation["ok"]
    assert not validation["admission_ready"]
    assert validation["error_count"] == 0
    assert validation["warning_count"] == 3
    assert validation["admission_blockers"] == [
        "missing_data_binding",
        "missing_risk_constraint",
    ]


def test_non_executable_boundary_warning_does_not_block_record_admission(
    tmp_path: Path,
) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    payload = yaml.safe_load(STRATEGY.read_text(encoding="utf-8"))
    payload["metadata"]["data_binding"] = "sha256:" + "a" * 64
    payload["strategy"]["nodes"].append(
        {
            "id": "risk_cap",
            "token_ref": {
                "namespace": "core",
                "name": "risk.position_cap",
                "version": 1,
                "behavior_version": 1,
            },
            "inputs": {},
            "params": {"cap": 1.0},
            "signature": {},
        }
    )
    result = tools.strategy_validate(yaml.safe_dump(payload, sort_keys=False))
    assert result["ok"]
    assert result["admission_ready"]
    assert result["admission_blockers"] == []
    assert "not_executable_by_adapter" in {
        item["code"] for item in result["diagnostics"]
    }


def test_finrobot_accepts_yaml_text_and_emits_stable_agent_diagnostics(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    payload = yaml.safe_load(STRATEGY.read_text(encoding="utf-8"))
    payload["strategy"]["nodes"][0]["token_ref"]["namespace"] = "missing"
    result = tools.strategy_validate(yaml.safe_dump(payload, sort_keys=False))
    codes = {item["code"] for item in result["diagnostics"]}
    assert "unsupported_token" in codes
    assert "missing_data_binding" in codes
    assert "missing_risk_constraint" in codes
    assert "not_executable_by_adapter" in codes
    assert not result["ok"]


def test_custom_token_diagnostic_requires_approval(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    payload = yaml.safe_load(STRATEGY.read_text(encoding="utf-8"))
    payload["strategy"]["nodes"][0]["token_ref"]["namespace"] = "custom"
    result = tools.strategy_validate(yaml.safe_dump(payload, sort_keys=False))
    assert "custom_token_requires_approval" in {
        item["code"] for item in result["diagnostics"]
    }

    project_custom = tools.strategy_validate(
        ROOT
        / "examples"
        / "strategies"
        / "12_custom_token_kalman_signal"
        / "strategy.gkr.yaml"
    )
    assert "custom_token_requires_approval" in {
        item["code"] for item in project_custom["diagnostics"]
    }


def test_large_canonical_delivery_uses_verified_cas_descriptor(tmp_path: Path) -> None:
    store = ContentAddressedStore(tmp_path / "store")
    tools = FinRobotReadOnlyTools(store)
    payload = yaml.safe_load(STRATEGY.read_text(encoding="utf-8"))
    payload["metadata"]["bounded_padding"] = "x" * 300_000
    identity = tools.strategy_identity(yaml.safe_dump(payload, sort_keys=False))
    assert identity["canonical"]["delivery"] == "content_addressed_store"
    descriptor = ArtifactDescriptor.model_validate(identity["canonical"]["descriptor"])
    assert store.verify(descriptor)


def test_finrobot_bridge_is_vendor_neutral_callable_config(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    config = finrobot_toolkit_config(tools)
    assert len(config) == 6
    assert all(callable(item) for item in config)
    assert {item.__name__ for item in config} == {
        "artifact_verify",
        "claim_readiness",
        "evidence_inspect",
        "strategy_identity",
        "strategy_validate",
        "token_resolve",
    }
