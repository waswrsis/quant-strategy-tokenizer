# QST

Deterministic strategy identity, evidence, and governance for financial agents.

QST records strategy identity, external workflow evidence, agent provenance,
claim decisions, declared customizations, and human-governed token proposals.
Its v0.4 Graph Kernel Records remain a compatibility surface.

It is not a trading bot, broker adapter, exchange adapter, backtester, optimizer
runtime, or production execution engine.

## Status

The tagged v0.4 line is an **archived agent-ready research prototype**. The local
`research/qst-1.0-agent-provenance` branch is a `1.0.0a1` candidate. Eleven stages are
locally committed and frozen; nothing on this branch has been pushed.

See [QST 1.0 rearchitecture](docs/rearchitecture/README.md) for the staged construction
and freeze policy.

The alpha candidate includes:

- typed `qst-ir/0.4` strategy records
- deterministic `qst-canonical/0.4` canonical JSON
- graph, parameter, and instance hashes
- token surface governance and conformance tests
- typed Evidence, Attestation, Claim, Customization, and Receipt records
- content-addressed artifact storage and a rebuildable SQLite index
- deterministic Token Gap Resolver and human-governed Token Incubator
- mode-aware Ed25519 authority records with quorum, delegation, and revocation
- use-case authority profiles with identity-bearing declared overrides
- FinRobot, FinGPT, FinRL-Meta, FinRL, FinRL-X, and Qlib evidence adapters

## Install

```bash
pip install -e ".[dev]"
```

## Quick Check

```bash
python -m qst.cli vocabulary --check
python -m qst.cli validate examples/strategies/kdj_cross_basic.gkr.yaml
python -m qst.cli hash examples/strategies/kdj_cross_basic.gkr.yaml
python -m qst.cli canonicalize examples/strategies/kdj_cross_basic.gkr.yaml --output .local_audit/kdj.canonical.json
```

## AI4Finance Evidence

AI4Finance adapters consume declared manifests and existing output artifacts. FinRobot,
FinRL, FinRL-X, and Qlib have L3 golden fixtures; FinGPT and FinRL-Meta remain L2.
No adapter launches an external workflow.

## Qlib Compatibility Import

QST includes a partial Qlib workflow YAML importer:

```bash
python -m qst.cli adapter qlib import examples/adapters/qlib/workflow_config_lightgbm_alpha158.yaml --output .local_audit/qlib_lightgbm_alpha158.gkr.yaml --coverage .local_audit/qlib_lightgbm_alpha158.coverage.json
python -m qst.cli validate .local_audit/qlib_lightgbm_alpha158.gkr.yaml
python -m qst.cli hash .local_audit/qlib_lightgbm_alpha158.gkr.yaml
python -m qst.cli canonicalize .local_audit/qlib_lightgbm_alpha158.gkr.yaml --output .local_audit/qlib_lightgbm_alpha158.canonical.json
```

The adapter is record-layer evidence only. It does not import Qlib, run qrun,
train models, run inference, execute backtests, connect to brokers or exchanges,
or claim lossless Qlib conversion.

## What It Provides

- **Identity:** domain-separated strategy, evidence, experiment, and agent receipts.
- **Evidence:** immutable actors, activities, artifacts, envelopes, and attestations.
- **Claims:** policy decisions that cannot be substituted by evidence or assertions.
- **Governance:** declared customization and human-approved token incubation.
- **Authority:** switchable record-only, advisory, and enforce modes without treating
  unverified records as authorized.
- **Adapters:** read-only AI4Finance collectors with explicit maturity levels.
- **Compatibility:** frozen `qst-ir/0.4`, token vocabulary, demos, and hashes.

## Boundaries

QST deliberately does not provide:

- live trading
- broker or exchange integration
- full backtesting
- Qlib runtime replacement
- qrun execution
- model training or inference execution
- lossless Qlib conversion
- arbitrary Python strategy parsing
- production portfolio optimization
- profitability claims

QST 1.0 does not execute custom code. The former v0.4 executor is available only through
the explicit `qst compat-v04 token ...` compatibility namespace and is excluded from
QST 1.0 product claims.

## Handoff

Start with the active alpha documents:

- [QST 1.0 Rearchitecture](docs/rearchitecture/README.md)
- [Product Redefinition ADR](docs/rearchitecture/ADR-0001-qst-1.0-product-redefinition.md)
- [Final Handoff](docs/FINAL_HANDOFF.md)
- [Final Scope](docs/FINAL_SCOPE.md)
- [Final Acceptance](docs/FINAL_ACCEPTANCE.md)
- [Agent Takeover Prompt](docs/agent/AGENT_TAKEOVER_PROMPT.md)
- [Agent Playbook](docs/agent/AGENT_PLAYBOOK.md)
- [Usage Guide](docs/agent/USAGE_GUIDE.md)

## Key Paths

```text
qst/                         Python package and CLI
qst/evidence/                Typed evidence envelopes
qst/provenance/              Actor, activity, and artifact records
qst/incubator/               Human-governed token proposals
qst/authority/               Signed authority records and mode-aware governance
qst/adapters/ai4finance/     Read-only AI4Finance evidence adapters
examples/strategies/         12 public GKR strategy examples
examples/adapters/qlib/      Qlib partial workflow adapter examples
examples/custom_token/       Custom-token reference example
tests/reference/             Deterministic reference fixtures and traces
tests/adapters/qlib/         Qlib adapter proof tests
docs/agent/                  Agent handoff and prompt guidance
docs/adapters/               Adapter boundary and Qlib adapter guide
docs/reports/                Coverage Frontier and acceptance reports
```

## Documentation

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Reference](docs/reference.md)
- [Token Family Registry](docs/token_family_registry.md)
- [Token Coverage](docs/token_coverage.md)
- [Coverage Report](docs/reports/strategy_coverage_report.md)
- [Qlib Adapter Boundary](docs/adapters/QLIB_ADAPTER_BOUNDARY.md)
- [Agent Guidance](docs/agent/README.md)

## Project Identity

- Python import package: `qst`
- CLI: `qst`
- Distribution name: `quant-strategy-tokenizer`
- Editable strategy source: `.gkr.yaml`
- Packaged record suffix: `.gkr`
- IR: `qst-ir/0.4`
- Canonical schema: `qst-canonical/0.4`
- Package candidate: `1.0.0a1`
