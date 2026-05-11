"""
Module: order_planner

Module purpose
--------------
Convert strategy decisions or candidate rows into a structured, venue-neutral
order plan. This module never sends orders. It only describes intended legs.

Core idea
---------
Trading systems should separate "what we want to do" from "how a venue submits
it". The planner turns normalized symbol/side/price/notional inputs, or
explicit caller-supplied leg rows, into a stable list of order legs.
Venue-specific fields are kept in metadata so another adapter can translate the
plan later.

Inputs
------
- `decisions`: list of dict-like rows. Raw candidate rows are accepted.
- Required by default: `symbol`, `side`.
- Optional: `price`, `notional`, `quantity`, `order_type`, `stop_loss`,
  `take_profit`, and explicit `legs`.
- Field names are configurable via params.

Outputs
-------
- `ModuleResult.value` is `OrderPlannerReport`.
- `plans` contains one `OrderPlan` per accepted decision.
- `rejected` records rows that could not be converted and why.

Failure semantics
-----------------
Missing or invalid required fields reject only that row. The module returns a
failed `ModuleResult` only when the request itself is unusable, for example when
`decisions` is not iterable.

Market generalization
---------------------
No venue, asset-class, or broker assumptions are embedded. Quantities are
unitless from the module's view; downstream execution adapters apply lot size,
tick size, contract multiplier, reduce-only, or margin-specific translation.
"""

from __future__ import annotations

from collections.abc import Iterable as IterableABC, Mapping as MappingABC
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from .contracts import (
    DetailLevel,
    InstrumentRef,
    ModuleEvent,
    ModuleResult,
    ModuleRunContext,
    detail_at_least,
)
from .row_utils import finite_float


@dataclass
class OrderLeg:
    """One venue-neutral intended order leg.

    Fields
    ------
    symbol:
        Tradable identifier after upstream symbol normalization.
    side:
        `buy` or `sell` from the strategy perspective.
    intent:
        Semantic role: `entry`, `add`, `take_profit`, `stop_loss`, `exit`.
    order_type:
        `market`, `limit`, `stop`, or `take_profit`.
    quantity:
        Base/contract quantity. May be `None` when close-position semantics are
        requested and venue adapter supports it.
    notional:
        Quote/portfolio value requested by the strategy before venue rounding.
    price:
        Limit or reference price, if applicable.
    stop_price:
        Trigger price for stop/take-profit style orders.
    reduce_only:
        Whether the leg is intended only to reduce existing risk.
    close_position:
        Whether this leg is intended to close the full position.
    tag:
        Client-side semantic tag for audit and downstream cid generation.
    metadata:
        Extra diagnostics or venue-neutral hints. Venue-specific raw fields
        should be placed here by upstream callers, not interpreted here.
    """

    symbol: str
    side: str
    intent: str
    order_type: str
    quantity: Optional[float] = None
    notional: Optional[float] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None
    reduce_only: bool = False
    close_position: bool = False
    tag: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderPlan:
    """A complete intended order set for one symbol/decision."""

    symbol: str
    side: str
    legs: list[OrderLeg]
    source: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderPlannerParams:
    """Configurable field names.

    The module intentionally does not contain sizing, first-entry fractions, or
    add-ladder policy. Those decisions must be reflected in row fields or in
    explicit `legs` passed by the caller.

    Configuration:
    - `symbol_field`, `side_field`: fields that identify instrument and side.
    - `price_field`, `notional_field`, `quantity_field`: fields used to derive
      quantity. If quantity is absent and notional/price are present, quantity
      is computed as notional / price.
    - `order_type_field`, `intent_field`, `tag_field`, `tag_prefix_field`:
      optional semantic fields copied into generated `OrderLeg` objects.
    - `legs_field`: field containing explicit caller-supplied leg dictionaries.
      When present, the module converts those legs instead of inventing policy.
    - `add_levels_field`: optional compatibility field containing add-leg
      dictionaries; each add level must include enough price/notional data.
    - `stop_loss_field`, `take_profit_field`: optional trigger fields used to
      append reduce-only exit legs.
    - `require_price_for_notional_quantity`: reject rows where notional cannot
      be converted into quantity because price is missing.
    - `detail`: controls optional diagnostics included in the report.
    """

    symbol_field: str = "symbol"
    side_field: str = "side"
    price_field: str = "price"
    notional_field: str = "notional"
    quantity_field: str = "quantity"
    order_type_field: str = "order_type"
    intent_field: str = "intent"
    tag_field: str = "tag"
    tag_prefix_field: str = "tag_prefix"
    legs_field: str = "legs"
    add_levels_field: str = "add_levels"
    stop_loss_field: str = "stop_loss"
    take_profit_field: str = "take_profit"
    require_price_for_notional_quantity: bool = True
    detail: DetailLevel = DetailLevel.STANDARD


