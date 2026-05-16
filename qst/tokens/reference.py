"""Deterministic reference helpers for primitive token contracts.

These helpers are conformance aids for TokenSpec contracts. They are not a
strategy runtime and are intentionally not called by IR validation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any, Literal, cast, overload

SeriesRow = tuple[str, Any]
NumericSeries = list[tuple[str, float]]
BoolSeries = list[tuple[str, bool]]


class TokenReferenceError(ValueError):
    """Reference helper failure with a stable diagnostic-like code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def evaluate_math_token(name: str, *args: Any, **params: Any) -> object:
    """Evaluate a Stage 3A.1 `math.*` primitive reference helper."""

    token = _local_name(name, "math.")

    if token in {"add", "sub", "mul", "div", "pow"}:
        left, right = _expect_args(token, args, 2)
        a = _coerce_number(left)
        b = _coerce_number(right)
        if token == "add":
            return a + b
        if token == "sub":
            return a - b
        if token == "mul":
            return a * b
        if token == "pow":
            return _finite_result(a**b)
        if b == 0:
            raise TokenReferenceError(
                "QST_TOKEN_MATH_DIVIDE_BY_ZERO",
                "math.div cannot divide by zero.",
            )
        return _finite_result(a / b)

    if token in {"neg", "abs", "sqrt", "log", "exp", "floor", "ceil", "round", "sign"}:
        (raw,) = _expect_args(token, args, 1)
        x = _coerce_number(raw)
        if token == "neg":
            return -x
        if token == "abs":
            return abs(x)
        if token == "sqrt":
            if x < 0:
                raise TokenReferenceError(
                    "QST_TOKEN_MATH_DOMAIN_ERROR",
                    "math.sqrt requires a non-negative input.",
                )
            return _finite_result(math.sqrt(x))
        if token == "log":
            if x <= 0:
                raise TokenReferenceError(
                    "QST_TOKEN_MATH_DOMAIN_ERROR",
                    "math.log requires a positive input.",
                )
            return _finite_result(math.log(x))
        if token == "exp":
            return _finite_result(math.exp(x))
        if token == "floor":
            return math.floor(x)
        if token == "ceil":
            return math.ceil(x)
        if token == "round":
            ndigits = params.get("ndigits", 0)
            if isinstance(ndigits, bool) or not isinstance(ndigits, int):
                raise TokenReferenceError(
                    "QST_TOKEN_PARAM_TYPE_INVALID",
                    "math.round ndigits must be an integer.",
                )
            return round(x, ndigits)
        return 1 if x > 0 else -1 if x < 0 else 0

    if token in {"min", "max"}:
        (raw_values,) = _expect_args(token, args, 1)
        values = [_coerce_number(value) for value in _iter_values(raw_values)]
        if not values and not bool(params.get("allow_empty", False)):
            raise TokenReferenceError(
                "QST_TOKEN_EMPTY_INPUT",
                f"math.{token} requires at least one input.",
            )
        if not values:
            return None
        return min(values) if token == "min" else max(values)

    if token == "clip":
        (raw,) = _expect_args(token, args, 1)
        x = _coerce_number(raw)
        lower = _coerce_number(params.get("lower"))
        upper = _coerce_number(params.get("upper"))
        if lower > upper:
            raise TokenReferenceError(
                "QST_TOKEN_MATH_RANGE_INVALID",
                "math.clip lower must be less than or equal to upper.",
            )
        return min(max(x, lower), upper)

    if token in {"isnan", "isfinite"}:
        (raw,) = _expect_args(token, args, 1)
        x = _coerce_number(raw, allow_nonfinite=True)
        return math.isnan(x) if token == "isnan" else math.isfinite(x)

    if token == "where":
        condition, if_true, if_false = _expect_args(token, args, 3)
        if not isinstance(condition, bool):
            raise TokenReferenceError(
                "QST_TOKEN_BOOL_TYPE_INVALID",
                "math.where condition must be boolean.",
            )
        return _coerce_number(if_true if condition else if_false)

    if token == "fill_nan":
        (raw,) = _expect_args(token, args, 1)
        x = _coerce_number(raw, allow_nonfinite=True)
        replacement = _coerce_number(params.get("replacement"))
        if math.isnan(x):
            return replacement
        if not math.isfinite(x):
            raise TokenReferenceError(
                "QST_TOKEN_NUMERIC_NONFINITE",
                "math.fill_nan only handles NaN, not Infinity.",
            )
        return x

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported math token: {name}")


