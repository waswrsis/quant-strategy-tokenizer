# External Benchmark Sources

This report records the intent-level sources used for the PR 2 external benchmark seed.
It does not copy source code, trading rules, proprietary datasets, or executable
implementations. Each record is used only to classify a strategy pattern against the
current QST record, token, and boundary model.

Extraction date: 2026-05-17

## Policy

- Use public descriptions only.
- Extract strategy intent, required data shape, and boundary requirements.
- Do not copy proprietary code or parameter sets.
- Treat references as benchmark seeds, not claims of profitability or completeness.
- If a source requires broker, exchange, live execution, HFT runtime, EventStream, or
  Distribution semantics, classify that boundary honestly instead of downgrading it.

## Pattern Source Records

| Pattern id | Category | Classification | Source id | Confidence |
| --- | --- | --- | --- | --- |
| `ext_001_ma_crossover` | `indicator_rule` | `supported` | `src-moving-average-crossover` | high |
| `ext_002_rsi_mean_reversion` | `mean_reversion` | `supported` | `src-mean-reversion` | medium |
| `ext_003_time_series_momentum` | `trend_following` | `supported` | `src-trend-following` | high |
| `ext_004_channel_breakout` | `breakout` | `supported` | `src-trend-following` | medium |
| `ext_005_pairs_trade` | `mean_reversion` | `custom_token_required` | `src-pairs-trade` | high |
| `ext_006_bollinger_contrarian` | `mean_reversion` | `supported` | `src-bollinger-bands` | high |
| `ext_007_donchian_trend` | `trend_following` | `supported` | `src-trend-following` | medium |
| `ext_008_volatility_target` | `weight_record` | `supported` | `src-time-series-momentum-vol-scaling` | medium |
| `ext_009_cross_sectional_momentum` | `panel_factor` | `supported` | `src-momentum-investing` | high |
| `ext_010_market_neutral_factor` | `panel_factor` | `supported` | `src-pairs-trade` | medium |
| `ext_011_stop_loss_rule` | `state_gate` | `partially_supported` | `src-stop-loss` | high |
| `ext_012_trailing_stop_rule` | `state_gate` | `partially_supported` | `src-stop-loss` | medium |
| `ext_013_ml_classifier_signal` | `custom_model` | `custom_token_required` | `src-ml-trading` | medium |
| `ext_014_sentiment_signal` | `custom_signal` | `custom_token_required` | `src-sentiment-trading` | medium |
| `ext_015_earnings_event_drift` | `reserved_event_stream` | `reserved` | `src-event-driven` | high |
| `ext_016_order_book_imbalance` | `reserved_event_stream` | `reserved` | `src-order-book` | high |
| `ext_017_live_broker_execution` | `non_goal_execution` | `non_goal` | `src-trading-strategy` | high |
| `ext_018_exchange_market_making` | `non_goal_execution` | `non_goal` | `src-market-making` | high |
| `ext_019_distribution_var` | `custom_model` | `reserved` | `src-value-at-risk` | high |
| `ext_020_portfolio_optimizer` | `weight_record` | `reserved` | `src-portfolio-optimization` | high |

## Shared Source Records

### src-moving-average-crossover

source_type: `public_reference`

title: Moving average crossover

reference: https://en.wikipedia.org/wiki/Moving_average_crossover

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted the common fast/slow moving-average
crossover pattern and mapped it to QST moving-average plus crossing-token surface.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_001_ma_crossover`

### src-mean-reversion

source_type: `public_reference`

title: Mean reversion in finance

reference: https://en.wikipedia.org/wiki/Mean_reversion_(finance)

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted timing around reversion to an average
or range; specific implementation variants remain matrix rows, not copied algorithms.

license_notes: Public web reference; no source code copied.

confidence: medium

used_by: `ext_002_rsi_mean_reversion`

### src-trend-following

source_type: `public_reference`

title: Trend following

reference: https://en.wikipedia.org/wiki/Trend_following

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted trend continuation and channel-breakout
families, not any proprietary trading system.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_003_time_series_momentum`, `ext_004_channel_breakout`,
`ext_007_donchian_trend`

### src-pairs-trade

source_type: `public_reference`

title: Pairs trade

