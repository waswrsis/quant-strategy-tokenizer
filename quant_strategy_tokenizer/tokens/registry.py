"""Token registry.

P0 rule:
- Token modules are imported lazily by get_registry().
- Registry is frozen after built-in tokens are loaded.
- Production code only reads through get_registry().
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from .spec import TokenSpec

DEFAULT_TEMPORAL: dict[str, Any] = {
    "uses_future_data": False,
    "output_available_at": "bar_close",
    "warmup_behavior": "instant",
}
DEFAULT_FAILURE_POLICY: dict[str, Any] = {
    "on_missing_input": "error",
    "on_insufficient_data": "unknown",
    "on_param_violation": "error",
}


@dataclass(frozen=True)
class RegisteredToken:
    """Runtime token object: serializable spec plus Python executor."""

    spec: TokenSpec
    executor: Callable[..., Any]


class Registry:
    """Mutable-until-frozen token registry."""

    def __init__(self) -> None:
        self._tokens: dict[tuple[str, int], RegisteredToken] = {}
        self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def register(self, registered: RegisteredToken) -> None:
        if self._frozen:
            raise RuntimeError(
                f"Registry frozen; cannot register {registered.spec.id}/v{registered.spec.version}"
            )

        spec = registered.spec
        key = (spec.id, spec.version)

        if key in self._tokens:
            raise ValueError(f"Token {spec.id}/v{spec.version} already registered")

        overlap = set(spec.inputs) & set(spec.params_schema)
        if overlap:
            raise ValueError(f"Token {spec.id}: input/param name collision: {sorted(overlap)}")

        self._tokens[key] = registered

    def freeze(self) -> None:
        self._frozen = True

    def get(self, token_id: str, version: int = 1) -> RegisteredToken:
        try:
            return self._tokens[(token_id, version)]
        except KeyError:
            raise KeyError(f"Token {token_id}/v{version} not found") from None

    def list_tokens(
        self,
        layer: Literal["computation", "infrastructure"] | None = None,
        lifecycle: str | None = None,
    ) -> list[TokenSpec]:
        specs = [registered.spec for registered in self._tokens.values()]
        filtered = [
            spec
            for spec in specs
            if (layer is None or spec.layer == layer)
            and (lifecycle is None or spec.lifecycle == lifecycle)
        ]
        return sorted(filtered, key=lambda spec: (spec.layer, spec.category, spec.id, spec.version))


_REGISTRY = Registry()
_BUILTINS_LOADED = False


def _load_builtin_tokens() -> None:
    """Import all P0 built-in token modules exactly once."""

    global _BUILTINS_LOADED

    if _BUILTINS_LOADED:
        return

    from quant_strategy_tokenizer.tokens.computation import (
        compare,  # noqa: F401
        data,  # noqa: F401
        logic,  # noqa: F401
        math,  # noqa: F401
        norm,  # noqa: F401
        smooth,  # noqa: F401
        window,  # noqa: F401
    )
    from quant_strategy_tokenizer.tokens.infrastructure import (
        decision,  # noqa: F401
        plan,  # noqa: F401
    )

    _BUILTINS_LOADED = True


def get_registry() -> Registry:
    """Return the frozen built-in registry."""

    _load_builtin_tokens()
    if not _REGISTRY.is_frozen:
        _REGISTRY.freeze()
    return _REGISTRY


def get_mutable_registry_for_bootstrap() -> Registry:
    """Internal use only: used by @token during import-time registration."""

    return _REGISTRY


def token(
    *,
    id: str,
    layer: Literal["computation", "infrastructure"],
    category: str,
    inputs: dict[str, str],
    outputs: dict[str, str],
    version: int = 1,
    behavior_version: int = 1,
    state_tag: Literal["stateless", "lti_recursive", "nonlinear_recursive", "discrete_fsm"] = "stateless",
    purity: Literal[
        "pure",
        "contextual_read",
        "external_read",
        "external_write",
        "forbidden",
    ] = "pure",
    params_schema: dict[str, Any] | None = None,
    temporal: dict[str, Any] | None = None,
    failure_policy: dict[str, Any] | None = None,
    contracts: list[dict[str, Any]] | None = None,
    usage_examples: list[dict[str, Any]] | None = None,
    lifecycle: Literal[
        "experimental",
        "core_candidate",
        "core_stable",
        "deprecated",
        "removed",
    ] = "core_candidate",
    description: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a token executor and return it unchanged."""

    def wrapper(executor: Callable[..., Any]) -> Callable[..., Any]:
        spec = TokenSpec(
            id=id,
            version=version,
            behavior_version=behavior_version,
            layer=layer,
            category=category,
            state_tag=state_tag,
            purity=purity,
            inputs=inputs,
            outputs=outputs,
            params_schema=params_schema or {},
            temporal=temporal or DEFAULT_TEMPORAL,
            failure_policy=failure_policy or DEFAULT_FAILURE_POLICY,
            behavior_contract=contracts or [],
            usage_examples=usage_examples or [],
            lifecycle=lifecycle,
            description=description,
        )

        registered = RegisteredToken(spec=spec, executor=executor)
        get_mutable_registry_for_bootstrap().register(registered)
        return executor

    return wrapper
