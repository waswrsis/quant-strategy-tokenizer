from __future__ import annotations

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput, jsonable_value, normalize_token_output
from quant_strategy_tokenizer.types.decision import Accept, Reject, parse_decision
from quant_strategy_tokenizer.types.frame import validate_frame
from quant_strategy_tokenizer.types.plan import NoopPlan, parse_plan
from quant_strategy_tokenizer.types.series import validate_timeseries


def test_decision_and_plan_parse() -> None:
    decision = parse_decision({"kind": "accept", "reason": "ok"})
    assert isinstance(decision, Accept)
    plan = parse_plan({"kind": "noop", "decision": {"kind": "reject", "reason": "no"}})
    assert isinstance(plan, NoopPlan)
    assert isinstance(plan.decision, Reject)


def test_validate_series_frame_and_output_jsonable() -> None:
    series = validate_timeseries(pd.Series([1.0, None]))
    frame = validate_frame(pd.DataFrame({"close": [1.0]}))
    output = normalize_token_output({"value": series})
    assert isinstance(output, TokenOutput)
    assert jsonable_value(frame) == [{"close": 1.0}]
    assert jsonable_value(output.values["value"]) == [1.0, None]
