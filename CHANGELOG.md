# Changelog

## P4a-1c Multi-Symbol Strict Alignment

- Added strict multi-symbol timestamp grid validation for `MarketFrame` OHLCV bars.
- Preserved existing `compute_frame_hash()` material and P4a-1b frame hash evidence.
- Added JSON, CSV, pandas, Arrow, and Parquet regression coverage for aligned and missing market grids.
- Kept sparse market data, `allow_missing`, nullable DecimalString fields, frequency inference, and runtime changes out of scope.

## P4a-0 Artifact Schema Hard Gate

- Added public canonical JSON bytes support while preserving P3 lock byte compatibility.
- Added P4 artifact base models and schemas for execution reports, backtest evidence, portfolio snapshots, and adapter manifests.
- Added strict DecimalString validation and canonical normalization for artifact numeric fields.
- Added artifact identity rules, POSIX relative path checks, raw payload hash pairing, and adapter version policy checks.
- Added P4a-0 artifact schema, canonical JSON, toy e2e, and P2/P3 backward compatibility tests.
