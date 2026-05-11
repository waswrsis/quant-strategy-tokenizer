# Strategy Engineering Principles

```text
Apply the following strategy-engineering principles:

1. Strategy logic and production safety are inseparable.
   A profitable signal is not production-ready unless execution, state, error handling, and recovery behavior are correct.

2. Risk semantics must match code semantics.
   If the design says "pause, retry later, then flatten", the code must implement exactly that path, including initialization, retries, cooldowns, and failure exhaustion.

3. Unknown is a first-class state.
   API failure, openOrders blindness, order-history failure, insufficient data, and state ambiguity must be represented explicitly. Do not treat empty results as success unless the source is authoritative.

4. Fail-closed on risk filters.
   If market freeze, MRQ, universe history, exchange restrictions, or execution cleanup cannot be verified, the system should avoid adding new risk.

5. Separate signal, sizing, risk, execution, and state.
   Each module should have clear inputs, outputs, failure semantics, and no hidden global side effects.

6. Live data outranks idealized backtests for production diagnostics.
   Use backtests to understand signal shape and regime exposure, but use live fills, exits, slippage, missed orders, and incident logs to evaluate deployability.

7. State isolation is mandatory.
   Each strategy instance must have explicit strategy_id, instance_id, account_scope, cid_prefix, and schema_version. Missing identity should be treated as unsafe unless migration is explicitly enabled.

8. Critical events require action classes.
   Do not let minor cleanup failures share the same global-flatten threshold as true residual-position failures.

9. Modules should be recomposable.
   A module should accept caller-provided data, normalize reasonable raw inputs, return rich structured output, and avoid exchange calls or file writes unless it is explicitly an adapter module.

10. Every code change requires post-change audit.
    After implementation, check for semantic drift, fail-open regressions, parameter drift, state compatibility, and deployment risk.
```

