# Coverage Frontier Dogfood Target Set

This report records the five-case dogfood target set for Coverage Frontier v0.3.
It extends the PR 4 MVP dogfood case into the publication-target evidence set
without changing QST token, IR, canonical/hash, runtime, prompt, schema, example,
broker, exchange, or strategy execution semantics.

Dogfood evidence remains excluded from headline frontier coverage percentages.
It is reported separately as breadth/depth evidence for the strategy record layer.

## Target Status

| Target | Requirement | Current count | Status |
| --- | ---: | ---: | --- |
| MVP dogfood | >= 1 case | 5 | pass |
| Frontier publication target | >= 5 cases | 5 | pass |

## Cases

| ID | Classification | Candidate GKR | Evidence status |
| --- | --- | --- | --- |
| `dog_001_original_multi_asset_mean_reversion_grid` | `partially_supported` | `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | validate/hash/canonicalize pass |
| `dog_002_single_asset_trend_following_fsm` | `partially_supported` | `tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml` | validate/hash/canonicalize pass |
| `dog_003_cross_sectional_factor_panel` | `partially_supported` | `tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml` | validate/hash/canonicalize pass |
| `dog_004_custom_ml_score_signal` | `custom_token_required` | none | custom-token route only |
| `dog_005_reserved_event_stream_orderbook` | `reserved` | none | reserved-design boundary only |

## Candidate Evidence

| Case | Command | Exit code | Result |
| --- | --- | ---: | --- |
| `dog_002_single_asset_trend_following_fsm` | `python -m qst.cli validate tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml` | 0 | validates |
| `dog_002_single_asset_trend_following_fsm` | `python -m qst.cli hash tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml` | 0 | hashes recorded |
| `dog_002_single_asset_trend_following_fsm` | `python -m qst.cli canonicalize tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml --output .local_audit/single_asset_trend_following_fsm.canonical.json` | 0 | local canonical artifact generated |
| `dog_003_cross_sectional_factor_panel` | `python -m qst.cli validate tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml` | 0 | validates |
| `dog_003_cross_sectional_factor_panel` | `python -m qst.cli hash tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml` | 0 | hashes recorded |
| `dog_003_cross_sectional_factor_panel` | `python -m qst.cli canonicalize tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml --output .local_audit/cross_sectional_factor_panel.canonical.json` | 0 | local canonical artifact generated |

Hashes:

| Case | graph_hash | param_hash | instance_hash |
| --- | --- | --- | --- |
| `dog_002_single_asset_trend_following_fsm` | `sha256:c1b5f1e80ea6c704d0c99b3fb4a89845ad609d12ed67d46a55bc6630c70f7a8d` | `sha256:0303e75b1996ca9da817d3b5fcab550b03fc2381096d849a730073ba04809003` | `sha256:ea3022ae2b93e0494fa81c1fa657a21e37a0882cf1497fdc591e8fa1202d41d4` |
| `dog_003_cross_sectional_factor_panel` | `sha256:66945174c2482b2e9fc9b912e9123eded097ab2278b79b9727540b5cd8ea39f2` | `sha256:3477b9883ee34664e8b9e88d77dc21b0695297333062b3ef56921061bef98e9d` | `sha256:5a753ec93c0787bce9a341c75549122f21e53599dcf74b6e9484850ddf98dbb9` |

## Boundary Notes

- `dog_002_single_asset_trend_following_fsm` records an EMA decision and cooldown
  gate only. Full position FSM lifecycle, broker-side stops, and fill feedback are
  out of scope.
- `dog_003_cross_sectional_factor_panel` records a panel factor ranking and
  weight shell only. Factor construction governance, sector metadata, optimizer,
  rebalance scheduler, broker, and exchange execution are out of scope.
- `dog_004_custom_ml_score_signal` is routed through custom-token governance.
  This report does not import, approve, grant, or execute custom Python.
- `dog_005_reserved_event_stream_orderbook` remains reserved until EventStream,
  OrderBook, and event-time replay runtime layers exist. It must not be faked as
  ordinary time-series coverage.

## Verdict

The dogfood target set is complete for Coverage Frontier v0.3 publication-target
evidence. It does not create or imply runtime execution, backtest, profitability,
broker, exchange, or production trading coverage.
