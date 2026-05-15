"""Validation shim for the qst-ir/0.4 shell."""

from __future__ import annotations

from quant_strategy_tokenizer.ir_v04.panel_validation import validate_panel_type_layer_v04
from quant_strategy_tokenizer.ir_v04.schema import StrategyIRV04
from quant_strategy_tokenizer.ir_v04.temporal_validation import validate_temporal_v04
from quant_strategy_tokenizer.profile_v2 import ProfileName
from quant_strategy_tokenizer.validation_v2 import Diagnostic, ValidationResult


def validate_ir_v04(ir: StrategyIRV04, *, profile: ProfileName = "research") -> ValidationResult:
    """Return structured validation diagnostics for a qst-ir/0.4 shell.

    WP8c accepts ``core``, ``panel_type``, and ``panel_ops``. ``panel_ops`` must
    be explicitly paired with ``panel_type``; later weight/recipe capabilities
    and custom runtime declarations remain gated until their owning work
    packages.
    """

    diagnostics: list[Diagnostic] = []
    for capability in ir.capabilities:
        if capability in {"core", "panel_type", "panel_ops"}:
            continue
        diagnostics.append(
            Diagnostic(
                code="capability_not_accepted",
                severity="error",
                phase="profile",
                message=f"Capability {capability!r} is not accepted in the WP8c shell.",
                remediation="Remove the capability or wait for its owning work package.",
            )
        )
    if "panel_ops" in ir.capabilities and "panel_type" not in ir.capabilities:
        diagnostics.append(
            Diagnostic(
                code="QST_V2_CAPABILITY_PANEL_OPS_REQUIRES_PANEL_TYPE",
                severity="error",
                phase="profile",
                message="panel_ops must be explicitly declared together with panel_type.",
                remediation="Add panel_type or remove panel_ops.",
            )
        )
    diagnostics.extend(validate_panel_type_layer_v04(ir))
    diagnostics.extend(validate_temporal_v04(ir, profile=profile).diagnostics)
    return ValidationResult(diagnostics=diagnostics)
