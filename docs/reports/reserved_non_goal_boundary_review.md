# Reserved / Non-Goal Boundary Review

This PR11 review hardens the Coverage Frontier boundary evidence for strategy
patterns that QST must not present as executable, partial, or custom-token
coverage. It does not add EventStream, Distribution, Calendar, OrderBook,
optimizer solver, broker, exchange, live execution, or backtest runtime support.

## Evidence

- Matrix: `docs/reports/strategy_coverage_matrix.yaml`
- Boundary manifest: `tests/coverage_cases/reserved_non_goal_boundaries/boundary_cases.yaml`
- Report tool section: `docs/reports/strategy_coverage_report.md`

## Boundary Rules

- `reserved` means future design boundary. The row may become addressable only
  through an explicit future TypeSpec, runtime, or solver-determinism stage.
- `non_goal` means outside QST scope. The row must not be weakened into partial,
  custom-token, or supported coverage.
- Boundary false support is any supported, partial, or custom-token row that
  hides EventStream, OrderBook, HFT, Distribution, optimizer solver, broker,
  exchange, live order routing, or full backtest engine requirements.

## Reserved Rows

| Row | Boundary class | Diagnostic class | Future stage | Reason |
| --- | --- | --- | --- | --- |
| `int_071_optimizer_mean_variance` | optimizer_solver | optimizer_solver_contract_required | optimizer_solver_contract | Requires deterministic optimizer solver contract/runtime. |
| `int_072_event_join_asof` | event_stream | reserved_event_stream_required | extended_typespec_eventstream | Requires EventStream runtime/type. |
| `int_073_event_filter` | event_stream | reserved_event_stream_required | extended_typespec_eventstream | Requires EventStream runtime/type. |
| `int_074_distribution_normal_fit` | distribution | reserved_distribution_required | extended_typespec_distribution | Requires Distribution type/runtime. |
| `int_075_distribution_quantile` | distribution | reserved_distribution_required | extended_typespec_distribution | Requires Distribution type/runtime. |
| `int_079_order_book_imbalance` | order_book_event_stream | order_book_event_runtime_not_supported | extended_typespec_orderbook | Requires order-book event runtime. |
| `int_080_hft_latency_arbitrage` | hft_runtime | reserved_hft_runtime_required | extended_typespec_eventstream | Requires HFT runtime. |
| `ext_015_earnings_event_drift` | event_stream | reserved_event_stream_required | extended_typespec_eventstream | Requires event stream data/runtime. |
| `ext_016_order_book_imbalance` | order_book_event_stream | order_book_event_runtime_not_supported | extended_typespec_orderbook | Requires order-book event runtime. |
| `ext_019_distribution_var` | distribution | reserved_distribution_required | extended_typespec_distribution | Requires Distribution type/runtime. |
| `ext_020_portfolio_optimizer` | optimizer_solver | optimizer_solver_contract_required | optimizer_solver_contract | Requires optimizer solver contract/runtime. |
| `dog_005_reserved_event_stream_orderbook` | order_book_event_stream | order_book_event_runtime_not_supported | extended_typespec_orderbook | Requires EventStream, OrderBook, and event-time replay runtime. |

## Non-Goal Rows

| Row | Boundary class | Diagnostic class | Future stage | Reason |
| --- | --- | --- | --- | --- |
| `int_076_execution_submit_order` | broker_execution | broker_execution_non_goal | non_goal | Requires live broker/exchange order submission. |
| `int_077_execution_cancel_order` | broker_execution | broker_execution_non_goal | non_goal | Requires live broker/exchange order cancellation. |
| `int_078_execution_fill_report` | execution_feedback | execution_feedback_runtime_non_goal | non_goal | Requires execution feedback runtime. |
| `ext_017_live_broker_execution` | broker_execution | broker_execution_non_goal | non_goal | Requires live broker order placement. |
| `ext_018_exchange_market_making` | exchange_routing | exchange_routing_non_goal | non_goal | Requires exchange routing and live quote management. |

## Negative Fixture Classes

The manifest records negative intent fixtures for:

- EventStream intraday logic
- order-book replay and imbalance logic
- HFT latency arbitrage
- same-bar execution feedback
- Distribution / VaR style modeling
- optimizer solver allocation
- live broker execution
- exchange order routing
- full backtest engine requests

These fixtures are evidence for classification boundaries only. They are not
strategy fixtures and are not executable GKR examples.

## Decision

PR11 accepts no implementation fix. The required action is governance hardening:
reserved and non-goal rows must have explicit manifest evidence, stable
diagnostic classes, and report visibility. Future stages may address EventStream,
Distribution, OrderBook, or optimizer solver contracts through explicit design
work; broker/exchange/live execution/backtest capabilities remain non-goals for
QST.
