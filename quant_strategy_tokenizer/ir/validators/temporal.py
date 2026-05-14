"""Temporal safety validator for P1-extended-a."""

from __future__ import annotations

from quant_strategy_tokenizer.core.errors import ErrorKind
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validation_result import ValidationFailure
from quant_strategy_tokenizer.ir.validators.profile_policy import (
    STRICT_TEMPORAL_PROFILES,
    UNSAFE_STRICT_WINDOW_MODES,
)
from quant_strategy_tokenizer.tokens.registry import Registry


def _future_data_hint() -> dict[str, str]:
    return {"kind": "replace_token", "suggestion": "use trailing-window variant"}


def _unsafe_window_hint() -> dict[str, str]:
    return {
        "kind": "replace_token_or_change_profile",
        "suggestion": "use trailing window or research profile",
    }


def validate_temporal(
    ir: StrategyIR,
    profile: ProfileLiteral,
    registry: Registry,
) -> tuple[list[ValidationFailure], list[ValidationFailure]]:
    """Reject or warn on temporally unsafe token metadata."""

    failures: list[ValidationFailure] = []
    warnings: list[ValidationFailure] = []
    strict = profile in STRICT_TEMPORAL_PROFILES

    for node in ir.graph:
        spec = registry.get(node.token, node.v).spec
        temporal = spec.temporal

        if temporal.uses_future_data:
            target = failures if strict else warnings
            target.append(
                ValidationFailure(
                    kind=ErrorKind.future_data_violation.value
                    if strict
                    else ErrorKind.future_data_warning.value,
                    message=f"{node.token} uses future data",
                    node_id=node.id,
                    severity="error" if strict else "warning",
                    repair_hint=_future_data_hint(),
                    details={
                        "profile": profile,
                        "uses_future_data": True,
                        "window_mode": temporal.window_mode,
                    },
                )
            )

        if temporal.window_mode in UNSAFE_STRICT_WINDOW_MODES:
            target = failures if strict else warnings
            target.append(
                ValidationFailure(
                    kind=ErrorKind.unsafe_temporal_window.value,
                    message=f"{node.token} window_mode={temporal.window_mode} unsafe for {profile}",
                    node_id=node.id,
                    severity="error" if strict else "warning",
                    repair_hint=_unsafe_window_hint(),
                    details={"profile": profile, "window_mode": temporal.window_mode},
                )
            )

    return failures, warnings