def evaluate_bool_token(name: str, *args: Any, allow_empty: bool = False) -> object:
    """Evaluate a Stage 3A.1 `bool.*` primitive reference helper."""

    token = _local_name(name, "bool.")

    if token in {"and", "or", "xor"}:
        left, right = _expect_args(token, args, 2)
        a = _coerce_bool(left)
        b = _coerce_bool(right)
        if token == "and":
            return a and b
        if token == "or":
            return a or b
        return a != b

    if token == "not":
        (raw,) = _expect_args(token, args, 1)
        return not _coerce_bool(raw)

    if token in {"any", "all", "count_true"}:
        (raw_values,) = _expect_args(token, args, 1)
        values = [_coerce_bool(value) for value in _iter_values(raw_values)]
        if not values and not allow_empty:
            raise TokenReferenceError(
                "QST_TOKEN_EMPTY_INPUT",
                f"bool.{token} requires at least one input.",
            )
        if token == "any":
            return any(values)
        if token == "all":
            return all(values)
        return sum(1 for value in values if value)

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported bool token: {name}")


def evaluate_cmp_token(name: str, *args: Any, inclusive: bool = True) -> bool:
    """Evaluate a Stage 3A.1 `cmp.*` primitive reference helper."""

    token = _local_name(name, "cmp.")

    if token in {"eq", "ne", "gt", "gte", "lt", "lte"}:
        left, right = _expect_args(token, args, 2)
        a = _coerce_number(left)
        b = _coerce_number(right)
        return {
            "eq": a == b,
            "ne": a != b,
            "gt": a > b,
            "gte": a >= b,
            "lt": a < b,
            "lte": a <= b,
        }[token]

    if token in {"between", "outside"}:
        raw_x, raw_lower, raw_upper = _expect_args(token, args, 3)
        x = _coerce_number(raw_x)
        lower = _coerce_number(raw_lower)
        upper = _coerce_number(raw_upper)
        if lower > upper:
            raise TokenReferenceError(
                "QST_TOKEN_CMP_RANGE_INVALID",
                "cmp.between/cmp.outside require lower <= upper.",
            )
        inside = lower <= x <= upper if inclusive else lower < x < upper
        return inside if token == "between" else not inside

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported cmp token: {name}")


def evaluate_data_token(name: str, series: Sequence[SeriesRow], **params: Any) -> NumericSeries:
    """Evaluate Stage 3A.2 `data.*` series reference helpers."""

    token = _local_name(name, "data.")
    rows = _numeric_series(series)

    if token == "identity":
        return rows

    if token == "shift":
        periods = _coerce_int_param(params.get("periods", 1), "periods")
        if periods < 0 and not bool(params.get("allow_unsafe_future", False)):
            raise TokenReferenceError(
                "QST_TOKEN_UNSAFE_FUTURE_SHIFT",
                "data.shift with negative periods uses future data.",
            )
        if periods == 0:
            return rows
        if periods > 0:
            return [(rows[index][0], rows[index - periods][1]) for index in range(periods, len(rows))]
        offset = abs(periods)
        return [(rows[index][0], rows[index + offset][1]) for index in range(0, len(rows) - offset)]

    if token in {"diff", "pct_change", "log_return"}:
        output: NumericSeries = []
        for index in range(1, len(rows)):
            timestamp, current = rows[index]
            previous = rows[index - 1][1]
            if token == "diff":
                value = current - previous
            elif token == "pct_change":
                if previous == 0:
                    raise TokenReferenceError(
                        "QST_TOKEN_DATA_DIVIDE_BY_ZERO",
                        "data.pct_change previous value cannot be zero.",
                    )
                value = current / previous - 1
            else:
                if current <= 0 or previous <= 0:
                    raise TokenReferenceError(
                        "QST_TOKEN_DATA_LOG_RETURN_DOMAIN_ERROR",
                        "data.log_return requires positive current and previous values.",
                    )
                value = math.log(current / previous)
            output.append((timestamp, _finite_result(value)))
        return output

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported data token: {name}")


