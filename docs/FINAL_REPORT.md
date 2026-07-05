# Final Report

## Summary

QST `1.0.0a2` is a locally frozen alpha candidate for deterministic financial-agent
strategy identity, provenance, evidence, claim control, customization, and token
governance. It builds on the archived v0.4 GKR and token research prototype without
silently changing its hashes or public examples.

## Proved Locally

- Resolver decisions include vocabulary, aliases, recipes, proposals, profiles, and
  resolver-policy identities.
- Evidence, attestations, and claim decisions are separate tamper-evident records.
- Opaque artifacts use bounded streaming hashes and a rebuildable local index.
- AI4Finance adapters collect declared output evidence without executing workflows.
- Agents may draft tokens; only humans can approve publication and activation.
- Customization is declared, approval-bound where required, and identity-changing.
- Strategy, experiment, and agent receipt hashes remain distinct.
- v0.4 strategy hashes, vocabulary, demos, and Qlib import stay compatible.

## Boundary

QST does not train, infer, backtest, trade, route orders, replace AI4Finance runtimes,
or prove profitability. The v0.4 custom executor is retained only under the explicit
`compat-v04` namespace.

## Publication Status

All rearchitecture commits and freeze tags are local. GitHub publication requires the
user's separate approval.
