# QST

QST is a typed, canonical strategy record system for research and review workflows. It defines a structured strategy IR, deterministic canonical JSON, stable hash classes, reference token semantics, package metadata, and validation traces for Graph Kernel Records (GKR).

QST is not a trading bot, broker adapter, exchange adapter, portfolio optimizer, or production execution engine. It is the record and verification layer that those systems can consume after they implement their own controls.

## Current Status

The active public tree targets:

- Python import package: `qst`
- CLI: `qst`
- Distribution name: `quant-strategy-tokenizer`
- Editable strategy source: `.gkr.yaml`
- Packaged Graph Kernel Record suffix: `.gkr`
- Internal schema identity: `qst-ir/0.4` and `qst-canonical/0.4`

The public tree is intentionally current-only. Earlier construction notes and audit history are preserved outside the active documentation set in the release artifact attached to the pre-reset tag.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

Validate the vocabulary and inspect a reference strategy:

```bash
qst vocabulary --check
qst validate examples/strategies/kdj_cross_basic.gkr.yaml
qst hash examples/strategies/kdj_cross_basic.gkr.yaml
qst canonicalize examples/strategies/kdj_cross_basic.gkr.yaml --output /tmp/kdj.canonical.json
```

Run the same commands through the module entry point:

```bash
python -m qst --help
python -m qst.cli hash examples/strategies/kdj_with_ema_filter.gkr.yaml
```

Custom-token workflows are explicit and approval-bound:

```bash
qst token verify --help
qst token approve --help
qst token execute --help
```

Public token-surface demos live under `examples/strategies/<case>/strategy.gkr.yaml`:

```bash
qst validate examples/strategies/01_ema_cross/strategy.gkr.yaml
qst hash examples/strategies/12_custom_token_kalman_signal/strategy.gkr.yaml
```

The 12-demo index is [examples/strategies/README.md](examples/strategies/README.md).
Each demo has validation diagnostics and graph/param/instance hash sentinels
under `tests/reference/strategies/<case>/`.

## What QST Provides

- A single active IR target with typed nodes, structured token refs, capabilities, and port signatures.
- Canonical JSON and deterministic hash helpers for graph, params, instance, behavior, signatures, token specs, token packs, runtime environments, audits, and reference artifacts.
- TypeSpec and PortSpec models for scalar, time-series, panel, decision, state, event, and stream surfaces.
- Temporal validation, numeric policy metadata, token evolution policy, TokenSpec and TokenPack metadata, and registry resolution.
- Token surface metadata for family, maturity, execution support, contracts, and agent-facing usage notes.
- Reference semantics for state, FSM, decision algebra, panel operators, weight operators, and custom token integrity/approval/execution boundaries.
- Reference validation fixtures under `tests/reference/` for temporal, state, panel, and custom-token cases.

## Repository Layout

```text
qst/                         Python package and CLI
docs/architecture.md         System architecture
docs/security.md             Trust and execution boundary
docs/reference.md            Schema and artifact reference
docs/token_family_registry.md Token family, maturity, and execution-support registry
docs/token_coverage.md       Token coverage and hash impact matrix
docs/adr/                    Active architecture decisions
docs/agent/                  Agent workflow and conformance guidance
docs/project_history/        Public background material
examples/strategies/         Public GKR strategy examples
examples/strategies/README.md Public demo index and coverage table
examples/custom_token/       Custom-token reference example
tests/reference/             Deterministic reference fixtures and traces
docs/reports/                Token surface acceptance and gap-review reports
tests/                       Unit and conformance tests
```

## Security Boundary

Custom token verification does not import or execute user code. Execution requires integrity verification, local approval, an execution grant, and output validation against TokenSpec ports and numeric policy. There is no sandbox in this tree; executing a custom token means executing approved local Python code.

See [docs/security.md](docs/security.md).

## Limitations

- No broad strategy runtime is provided for every IR node.
- No broker, exchange, order router, or production trading engine is included.
- No portfolio optimizer or simultaneous constraint solver is included.
- Token maturity `accepted` does not imply broad runtime executability; check `execution_support`.
- Panel numeric behavior is semantic float64 reference behavior, not bit-exact reproducibility.
- `.gkr` package handling is reserved by suffix and documentation boundary; this tree does not add a packaged runtime.

## Documentation

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Reference](docs/reference.md)
- [Token Family Registry](docs/token_family_registry.md)
- [Token Coverage](docs/token_coverage.md)
- [Stage 3B Token Surface Acceptance](docs/reports/token_surface_acceptance.md)
- [GKR Artifact Naming ADR](docs/adr/gkr-artifact-naming.md)
- [Token-First Surface ADR](docs/adr/token-first-after-core.md)
- [Agent Guidance](docs/agent/README.md)
- [Project Background](docs/project_history/PROJECT_EXPERIENCE.md)
