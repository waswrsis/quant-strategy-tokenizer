"""
quant_strategy_tokenizer.state_model
====================================
Module purpose: create, validate, and merge portable strategy state envelopes without file I/O.
Core idea: Keep state identity in a small envelope and strategy-specific data in payload, then validate schema version, strategy id, instance id, and account scope before merging updates. Assumes state contamination is a serious risk and identity mismatches should fail closed by default.
Inputs: optional existing state, optional payload_updates, expected identity params, and ModuleRunContext.
Outputs: StateModelReport with validated or created state, mismatches, created/upgraded flags, and warnings.
Failure semantics: missing state fails unless creation is allowed; identity or schema mismatches fail when fail_on_identity_mismatch is enabled.
Market generalization: state envelope is generic and can hold crypto, equity, futures, FX, research, or simulation payloads.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext


@dataclass
class StateEnvelope:
    """Portable state envelope."""

    schema_version: int
    strategy_id: str
    instance_id: str
    account_scope: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateModelParams:
    """Expected state identity and merge policy.

    Configuration:
    - `schema_version`: expected envelope schema version.
    - `strategy_id`: strategy namespace expected in the state envelope.
    - `instance_id`: running instance namespace, useful for public/private
      separation or simulations.
    - `account_scope`: account or portfolio namespace expected in state.
    - `allow_create`: create a new envelope when no state is provided.
    - `allow_schema_upgrade`: permit in-memory upgrade from older versions.
    - `fail_on_identity_mismatch`: fail instead of returning mismatched state.
    - `deep_merge_payload`: recursively merge `payload_updates` into payload.
    """

    schema_version: int = 1
    strategy_id: str = "strategy"
    instance_id: str = "default"
    account_scope: str = "default"
    allow_create: bool = True
    allow_schema_upgrade: bool = False
    fail_on_identity_mismatch: bool = True
    deep_merge_payload: bool = True


@dataclass
class StateModelRequest:
    """Request payload for `run`."""

    state: Mapping[str, Any] | StateEnvelope | None = None
    payload_updates: Mapping[str, Any] = field(default_factory=dict)
    params: StateModelParams = field(default_factory=StateModelParams)
    context: ModuleRunContext = field(default_factory=ModuleRunContext)


@dataclass
class StateModelReport:
    """State validation/merge output."""

    state: dict[str, Any]
    created: bool
    mismatches: list[dict[str, Any]]
    summary: dict[str, Any]


def _to_dict(state: Mapping[str, Any] | StateEnvelope | None) -> dict[str, Any] | None:
    if state is None:
        return None
    if isinstance(state, StateEnvelope):
        return {
            "schema_version": state.schema_version,
            "strategy_id": state.strategy_id,
            "instance_id": state.instance_id,
            "account_scope": state.account_scope,
            "payload": deepcopy(state.payload),
            "metadata": deepcopy(state.metadata),
        }
    if isinstance(state, Mapping):
        return deepcopy(dict(state))
    raise TypeError(f"state must be mapping-like, got {type(state).__name__}")


def _deep_merge(base: dict[str, Any], updates: Mapping[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def _new_state(params: StateModelParams) -> dict[str, Any]:
    return {
        "schema_version": params.schema_version,
        "strategy_id": params.strategy_id,
        "instance_id": params.instance_id,
        "account_scope": params.account_scope,
        "payload": {},
        "metadata": {},
    }


def run(request: StateModelRequest) -> ModuleResult[StateModelReport]:
    """Validate or create a state envelope and merge payload updates."""

    params = request.params
    events: list[ModuleEvent] = []

    try:
        state = _to_dict(request.state)
    except Exception as exc:
        return ModuleResult.fail(
            "invalid_state_object",
            str(exc),
        )

    created = False
    if state is None:
        if not params.allow_create:
            return ModuleResult.fail(
                "state_missing",
                "state is missing and creation is disabled",
            )
        state = _new_state(params)
        created = True
        events.append(ModuleEvent(event="state_model.created", level="INFO"))

    mismatches: list[dict[str, Any]] = []
    expected = {
        "strategy_id": params.strategy_id,
        "instance_id": params.instance_id,
        "account_scope": params.account_scope,
    }
    for key, exp in expected.items():
        actual = state.get(key)
        if actual != exp:
            mismatches.append({"field": key, "expected": exp, "actual": actual})

    actual_schema = state.get("schema_version")
    if actual_schema != params.schema_version:
        if params.allow_schema_upgrade and isinstance(actual_schema, int) and actual_schema < params.schema_version:
            state["schema_version"] = params.schema_version
            events.append(
                ModuleEvent(
                    event="state_model.schema_upgraded",
                    level="WARNING",
                    fields={"from": actual_schema, "to": params.schema_version},
                )
            )
        else:
            mismatches.append(
                {"field": "schema_version", "expected": params.schema_version, "actual": actual_schema}
            )

    if mismatches and params.fail_on_identity_mismatch:
        return ModuleResult.fail(
            "state_identity_mismatch",
            "state envelope identity/schema mismatch",
            details={"mismatches": mismatches},
            events=events,
        )

    payload = state.get("payload")
    if not isinstance(payload, dict):
        payload = {}
        events.append(ModuleEvent(event="state_model.payload_reset", level="WARNING"))

    if params.deep_merge_payload:
        payload = _deep_merge(payload, request.payload_updates)
    else:
        payload = {**payload, **deepcopy(dict(request.payload_updates))}
    state["payload"] = payload
    state.setdefault("metadata", {})

    return ModuleResult.success(
        StateModelReport(
            state=state,
            created=created,
            mismatches=mismatches,
            summary={
                "created": created,
                "mismatches": len(mismatches),
                "payload_keys": sorted(payload.keys()),
            },
        ),
        events=events,
    )


__all__ = [
    "StateEnvelope",
    "StateModelParams",
    "StateModelReport",
    "StateModelRequest",
    "run",
]
