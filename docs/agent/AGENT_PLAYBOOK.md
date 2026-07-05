# Agent Playbook

## Operating Sequence

1. Inspect `git status --short`, branch, HEAD, and relevant local changes.
2. Classify the task as strategy identity, evidence collection, receipt construction,
   claim evaluation, authority governance, token work, adapter work, or compatibility.
3. Read the narrow guide for that task. Do not load the v0.4 prompt pack as QST 1.0
   governance authority.
4. Preserve the separation between fact, evidence, receipt, claim, approval, activation,
   and execution.
5. Make the smallest scoped change and add negative-path tests.
6. Run focused tests, then shared gates when a public model or workflow changes.
7. Report commands, results, current limitations, and whether anything was pushed.

## Task Routing

| Task | Read first | Primary code |
|---|---|---|
| strategy identity or memory | `RECORD_LAYER_WORKFLOW.md` | `qst/ir`, `qst/hash`, `qst/receipts`, `qst/admission.py` |
| external result or backtested claim | `RECORD_LAYER_WORKFLOW.md` | `qst/evidence`, `qst/receipts`, `qst/claims` |
| FinRobot integration or report | `USAGE_GUIDE.md` and FinRobot acceptance report | `qst/integrations/finrobot`, `qst/report_audit` |
| signatures, quorum, or enforcement | `docs/rearchitecture/AUTHORITY_GOVERNANCE.md` | `qst/authority` |
| token gap or proposal | `TOKEN_REGISTRATION_GUIDE.md` | `qst/resolver`, `qst/incubator` |
| Qlib workflow import | `docs/adapters/QLIB_ADAPTER_GUIDE.md` | `qst/adapters/qlib` |
| v0.4 strategy authoring | compatibility prompt pack | `qst/compat/v04`, GKR examples |

## Evidence Rules

- Prefer hashes and artifact descriptors over embedded output.
- Preserve source date range, ticker/instrument, adapter version, costs, slippage, seeds,
  and metric definitions.
- Never call a strategy `backtested` without an admitted ExperimentReceipt 2.0.
- Never call custom code approved because integrity verification passed.
- Never let an agent approve its own token, claim, publication, or activation.
- Keep report output in the declared workspace and mark it as a draft for human review.

## Authority Selection

Use `record_only` for low-risk research capture, `advisory` when findings should be
surfaced without blocking, and `enforce` for controlled publication or activation. Do
not switch to a weaker mode merely to make a failing gate pass. Any override must be
declared with a reason and remains identity-bearing policy material.

## Common Gates

```bash
python -m ruff check .
python -m mypy qst
python -m qst.lint.stateless qst
python -m pytest tests -q
python -m pytest --cov=qst --cov-fail-under=85 -q
python -m qst.cli vocabulary --check
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check
git diff --check
```

## Stop Conditions

Stop and escalate if a request requires hidden customization, fabricated evidence,
validator bypass, reserved-runtime simulation through a weaker type, execution of
unapproved custom code, or broker/exchange/backtest/live-trading behavior.
