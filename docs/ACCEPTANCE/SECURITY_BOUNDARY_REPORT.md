# Security Boundary Report

Date: 2026-05-15

Code freeze baseline: `1ede6998bf442c22102b6a83530ef89a0cdadaaa`

## 1. Custom Token Runtime

### Threat Model

An attacker may provide a malicious TokenPack, source tree, wheel, installed distribution, or qstpkg. The attacker may attempt import-time side effects during verify, bypass approval or grant checks, reuse stale grants, or return malformed output from a custom token entrypoint.

### Enforced Boundaries

- `verify_integrity` never imports, loads entry points from, inspects, or executes custom code.
- `approve_token_pack` never imports or executes custom code.
- `execute_custom_token` requires integrity pass, approval-backed authorization, and an `ExecutionGrant`.
- `ApprovalRecord` requires `allow_token=true` and `ack_risk=true`; incomplete persisted approvals are ignored.
- `ExecutionGrant` is hash-bound, profile-bound, run-id-bound, and expires.
- Custom token output must match declared TokenSpec output ports exactly.
- `TimeSeries[float]` and `Panel[float]` outputs reject `bool`.
- `installed_distribution` verification reads actual installed file bytes and checks supported RECORD SHA-256 material.

### Evidence

- `tests/custom_runtime_v2/test_service.py`
- `tests/custom_runtime_v2/test_package_integration.py`
- `tests/e2e/test_p_validate_custom_token_v04.py`

### Known Limitations

- Custom token runtime v0.1 has no sandbox.
- A local user can execute arbitrary code outside QST.
- `installed_distribution` evidence depends on local installed file integrity.

## 2. qstpkg Trust Boundary

### Threat Model

A qstpkg may embed TokenSpecs, TokenPacks, source references, audit material, or artifact references and attempt to make the receiver treat packaged material as trusted.

### Enforced Boundaries

- qstpkg verification checks metadata and hashes but does not import embedded source.
- qstpkg does not transmit portable approval.
- Receiving a qstpkg never implies local trust.
- TokenPack policy rejects embedded executable code unless the package policy allows spec-and-source material.

### Evidence

- `tests/tokens_v2/test_package_policy.py`
- `tests/package/test_verify_package.py`
- `tests/custom_runtime_v2/test_package_integration.py`

### Known Limitations

- qstpkg verification is structural and hash-based; it does not prove financial or numerical equivalence.
- Local approval remains a separate local security decision.

## 3. Agent API Boundary

### Threat Model

An agent may request custom-token actions on behalf of a user and may attempt to collapse explain, approval, and execution into one step.

### Enforced Boundaries

- Agent API can verify and explain token risk.
- Agent API can build an approval request, but approval persistence is a host/user-confirmed action.
- Agent execution uses an existing `ApprovalStore`, an approval-backed authorization result, and a run-bound `ExecutionGrant`.
- Agent execution cannot make qstpkg contents become portable approval.

### Evidence

- `quant_strategy_tokenizer/agent/api.py` inspection.
- `tests/custom_runtime_v2/test_service.py` approval and grant checks.

## 4. CLI Boundary

### Threat Model

User-facing commands may accidentally collapse verify, approve, and execute or hide custom-token risk.

### Enforced Boundaries

- `qst token verify` reports integrity and authorization but does not approve or execute.
- `qst token approve` requires explicit `--allow-token` and `--ack-risk`.
- `qst token execute` requires a valid approval path and explicit `--current-time-utc` for deterministic grant issuance and expiry validation.
- No approve-and-run command is accepted.

### Evidence

- `tests/cli/test_cli_wp9_token.py`
- `python -m quant_strategy_tokenizer.cli token verify --help`
- `python -m quant_strategy_tokenizer.cli token approve --help`
- `python -m quant_strategy_tokenizer.cli token execute --help`

## 5. Downstream Contracts

Future adapters, agents, runtimes, and package tools must preserve these constraints:

- No downstream tool may treat qstpkg contents as approval.
- No downstream tool may execute custom token code after verify only.
- No downstream tool may skip TokenSpec output schema validation.
- No downstream tool may silently extend accepted `qst-ir/0.4` semantics.
- Any sandbox, production isolation, or production broker integration must be accepted as a new design.