@dataclass
class OrderPlannerRequest:
    """Request payload for `run`."""

    decisions: Iterable[Mapping[str, Any]]
    params: OrderPlannerParams = field(default_factory=OrderPlannerParams)
    context: ModuleRunContext = field(default_factory=ModuleRunContext)
    instrument: InstrumentRef | None = None


@dataclass
class OrderPlannerReport:
    """Detailed planner output."""

    plans: list[OrderPlan]
    rejected: list[dict[str, Any]]
    summary: dict[str, Any]


def _row_to_dict(row: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "__dict__"):
        return dict(vars(row))
    raise TypeError(f"decision row must be mapping-like, got {type(row).__name__}")


def _as_float(value: Any) -> Optional[float]:
    return finite_float(value)


def _opposite_side(side: str) -> str:
    s = side.lower()
    if s in {"buy", "long"}:
        return "sell"
    if s in {"sell", "short"}:
        return "buy"
    return s


def _normalize_side(side: Any) -> Optional[str]:
    if side is None:
        return None
    s = str(side).strip().lower()
    if s in {"buy", "long"}:
        return "buy"
    if s in {"sell", "short"}:
        return "sell"
    return None


def _tag(prefix: str, value: str) -> str:
    value = str(value or "").strip()
    prefix = str(prefix or "").strip()
    if prefix and value:
        return f"{prefix}.{value}"
    return value or prefix


def _bool_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _leg_from_mapping(raw: Mapping[str, Any], *, fallback_symbol: str, fallback_side: str, params: OrderPlannerParams) -> OrderLeg:
    side = _normalize_side(raw.get(params.side_field, fallback_side)) or fallback_side
    price = _as_float(raw.get(params.price_field))
    quantity = _as_float(raw.get(params.quantity_field))
    notional = _as_float(raw.get(params.notional_field))
    stop_price = _as_float(raw.get("stop_price", raw.get(params.price_field)))
    order_type = str(raw.get(params.order_type_field) or ("limit" if price is not None else "market")).strip().lower()
    intent = str(raw.get(params.intent_field) or "entry").strip().lower()
    tag_prefix = str(raw.get(params.tag_prefix_field) or "").strip()
    tag = str(raw.get(params.tag_field) or _tag(tag_prefix, intent)).strip()
    raw_metadata = raw.get("metadata")
    if raw_metadata is None:
        metadata: dict[str, Any] = {}
    elif isinstance(raw_metadata, MappingABC):
        metadata = dict(raw_metadata)
    else:
        raise ValueError("metadata must be a mapping")
    return OrderLeg(
        symbol=str(raw.get(params.symbol_field) or raw.get("symbol") or fallback_symbol),
        side=side,
        intent=intent,
        order_type=order_type,
        quantity=quantity,
        notional=notional,
        price=price,
        stop_price=stop_price if order_type in {"stop", "take_profit", "stop_loss"} else raw.get("stop_price"),
        reduce_only=_bool_value(raw.get("reduce_only"), default=False),
        close_position=_bool_value(raw.get("close_position"), default=False),
        tag=tag,
        metadata=metadata,
    )


