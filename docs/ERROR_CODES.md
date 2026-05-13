# QST Error Codes

This document lists stable validation and runtime error kinds used by P0 and P1-core.

| Code | Layer | Meaning | Typical repair |
|---|---|---|---|
| `missing_token` | validation | A graph node references an unknown token id/version. | Use a registered token or add a compatible token version. |
| `missing_input` | validation/runtime | A node input or external reference cannot be resolved. | Wire the missing upstream output or provide the external input. |
| `type_mismatch` | validation | A node receives a value that does not match its declared token input type. | Insert the expected conversion token, often `decision.lift_bool`. |
| `cycle_detected` | validation/recipe | The graph or recipe expansion contains a cycle. | Break the dependency cycle. |
| `params_schema` | validation | Token params do not match the token parameter schema. | Provide the required params with compatible types. |
| `validation_failed` | runtime | Runtime refused to execute because canonical validation failed. | Inspect validation failures and repair hints. |
| `executor_exception` | runtime | A token executor raised an exception. | Inspect the trace node warning or exception text. |
| `missing_risk_path` | validation | A guarded profile has `plan.order_intent` without an upstream `risk.*` token. | Insert `risk.position_cap` or `risk.notional_cap` before `plan.order_intent`. |
| `profile_violation` | validation | The strategy envelope/profile is inconsistent with P1-core rules. | Adjust `_envelope.profile` or strategy wiring. |

P1-core keeps P0 repair hints compatible. In particular, `strategies/broken_no_lift.qst.yaml` must continue to produce a `type_mismatch` failure with a repair hint suggesting `decision.lift_bool`.
