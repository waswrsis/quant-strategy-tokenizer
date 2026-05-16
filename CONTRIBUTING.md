# Contributing

QST is an accepted reference kernel. Changes should preserve the final project
boundaries recorded in [QST_PROJECT_ACCEPTANCE.md](QST_PROJECT_ACCEPTANCE.md)
and [TOKEN_SYSTEM_V2_ACCEPTANCE.md](TOKEN_SYSTEM_V2_ACCEPTANCE.md).

## Invariants

- Do not change accepted legacy P0-P4 hash, canonicalization, lock, package,
  runtime, mutation, search, fork, or CLI behavior without an explicit ADR or
  work package.
- Do not change accepted `qst-ir/0.4` schema, hash, TokenSpec, TokenPack,
  temporal, state, decision, panel, custom-token, or migration semantics without
  an explicit ADR or work package.
- Keep custom-token integrity verification free of imports, entry-point loading,
  introspection of custom modules, and execution.
- Keep approvals local. qstpkg contents must not become portable trust.
- Preserve the frozen hash evidence recorded in
  [docs/ACCEPTANCE/HASH_STABILITY_REPORT.md](docs/ACCEPTANCE/HASH_STABILITY_REPORT.md).

## Quality Gates

Run these before committing:

```bash
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=90
```

Focused compatibility checks:

```bash
python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v
python -m pytest tests/package tests/custom_runtime_v2 tests/migration_v2 -v
python -m quant_strategy_tokenizer.cli vocabulary --check
python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml
```

## Registry Rules

- Production code reads legacy token specs through `get_registry()`.
- Production code reads legacy recipes through `get_recipe_registry()`.
- Tests must not mutate global registries.
- Temporary legacy tokens use `isolated_registry`.
- Temporary legacy recipes use `isolated_recipe_registry`.
- Token System v2 work uses `TokenRegistryV2` and TokenPack manifests rather
  than legacy registry internals.

## Documentation Rules

- Keep README focused on current usage and maintenance.
- Keep final acceptance evidence in `QST_PROJECT_ACCEPTANCE.md`,
  `TOKEN_SYSTEM_V2_ACCEPTANCE.md`, and `docs/ACCEPTANCE/`.
- Keep architecture decisions in `docs/ADR/`.
- Avoid reintroducing construction-plan or stage-by-stage acceptance journals
  into the repository root.

## Stateless Lint

Stateless lint is a best-effort guardrail, not a formal effect system. Local
false positives can be disabled with:

```python
# qst-lint: disable-next-line -- deterministic test clock stub
```

The reason after `--` is required for review.
