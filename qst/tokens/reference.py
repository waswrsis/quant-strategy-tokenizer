"""Deterministic reference helpers for primitive token contracts.

These helpers are conformance aids for TokenSpec contracts. They are not a
strategy runtime and are intentionally not called by IR validation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, cast


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
