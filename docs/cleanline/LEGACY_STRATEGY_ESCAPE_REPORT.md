# Legacy Strategy Escape Report

Date: 2026-05-16 UTC

## Summary

Known repository `qst-ir/0.3` strategies were scanned before removing migration tooling. All repository strategies found by the scan migrated successfully through the WP10 migration API to `qst-ir/0.4` snapshots under `docs/cleanline/migrated_strategies/`.

The public `qst migrate-ir` command was also probed and failed while writing a deep migration report through the legacy canonical JSON depth gate. This failure is recorded as evidence that the bridge was crossed using the underlying migration API before deleting the migration CLI.

## Repository Scan

Source file: `docs/cleanline/LEGACY_STRATEGY_SCAN.txt`

Migrated repository strategies:

- `strategies/kdj_cross_basic.qst.yaml`
- `strategies/examples_kdj_with_ema_filter.qst.yaml`
- `strategies/examples_kdj_with_ema_filter.pretrade.qst.yaml`
- `strategies/uses_ewm_with_provenance.qst.yaml`
- `strategies/uses_cse_duplicate_chain.qst.yaml`
- `strategies/broken_no_lift.qst.yaml`

Migration details and target hashes are recorded in `docs/cleanline/LEGACY_STRATEGY_MIGRATION_RESULTS.json`.

## Workspace Scan

Additional old strategies found outside this repository were duplicates in `QST_P0_CONSTRUCTION_WORKSPACE`:

- `QST_P0_CONSTRUCTION_WORKSPACE/strategies/kdj_cross_basic.qst.yaml`
- `QST_P0_CONSTRUCTION_WORKSPACE/strategies/broken_no_lift.qst.yaml`

They are covered by the repository migrations above and are not copied into the cleanline repository.

## Abandoned Strategies

None.

## Failed Migrations

None through the migration API.

The CLI report writer path failed with `canonical JSON depth exceeds 8` while writing deep migration report material. No strategy was abandoned because of this CLI failure.

## Owner Signoff

All known in-repository `qst-ir/0.3` strategy files have either migrated successfully or are duplicate external workspace samples covered by migrated repository equivalents. Stage R may remove active migration tooling after this report.