def evaluate_time_token(name: str, series: Sequence[SeriesRow], **params: Any) -> NumericSeries:
    """Evaluate Stage 3A.2 `time.*` series reference helpers."""

    token = _local_name(name, "time.")
    rows = _numeric_series(series)

    if token == "session_filter":
        start = _coerce_hhmm(params.get("start_hhmm"), "start_hhmm")
        end = _coerce_hhmm(params.get("end_hhmm"), "end_hhmm")
        if start > end:
            raise TokenReferenceError(
                "QST_TOKEN_TIME_RANGE_INVALID",
                "time.session_filter requires start_hhmm <= end_hhmm.",
            )
        return [(timestamp, value) for timestamp, value in rows if start <= _timestamp_hhmm(timestamp) <= end]

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported time token: {name}")


def evaluate_align_token(
    name: str,
    series: Sequence[SeriesRow],
    other: Sequence[SeriesRow] | None = None,
) -> object:
    """Evaluate Stage 3A.2 `align.*` series reference helpers."""

    token = _local_name(name, "align.")

    if token in {"forward_fill", "drop_missing"}:
        rows = _numeric_series(series, allow_none=True)
        if token == "drop_missing":
            return [(timestamp, value) for timestamp, value in rows if value is not None]
        output: list[tuple[str, float | None]] = []
        last_seen: float | None = None
        for timestamp, value in rows:
            if value is not None:
                last_seen = value
            output.append((timestamp, last_seen))
        return output

    if other is None:
        raise TokenReferenceError(
            "QST_TOKEN_ARITY_INVALID",
            f"align.{token} requires left and right series.",
        )

    left_rows = _numeric_series(series)
    right_rows = _numeric_series(other)
    right_by_timestamp = dict(right_rows)

    if token == "inner_join":
        left: NumericSeries = []
        right: NumericSeries = []
        for timestamp, value in left_rows:
            if timestamp in right_by_timestamp:
                left.append((timestamp, value))
                right.append((timestamp, right_by_timestamp[timestamp]))
        return left, right

    if token == "left_join":
        left_output: NumericSeries = []
        right_output: list[tuple[str, float | None]] = []
        for timestamp, value in left_rows:
            left_output.append((timestamp, value))
            right_output.append((timestamp, right_by_timestamp.get(timestamp)))
        return left_output, right_output

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported align token: {name}")


def evaluate_window_token(name: str, series: Sequence[SeriesRow], **params: Any) -> object:
    """Evaluate Stage 3A.2 `window.*` trailing-window reference helpers."""

    token = _local_name(name, "window.")
    rows = _numeric_series(series)
    window, min_periods = _window_params(params)
    output: list[tuple[str, float | int]] = []

    for index, (timestamp, current) in enumerate(rows):
        values = [value for _, value in rows[max(0, index - window + 1) : index + 1]]
        if len(values) < min_periods:
            continue
        if token == "max":
            value: float | int = max(values)
        elif token == "min":
            value = min(values)
        elif token == "sum":
            value = sum(values)
        elif token == "count":
            value = len(values)
        elif token == "mean":
            value = sum(values) / len(values)
        elif token == "std":
            value = _population_std(values)
        elif token == "zscore":
            std = _population_std(values)
            value = 0 if std == 0 else (current - sum(values) / len(values)) / std
        else:
            raise TokenReferenceError(
                "QST_TOKEN_REFERENCE_UNSUPPORTED",
                f"Unsupported window token: {name}",
            )
        output.append((timestamp, value))
    return output


