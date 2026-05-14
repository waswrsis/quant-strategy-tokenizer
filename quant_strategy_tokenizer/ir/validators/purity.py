"""Purity validator for P1-extended-a."""

from __future__ import annotations

from quant_strategy_tokenizer.core.errors import ErrorKind
from quant_strategy_tokenizer.ir.envelope import ProfileLiteral
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.ir.validation_result import ValidationFailure
from quant_strategy_tokenizer.ir.validators.profile_policy import PROFILE_MAX_PURITY, PURITY_ORDER
from quant_strategy_tokenizer.tokens.registry import Registry


def _purity_repair_hint(max_allowed: str) -> dict[str, object]:
    return {
        "kind": "replace_token_or_change_profile",
        "allowed_max": max_allowed,
        "options": [
            {"op": "ChangeProfile", "to": "research"},
            {"op": "ReplaceToken", "reason": "use contextual_read equivalent"},
        ],
    }


def _external_write_repair_hint() -> dict[str, str]:
    return {"kind": "replace_token", "reason": "external_write_not_allowed"}


def validate_purity(ir: StrategyIR, profile: ProfileLiteral, registry: Registry) -> list[ValidationFailure]:
    """Reject token purity above the profile policy."""

    failures: list[ValidationFailure] = []
    max_allowed = PROFILE_MAX_PURITY[profile]
    max_order = PURITY_ORDER[max_allowed]

    for node in ir.graph:
        spec = registry.get(node.token, node.v).spec
        purity = spec.purity
        if purity in {"external_write", "forbidden"}:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.purity_violation.value,
                    message=f"{node.token} has {purity} side effect",
                    node_id=node.id,
                    severity="error",
                    repair_hint=_external_write_repair_hint(),
                    details={"purity": purity, "profile": profile},
                )
            )
            continue

        if PURITY_ORDER[purity] > max_order:
            failures.append(
                ValidationFailure(
                    kind=ErrorKind.purity_violation.value,
                    message=(
                        f"{node.token} has purity={purity}, but "
                        f"profile={profile} allows <= {max_allowed}"
                    ),
                    node_id=node.id,
                    severity="error",
                    repair_hint=_purity_repair_hint(max_allowed),
                    details={"purity": purity, "profile": profile, "allowed_max": max_allowed},
                )
            )

    return failures
