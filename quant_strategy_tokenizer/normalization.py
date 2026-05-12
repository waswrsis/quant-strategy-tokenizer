"""
quant_strategy_tokenizer.normalization
======================================
Module purpose: convert raw user inputs into predictable pandas DataFrames.
Core idea: Accept convenient raw shapes, resolve logical field names through DataFrameSpec, and coerce only the fields a module declares. Assumes computation should happen after explicit field resolution rather than implicit mutation of user data.
Inputs: DataFrame, Series, list[dict], dict[list], scalar sequences, or custom objects handled by ExtractorSpec.
Outputs: NormalizedFrame with frame, used_fields, missing fields, input profile, and warnings.
Failure semantics: unsupported input, empty input, bad extractor output, missing required fields, invalid timestamps, or all-NaN numeric fields return ModuleResult.fail.
Market generalization: normalization maps fields only; it does not assume OHLCV source, symbol format, venue, or market type.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable as IterableABC
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .contracts import DataFrameSpec, ExtractorSpec, ModuleResult


DEFAULT_ALIASES: Dict[str, List[str]] = {
    "ts": ["ts", "time", "timestamp", "datetime", "date"],
    "open": ["open", "Open", "o"],
    "high": ["high", "High", "h"],
    "low": ["low", "Low", "l"],
    "close": ["close", "Close", "c", "last", "price"],
    "volume": ["volume", "Volume", "v", "vol", "tick_volume"],
    "value": ["value", "Value", "close", "Close", "c"],
    "price": ["price", "Price", "close", "Close", "last"],
    "closed": ["closed", "is_closed", "complete"],
}


@dataclass
class NormalizedFrame:
    frame: pd.DataFrame
    used_fields: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    optional_missing_fields: List[str] = field(default_factory=list)
    input_profile: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def normalize_frame(
    raw: Any,
    *,
    required_fields: Iterable[str],
    optional_fields: Iterable[str] = (),
    spec: Optional[DataFrameSpec] = None,
    extractor: Optional[ExtractorSpec] = None,
) -> ModuleResult[NormalizedFrame]:
    spec = spec or DataFrameSpec()
    required = list(required_fields or [])
    optional = list(optional_fields or [])
    df_result = _raw_to_dataframe(raw, extractor=extractor)
    if not df_result.ok:
        return ModuleResult.fail(
            df_result.failure.kind if df_result.failure else "invalid_input",
            df_result.failure.message if df_result.failure else "failed to normalize input",
            field=df_result.failure.field if df_result.failure else "",
            details=df_result.failure.details if df_result.failure else {},
        )
    df = df_result.value
    if df is None:
        return ModuleResult.fail("internal_error", "normalization produced no DataFrame")
    if len(df) <= 0:
        return ModuleResult.fail("empty_input", "input contains no rows")

    warnings: List[str] = list(df_result.warnings)
    used: Dict[str, str] = {}
    missing: List[str] = []
    optional_missing: List[str] = []
    aliases = {**DEFAULT_ALIASES, **dict(spec.aliases or {})}

    for field_name in required:
        col = resolve_field_column(field_name, df, spec=spec, aliases=aliases)
        if col is None:
            missing.append(field_name)
        else:
            used[field_name] = col
    if missing:
        return ModuleResult.fail(
            "missing_required_field",
            f"missing required fields: {missing}",
            details={"missing_fields": missing, "columns": [str(c) for c in df.columns]},
        )

    for field_name in optional:
        col = resolve_field_column(field_name, df, spec=spec, aliases=aliases)
        if col is None:
            optional_missing.append(field_name)
        else:
            used[field_name] = col

    for field_name, col in used.items():
        if field_name == "ts":
            converted = pd.to_datetime(df[col], utc=False, errors="coerce")
            if converted.isna().any():
                return ModuleResult.fail("invalid_timestamp", f"timestamp column {col} contains invalid values", field=col)
            try:
                tz = converted.dt.tz
            except Exception:
                tz = None
            if spec.require_utc and tz is None:
                return ModuleResult.fail("invalid_timestamp", f"timestamp column {col} must be timezone-aware UTC", field=col)
            if spec.require_utc and str(tz) not in {"UTC", "UTC+00:00"}:
                return ModuleResult.fail("invalid_timestamp", f"timestamp column {col} must be UTC, got {tz}", field=col)
            df[col] = converted
            continue
        if field_name == "closed":
            continue
        try:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except Exception as exc:
            return ModuleResult.fail("invalid_numeric", f"field {field_name} cannot be converted to numeric", field=col, details={"error": str(exc)})
        if df[col].isna().all():
            return ModuleResult.fail("invalid_numeric", f"field {field_name} contains no numeric values", field=col)

    if spec.closed_only:
        closed_col = used.get("closed") or resolve_field_column("closed", df, spec=spec, aliases=aliases)
        if closed_col is not None:
            try:
                if (df[closed_col] == False).any():  # noqa: E712
                    return ModuleResult.fail("unclosed_bar", "input contains unclosed bars", field=closed_col)
            except Exception:
                warnings.append(f"could not evaluate closed flag column {closed_col}")

    profile = {
        "input_type": type(raw).__name__,
        "rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "allow_aliases": bool(spec.allow_aliases),
    }
    return ModuleResult.success(
        NormalizedFrame(
            frame=df,
            used_fields=used,
            missing_fields=missing,
            optional_missing_fields=optional_missing,
            input_profile=profile,
            warnings=warnings,
        ),
        warnings=warnings,
    )


def resolve_field_column(field_name: str, df: pd.DataFrame, *, spec: DataFrameSpec, aliases: Dict[str, List[str]]) -> Optional[Any]:
    explicit = {
        "ts": spec.ts_col,
        "open": spec.open_col,
        "high": spec.high_col,
        "low": spec.low_col,
        "close": spec.close_col,
        "volume": spec.volume_col,
        "value": spec.value_col,
        "price": spec.price_col,
        "closed": spec.closed_col,
    }.get(field_name, field_name)
    cols = {str(c): c for c in df.columns}
    if explicit in cols:
        return cols[explicit]
    if spec.allow_aliases:
        for cand in aliases.get(field_name, []):
            if cand in cols:
                return cols[cand]
    return None


def _raw_to_dataframe(raw: Any, *, extractor: Optional[ExtractorSpec] = None) -> ModuleResult[pd.DataFrame]:
    try:
        if extractor and extractor.extractors:
            data = {name: fn(raw) for name, fn in extractor.extractors.items()}
            return _extractor_data_to_frame(data)
        if isinstance(raw, pd.DataFrame):
            return ModuleResult.success(raw.copy())
        if isinstance(raw, pd.Series):
            name = str(raw.name or "value")
            return ModuleResult.success(pd.DataFrame({name: raw.to_list()}))
        if isinstance(raw, dict):
            return ModuleResult.success(pd.DataFrame(raw))
        if isinstance(raw, (list, tuple)):
            if len(raw) == 0:
                return ModuleResult.fail("empty_input", "input sequence is empty")
            first = raw[0]
            if isinstance(first, dict):
                return ModuleResult.success(pd.DataFrame(list(raw)))
            return ModuleResult.success(pd.DataFrame({"value": list(raw)}))
    except Exception as exc:
        return ModuleResult.fail("invalid_input", "could not convert raw input to DataFrame", details={"error": str(exc)})
    return ModuleResult.fail(
        "unsupported_input",
        f"unsupported input type: {type(raw).__name__}; provide DataFrame, Series, list, dict, or ExtractorSpec",
    )


def _extractor_data_to_frame(data: Dict[str, Any]) -> ModuleResult[pd.DataFrame]:
    columns: Dict[str, List[Any]] = {}
    lengths: List[int] = []
    for name, value in data.items():
        vals = _as_column_values(value)
        columns[str(name)] = vals
        lengths.append(len(vals))
    if not lengths:
        return ModuleResult.fail("invalid_input", "extractor produced no columns")
    max_len = max(lengths)
    if max_len <= 0:
        return ModuleResult.fail("empty_input", "extractor produced no rows")
    expanded: Dict[str, List[Any]] = {}
    bad_lengths: Dict[str, int] = {}
    for name, vals in columns.items():
        if len(vals) == max_len:
            expanded[name] = vals
        elif len(vals) == 1:
            expanded[name] = vals * max_len
        else:
            bad_lengths[name] = len(vals)
    if bad_lengths:
        return ModuleResult.fail(
            "invalid_input",
            "extractor columns have incompatible lengths",
            details={"lengths": {name: len(vals) for name, vals in columns.items()}},
        )
    return ModuleResult.success(pd.DataFrame(expanded))


def _as_column_values(value: Any) -> List[Any]:
    if isinstance(value, pd.Series):
        return value.to_list()
    if isinstance(value, pd.Index):
        return value.to_list()
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, dict):
        return [value]
    if hasattr(value, "tolist"):
        converted = value.tolist()
        if isinstance(converted, list):
            return converted
        return [converted]
    if isinstance(value, IterableABC):
        return list(value)
    return [value]


__all__ = ["NormalizedFrame", "normalize_frame", "resolve_field_column", "DEFAULT_ALIASES"]