def evaluate_signal_token(name: str, *args: Any, **params: Any) -> BoolSeries | NumericSeries:
    """Evaluate Stage 3A.2 `signal.*`, `norm.*`, and `smooth.*` helpers."""

    if name.startswith("core."):
        name = name.removeprefix("core.")

    if name.startswith("signal."):
        token = name.removeprefix("signal.")
        if token in {"cross_above", "cross_below", "crosses"}:
            left, right = _expect_args(token, args, 2)
            joined_left, joined_right = cast(
                tuple[NumericSeries, NumericSeries],
                evaluate_align_token("align.inner_join", left, right),
            )
            output: BoolSeries = []
            for index in range(1, len(joined_left)):
                timestamp, current_left = joined_left[index]
                current_right = joined_right[index][1]
                previous_left = joined_left[index - 1][1]
                previous_right = joined_right[index - 1][1]
                crossed_above = previous_left <= previous_right and current_left > current_right
                crossed_below = previous_left >= previous_right and current_left < current_right
                if token == "cross_above":
                    value = crossed_above
                elif token == "cross_below":
                    value = crossed_below
                else:
                    value = crossed_above or crossed_below
                output.append((timestamp, value))
            return output

        if token in {"threshold_above", "threshold_below"}:
            (series,) = _expect_args(token, args, 1)
            threshold = _coerce_number(params.get("threshold"))
            inclusive = bool(params.get("inclusive", True))
            output = []
            for timestamp, numeric_value in _numeric_series(series):
                if token == "threshold_above":
                    passed = numeric_value >= threshold if inclusive else numeric_value > threshold
                else:
                    passed = numeric_value <= threshold if inclusive else numeric_value < threshold
                output.append((timestamp, passed))
            return output

    if name.startswith("norm."):
        token = name.removeprefix("norm.")
        if token == "range_position":
            value_rows, high_rows, low_rows = _expect_args(token, args, 3)
            value_joined, high_joined = cast(
                tuple[NumericSeries, NumericSeries],
                evaluate_align_token("align.inner_join", value_rows, high_rows),
            )
            value_joined, low_joined = cast(
                tuple[NumericSeries, NumericSeries],
                evaluate_align_token("align.inner_join", value_joined, low_rows),
            )
            high_by_timestamp = dict(high_joined)
            low_by_timestamp = dict(low_joined)
            output_num: NumericSeries = []
            for timestamp, numeric_value in value_joined:
                high = high_by_timestamp[timestamp]
                low = low_by_timestamp[timestamp]
                if high == low:
                    raise TokenReferenceError(
                        "QST_TOKEN_SIGNAL_RANGE_ZERO",
                        "norm.range_position requires high != low.",
                    )
                output_num.append((timestamp, (numeric_value - low) / (high - low)))
            return output_num

    if name.startswith("smooth."):
        token = name.removeprefix("smooth.")
        if token == "linear_recursive":
            (series,) = _expect_args(token, args, 1)
            alpha = _coerce_number(params.get("alpha", 0.5))
            if alpha <= 0 or alpha > 1:
                raise TokenReferenceError(
                    "QST_TOKEN_SMOOTH_ALPHA_INVALID",
                    "smooth.linear_recursive requires 0 < alpha <= 1.",
                )
            output_num = []
            previous: float | None = None
            for timestamp, numeric_value in _numeric_series(series):
                previous = (
                    numeric_value
                    if previous is None
                    else alpha * numeric_value + (1 - alpha) * previous
                )
                output_num.append((timestamp, previous))
            return output_num

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported signal token: {name}")


