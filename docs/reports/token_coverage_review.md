# Token Coverage Review

Stage 3B reviews common strategy patterns against the Stage 3A token surface. Reserved-design tokens are not counted as core coverage. Custom-token capability is counted only when the boundary is explicitly custom/external.

## Strategy Pattern Matrix

| Strategy Pattern | Status | Required Families | Missing Piece | Next Action |
|---|---|---|---|---|
| trend following | covered with accepted tokens | data, window, indicator, signal, decision | none | Use demos 01 and 04 as references. |
| mean reversion | covered with accepted tokens | indicator, compare, decision | none | Use demos 02 and 03. |
| breakout | covered with accepted tokens | window, indicator, signal | none | Use demo 04. |
| volatility filter | covered with accepted tokens | window, risk | none | Use risk reference helpers. |
| volatility targeting | covered with accepted tokens | risk, weight | portfolio runtime | Validation/hash only; no rebalance engine. |
| RSI reversal | covered with accepted tokens | indicator, compare, decision | none | Use demo 02. |
| Bollinger mean reversion | covered with accepted tokens | indicator, compare | none | Use demo 03. |
| Donchian breakout | covered with accepted tokens | indicator.channel_breakout, window | none | Use demo 04. |
| KDJ filter | requires custom token | custom_runtime, indicator | built-in KDJ token | Keep as reference strategy/custom token candidate. |
| MACD trend | covered with accepted tokens | indicator.macd, signal, decision | none | PR6 core rule evidence covers the record. |
| stateful cooldown | covered with accepted tokens | gate, state, decision | none | Use demo 05. |
| market freeze | covered with accepted tokens | gate, state, decision | none | Reference facade only. |
| circuit breaker | covered with accepted tokens | gate, state, decision | none | Use demo 06. |
| observe period | covered with accepted tokens | gate, state | none | Reference facade only. |
| cross-sectional top-k | covered with accepted tokens | panel, selection | none | Use demo 07. |
| cross-sectional bottom-k | covered with accepted tokens | panel, selection | none | Use demo 09. |
| market neutral rank | covered with accepted tokens | panel, weight | portfolio runtime | Use demo 08; no optimizer implied. |
| factor residualization | covered with accepted tokens | panel.residualize | none | Use demo 09. |
| group neutralization | covered with accepted tokens | panel.group_demean, factor.sector_neutral_rank | explicit group metadata | PR8 accepts records when GroupSpec metadata is present. |
| risk stop | requires runtime/adapter | risk, decision | position/order state | External boundary unless modeled as custom token. |
| trailing stop | Derived/Recipe Gap | state, window, decision | canonical recipe | P1 recipe/demo candidate. |
| turnover control | covered with accepted tokens | risk.turnover_cap | rebalance runtime | Use demo 11 as validation artifact. |
| rebalance band | Derived/Recipe Gap | risk, state, weight | canonical recipe | P1 recipe/demo candidate. |
| inverse vol weighting | covered with accepted tokens | weight.inverse_vol_weight | none | PR8 record evidence covers inverse-vol weighting without optimizer/rebalance execution. |
| vol target weighting | covered with accepted tokens | risk.volatility_target | portfolio runtime | Use demo 10. |
| optimizer portfolio | covered with experimental tokens | optimizer.mean_variance | solver determinism/runtime | Do not promote before solver contract. |
| execution feedback | requires reserved_design family | execution.* | execution runtime/adapter | Stage 3B classifies as future boundary. |
| custom token transform | covered with accepted tokens | custom_runtime | local approval | Use demo 12. |
| continuous score decision | covered with experimental tokens | score.calibrate, decision | calibration semantics | Keep score.calibrate experimental. |
| event-driven reserved | requires new TypeSpec | event.* | EventStream[T] | Extended TypeSpec candidate. |
| distribution reserved | requires new TypeSpec | distribution.* | Distribution[T] | Extended TypeSpec candidate. |
| instrument metadata screen | requires new TypeSpec | data, event | Instrument/Calendar metadata | Extended TypeSpec or data-model stage. |

## Decision

Most scalar/time-series/state/panel/risk examples are covered with accepted tokens. PR6 retires the MACD token gap, PR7 retires the stale beta-estimator numeric determinism gap, and PR8 retires inverse-vol weighting plus current sector-neutral rank evidence when explicit group metadata is supplied. The largest remaining P0/P1 gaps are recipe demonstrations and future type/data-model boundaries for event, distribution, and instrument metadata.
