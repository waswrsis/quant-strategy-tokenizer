"""Execution plan construction with CSE reuse decisions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.execution.fingerprint import compute_all_fingerprints
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.tokens.registry import Registry


class PlanNode(BaseModel):
    """One canonical graph node execution action."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    action: Literal["compute", "reuse"]
    fingerprint: str
    plan_id: str | None = None
    reused_from: str | None = None


class ExecutionPlan(BaseModel):
    """Execution plan derived from canonical IR."""

    model_config = ConfigDict(extra="forbid")

    nodes: list[PlanNode] = Field(default_factory=list)


def make_execution_plan(
    canonical_ir: StrategyIR,
    *,
    registry: Registry | None = None,
) -> ExecutionPlan:
    """Build an execution plan and mark later equivalent nodes as reuse."""

    fingerprints = compute_all_fingerprints(canonical_ir.graph, registry=registry)
    fingerprint_to_source: dict[str, str] = {}
    plan_nodes: list[PlanNode] = []
    compute_count = 0

    for node in canonical_ir.graph:
        fingerprint = fingerprints[node.id]
        if fingerprint in fingerprint_to_source:
            plan_nodes.append(
                PlanNode(
                    node_id=node.id,
                    action="reuse",
                    fingerprint=fingerprint,
                    reused_from=fingerprint_to_source[fingerprint],
                )
            )
            continue

        fingerprint_to_source[fingerprint] = node.id
        plan_nodes.append(
            PlanNode(
                node_id=node.id,
                action="compute",
                fingerprint=fingerprint,
                plan_id=f"plan_{compute_count}",
            )
        )
        compute_count += 1

    return ExecutionPlan(nodes=plan_nodes)
