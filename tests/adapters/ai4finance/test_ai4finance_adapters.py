from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from qst.adapters.ai4finance import (
    ADAPTER_TYPES,
    FinGPTEvidenceAdapter,
    FinRLEvidenceAdapter,
    FinRLMetaEvidenceAdapter,
    FinRLXEvidenceAdapter,
    FinRobotEvidenceAdapter,
    QlibEvidenceAdapter,
)
from qst.collectors import EvidenceAdapter
from qst.evidence import EvidenceEnvelope, ExternalRecordEvidencePayload, seal_evidence
from qst.integrations.finrobot import FinRobotReadOnlyTools
from qst.storage import ContentAddressedStore

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "ai4finance"
NOW = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("adapter_type", "fixture", "expected_maturity"),
    [
        (FinRobotEvidenceAdapter, "finrobot.yaml", "L3"),
        (FinGPTEvidenceAdapter, "fingpt.yaml", "L2"),
        (FinRLMetaEvidenceAdapter, "finrl_meta.yaml", "L2"),
        (FinRLEvidenceAdapter, "finrl.yaml", "L3"),
        (FinRLXEvidenceAdapter, "finrl_x.yaml", "L3"),
        (QlibEvidenceAdapter, "qlib.yaml", "L3"),
    ],
)
def test_adapter_probe_discovery_and_plan(
    tmp_path: Path, adapter_type: type, fixture: str, expected_maturity: str
) -> None:
    adapter = adapter_type(ContentAddressedStore(tmp_path / "store"))
    source = str(FIXTURES / fixture)
    assert isinstance(adapter, EvidenceAdapter)
    assert adapter.probe(source)["ok"] is True
    assert adapter.probe(source)["maturity"] == expected_maturity
    assert adapter.discover(source)["run_id"]
    assert adapter.extract_plan(source)
    assert "execute" not in dir(adapter)


def test_only_l3_adapters_are_workflow_claim_eligible(tmp_path: Path) -> None:
    store = ContentAddressedStore(tmp_path / "store")
    adapters = {system: adapter_type(store) for system, adapter_type in ADAPTER_TYPES.items()}
    assert not adapters["fingpt"].descriptor.workflow_claim_eligible
    assert not adapters["finrl_meta"].descriptor.workflow_claim_eligible
    assert adapters["finrobot"].descriptor.workflow_claim_eligible
    assert adapters["finrl"].descriptor.workflow_claim_eligible
    assert adapters["finrl_x"].descriptor.workflow_claim_eligible
    assert adapters["qlib"].descriptor.workflow_claim_eligible


@pytest.mark.parametrize(
    ("adapter_type", "fixture"),
    [
        (FinRobotEvidenceAdapter, "finrobot.yaml"),
        (FinRLEvidenceAdapter, "finrl.yaml"),
        (FinRLXEvidenceAdapter, "finrl_x.yaml"),
        (QlibEvidenceAdapter, "qlib.yaml"),
    ],
)
def test_l3_golden_artifacts_are_collected_and_verified(
    tmp_path: Path, adapter_type: type, fixture: str
) -> None:
    adapter = adapter_type(ContentAddressedStore(tmp_path / fixture))
    source = str(FIXTURES / fixture)
    result = adapter.collect_run(source)
    descriptors = adapter.describe_artifacts(source)
    assert result["status"] == "complete"
    assert descriptors
    assert all(adapter.store.verify(item) for item in descriptors)
    evidence = seal_evidence(
        EvidenceEnvelope(
            subject_ref=result["run_id"],
            observed_at=NOW,
            payload=ExternalRecordEvidencePayload(
                adapter_id=adapter.descriptor.adapter_id,
                record_type="golden_workflow",
                record_schema="qst-ai4finance-workflow/1.0",
                record=result,
            ),
        )
    )
    assert adapter.verify(evidence)


def test_adapter_rejects_wrong_project_manifest(tmp_path: Path) -> None:
    adapter = FinRobotEvidenceAdapter(ContentAddressedStore(tmp_path / "store"))
    with pytest.raises(ValueError, match="cannot read system"):
        adapter.extract_plan(str(FIXTURES / "finrl.yaml"))


def test_finrobot_exposes_six_compact_read_only_tools(tmp_path: Path) -> None:
    tools = FinRobotReadOnlyTools(ContentAddressedStore(tmp_path / "store"))
    public_tools = {
        "strategy_validate",
        "strategy_identity",
        "token_resolve",
        "evidence_inspect",
        "artifact_verify",
        "claim_readiness",
    }
    assert public_tools <= set(dir(tools))
    assert "execute" not in dir(tools)
    resolved = tools.token_resolve({"concept": "core.math.add"})
    assert resolved["route"] == "direct_token_match"
    assert resolved["candidate_count"] == 1
    assert resolved["top_candidate"] == "core.math.add"
