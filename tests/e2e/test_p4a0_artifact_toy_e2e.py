from __future__ import annotations

from quant_strategy_tokenizer.artifacts import (
    ArtifactRef,
    BacktestEvidence,
    BacktestStats,
    ExecutionReport,
    PortfolioSnapshot,
    ProvenanceChain,
    compute_artifact_id,
)
from tests.artifacts.schema_helpers import validate_schema

PARENT_ORDER_INTENT_HASH = "sha256:" + "4" * 64


def _with_artifact_id(artifact):
    artifact_id = compute_artifact_id(artifact.model_dump(mode="json"))
    return artifact.model_copy(update={"artifact_id": artifact_id})


def test_p4a0_artifact_toy_chain() -> None:
    execution_report = _with_artifact_id(
        ExecutionReport(
            event_type="trade",
            state="filled",
            qty_intended="1",
            qty_last="1",
            qty_filled="1",
            qty_remaining="0",
            last_fill_price="100",
            provenance=ProvenanceChain(
                parent_artifacts=[PARENT_ORDER_INTENT_HASH],
                operation="mock_order_intent_to_execution_report",
            ),
            raw_payload_hash="sha256:" + "5" * 64,
            raw_payload_ref="artifacts/execution/raw/fix_001.fix",
            source_protocol="fix",
            source_system="mock_exchange",
            venue="mock",
        )
    )

    portfolio_snapshot = _with_artifact_id(
        PortfolioSnapshot(
            timestamp="2026-05-14T18:00:00Z",
            base_currency="USD",
            cash="900",
            equity="1000",
            positions=[],
            provenance=ProvenanceChain(
                parent_artifacts=[execution_report.artifact_id or ""],
                operation="mock_execution_to_portfolio_snapshot",
            ),
        )
    )

    backtest_evidence = _with_artifact_id(
        BacktestEvidence(
            strategy_instance_hash="sha256:" + "6" * 64,
            stats=BacktestStats(total_return="0.1", num_trades=1),
            execution_reports=[
                ArtifactRef(
                    path="artifacts/execution/reports/er_001.json",
                    hash=execution_report.artifact_id or "",
                )
            ],
            portfolio_snapshots=[
                ArtifactRef(
                    path="artifacts/portfolio/snapshots/ps_001.json",
                    hash=portfolio_snapshot.artifact_id or "",
                )
            ],
            provenance=ProvenanceChain(
                parent_artifacts=[
                    execution_report.artifact_id or "",
                    portfolio_snapshot.artifact_id or "",
                ],
                operation="mock_backtest_evidence",
            ),
        )
    )

    assert execution_report.artifact_id
    assert portfolio_snapshot.provenance.parent_artifacts == [execution_report.artifact_id]
    assert backtest_evidence.provenance.parent_artifacts == [
        execution_report.artifact_id,
        portfolio_snapshot.artifact_id,
    ]
    validate_schema("execution_report.schema.json", execution_report.model_dump(mode="json"))
    validate_schema("portfolio_snapshot.schema.json", portfolio_snapshot.model_dump(mode="json"))
    validate_schema("backtest_evidence.schema.json", backtest_evidence.model_dump(mode="json"))
