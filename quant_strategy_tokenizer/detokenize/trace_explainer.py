"""Trace explanation emitter."""

from __future__ import annotations

import json
from typing import Literal

from quant_strategy_tokenizer.core.output import jsonable_value
from quant_strategy_tokenizer.runtime.trace import Trace

TraceExplainLevel = Literal["human", "agent", "raw"]


def explain_trace(trace: Trace, level: TraceExplainLevel = "human") -> str:
    """Explain an execution trace at human, agent, or raw detail level."""

    if level == "raw":
        return json.dumps(jsonable_value(trace.model_dump()), ensure_ascii=False, indent=2)

    if level == "agent":
        payload = {
            "run_id": trace.run_id,
            "strategy_instance_hash": trace.strategy_instance_hash,
            "unknown_count": trace.unknown_count,
            "error_count": trace.error_count,
            "nodes": [
                {
                    "id": node.id,
                    "token": node.token,
                    "status": node.status,
                    "warnings": node.warnings,
                    "error_kind": node.error_kind,
                }
                for node in trace.nodes
            ],
            "outputs": trace.outputs,
        }
        return json.dumps(jsonable_value(payload), ensure_ascii=False, indent=2)

    lines = [
        f"Trace: {trace.run_id}",
        f"Strategy instance: {trace.strategy_instance_hash}",
        f"Nodes: {len(trace.nodes)}; unknown={trace.unknown_count}; error={trace.error_count}",
    ]
    blocked = [
        node
        for node in trace.nodes
        if any(
            summary.get("value", {}).get("kind") == "block"
            for summary in node.output_summary.values()
            if isinstance(summary, dict)
        )
    ]
    if blocked:
        lines.append("Blocked by risk path:")
        for node in blocked:
            lines.append(f"  - {node.id} ({node.token})")
    if trace.outputs:
        lines.append("Outputs:")
        for key, value in trace.outputs.items():
            lines.append(f"  - {key}: {json.dumps(jsonable_value(value), ensure_ascii=False)}")
    return "\n".join(lines)
