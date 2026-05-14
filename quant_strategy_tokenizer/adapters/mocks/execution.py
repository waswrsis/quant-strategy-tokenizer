"""Deterministic mock execution adapter."""

from __future__ import annotations

from typing import ClassVar

from quant_strategy_tokenizer.adapters.mocks.common import adapter_identity, with_artifact_id
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.artifacts.decimal_string import normalize_to_canonical
from quant_strategy_tokenizer.artifacts.execution_report import ExecutionReport
from quant_strategy_tokenizer.types.plan import NoopPlan, OrderIntentPlan, Plan


class MockExecutionAdapter:
    """Mock execution adapter with stateless deterministic submit/poll behavior."""

    capabilities: ClassVar[list[str]] = ["execution"]

    def get_identity(self) -> AdapterIdentity:
        return adapter_identity("mock-execution")

    def submit_plan(
        self,
        plan: Plan,
        *,
        confirm: bool = False,
        client_order_id: str | None = None,
    ) -> ExecutionReport:
        if isinstance(plan, NoopPlan):
            report = ExecutionReport(
                event_type="reject",
                state="rejected",
                qty_intended="0",
                qty_last="0",
                qty_filled="0",
                qty_remaining="0",
                reject_reason=plan.reason,
                source_protocol="mock-execution",
                source_system=client_order_id,
                venue="mock",
                metadata={"confirm": confirm, "plan_kind": plan.kind},
            )
            return with_artifact_id(report)

        assert isinstance(plan, OrderIntentPlan)
        qty = normalize_to_canonical(plan.sizing)
        report = ExecutionReport(
            event_type="new",
            state="acknowledged" if confirm else "pending_new",
            qty_intended=qty,
            qty_last="0",
            qty_filled="0",
            qty_remaining=qty,
            source_protocol="mock-execution",
            source_system=client_order_id,
            venue="mock",
            metadata={"confirm": confirm, "side": plan.side, "plan_kind": plan.kind},
        )
        return with_artifact_id(report)

    def poll_report(self, execution_report_id: str) -> ExecutionReport:
        report = ExecutionReport(
            event_type="trade",
            state="filled",
            qty_intended="1",
            qty_last="1",
            qty_filled="1",
            qty_remaining="0",
            last_fill_price="1",
            avg_fill_price="1",
            source_protocol="mock-execution",
            source_system=execution_report_id,
            venue="mock",
            metadata={"poll_source_report": execution_report_id},
        )
        return with_artifact_id(report)
