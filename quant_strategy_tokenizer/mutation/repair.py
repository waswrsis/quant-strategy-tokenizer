"""Convert validator repair hints into P2b-0 mutation ops."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.mutation.ops import InsertBefore, MutationOp


class RepairHintError(ValueError):
    """Repair hint cannot be converted to a P2b-0 mutation op."""


def mutation_from_repair_hint(repair_hint: dict[str, Any]) -> MutationOp:
    """Convert the first supported repair hint op to a mutation op."""

    for raw_op in repair_hint.get("ops", []):
        if raw_op.get("op") != "InsertBefore":
            continue
        insert_node = dict(raw_op.get("insert_node") or {})
        if not insert_node:
            raise RepairHintError("InsertBefore repair hint missing insert_node")
        target_node_id = raw_op.get("target_node") or raw_op.get("target_node_id")
        if not isinstance(target_node_id, str):
            raise RepairHintError("InsertBefore repair hint missing target_node")
        if isinstance(insert_node.get("id"), str):
            insert_node["id"] = insert_node["id"].replace("$AUTO", target_node_id)
        return InsertBefore(
            target_node_id=target_node_id,
            target_input_name=raw_op.get("target_input_name", "decision"),
            new_node_spec={
                **insert_node,
                "primary_input": raw_op.get("primary_input", "decision"),
                "primary_output": raw_op.get("primary_output", "decision"),
            },
        )
    raise RepairHintError("No supported P2b-0 repair hint op found")
