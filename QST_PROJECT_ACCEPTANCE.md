# QST Project-Wide Acceptance

Date: 2026-05-15

Acceptance standard: `acceptance-plan/0.1.1`

## Acceptance Baselines

- Code freeze baseline: `1ede6998bf442c22102b6a83530ef89a0cdadaaa`
- Final acceptance commit: the docs/status-only commit that contains this record
- Branch: `main`
- Working tree at G0: clean
- Acceptance operator: Codex
- Acceptance window: 2026-05-15 through 2026-05-22

The final acceptance commit contains documentation, evidence, and status updates only. It does not change code, schemas, hash algorithms, token semantics, runtime behavior, adapter behavior, or the custom-token trust model after the code freeze baseline.

## Status

QST project-wide acceptance is completed for the accepted foundation present at the code freeze baseline.

Accepted project scope:

- P0 frozen primitive baseline.
- P1-core and P1-extended-a guarded validation.
- P2 provenance, mutation, CSE, kernel-substitution spike, and explain tooling.
- P3 lock, qstpkg, package verification, agent search/discover, and fork lineage.
- P4-core artifacts, frames, qstpkg artifact extension, ports, signal extraction, mock adapters, and P4b CLI.
- Token System v2 WP0-WP10.

Out of accepted scope:

- Full v0.4 runtime execution engine.
- Complete v0.4 authoring CLI.
- Real vectorbt / qlib / ccxt / mlflow / backtrader adapters.
- Production trading integration.
- Sandboxed custom-token execution.
- Bit-exact numerical engine.
- Portfolio optimizer.
- P4b-v2 external ports.
- Plugin marketplace, MCP server, P5 experimental mutation, and RL.

## Gate Summary

| Gate | Result | Evidence |
|---|---|---|
| G0 Acceptance freeze | PASS | Code freeze baseline recorded; working tree clean. |
| G1 Engineering baseline | PASS | Ruff, mypy, stateless lint, and coverage gate pass with coverage above 90%. |
| G2 Legacy compatibility | PASS | P0-P4 compatibility tests and frozen hash checks pass. |
| G3 Architecture and phase integrity | PASS | Roadmap, ADRs, migration boundary, and active/legacy IR roles are consistent. |
| G4 Token System v2 modules | PASS | WP0-WP10 module tests pass. |
| G5 Hash/schema/artifact stability | PASS | See `docs/ACCEPTANCE/HASH_STABILITY_REPORT.md`. |
| G6 Security and trust boundary | PASS | See `docs/ACCEPTANCE/SECURITY_BOUNDARY_REPORT.md`. |
| G7 CLI behavior | PASS | Legacy hash/vocabulary CLI and v0.4 migration/token help surfaces pass. |
| G8 Documentation consistency | PASS | README, roadmap, changelog, ADRs, and acceptance docs describe the accepted state. |
| G9 Dogfooding / reference strategies | PASS | PV-A, PV-B, PV-C, and PV-D artifacts are tested and hash-pinned. |
| G10 Ecosystem readiness | PASS | TokenPack, qstpkg, migration, and adapter boundaries are usable without importing business frameworks. |
| G11 Feasibility review | PASS | QST is coherent as a typed, temporal-safe, state-aware, panel-capable, custom-token-extensible IR/package foundation. |
| G12 Final sign-off | PASS | Required acceptance artifacts are committed. |

## Local Gate Evidence

Required local commands pass on the final docs/status-only acceptance commit:

- `python -m ruff check .`
- `python -m mypy quant_strategy_tokenizer`
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=90`
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`
- `python -m pytest tests/e2e/test_p2_p3_backward_compat.py -v`
- `python -m pytest tests/e2e -k "backward or compat or hash_not_drift" -v`
- `python -m pytest tests/package -v`
- Token System v2 module gates for `ir_v04`, `hash_v2`, `types_v2`, `ports_v2`, `tokens_v2`, `profile_v2`, `numeric_v2`, `token_evolution_v2`, `validation_v2`, `state_v2`, `decision_v2`, `panel_v2`, `custom_runtime_v2`, and `migration_v2`.
- P-Validate gates for temporal, state, panel, and custom-token reference cases.
- Legacy hash CLI checks for `kdj_cross_basic.qst.yaml` and `examples_kdj_with_ema_filter.qst.yaml`.
- `python -m compileall quant_strategy_tokenizer`
- `python -m pip check`
- Python forbidden business-framework import check.

Accepted coverage floor: 90%.

## Frozen Hash Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Final Declaration

QST project-wide acceptance is completed at the final docs/status-only acceptance commit.

P0-P4 accepted foundations remain preserved. Token System v2 WP0-WP10 are accepted. The active token-kernel target is `qst-ir/0.4`. Legacy `qst-ir/0.3` and `qst-ir/0.3.1` remain loadable, verifiable, explainable, and migratable. Future changes to accepted v0.4 hash, schema, token, package, or security semantics require a new ADR or work package.
