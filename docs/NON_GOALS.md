# Non-Goals

QST is not:

- a trading bot
- a broker adapter
- an exchange adapter
- a live execution system
- a full backtest engine
- a Qlib runtime replacement
- a qrun launcher
- a model training system
- an inference execution system
- a portfolio optimizer execution engine
- a lossless Qlib converter
- an arbitrary Python strategy parser
- a production risk system
- a profitability claim

All AI4Finance adapters are intentionally read-only. They collect declared plans,
existing results, and artifact identities; they do not execute external systems.

The legacy v0.4 custom executor is not a QST 1.0 feature and is accessible only through
the explicit compatibility namespace.
