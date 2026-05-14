"""Opt-in P2c-extended kernel substitution spike."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.composition.verifier import upgrade_verification
from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.execution.plan import PlanNode, make_execution_plan
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import GraphNode, StrategyIR
from quant_strategy_tokenizer.provenance import ProvenanceTag
from quant_strategy_tokenizer.provenance.registry import get_tagspec_registry
from quant_strategy_tokenizer.tokens._helpers import float_series

KERNEL_ID_INDICATOR_EWM_V1 = "builtin.indicator_ewm_v1_fastpath"


class KernelBinding(BaseModel):
    """Serializable kernel binding declared by a TagSpec."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kernel_id: str
    semantic_id: str
    version: int = 1
    runtime: Literal["python"] = "python"
    target_token: str
    status: Literal["spike"] = "spike"
    description: str = ""


class KernelEligibility(BaseModel):
    """Kernel eligibility decision for one canonical node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    eligible: bool
    kernel_id: str | None = None
    semantic_id: str | None = None
    version: int | None = None
    blocked_reasons: list[str] = Field(default_factory=list)


class KernelPlanReport(BaseModel):
    """Debug report for kernel eligibility over an execution plan."""

    model_config = ConfigDict(extra="forbid")

    hashes: dict[str, str]
    nodes: list[KernelEligibility]
    plan_actions: list[dict[str, Any]]
    eligible_count: int


KernelExecutor = Callable[
    [Mapping[str, Any], Mapping[str, Any], ProvenanceTag],
    TokenOutput,
]


@dataclass(frozen=True)
class RegisteredKernel:
    """Runtime kernel plus its serializable binding."""

    binding: KernelBinding
    executor: KernelExecutor


class KernelRegistry:
    """In-memory registry for opt-in spike kernels."""

    def __init__(self) -> None:
        self._kernels: dict[str, RegisteredKernel] = {}

    def register(self, kernel: RegisteredKernel) -> None:
        if kernel.binding.kernel_id in self._kernels:
            raise ValueError(f"Kernel {kernel.binding.kernel_id} already registered")
        self._kernels[kernel.binding.kernel_id] = kernel

    def get(self, kernel_id: str) -> RegisteredKernel:
        try:
            return self._kernels[kernel_id]
        except KeyError:
            raise KeyError(f"Kernel {kernel_id} not found") from None

    def list_kernels(self) -> list[RegisteredKernel]:
        return list(self._kernels.values())


def _indicator_ewm_v1_fastpath(
    inputs: Mapping[str, Any],
    params: Mapping[str, Any],
    provenance: ProvenanceTag,
) -> TokenOutput:
    """Equivalent opt-in kernel for indicator.ewm/v1 expanded nodes."""

    values = float_series(inputs["series"])
    if values.empty:
        return TokenOutput(status="unknown", unknown_reason="insufficient_data", values={"value": values})

    alpha = float(params.get("alpha", 2.0 / (float(provenance.params["span"]) + 1.0)))
    init = params.get("init", provenance.params.get("init", "first_value"))

    out: list[float] = []
    if init == "first_value":
        first_valid = values.dropna()
        prev = float(first_valid.iloc[0]) if not first_valid.empty else np.nan
    else:
        prev = float(init)

    for raw in values:
        x = float(raw) if pd.notna(raw) else np.nan
        if np.isnan(x):
            out.append(prev)
            continue
        if init == "first_value" and not out and pd.notna(values.iloc[0]):
            prev = x
        else:
            prev = alpha * x + (1.0 - alpha) * prev
        out.append(prev)

    return TokenOutput(values={"value": pd.Series(out, index=values.index, dtype=float)})


def get_kernel_registry() -> KernelRegistry:
    """Return the built-in opt-in kernel registry."""

    registry = KernelRegistry()
    registry.register(
        RegisteredKernel(
            binding=KernelBinding(
                kernel_id=KERNEL_ID_INDICATOR_EWM_V1,
                semantic_id="indicator.ewm",
                version=1,
                target_token="smooth.linear_recursive",  # noqa: S106
                description="P2c-extended spike fast-path for indicator.ewm/v1.",
            ),
            executor=_indicator_ewm_v1_fastpath,
        )
    )
    return registry


def _allowed_kernel_ids(raw: list[dict[str, Any]]) -> set[str]:
    return {
        item["kernel_id"]
        for item in raw
        if isinstance(item, dict) and isinstance(item.get("kernel_id"), str)
    }


def kernel_eligibility_for_node(
    node: GraphNode,
    *,
    kernel_registry: KernelRegistry | None = None,
) -> KernelEligibility:
    """Return the opt-in kernel eligibility decision for one canonical node."""

    kernels = kernel_registry or get_kernel_registry()
    if not node.provenance:
        return KernelEligibility(node_id=node.id, eligible=False, blocked_reasons=["missing_provenance"])

    tag = node.provenance[0]
    semantic_id = tag.semantic_id
    version = tag.version
    binding = next(
        (
            kernel.binding
            for kernel in kernels.list_kernels()
            if kernel.binding.semantic_id == semantic_id and kernel.binding.version == version
        ),
        None,
    )
    if binding is None:
        return KernelEligibility(
            node_id=node.id,
            eligible=False,
            semantic_id=semantic_id,
            version=version,
            blocked_reasons=["unsupported_semantic"],
        )

    reasons: list[str] = []
    try:
        spec = get_tagspec_registry().get(semantic_id, version)
    except KeyError:
        reasons.append("tagspec_not_found")
    else:
        verified = upgrade_verification(spec)
        if not verified.verification.fully_verified:
            reasons.append("tagspec_not_fully_verified")
        if binding.kernel_id not in _allowed_kernel_ids(verified.allowed_kernels):
            reasons.append("kernel_not_allowed_by_tagspec")

    if node.token != binding.target_token:
        reasons.append("target_token_mismatch")

    if reasons:
        return KernelEligibility(
            node_id=node.id,
            eligible=False,
            semantic_id=semantic_id,
            version=version,
            blocked_reasons=reasons,
        )

    return KernelEligibility(
        node_id=node.id,
        eligible=True,
        kernel_id=binding.kernel_id,
        semantic_id=semantic_id,
        version=version,
    )


def make_kernel_plan_report(canonical_ir: StrategyIR) -> KernelPlanReport:
    """Return a JSON-friendly kernel eligibility and execution-plan report."""

    hashes = compute_hashes(canonical_ir)
    plan = make_execution_plan(canonical_ir)
    node_by_id = {node.id: node for node in canonical_ir.graph}
    decisions = [
        kernel_eligibility_for_node(node_by_id[plan_node.node_id])
        for plan_node in plan.nodes
    ]
    return KernelPlanReport(
        hashes=hashes.as_dict(),
        nodes=decisions,
        plan_actions=[_plan_node_payload(node) for node in plan.nodes],
        eligible_count=sum(1 for item in decisions if item.eligible),
    )


def _plan_node_payload(node: PlanNode) -> dict[str, Any]:
    return node.model_dump(mode="json", exclude_none=True)
