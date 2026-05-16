# QST Coverage System

This directory defines how QST measures strategy record-layer coverage. Coverage here
means expression, validation, canonicalization, hashing, and agent authoring evidence for
strategy records. It does not mean broker, exchange, live trading, HFT, full backtest,
portfolio optimizer, or production execution coverage.

## Target Audiences

- Agent developers: can an agent classify, author, repair, and report QST records reliably?
- Quant researchers: can a research strategy be represented as a typed GKR record?
- Audit and compliance users: are claims falsifiable and backed by canonical/hash evidence?
- Ecosystem integrators: where can the record layer be extended without weakening trust?

## Coverage Scope

QST reports multiple coverage views instead of one undifferentiated percentage:

- internal benchmark coverage
- external benchmark coverage
- user-submitted coverage
- dogfood coverage
- direct built-in GKR coverage
- partial record coverage
- custom-token route coverage
- false-supported rate
- kernel-gap count

The system optimizes honest record-layer coverage and a low false-supported rate, not the
largest possible supported percentage.

## Governance Protocols

- `coverage_taxonomy.md` defines classes, benchmark groups, and layers.
- `market_weight_protocol.md` defines transparent market-weight scoring.
- `false_supported_protocol.md` defines mechanical, semantic, and boundary false support.
- `custom_token_route_policy.md` caps and discounts custom-token route coverage.
- `kernel_gap_decision_protocol.md` prevents token bloat from hiding kernel gaps.

## PR 1 Stop Condition

This protocol set is the implementation baseline for Coverage Frontier v0.3 PR 1. Do not
expand it into a v0.4 planning exercise before PR 1 produces implementation evidence.
The next useful feedback should come from matrix rows, report tooling, and dogfood cases.

