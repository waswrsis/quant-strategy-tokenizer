"""Execution port protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.artifacts.execution_report import ExecutionReport
from quant_strategy_tokenizer.types.plan import Plan


@runtime_checkable
class ExecutionPort(Protocol):
    """Adapter protocol for immutable execution report workflows."""

    def get_identity(self) -> AdapterIdentity: ...

    def submit_plan(
        self,
        plan: Plan,
        *,
        confirm: bool = False,
        client_order_id: str | None = None,
    ) -> ExecutionReport: ...

    def poll_report(self, execution_report_id: str) -> ExecutionReport: ...
