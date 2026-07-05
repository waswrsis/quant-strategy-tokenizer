# Agent Conformance

A change is conformant when it preserves or explicitly versions:

- `qst-ir/0.4` and `qst-canonical/0.4` identity;
- deterministic canonical JSON and domain-separated hash material;
- Strategy, Experiment, Agent, ClaimPolicy, and ClaimDecision 2.0 receipt boundaries;
- verified evidence requirements for every `backtested` claim;
- explicit non-goals for strategy-memory admission;
- local human approval for custom-token publication, activation, and execution;
- authority mode, scope, quorum, delegation, and revocation semantics;
- reserved-design and non-goal classifications;
- `.gkr.yaml` public strategy inputs and the 12-demo compatibility set;
- no business-framework runtime imports in QST sidecar adapters; and
- no broker, exchange, live execution, hidden backtest, or profitability claim.

Documentation must distinguish local evidence from CI, remote, upstream, or production
state. A sidecar integration is not an upstream integration until that external project
has accepted and verified it.
