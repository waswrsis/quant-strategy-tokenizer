from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quant_strategy_tokenizer.ir.model import ExternalSpec, GraphNode, StrategyIR
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry
from quant_strategy_tokenizer.tokens.registry import RegisteredToken, Registry
from quant_strategy_tokenizer.tokens.spec import TemporalSpec, TokenSpec


def _noop_executor(**_: Any) -> object:
    return object()


def make_token(
    token_id: str,
    *,
    purity: str = "pure",
    temporal: dict[str, Any] | None = None,
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    executor: Callable[..., object] = _noop_executor,
) -> RegisteredToken:
    return RegisteredToken(
        spec=TokenSpec(
            id=token_id,
            layer="computation" if token_id.startswith("test.") else "infrastructure",
            category=token_id.split(".", 1)[0],
            state_tag="stateless",
            purity=purity,  # type: ignore[arg-type]
            inputs=inputs or {},
            outputs=outputs or {"decision": "Decision"},
            temporal=TemporalSpec.model_validate(
                temporal
                or {
                    "uses_future_data": False,
                    "window_mode": "none",
                    "output_available_at": "same_bar_close",
                    "max_lookback": None,
                }
            ),
            failure_policy={},
        ),
        executor=executor,
    )


def make_policy_registry(token: RegisteredToken) -> Registry:
    registry = Registry()
    registry.register(token)
    registry.register(
        make_token(
            "risk.position_cap",
            purity="contextual_read",
            inputs={"decision": "Decision", "state": "State"},
            outputs={"decision": "Decision"},
        )
    )
    registry.register(
        make_token(
            "plan.order_intent",
            purity="contextual_read",
            inputs={"decision": "Decision", "sizing": "Number"},
            outputs={"plan": "Plan"},
        )
    )
    return registry


def make_pretrade_ir(token_id: str = "test.signal") -> StrategyIR:
    return StrategyIR(
        ir_version="qst-ir/0.3",
        canonical_version="qst-canonical/0.1",
        strategy="validator_policy_case",
        strategy_version=1,
        form="canonical",
        externals={
            "state": ExternalSpec(type="State", required=True),
            "sizing": ExternalSpec(type="Number", required=True),
        },
        recipes=[],
        graph=[
            GraphNode(id="n0", token=token_id, v=1, params={}, inputs={}),
            GraphNode(
                id="n1",
                token="risk.position_cap",
                v=1,
                params={"max_position": 1, "symbol_key": "current_symbol"},
                inputs={"decision": "n0.decision", "state": "$externals.state"},
            ),
            GraphNode(
                id="n2",
                token="plan.order_intent",
                v=1,
                params={"side": "long"},
                inputs={"decision": "n1.decision", "sizing": "$externals.sizing"},
            ),
        ],
        outputs={"plan": "n2.plan"},
    )


def make_research_ir(token_id: str = "test.signal") -> StrategyIR:
    return StrategyIR(
        ir_version="qst-ir/0.3",
        canonical_version="qst-canonical/0.1",
        strategy="validator_policy_case",
        strategy_version=1,
        form="canonical",
        externals={},
        recipes=[],
        graph=[GraphNode(id="n0", token=token_id, v=1, params={}, inputs={})],
        outputs={"decision": "n0.decision"},
    )


def empty_recipe_registry() -> RecipeRegistry:
    return RecipeRegistry()
