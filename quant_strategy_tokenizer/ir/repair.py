"""Repair hint generators for the P0 validator."""

from __future__ import annotations

from typing import Any


def type_mismatch_hint(target_node: str, source_ref: str) -> dict[str, Any]:
    """Suggest lifting a bool series before decision.reduce."""

    return {
        "ops": [
            {
                "op": "InsertBefore",
                "target_node": target_node,
                "insert_node": {
                    "id": "lift_$AUTO",
                    "token": "decision.lift_bool",
                    "v": 1,
                    "params": {"at": "now"},
                    "inputs": {"series": source_ref},
                },
                "rationale": "wrap bool series as Decision",
            }
        ],
        "confidence_band": "high",
    }


def missing_unknown_handling_hint(target_node: str) -> dict[str, Any]:
    """Suggest the P0 default unknown handling policy."""

    return {
        "ops": [
            {
                "op": "ChangeParam",
                "target_node": target_node,
                "key": "unknown_handling",
                "value": "treat_as_reject",
            }
        ],
        "rationale": "P0 default; stricter profiles can choose another policy later.",
        "confidence_band": "medium",
    }


def missing_input_hint(candidates: list[str]) -> dict[str, Any]:
    """Suggest candidate upstream refs."""

    return {
        "candidates": candidates,
        "rationale": "candidates are upstream outputs with compatible or nearby type refs",
        "confidence_band": "medium",
    }


def missing_risk_path_hint(target_node: str | None = None) -> dict[str, Any]:
    """Suggest inserting a risk guard before order-intent planning."""

    return {
        "ops": [
            {
                "op": "InsertBefore",
                "target_node": target_node or "plan.order_intent",
                "insert_node": {
                    "id": "risk_$AUTO",
                    "token": "risk.position_cap",
                    "v": 1,
                    "params": {"max_position": 1, "symbol_key": "current_symbol"},
                    "inputs": {
                        "decision": "<upstream decision>",
                        "state": "$externals.state",
                    },
                },
                "rationale": "pretrade profile requires a risk.* ancestor before plan.order_intent",
            }
        ],
        "confidence_band": "medium",
    }