def run(request: OrderPlannerRequest) -> ModuleResult[OrderPlannerReport]:
    """Build venue-neutral order plans from raw strategy decisions."""

    params = request.params
    events: list[ModuleEvent] = []
    plans: list[OrderPlan] = []
    rejected: list[dict[str, Any]] = []

    try:
        rows = list(request.decisions)
    except Exception as exc:
        return ModuleResult.fail(
            "decisions_not_iterable",
            str(exc),
        )

    for idx, raw_row in enumerate(rows):
        try:
            row = _row_to_dict(raw_row)
        except Exception as exc:
            rejected.append({"index": idx, "reason": "invalid_row", "error": str(exc)})
            continue

        symbol = str(row.get(params.symbol_field, "")).strip()
        side = _normalize_side(row.get(params.side_field))
        price = _as_float(row.get(params.price_field))
        row_notional = _as_float(row.get(params.notional_field))
        quantity = _as_float(row.get(params.quantity_field))
        stop_loss = _as_float(row.get(params.stop_loss_field))
        take_profit = _as_float(row.get(params.take_profit_field))
        tag_prefix = str(row.get(params.tag_prefix_field) or "").strip()

        if not symbol:
            rejected.append({"index": idx, "reason": "missing_symbol"})
            continue
        if side is None:
            rejected.append({"index": idx, "symbol": symbol, "reason": "invalid_side"})
            continue

        notional = None
        if row_notional is not None:
            notional = max(row_notional, 0.0)
        if quantity is None and notional is not None:
            if price is None or price <= 0:
                if params.require_price_for_notional_quantity:
                    rejected.append(
                        {
                            "index": idx,
                            "symbol": symbol,
                            "reason": "price_required_for_notional_quantity",
                        }
                    )
                    continue
            else:
                quantity = notional / price

        if quantity is not None and quantity <= 0:
            rejected.append({"index": idx, "symbol": symbol, "reason": "non_positive_quantity"})
            continue

        explicit_legs = row.get(params.legs_field)
        legs: list[OrderLeg] = []
        if isinstance(explicit_legs, IterableABC) and not isinstance(explicit_legs, (str, bytes, MappingABC)):
            for leg_idx, raw_leg in enumerate(explicit_legs):
                if not isinstance(raw_leg, MappingABC):
                    rejected.append({"index": idx, "symbol": symbol, "reason": "invalid_explicit_leg", "leg_index": leg_idx})
                    continue
                try:
                    legs.append(_leg_from_mapping(raw_leg, fallback_symbol=symbol, fallback_side=side, params=params))
                except Exception as exc:
                    rejected.append({"index": idx, "symbol": symbol, "reason": "invalid_explicit_leg", "leg_index": leg_idx, "error": str(exc)})
                    continue
        else:
            order_type = str(row.get(params.order_type_field) or ("limit" if price is not None else "market")).strip().lower()
            legs.append(
                OrderLeg(
                    symbol=symbol,
                    side=side,
                    intent=str(row.get(params.intent_field) or "entry").strip().lower(),
                    order_type=order_type,
                    quantity=quantity,
                    notional=notional,
                    price=price if order_type == "limit" else None,
                    tag=str(row.get(params.tag_field) or _tag(tag_prefix, "entry")),
                )
            )

        exit_side = _opposite_side(side)
        if take_profit is not None:
            legs.append(
                OrderLeg(
                    symbol=symbol,
                    side=exit_side,
                    intent="take_profit",
                    order_type="take_profit",
                    quantity=quantity,
                    stop_price=take_profit,
                    reduce_only=True,
                    close_position=quantity is None,
                    tag=_tag(tag_prefix, "take_profit"),
                )
            )
        if stop_loss is not None:
            legs.append(
                OrderLeg(
                    symbol=symbol,
                    side=exit_side,
                    intent="stop_loss",
                    order_type="stop",
                    quantity=quantity,
                    stop_price=stop_loss,
                    reduce_only=True,
                    close_position=quantity is None,
                    tag=_tag(tag_prefix, "stop_loss"),
                )
            )

        row_add_levels = row.get(params.add_levels_field) or []
        for level_idx, level in enumerate(row_add_levels if isinstance(row_add_levels, IterableABC) and not isinstance(row_add_levels, (str, bytes, MappingABC)) else []):
            if not isinstance(level, MappingABC):
                rejected.append({"index": idx, "symbol": symbol, "reason": "invalid_add_level", "level": level_idx})
                continue
            if price is None or row_notional is None:
                rejected.append(
                    {
                        "index": idx,
                        "symbol": symbol,
                        "reason": "add_level_skipped_missing_price_or_notional",
                        "level": level_idx,
                    }
                )
                continue
            offset_pct = _as_float(level.get("offset_pct")) or 0.0
            add_price = _as_float(level.get(params.price_field))
            if add_price is None:
                add_price = price * (1.0 - offset_pct if side == "buy" else 1.0 + offset_pct)
            add_notional = _as_float(level.get(params.notional_field))
            if add_notional is None:
                fraction = _as_float(level.get("notional_fraction"))
                add_notional = row_notional * fraction if fraction is not None else row_notional
            add_notional = max(add_notional, 0.0)
            legs.append(
                OrderLeg(
                    symbol=symbol,
                    side=side,
                    intent=str(level.get(params.intent_field) or "add").strip().lower(),
                    order_type=str(level.get(params.order_type_field) or "limit").strip().lower(),
                    quantity=_as_float(level.get(params.quantity_field)) or (add_notional / add_price if add_price > 0 else None),
                    notional=add_notional,
                    price=add_price,
                    tag=str(level.get(params.tag_field) or _tag(tag_prefix, "add")),
                    metadata={"offset_pct": offset_pct, "level_index": level_idx},
                )
            )

        if not legs:
            rejected.append({"index": idx, "symbol": symbol, "reason": "no_order_legs"})
            continue

        diagnostics: dict[str, Any] = {
            "leg_count": len(legs),
            "entry_quantity_source": "row_quantity" if row.get(params.quantity_field) not in (None, "") else "notional_price",
        }
        if request.instrument is not None and detail_at_least(params.detail, DetailLevel.FULL):
            diagnostics["instrument"] = request.instrument

        plans.append(
            OrderPlan(
                symbol=symbol,
                side=side,
                legs=legs,
                source=row,
                diagnostics=diagnostics,
            )
        )

    events.append(
        ModuleEvent(
            event="order_plan.completed",
            level="INFO",
            fields={"plans": len(plans), "rejected": len(rejected)},
        )
    )

    return ModuleResult.success(
        OrderPlannerReport(
            plans=plans,
            rejected=rejected,
            summary={"input_rows": len(rows), "plans": len(plans), "rejected": len(rejected)},
        ),
        events=events,
    )


__all__ = [
    "OrderLeg",
    "OrderPlan",
    "OrderPlannerParams",
    "OrderPlannerReport",
    "OrderPlannerRequest",
    "run",
]
