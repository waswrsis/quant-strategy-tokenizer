from __future__ import annotations

import pytest
from pydantic import ValidationError

from quant_strategy_tokenizer.runtime.signal_extraction import SignalExtractionPolicy


def test_signal_extraction_policy_defaults() -> None:
    policy = SignalExtractionPolicy()

    assert policy.output_node_name == "plan"
    assert policy.decision_to_signal == "accept_as_long"
    assert policy.plan_to_signal == "order_intent_side"
    assert policy.score_threshold is None
    assert policy.active_size == "1"
    assert policy.market_external_name == "market"
    assert policy.profile == "research"
    assert policy.multi_symbol_policy == "long_format"


@pytest.mark.parametrize("bad_size", ["1.0", "0.10", "-0"])
def test_signal_extraction_policy_active_size_is_decimal_string(bad_size: str) -> None:
    with pytest.raises(ValidationError):
        SignalExtractionPolicy(active_size=bad_size)
