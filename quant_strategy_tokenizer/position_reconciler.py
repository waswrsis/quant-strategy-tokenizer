"""
quant_strategy_tokenizer.position_reconciler
============================================
Module purpose: compare previous and current position snapshots and classify exposure transitions.
Core idea: Normalize signed quantities by symbol, compare old and new exposures, and use optional close evidence to distinguish expected flat from unknown or unexpected flat. Assumes venue queries are outside the module and missing evidence must remain explicit.
Inputs: previous_positions, current_positions, optional close_evidence, field mapping params, and ModuleRunContext.
Outputs: PositionReconcilerReport with transitions, unchanged symbols, unknown transitions, warnings, and diagnostics.
Failure semantics: malformed rows are warned or skipped; non-iterable snapshots or unusable request data return ModuleResult.fail.
Market generalization: quantity semantics are caller-mapped and can represent spot, futures, CFDs, paper positions, or simulations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from .contracts import ModuleEvent, ModuleResult, ModuleRunContext


@dataclass
class PositionTransition:
    """One symbol-level position state change."""

    symbol: str
    previous_qty: float
    current_qty: float
    transition: str
    classification: str
    confidence: str
    evidence: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionReconcilerParams:
    """Field names and unknown-flat policy.

    Configuration:
    - `symbol_field`: snapshot field containing the instrument identifier.
    - `quantity_field`: numeric exposure field; may be signed or paired with
      `side_field`.
    - `side_field`: optional side label used to sign positive quantities.
    - `zero_epsilon`: absolute quantity tolerance treated as flat/unchanged.
    - `unknown_on_missing_close_evidence`: when True, a full flat transition
      without evidence is classified unknown rather than unexpected.
    - `accept_price_fallback_evidence`: allow caller-supplied price fallback
      evidence to classify a close when order evidence is absent.
    """

    symbol_field: str = "symbol"
    quantity_field: str = "quantity"
    side_field: str = "side"
    zero_epsilon: float = 1e-12
    unknown_on_missing_close_evidence: bool = True
    accept_price_fallback_evidence: bool = True


@dataclass
class PositionReconcilerRequest:
    """Request payload for `run`."""

    previous_positions: Iterable[Mapping[str, Any]]
    current_positions: Iterable[Mapping[str, Any]]
    close_evidence: Mapping[str, Any] = field(default_factory=dict)
    params: PositionReconcilerParams = field(default_factory=PositionReconcilerParams)
    context: ModuleRunContext = field(default_factory=ModuleRunContext)


@dataclass
class PositionReconcilerReport:
    """Reconciliation output."""

    transitions: list[PositionTransition]
    unknown: list[PositionTransition]
    summary: dict[str, Any]


def _as_dict(row: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "__dict__"):
        return dict(vars(row))
    raise TypeError(f"position row must be mapping-like, got {type(row).__name__}")


def _signed_qty(row: dict[str, Any], params: PositionReconcilerParams) -> float:
    raw_qty = row.get(params.quantity_field, 0.0)
    qty = float(raw_qty or 0.0)
    side = str(row.get(params.side_field, "")).lower()
    if qty >= 0 and side in {"short", "sell"}:
        qty = -qty
    return qty


def _snapshot(rows: Iterable[Mapping[str, Any]], params: PositionReconcilerParams) -> tuple[dict[str, float], list[dict[str, Any]]]:
    out: dict[str, float] = {}
    errors: list[dict[str, Any]] = []
    for idx, raw in enumerate(rows):
        try:
            row = _as_dict(raw)
            symbol = str(row.get(params.symbol_field, "")).strip()
            if not symbol:
                raise ValueError("missing symbol")
            out[symbol] = out.get(symbol, 0.0) + _signed_qty(row, params)
        except Exception as exc:
            errors.append({"index": idx, "error": str(exc)})
    return out, errors


def _is_zero(qty: float, eps: float) -> bool:
    return abs(qty) <= eps


def _classify_close(symbol: str, evidence: Any, params: PositionReconcilerParams) -> tuple[str, str, dict[str, Any]]:
    if evidence is None:
        if params.unknown_on_missing_close_evidence:
            return "unknown_flat", "unknown", {}
        return "unexpected_flat", "low", {}
    if isinstance(evidence, Mapping):
        ev = dict(evidence)
        kind = str(ev.get("kind") or ev.get("classification") or "").lower()
        if kind in {"take_profit", "tp", "stop_loss", "sl", "exit", "manual", "liquidation"}:
            normalized = {"tp": "take_profit", "sl": "stop_loss"}.get(kind, kind)
            return normalized, "high", ev
        if params.accept_price_fallback_evidence and ev.get("price_fallback"):
            return str(ev.get("price_fallback")), "medium", ev
        if ev.get("unknown"):
            return "unknown_flat", "unknown", ev
        return "unexpected_flat", "low", ev
    if isinstance(evidence, list) and evidence:
        return _classify_close(symbol, evidence[0], params)
    return "unknown_flat", "unknown", {"raw_evidence": evidence}


def run(request: PositionReconcilerRequest) -> ModuleResult[PositionReconcilerReport]:
    """Reconcile two supplied position snapshots."""

    params = request.params
    events: list[ModuleEvent] = []

    try:
        previous_rows = list(request.previous_positions)
        current_rows = list(request.current_positions)
    except Exception as exc:
        return ModuleResult.fail(
            "snapshots_not_iterable",
            str(exc),
        )

    previous, prev_errors = _snapshot(previous_rows, params)
    current, cur_errors = _snapshot(current_rows, params)
    for err in prev_errors:
        events.append(ModuleEvent(event="position_reconciler.previous_row_skipped", level="WARNING", fields=err))
    for err in cur_errors:
        events.append(ModuleEvent(event="position_reconciler.current_row_skipped", level="WARNING", fields=err))

    symbols = sorted(set(previous) | set(current))
    transitions: list[PositionTransition] = []
    unknown: list[PositionTransition] = []

    for symbol in symbols:
        prev_q = previous.get(symbol, 0.0)
        cur_q = current.get(symbol, 0.0)
        if _is_zero(prev_q - cur_q, params.zero_epsilon):
            continue

        if _is_zero(prev_q, params.zero_epsilon) and not _is_zero(cur_q, params.zero_epsilon):
            transition = "opened"
            classification = "new_risk"
            confidence = "high"
            evidence: dict[str, Any] = {}
        elif not _is_zero(prev_q, params.zero_epsilon) and _is_zero(cur_q, params.zero_epsilon):
            transition = "closed"
            classification, confidence, evidence = _classify_close(
                symbol, request.close_evidence.get(symbol), params
            )
        elif prev_q * cur_q < 0:
            transition = "flipped"
            classification = "position_flip"
            confidence = "high"
            evidence = {}
        elif abs(cur_q) > abs(prev_q):
            transition = "increased"
            classification = "risk_increase"
            confidence = "high"
            evidence = {}
        else:
            transition = "reduced"
            classification = "partial_reduce"
            confidence = "high"
            evidence = {}

        item = PositionTransition(
            symbol=symbol,
            previous_qty=prev_q,
            current_qty=cur_q,
            transition=transition,
            classification=classification,
            confidence=confidence,
            evidence=evidence,
            diagnostics={"delta_qty": cur_q - prev_q},
        )
        transitions.append(item)
        if classification == "unknown_flat":
            unknown.append(item)

    return ModuleResult.success(
        PositionReconcilerReport(
            transitions=transitions,
            unknown=unknown,
            summary={
                "previous_symbols": len(previous),
                "current_symbols": len(current),
                "transitions": len(transitions),
                "unknown": len(unknown),
                "row_errors": len(prev_errors) + len(cur_errors),
            },
        ),
        events=events,
    )


__all__ = [
    "PositionReconcilerParams",
    "PositionReconcilerReport",
    "PositionReconcilerRequest",
    "PositionTransition",
    "run",
]