def evaluate_indicator_token(name: str, series: Sequence[SeriesRow], **params: Any) -> object:
    """Evaluate Stage 3A.2 `indicator.*` reference helpers."""

    token = _local_name(name, "indicator.")
    rows = _numeric_series(series)

    if token == "sma":
        return evaluate_window_token("window.mean", rows, **params)

    if token == "ema":
        window, _ = _window_params(params)
        alpha = 2 / (window + 1)
        output: NumericSeries = []
        previous: float | None = None
        for timestamp, value in rows:
            previous = value if previous is None else alpha * value + (1 - alpha) * previous
            output.append((timestamp, previous))
        return output

    if token == "rsi":
        window, _ = _window_params(params)
        if len(rows) <= window:
            return []
        gains: list[float] = []
        losses: list[float] = []
        output = []
        avg_gain: float | None = None
        avg_loss: float | None = None
        for index in range(1, len(rows)):
            change = rows[index][1] - rows[index - 1][1]
            gain = max(change, 0)
            loss = max(-change, 0)
            gains.append(gain)
            losses.append(loss)
            if index < window:
                continue
            if index == window:
                avg_gain = sum(gains[:window]) / window
                avg_loss = sum(losses[:window]) / window
            else:
                assert avg_gain is not None and avg_loss is not None
                avg_gain = (avg_gain * (window - 1) + gain) / window
                avg_loss = (avg_loss * (window - 1) + loss) / window
            timestamp = rows[index][0]
            output.append((timestamp, _rsi_from_avgs(avg_gain, avg_loss)))
        return output

    if token == "bollinger":
        width = _coerce_number(params.get("width", 2))
        mean_rows = cast(NumericSeries, evaluate_window_token("window.mean", rows, **params))
        std_rows = cast(NumericSeries, evaluate_window_token("window.std", rows, **params))
        std_by_timestamp = dict(std_rows)
        middle: NumericSeries = []
        upper: NumericSeries = []
        lower: NumericSeries = []
        for timestamp, mean_value in mean_rows:
            std = std_by_timestamp[timestamp]
            middle.append((timestamp, mean_value))
            upper.append((timestamp, mean_value + width * std))
            lower.append((timestamp, mean_value - width * std))
        return {"middle": middle, "upper": upper, "lower": lower}

    raise TokenReferenceError("QST_TOKEN_REFERENCE_UNSUPPORTED", f"Unsupported indicator token: {name}")


def evaluate_channel_breakout_token(
    high: Sequence[SeriesRow],
    low: Sequence[SeriesRow],
    close: Sequence[SeriesRow],
    **params: Any,
) -> BoolSeries:
    """Evaluate `indicator.channel_breakout` using previous trailing high/low only."""

    window, _ = _window_params(params)
    joined_high, joined_low = cast(
        tuple[NumericSeries, NumericSeries],
        evaluate_align_token("align.inner_join", high, low),
    )
    joined_high, joined_close = cast(
        tuple[NumericSeries, NumericSeries],
        evaluate_align_token("align.inner_join", joined_high, close),
    )
    low_by_timestamp = dict(joined_low)
    close_by_timestamp = dict(joined_close)
    aligned = [
        (timestamp, high_value, low_by_timestamp[timestamp], close_by_timestamp[timestamp])
        for timestamp, high_value in joined_high
    ]
    output: BoolSeries = []
    for index in range(window, len(aligned)):
        previous = aligned[index - window : index]
        timestamp, _, _, close_value = aligned[index]
        previous_high = max(row[1] for row in previous)
        previous_low = min(row[2] for row in previous)
        output.append((timestamp, close_value > previous_high or close_value < previous_low))
    return output


def _local_name(name: str, prefix: str) -> str:
    if name.startswith("core."):
        name = name.removeprefix("core.")
    if name.startswith(prefix):
        return name.removeprefix(prefix)
    raise TokenReferenceError(
        "QST_TOKEN_REFERENCE_UNSUPPORTED",
        f"Expected token name with prefix {prefix}: {name}",
    )


def _expect_args(token: str, args: tuple[Any, ...], count: int) -> tuple[Any, ...]:
    if len(args) != count:
        raise TokenReferenceError(
            "QST_TOKEN_ARITY_INVALID",
            f"{token} expected {count} argument(s), got {len(args)}.",
        )
    return args


def _iter_values(raw_values: Any) -> Iterable[Any]:
    if isinstance(raw_values, (str, bytes)):
        raise TokenReferenceError(
            "QST_TOKEN_INPUT_TYPE_INVALID",
            "Reduction input must be an iterable of values.",
        )
    try:
        iter(raw_values)
    except TypeError as exc:
        raise TokenReferenceError(
            "QST_TOKEN_INPUT_TYPE_INVALID",
            "Reduction input must be an iterable of values.",
        ) from exc
    return cast(Iterable[Any], raw_values)


