# Agent Takeover Prompt

You are taking over the local QST `1.0.0a2` agent-provenance candidate. The tagged v0.4
line remains an archived agent-ready research prototype and compatibility baseline.

Treat the repository as a deterministic record, validation, coverage, and
handoff system. QST is not a broker, exchange adapter, live execution engine,
full backtester, profitability engine, or Qlib runtime replacement.

## First Reads

Read these before changing code:

- `README.md`
- `docs/FINAL_HANDOFF.md`
- `docs/FINAL_SCOPE.md`
- `docs/FINAL_ACCEPTANCE.md`
- `docs/rearchitecture/README.md`
- `docs/rearchitecture/ADR-0001-qst-1.0-product-redefinition.md`
- `docs/agent/README.md`
- `docs/agent/prompts/qst_stage_3c_v0_3_2/README.md`
- `docs/reports/strategy_coverage_report.md`
- `docs/adapters/QLIB_ADAPTER_BOUNDARY.md`
- `docs/adapters/QLIB_ADAPTER_GUIDE.md`

## Current Facts

- Python import package: `qst`.
- Distribution name: `quant-strategy-tokenizer`.
- Editable strategy files: `.gkr.yaml`.
- Internal schemas: `qst-ir/0.4` and `qst-canonical/0.4`.
- Qlib partial adapter proof command: `qst adapter qlib import`.
- Legacy custom runtime command namespace: `qst compat-v04 token`.
- Adapter-local refs use the `adapter` namespace and are not built-in token
  vocabulary.

## Operating Rules

- Run repo evidence commands before making broad claims.
- Do not invent unavailable CLI commands.
- Do not claim runtime execution, qrun execution, model training, inference,
  backtesting, broker integration, exchange integration, live execution, or
  lossless Qlib conversion.
- Never treat the v0.4 compatibility executor as a QST 1.0 capability.
- Keep draft, validation, human approval, publication, and activation separate.
- Preserve coverage taxonomy classifications and reserved/non-goal boundaries.

## Minimal Smoke Commands

```bash
python -m qst.cli vocabulary --check
python -m qst.cli validate examples/strategies/kdj_cross_basic.gkr.yaml
python -m qst.cli hash examples/strategies/kdj_cross_basic.gkr.yaml
python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check
python -m qst.cli adapter qlib import examples/adapters/qlib/workflow_config_lightgbm_alpha158.yaml --output .local_audit/qlib_lightgbm_alpha158.gkr.yaml --coverage .local_audit/qlib_lightgbm_alpha158.coverage.json
```

If a command cannot run, record the command, environment, error, and whether
the limitation blocks the requested task.
