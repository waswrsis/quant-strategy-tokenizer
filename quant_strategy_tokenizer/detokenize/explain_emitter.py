"""L1 natural-language explanation emitter."""

from __future__ import annotations

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.model import GraphNode, StrategyIR
from quant_strategy_tokenizer.provenance import ProvenanceTag


def _explain_agent(ir: StrategyIR) -> str:
    canonical = canonicalize(ir)
    hashes = compute_hashes(canonical)
    lines = [
        f"Strategy: {ir.strategy} (v{ir.strategy_version})",
        "Agent explanation:",
        "",
        "Computation:",
    ]
    for node in canonical.graph:
        tag = _first_provenance(node)
        if tag is not None:
            params = ", ".join(f"{key}={value}" for key, value in sorted(tag.params.items()))
            suffix = f" params({params})" if params else ""
            role = f" role={tag.role}" if tag.role else ""
            lines.append(f"  - {tag.semantic_id} v{tag.version}{role}{suffix}.")
        else:
            lines.append(f"  - Primitive node '{node.id}' uses {node.token}.")
    lines.extend(
        [
            "",
            "Hash:",
            f"  graph_hash:    {hashes.graph_hash}",
            f"  param_hash:    {hashes.param_hash}",
            f"  instance_hash: {hashes.instance_hash}",
        ]
    )
    return "\n".join(lines)


def _first_provenance(node: GraphNode) -> ProvenanceTag | None:
    return node.provenance[0] if node.provenance else None


def explain_ir(ir: StrategyIR, level: str = "L1") -> str:
    """Emit a concise L1 explanation for a Strategy IR."""

    if level == "agent":
        return _explain_agent(ir)
    if level != "L1":
        raise ValueError("QST supports L1 and agent explain levels")

    hashes = compute_hashes(ir)
    lines = [
        f"Strategy: {ir.strategy} (v{ir.strategy_version})",
        "Inputs: " + ", ".join(f"{name} ({spec.type})" for name, spec in ir.externals.items()),
        "",
        "Computation:",
    ]
    if ir.recipes:
        for recipe in ir.recipes:
            params = ", ".join(f"{key}={value}" for key, value in sorted(recipe.params.items()))
            suffix = f" with {params}" if params else ""
            lines.append(f"  - Recipe '{recipe.id}' ({recipe.recipe} v{recipe.version}){suffix}.")
    else:
        lines.append("  - Canonical primitive token graph.")

    decision_nodes = [node for node in ir.graph if node.token.startswith("decision.")]
    plan_nodes = [node for node in ir.graph if node.token.startswith("plan.")]
    lines.extend(["", "Decision:"])
    if decision_nodes:
        for node in decision_nodes:
            lines.append(f"  - Node '{node.id}' uses {node.token} with params {node.params}.")
    else:
        lines.append("  - No explicit decision nodes.")

    lines.extend(["", "Plan:"])
    if plan_nodes:
        for node in plan_nodes:
            lines.append(f"  - Node '{node.id}' produces a noop plan in P0.")
    else:
        lines.append("  - No plan node declared.")

    lines.extend(
        [
            "",
            "Hash:",
            f"  graph_hash:    {hashes.graph_hash}",
            f"  param_hash:    {hashes.param_hash}",
            f"  instance_hash: {hashes.instance_hash}",
        ]
    )
    return "\n".join(lines)