reference: https://en.wikipedia.org/wiki/Pairs_trade

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted pair-spread convergence and market-neutral
record patterns. Cointegration/spread model details are treated as custom-token route material.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_005_pairs_trade`, `ext_010_market_neutral_factor`

### src-bollinger-bands

source_type: `public_reference`

title: Bollinger Bands

reference: https://en.wikipedia.org/wiki/Bollinger_Bands

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted band touch and band breakout record
families; no parameter claims are copied.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_006_bollinger_contrarian`

### src-time-series-momentum-vol-scaling

source_type: `public_literature`

title: Time-series momentum and volatility scaling pattern

reference: Moskowitz, Ooi, and Pedersen, "Time Series Momentum", Journal of Financial
Economics, 2012.

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted generic own-return momentum and
volatility scaling as record-level concepts. No portfolio construction recipe or dataset
is copied.

license_notes: Bibliographic reference only; no source code copied.

confidence: medium

used_by: `ext_008_volatility_target`

### src-momentum-investing

source_type: `public_reference`

title: Momentum investing

reference: https://en.wikipedia.org/wiki/Momentum_investing

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted cross-sectional ranking by recent
returns as a record pattern.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_009_cross_sectional_momentum`

### src-stop-loss

source_type: `public_reference`

title: Stop-loss order and stop rule pattern

reference: https://en.wikipedia.org/wiki/Order_(exchange)

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted stop-loss and trailing-stop intent.
Broker-side stop placement is classified as outside QST record execution support.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_011_stop_loss_rule`, `ext_012_trailing_stop_rule`

### src-ml-trading

source_type: `public_literature`

title: Model-generated trading signal pattern

reference: Lopez de Prado, "Advances in Financial Machine Learning", Wiley, 2018.

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted the need to route model-generated
signals through an external/custom model boundary.

license_notes: Bibliographic reference only; no source code copied.

confidence: medium

used_by: `ext_013_ml_classifier_signal`

### src-sentiment-trading

source_type: `public_reference`

title: Sentiment analysis as a signal extraction pattern

reference: https://en.wikipedia.org/wiki/Sentiment_analysis

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted text/news sentiment as an external
feature-generation boundary.

license_notes: Public web reference; no source code copied.

confidence: medium

used_by: `ext_014_sentiment_signal`

### src-event-driven

source_type: `public_reference`

title: Event-driven investing

reference: https://en.wikipedia.org/wiki/Event-driven_investing

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted event-triggered strategy records.
EventStream type/runtime requirements are classified as reserved design.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_015_earnings_event_drift`

### src-order-book

source_type: `public_reference`

title: Order book

reference: https://en.wikipedia.org/wiki/Order_book

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted order-book imbalance as an event stream
and market microstructure boundary.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_016_order_book_imbalance`

### src-trading-strategy

source_type: `public_reference`

title: Algorithmic trading and live execution boundary

reference: https://en.wikipedia.org/wiki/Algorithmic_trading

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted live broker/exchange execution as a
non-goal when the strategy record requires order placement.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_017_live_broker_execution`

### src-market-making

source_type: `public_reference`

title: Market maker

reference: https://en.wikipedia.org/wiki/Market_maker

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted quote placement and inventory management
as live exchange behavior outside QST record coverage.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_018_exchange_market_making`

### src-value-at-risk

source_type: `public_reference`

title: Value at risk

reference: https://en.wikipedia.org/wiki/Value_at_risk

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted quantile/distribution risk model
requirements and mapped Distribution semantics to reserved design.

license_notes: Public web reference; no source code copied.

confidence: high

used_by: `ext_019_distribution_var`

### src-portfolio-optimization

source_type: `public_literature`

title: Mean-variance portfolio optimization

reference: Markowitz, "Portfolio Selection", Journal of Finance, 1952.

extraction_date: 2026-05-17

extraction_method: Intent summary only. Extracted solver-backed mean-variance allocation
as reserved until deterministic solver contracts exist.

license_notes: Bibliographic reference only; no source code copied.

confidence: high

used_by: `ext_020_portfolio_optimizer`

## Missing Categories

No required PR 2 external category is intentionally missing. Categories with weak or
heterogeneous public references are marked medium confidence rather than upgraded to high.
