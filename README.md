# Quant Strategy Tokenizer

Quant Strategy Tokenizer (QST) is a typed, canonical strategy representation and
reference kernel for quant strategy research artifacts. It provides:

- a current `qst-ir/0.4` strategy document model,
- deterministic canonical JSON and hash helpers,
- structured type and port contracts,
- temporal, numeric, state, decision, panel, weight, and custom-token reference semantics,
- TokenSpec and TokenPack metadata,
- deterministic validation artifacts for reference cases.

QST is not a trading robot, broker adapter, exchange connector, portfolio
optimizer, or production execution engine. It defines strategy semantics and
verification boundaries; operational adapters are intentionally outside the
active cleanline baseline.

## Status

The repository is in the Stage R cleanline baseline. Active code targets
`qst-ir/0.4` only. Historical construction plans, prior acceptance records, and
old transition documents live under [docs/archive](docs/archive/README.md) and
are non-normative.

The current baseline is recorded in [QST_CLEANLINE_BASELINE.md](QST_CLEANLINE_BASELINE.md).

## Install

```bash
python -m pip install -e ".[dev]"
```

Check the built-in token vocabulary:

```bash
python -m quant_strategy_tokenizer.cli vocabulary --check
```

## Quick Start

Validate and hash a current strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/examples/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples/kdj_cross_basic.qst.yaml
```

Emit canonical JSON:

```bash
python -m quant_strategy_tokenizer.cli canonicalize strategies/examples/kdj_cross_basic.qst.yaml --output out/kdj.canonical.json
```

Inspect custom-token commands:

```bash
python -m quant_strategy_tokenizer.cli token verify --help
python -m quant_strategy_tokenizer.cli token approve --help
python -m quant_strategy_tokenizer.cli token execute --help
```

## Capabilities

### Current IR And Hashes

The active strategy target is `qst-ir/0.4` with `qst-canonical/0.4`. Canonical
payloads use sorted-key JSON with finite numeric values and bounded depth.
Strategy hashes include graph, parameter, and instance identity.

### Token System

TokenSpec and TokenPack metadata describe portable token identity, ports,
numeric policy, lifecycle, risk, dependency, implementation, and runtime
environment material. The registry resolves TokenPacks without reading removed
historical registries.

### Validation Kernel

QST includes structured diagnostics, profile policies, port temporal resolution,
numeric policy metadata, token evolution policy, state/FSM helpers, decision
algebra, panel operators, and weight operators. Reference helpers are language
semantics, not high-performance compute kernels.

### P-Validate References

Reference strategies and fixtures under `strategies/v04/p_validate`,
`fixtures/v04/p_validate`, `expected_traces/v04/p_validate`, and
`expected_diagnostics/v04/p_validate` exercise temporal, state, panel, and
custom-token validation behavior.

### Custom Token Runtime Boundary

Custom-token execution is separated into integrity verification, local approval,
short-lived execution grants, execution, output validation, and audit hashing.
Integrity verification never imports or executes custom code. There is no
sandbox in this baseline.

## Repository Map

```text
quant_strategy_tokenizer/
  ir/              current strategy IR, canonicalization, validation
  types/           structured TypeSpec models
  ports/           PortSpec and temporal rule models
  tokens/          TokenSpec, TokenPack, registry, token lock metadata
  hash/            deterministic hash helpers
  validation/      diagnostics and validator registry
  profiles/        profile policy metadata
  numeric/         numeric policy metadata
  token_evolution/ lifecycle policy metadata
  decision/        decision algebra reference semantics
  state/           state and FSM reference semantics
  panel/           panel, selection, and weight reference semantics
  custom_runtime/  custom-token verify/approve/execute boundary
  artifacts/       artifact schemas and identity helpers
  frames/          frame data containers and local IO helpers
  lint/            repository lint helpers

docs/
  ADR/             active cleanline ADR
  JSON_SCHEMAS/    active schemas
  archive/         non-normative historical records
  cleanline/       Stage R inventory and reset reports

strategies/examples/        current strategy examples
strategies/v04/p_validate/  reference validation strategies
tokenpacks/                 reference TokenPacks
tests/                      current conformance and reference tests
```

## Security Boundary

QST treats custom token code as user-approved local Python code. Approval is
local state and is not portable trust. Execution requires a grant bound to token,
pack, implementation, runtime hashes, profile, approval record, and run id.

See [docs/SECURITY_BOUNDARY.md](docs/SECURITY_BOUNDARY.md).

## Limitations

- No production broker or exchange execution.
- No broad strategy runtime for the current IR.
- No sandbox for custom token Python entrypoints.
- Panel numeric behavior is semantic float64, not bit-exact.
- Installed distribution verification is local-environment integrity, not a
  portable reproducible build proof.
- No optimizer, risk engine, reinforcement learning layer, or live trading loop.

See [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).

## Development Gates

Common local checks:

```bash
python -m compileall quant_strategy_tokenizer
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest tests -q
python -m quant_strategy_tokenizer.cli vocabulary --check
```

Current hash sentinels:

```bash
python -m quant_strategy_tokenizer.cli hash strategies/examples/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples/examples_kdj_with_ema_filter.qst.yaml
```
