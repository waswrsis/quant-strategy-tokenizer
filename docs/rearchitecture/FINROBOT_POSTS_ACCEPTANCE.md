# FinRobot Posts Acceptance

## Scope

QST `1.0.0a2` closes the local record-layer requirements derived from
[FinRobot PR #106](https://github.com/AI4Finance-Foundation/FinRobot/pull/106) and the
[QST integration comment on issue #100](https://github.com/AI4Finance-Foundation/FinRobot/issues/100#issuecomment-4866488012).
This is local QST implementation evidence, not a claim that FinRobot has merged or
deployed the integration.

## Issue #100 Mapping

| Requirement | QST evidence |
|---|---|
| Separate strategy identity | `StrategyRecordReceipt` hashes the complete canonical GKR and retains graph, parameter, and instance hashes. |
| Separate experiment identity | `ExperimentReceipt` 2.0 binds strategy receipt, data snapshots, date range, adapter, parameters, costs, slippage, seeds, metric definitions, and result evidence. |
| Separate agent receipt | `AgentReceipt` 2.0 binds the experiment to agent/model/tool/prompt/task/approval/output/recommendation material. |
| Read-only FinRobot tool | `qst.integrations.finrobot.FinRobotReadOnlyTools` validates bounded paths or text and never executes a graph. |
| Canonical JSON and hashes | `strategy_identity` returns canonical content plus complete-strategy, graph, parameter, and instance hashes. Canonical content is inline through 256 KiB and otherwise stored in CAS. |
| Stable diagnostics | The bridge emits `unsupported_token`, `custom_token_requires_approval`, `missing_data_binding`, `missing_risk_constraint`, and `not_executable_by_adapter`. |
| Strategy-memory admission | `StrategyRecordReceipt` requires explicit non-goals and `admit_strategy_memory` rejects invalid or unvalidated records. |
| Backtested-label admission | Claim policy/decision 2.0 and `admit_backtested_claim` require a sealed experiment receipt and verified result evidence. |

## PR #106 Mapping

`FinancialReportProvenance` records run/time, agent role, task, model/prompt version,
normalized tool parameters, source document references, report sections, and output
artifacts. Secret material is represented by references and hashes, not embedded
credentials.

`review_financial_report` detects:

- missing or failed sources;
- ticker or report-period mismatches;
- output paths outside the declared workspace;
- unexplained valuation-assumption changes;
- report sections without evidence;
- failed, retried, fallback, or truncated tool output; and
- attempts to mark the artifact as something other than a draft for human review.

`qst.audit_jsonl` provides a deterministic 64 KiB-bounded, single-writer,
hash-chained JSONL export of record and artifact references. The typed CAS records remain
the source of truth; JSONL is an audit export, not a second authority system.

## Security and Authority Boundary

- FinRobot inputs are capped at 1 MiB.
- The bridge does not import FinRobot, AutoGen, Qlib, or custom Python.
- Tool inspection cannot approve a token, create an execution grant, admit a claim by
  assertion, write agent memory, run a model, run a backtest, or publish a report.
- Human approval, authority profiles, external execution, and result collection remain
  separate systems.

## Local Acceptance Commands

```bash
python -m pytest tests/receipts tests/integrations tests/report_audit -q
python -m pytest tests -q
python -m pytest --cov=qst --cov-fail-under=85 -q
python -m ruff check .
python -m mypy qst
python -m qst.lint.stateless qst
```

The final command results are recorded in the local commit report, not hardcoded here.
