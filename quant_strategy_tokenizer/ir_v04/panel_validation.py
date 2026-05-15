"""Panel type-layer validation for qst-ir/0.4."""

from __future__ import annotations

from pydantic import ValidationError

from quant_strategy_tokenizer.ir_v04.schema import NodeV04, StrategyIRV04
from quant_strategy_tokenizer.panel_v2 import parse_panel_type_by_output
from quant_strategy_tokenizer.validation_v2 import Diagnostic

PANEL_TYPE_CAPABILITY = "panel_type"
PANEL_OPERATOR_PREFIXES = ("panel.", "selection.", "weight.")


def validate_panel_type_layer_v04(ir: StrategyIRV04) -> list[Diagnostic]:
    """Validate WP8b Panel type-layer declarations."""

    diagnostics: list[Diagnostic] = []
    has_panel_type_capability = PANEL_TYPE_CAPABILITY in ir.capabilities
    for node in ir.strategy.nodes:
        diagnostics.extend(_validate_node_panel_metadata(node, has_panel_type_capability))
        diagnostics.extend(_validate_panel_operator_gate(node))
        diagnostics.extend(_validate_panel_state_gate(node))
    return diagnostics


def _validate_node_panel_metadata(node: NodeV04, has_panel_type_capability: bool) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    panel_outputs = _panel_outputs(node)
    metadata = node.metadata

    if "panel_type" in metadata:
        diagnostics.append(
            _diagnostic(
                "QST_V2_PANEL_TYPE_METADATA_LOCATION",
                node,
                None,
                "Panel type metadata must be output-scoped under metadata.panel_type_by_output.",
            )
        )

    raw_by_output = metadata.get("panel_type_by_output")
    parsed_by_output = {}
    if raw_by_output is not None:
        try:
            parsed_by_output = parse_panel_type_by_output(raw_by_output)
        except (TypeError, ValueError, ValidationError) as exc:
            diagnostics.append(
                _diagnostic(
                    "QST_V2_PANEL_TYPE_METADATA_INVALID",
                    node,
                    None,
                    f"metadata.panel_type_by_output is invalid: {exc}",
                )
            )
            parsed_by_output = {}

    for output_name, output_spec in node.signature.outputs.items():
        if output_name not in parsed_by_output:
            continue
        if output_spec.type.kind != "Panel":
            diagnostics.append(
                _diagnostic(
                    "QST_V2_PANEL_TYPE_METADATA_NON_PANEL_OUTPUT",
                    node,
                    output_name,
                    "Panel type metadata may only be attached to Panel outputs.",
                )
            )

    for output_name in parsed_by_output:
        if output_name not in node.signature.outputs:
            diagnostics.append(
                _diagnostic(
                    "QST_V2_PANEL_TYPE_METADATA_UNKNOWN_OUTPUT",
                    node,
                    output_name,
                    "Panel type metadata references an unknown output port.",
                )
            )

    for output_name in panel_outputs:
        if not has_panel_type_capability:
            diagnostics.append(
                _diagnostic(
                    "QST_V2_PANEL_TYPE_CAPABILITY_REQUIRED",
                    node,
                    output_name,
                    "Panel outputs require the panel_type capability.",
                )
            )
        if output_name not in parsed_by_output:
            diagnostics.append(
                _diagnostic(
                    "QST_V2_PANEL_TYPE_METADATA_REQUIRED",
                    node,
                    output_name,
                    "Panel outputs require metadata.panel_type_by_output for the output port.",
                )
            )
    return diagnostics


def _validate_panel_operator_gate(node: NodeV04) -> list[Diagnostic]:
    name = _token_name(node)
    if name is None or not name.startswith(PANEL_OPERATOR_PREFIXES):
        return []
    return [
        _diagnostic(
            "QST_V2_PANEL_OPERATOR_NOT_ACCEPTED",
            node,
            None,
            f"Panel operator token {name!r} is not accepted in WP8b.",
        )
    ]


def _validate_panel_state_gate(node: NodeV04) -> list[Diagnostic]:
    if _token_name(node) != "state.fsm":
        return []
    if not any(input_spec.type.kind == "Panel" for input_spec in node.signature.inputs.values()):
        return []
    return [
        _diagnostic(
            "QST_V2_PANEL_STATE_AUTOBROADCAST_UNSUPPORTED",
            node,
            None,
            "state.fsm does not auto-broadcast over Panel inputs in WP8b.",
        )
    ]


def _panel_outputs(node: NodeV04) -> list[str]:
    return [
        output_name
        for output_name, output_spec in node.signature.outputs.items()
        if output_spec.type.kind == "Panel"
    ]


def _token_name(node: NodeV04) -> str | None:
    if node.token_ref is not None:
        return node.token_ref.name
    return node.token


def _diagnostic(code: str, node: NodeV04, port: str | None, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity="error",
        phase="signature",
        message=message,
        node_id=node.id,
        port=port,
    )

