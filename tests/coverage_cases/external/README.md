# External Coverage Case Seeds

This directory contains PR 2 seed fixtures for the Coverage Frontier external benchmark.
They are not executable tests and are not loaded by pytest in PR 2.

The fixtures describe only extracted strategy intent, source id, matrix pattern id, and
expected classification. PR 3 owns validator and report tooling.

Files:

- `external_benchmark_seed.yaml`: lightweight fixture manifest for the 20 external
  benchmark rows in `docs/reports/strategy_coverage_matrix.yaml`.
