"""TokenPack metadata for WP7 Decision Algebra."""

from __future__ import annotations

from typing import Literal

from quant_strategy_tokenizer.ir_v04 import TokenRefV04
from quant_strategy_tokenizer.numeric_v2 import NumericPolicy
from quant_strategy_tokenizer.ports_v2 import InputSpec, OutputSpec
from quant_strategy_tokenizer.tokens_v2 import TokenPackManifestV2, TokenRiskSpec, TokenSpecV2
from quant_strategy_tokenizer.types_v2 import parse_type_spec

DECISION_ALGEBRA_PACK_ID = "qst-tokenpack-decision-algebra"
DECISION_ALGEBRA_PACK_VERSION = "0.1.0"

DecisionAlgebraCategory = Literal["fold_policy", "monoid", "aggregator"]


def decision_algebra_token_pack_v2() -> TokenPackManifestV2:
    """Return the WP7 core TokenPack metadata for Decision Algebra."""

    return TokenPackManifestV2(
        pack_id=DECISION_ALGEBRA_PACK_ID,
        version=DECISION_ALGEBRA_PACK_VERSION,
        namespaces=("core",),
        tokens=(
            _decision_token_spec("decision.any_accept", "monoid"),
            _decision_token_spec("decision.majority", "aggregator"),
            _decision_token_spec("decision.permissive_and", "fold_policy"),
            _decision_token_spec("decision.quorum", "aggregator"),
            _decision_token_spec("decision.strict_and", "fold_policy"),
            _decision_token_spec("decision.unknown_propagating_and", "monoid"),
            _decision_token_spec("decision.weighted_vote", "aggregator"),
        ),
        origin_tier="core",
    )


def _decision_token_spec(name: str, category: DecisionAlgebraCategory) -> TokenSpecV2:
    return TokenSpecV2(
        token_id=f"core.{name}",
        token_ref=TokenRefV04(
            namespace="core",
            name=name,
            version=1,
            behavior_version=1,
        ),
        version=1,
        behavior_version=1,
        origin_tier="core",
        inputs={"decisions": InputSpec(type=parse_type_spec("EventStream[object]"))},
        outputs={"decision": OutputSpec(type=parse_type_spec("Decision"))},
        params_schema=_params_schema(category),
        purity="pure",
        state={
            "decision_algebra": True,
            "category": category,
            "wp": "WP7",
        },
        numeric_policy=NumericPolicy(
            representation="decimal",
            deterministic_level="semantic",
            reduction_order="fixed_input_order",
            nan_policy="reject",
            inf_policy="reject",
        ),
        risk=TokenRiskSpec(risk_level="low"),
        tests=[
            {
                "kind": "reference_helper",
                "deterministic": True,
            }
        ],
    )


def _params_schema(category: DecisionAlgebraCategory) -> dict[str, object]:
    if category == "aggregator":
        return {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "score_policy": {
                    "enum": ["ignore", "weight_only", "score_times_weight"],
                },
                "unknown_policy": {"enum": ["abstain"]},
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score_policy": {"enum": ["max_annotation", None]},
        },
    }
