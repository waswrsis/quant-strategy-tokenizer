"""
quant_strategy_tokenizer.contracts
==========================
Module purpose: shared contracts for every extracted strategy module.
Core idea: use small dataclasses so modules can be chained, inspected, tested,
and called from simulations or live sidecars without importing the runner.
Inputs: raw data, DataFrameSpec column mappings, optional ExtractorSpec
callbacks, ModuleRunContext, and module Params dataclasses.
Outputs: ModuleResult[T] with detailed events, warnings, failures, and optional
OutputFiles.
Failure semantics: modules must return ModuleResult.fail(...) for missing data,
invalid schemas, unknown state, insufficient data, or unsupported inputs.
Market generalization: InstrumentRef does not assume quote, settlement, venue,
asset class, or symbol format.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Mapping, Optional, TypeVar

T = TypeVar("T")


class DetailLevel(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"
    DEBUG = "debug"


@dataclass
class InstrumentRef:
    """Optional instrument metadata used only for diagnostics.

    Configuration:
    - `symbol`: caller-facing identifier, required when an instrument is used.
    - `asset_class`: free-form class such as equity, futures, crypto, fx.
    - `market_type`: free-form venue/market mode such as spot or perpetual.
    - `base`, `quote`, `settlement`: optional decomposition of the instrument.
    - `venue`: data or execution venue name, if the caller wants it recorded.
    - `metadata`: extra caller-defined fields that modules should not parse.
    """

    symbol: str
    asset_class: str = ""
    market_type: str = ""
    base: str = ""
    quote: str = ""
    settlement: str = ""
    venue: str = ""
    metadata: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class DataFrameSpec:
    """Column mapping and validation rules for raw market data.

    Configuration:
    - `*_col`: explicit column names for timestamps, OHLCV, value, price, and
      closed flags. Change these when vendor columns differ from the standard.
    - `require_utc`: when True, timestamp columns must be timezone-aware UTC.
    - `closed_only`: when True, rows marked as not closed cause failure.
    - `allow_aliases`: when True, built-in and custom aliases may map fields.
    - `aliases`: caller-supplied alias lists, keyed by logical field name.
    """

    ts_col: str = "ts"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"
    value_col: str = "value"
    price_col: str = "price"
    closed_col: str = "closed"
    require_utc: bool = True
    closed_only: bool = False
    allow_aliases: bool = False
    aliases: Dict[str, List[str]] = dc_field(default_factory=dict)


@dataclass
class ExtractorSpec:
    """Callbacks for turning arbitrary user objects into columns.

    Configuration:
    - `extractors`: mapping of logical field name -> function(raw) returning a
      scalar or sequence. Use this when input is a custom object, SDK response,
      or nested structure rather than a DataFrame/list/dict.
    - `metadata`: optional notes about the extraction source for diagnostics.
    """

    extractors: Mapping[str, Callable[[Any], Any]] = dc_field(default_factory=dict)
    metadata: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class ModuleRunContext:
    """Runtime options shared by all modules.

    Configuration:
    - `run_id`: stable id used in report file names and audit traces.
    - `module`: caller label for the module invocation.
    - `strategy_id`: optional strategy namespace for reports.
    - `asof_ts`: caller's evaluation timestamp, seconds since epoch.
    - `profile`: free-form profile name chosen by the caller.
    - `detail_level`: controls how much series/diagnostic data is returned.
    - `output_dir`: when set, modules may write summary/events/data reports.
    - `parameters`: extra caller parameters kept for diagnostics only.
    - `metadata`: free-form runtime metadata not interpreted by modules.
    """

    run_id: str = ""
    module: str = ""
    strategy_id: str = ""
    asof_ts: Optional[float] = None
    profile: str = ""
    detail_level: DetailLevel = DetailLevel.STANDARD
    output_dir: Optional[str] = None
    parameters: Dict[str, Any] = dc_field(default_factory=dict)
    metadata: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class ModuleEvent:
    event: str
    level: str = "INFO"
    symbol: str = ""
    reason: str = ""
    fields: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class ModuleFailure:
    kind: str
    message: str
    field: str = ""
    details: Dict[str, Any] = dc_field(default_factory=dict)


@dataclass
class OutputFiles:
    summary_json: Optional[str] = None
    events_jsonl: Optional[str] = None
    data_json: Optional[str] = None


@dataclass
class ModuleResult(Generic[T]):
    ok: bool
    value: Optional[T] = None
    events: List[ModuleEvent] = dc_field(default_factory=list)
    warnings: List[str] = dc_field(default_factory=list)
    failure: Optional[ModuleFailure] = None
    files: Optional[OutputFiles] = None

    @classmethod
    def success(
        cls,
        value: T,
        *,
        events: Optional[List[ModuleEvent]] = None,
        warnings: Optional[List[str]] = None,
        files: Optional[OutputFiles] = None,
    ) -> "ModuleResult[T]":
        return cls(ok=True, value=value, events=list(events or []), warnings=list(warnings or []), files=files)

    @classmethod
    def fail(
        cls,
        kind: str,
        message: str,
        *,
        field: str = "",
        details: Optional[Dict[str, Any]] = None,
        events: Optional[List[ModuleEvent]] = None,
        warnings: Optional[List[str]] = None,
        files: Optional[OutputFiles] = None,
    ) -> "ModuleResult[T]":
        return cls(
            ok=False,
            value=None,
            events=list(events or []),
            warnings=list(warnings or []),
            failure=ModuleFailure(kind=kind, message=message, field=field, details=dict(details or {})),
            files=files,
        )


def _detail_value(value: DetailLevel | str) -> str:
    if isinstance(value, DetailLevel):
        return value.value
    raw = str(value)
    if raw.startswith("DetailLevel."):
        name = raw.split(".", 1)[1]
        try:
            return DetailLevel[name].value
        except Exception:
            return raw
    return raw


def detail_at_least(level: DetailLevel | str, threshold: DetailLevel | str) -> bool:
    order = {
        DetailLevel.MINIMAL.value: 0,
        DetailLevel.STANDARD.value: 1,
        DetailLevel.FULL.value: 2,
        DetailLevel.DEBUG.value: 3,
    }
    return order.get(_detail_value(level), 1) >= order.get(_detail_value(threshold), 1)


__all__ = [
    "DetailLevel",
    "InstrumentRef",
    "DataFrameSpec",
    "ExtractorSpec",
    "ModuleRunContext",
    "ModuleEvent",
    "ModuleFailure",
    "OutputFiles",
    "ModuleResult",
    "detail_at_least",
]