def _coerce_number(value: Any, *, allow_nonfinite: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TokenReferenceError(
            "QST_TOKEN_NUMERIC_TYPE_INVALID",
            "Numeric token input must be int or float, not bool.",
        )
    result = float(value)
    if not allow_nonfinite and not math.isfinite(result):
        raise TokenReferenceError(
            "QST_TOKEN_NUMERIC_NONFINITE",
            "Numeric token input must be finite.",
        )
    return result


def _coerce_int_param(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TokenReferenceError(
            "QST_TOKEN_PARAM_TYPE_INVALID",
            f"{name} must be an integer.",
        )
    return value


def _coerce_bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise TokenReferenceError(
            "QST_TOKEN_BOOL_TYPE_INVALID",
            "Boolean token input must be bool.",
        )
    return value


def _finite_result(value: float) -> float:
    if not math.isfinite(value):
        raise TokenReferenceError(
            "QST_TOKEN_NUMERIC_NONFINITE",
            "Numeric token output must be finite.",
        )
    return value


@overload
def _numeric_series(series: Sequence[SeriesRow], *, allow_none: Literal[False] = False) -> NumericSeries:
    ...


@overload
def _numeric_series(series: Sequence[SeriesRow], *, allow_none: Literal[True]) -> list[tuple[str, float | None]]:
    ...


def _numeric_series(series: Sequence[SeriesRow], *, allow_none: bool = False) -> Any:
    rows = _series_rows(series)
    output: list[tuple[str, float | None]] = []
    for timestamp, value in rows:
        if value is None and allow_none:
            output.append((timestamp, None))
        else:
            output.append((timestamp, _coerce_number(value)))
    return output


def _series_rows(series: Sequence[SeriesRow]) -> list[SeriesRow]:
    rows: list[SeriesRow] = []
    seen: set[str] = set()
    for raw_timestamp, value in series:
        if not isinstance(raw_timestamp, str) or not raw_timestamp:
            raise TokenReferenceError(
                "QST_TOKEN_SERIES_TIMESTAMP_INVALID",
                "Series timestamp must be a non-empty string.",
            )
        if raw_timestamp in seen:
            raise TokenReferenceError(
                "QST_TOKEN_SERIES_DUPLICATE_TIMESTAMP",
                f"Duplicate timestamp: {raw_timestamp}",
            )
        seen.add(raw_timestamp)
        rows.append((raw_timestamp, value))
    return sorted(rows, key=lambda row: row[0])


def _coerce_hhmm(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise TokenReferenceError(
            "QST_TOKEN_TIME_FORMAT_INVALID",
            f"{name} must use HH:MM format.",
        )
    hour, minute = value.split(":")
    if not hour.isdigit() or not minute.isdigit():
        raise TokenReferenceError("QST_TOKEN_TIME_FORMAT_INVALID", f"{name} must use HH:MM format.")
    if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        raise TokenReferenceError("QST_TOKEN_TIME_FORMAT_INVALID", f"{name} must be a valid time.")
    return value


def _timestamp_hhmm(timestamp: str) -> str:
    if "T" not in timestamp:
        raise TokenReferenceError(
            "QST_TOKEN_SERIES_TIMESTAMP_INVALID",
            "Timestamp must contain a T separator for session filtering.",
        )
    time_part = timestamp.split("T", 1)[1]
    if len(time_part) < 5:
        raise TokenReferenceError(
            "QST_TOKEN_SERIES_TIMESTAMP_INVALID",
            "Timestamp time component must include HH:MM.",
        )
    return _coerce_hhmm(time_part[:5], "timestamp")


def _window_params(params: dict[str, Any]) -> tuple[int, int]:
    window = _coerce_int_param(params.get("window"), "window")
    if window <= 0:
        raise TokenReferenceError("QST_TOKEN_WINDOW_INVALID", "window must be positive.")
    raw_min_periods = params.get("min_periods", window)
    min_periods = _coerce_int_param(raw_min_periods, "min_periods")
    if min_periods <= 0:
        raise TokenReferenceError("QST_TOKEN_WINDOW_INVALID", "min_periods must be positive.")
    return window, min_periods


def _population_std(values: Sequence[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _rsi_from_avgs(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0 and avg_loss == 0:
        return 50
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)
