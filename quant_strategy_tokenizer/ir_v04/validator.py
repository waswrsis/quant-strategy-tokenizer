"""Validation shim for the qst-ir/0.4 shell."""

from __future__ import annotations

from quant_strategy_tokenizer.ir_v04.schema import StrategyIRV04
from quant_strategy_tokenizer.validation_v2 import Diagnostic, ValidationResult


def validate_ir_v04(ir: StrategyIRV04) -> ValidationResult:
    """Return structured validation diagnostics for a qst-ir/0.4 shell.

    WP2 accepts only the ``core`` capability. ``panel`` and
    ``custom_token_runtime`` are parsed as inert shell declarations but remain
    gated until their later work packages.
    """

    diagnostics: list[Diagnostic] = []
    for capability in ir.capabilities:
        if capability == "core":
            continue
        diagnostics.append(
            Diagnostic(
                code="capability_not_accepted",
                severity="error",
                phase="profile",
                message=f"Capability {capability!r} is not accepted in the WP2 shell.",
                remediation="Remove the capability or wait for its owning work package.",
            )
        )
    return ValidationResult(diagnostics=diagnostics)
