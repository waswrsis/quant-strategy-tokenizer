"""Reference fuzzing harness for P2a-3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict

from quant_strategy_tokenizer.composition.contract import execute_recipe_instance

CI_STANDARD_CASES = 1000
DEFAULT_SEED = 20260514


class FuzzingReport(BaseModel):
    """Deterministic reference fuzzing report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recipe: str
    version: int
    profile: Literal["ci_standard"]
    seed: int
    cases: int
    failed: int
    max_abs_error: float
    output_digest: str


def reference_ewm(series: pd.Series, *, span: int, init: float | str = "first_value") -> pd.Series:
    """Independent EWM reference used by P2a-3 checks."""

    values = pd.Series(series, dtype=float)
    if values.empty:
        return values
    alpha = 2.0 / (float(span) + 1.0)
    out: list[float] = []
    if init == "first_value":
        first_valid = values.dropna()
        prev = float(first_valid.iloc[0]) if not first_valid.empty else np.nan
    else:
        prev = float(init)

    for raw in values:
        x = float(raw) if pd.notna(raw) else np.nan
        if np.isnan(x):
            out.append(prev)
            continue
        if init == "first_value" and not out and pd.notna(values.iloc[0]):
            prev = x
        else:
            prev = alpha * x + (1.0 - alpha) * prev
        out.append(prev)
    return pd.Series(out, index=values.index, dtype=float)


def _case_series(rng: np.random.Generator) -> pd.Series:
    length = int(rng.integers(3, 64))
    values = rng.normal(loc=0.0, scale=50.0, size=length)
    mask = rng.random(length) < 0.08
    values[mask] = np.nan
    return pd.Series(values, dtype=float)


def _jsonable_series(series: pd.Series) -> list[float | None]:
    return [None if pd.isna(item) else round(float(item), 12) for item in series.tolist()]


def run_indicator_ewm_fuzzing(
    *,
    cases: int = CI_STANDARD_CASES,
    seed: int = DEFAULT_SEED,
) -> FuzzingReport:
    """Run deterministic reference fuzzing for indicator.ewm."""

    rng = np.random.default_rng(seed)
    failed = 0
    max_abs_error = 0.0
    digest_parts: list[dict[str, Any]] = []

    for _ in range(cases):
        series = _case_series(rng)
        span = int(rng.integers(1, 64))
        init: float | str = "first_value"
        if bool(rng.integers(0, 2)):
            init = float(rng.normal(loc=0.0, scale=5.0))

        actual = execute_recipe_instance(
            "indicator.ewm",
            params={"span": span, "init": init},
            inputs={"series": series},
        )["value"]
        expected = reference_ewm(series, span=span, init=init)
        actual_arr = actual.to_numpy(dtype=float, na_value=np.nan)
        expected_arr = expected.to_numpy(dtype=float, na_value=np.nan)
        if not np.allclose(actual_arr, expected_arr, atol=1e-9, equal_nan=True):
            failed += 1
        finite_error = np.nan_to_num(np.abs(actual_arr - expected_arr), nan=0.0)
        max_abs_error = max(max_abs_error, float(finite_error.max(initial=0.0)))
        digest_parts.append(
            {
                "span": span,
                "init": init,
                "series": _jsonable_series(series),
                "output": _jsonable_series(actual),
            }
        )

    payload = json.dumps(digest_parts, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return FuzzingReport(
        recipe="indicator.ewm",
        version=1,
        profile="ci_standard",
        seed=seed,
        cases=cases,
        failed=failed,
        max_abs_error=max_abs_error,
        output_digest=digest,
    )


def load_fuzzing_report(path: str | Path) -> FuzzingReport:
    """Load a stored fuzzing report."""

    return FuzzingReport.model_validate_json(Path(path).read_text(encoding="utf-8"))


def check_fuzzing_meets_threshold(path: str | Path, profile: str = "ci_standard") -> bool:
    """Return whether the stored report meets and reproduces the requested threshold."""

    if profile != "ci_standard":
        raise ValueError(f"unsupported fuzzing profile: {profile}")
    report = load_fuzzing_report(path)
    if report.recipe != "indicator.ewm" or report.version != 1:
        return False
    if report.profile != "ci_standard" or report.cases < CI_STANDARD_CASES or report.failed != 0:
        return False
    reproduced = run_indicator_ewm_fuzzing(cases=report.cases, seed=report.seed)
    return (
        reproduced.failed == report.failed
        and reproduced.max_abs_error == report.max_abs_error
        and reproduced.output_digest == report.output_digest
    )
