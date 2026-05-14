from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.artifacts.execution_report import ExecutionReport
from quant_strategy_tokenizer.ports import ExecutionPort
from quant_strategy_tokenizer.types.decision import Accept
from quant_strategy_tokenizer.types.plan import OrderIntentPlan

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


class FakeExecutionPort:
    def get_identity(self) -> AdapterIdentity:
        return AdapterIdentity(adapter_id="fake-execution", adapter_version="1.0.0")

    def submit_plan(
        self,
        plan: object,
        *,
        confirm: bool = False,
        client_order_id: str | None = None,
    ) -> ExecutionReport:
        del plan, confirm, client_order_id
        return ExecutionReport(
            artifact_id=HASH_A,
            event_type="new",
            state="acknowledged",
            qty_intended="1",
            qty_last="0",
            qty_filled="0",
            qty_remaining="1",
            source_protocol="mock",
            venue="paper",
        )

    def poll_report(self, execution_report_id: str) -> ExecutionReport:
        del execution_report_id
        return ExecutionReport(
            artifact_id=HASH_B,
            event_type="trade",
            state="filled",
            qty_intended="1",
            qty_last="1",
            qty_filled="1",
            qty_remaining="0",
            last_fill_price="100",
            source_protocol="mock",
            venue="paper",
        )


def test_execution_port_submit_and_poll_return_distinct_immutable_reports() -> None:
    port = FakeExecutionPort()
    plan = OrderIntentPlan(decision=Accept(reason="entry"), side="long", sizing=1.0)

    submitted = port.submit_plan(plan, confirm=True, client_order_id="c1")
    polled = port.poll_report("r1")

    assert isinstance(port, ExecutionPort)
    assert submitted.artifact_id == HASH_A
    assert polled.artifact_id == HASH_B
    assert submitted != polled
    with pytest.raises(ValidationError):
        submitted.qty_last = "1"
