# ADR-0001: QST 1.0 Product Redefinition

- Status: accepted for local alpha construction
- Decision date: 2026-07-04
- Target package version: `1.0.0a1`
- Research branch: `research/qst-1.0-agent-provenance`

## Context

QST v0.4 proved deterministic GKR strategy identity, token metadata, validation,
reference semantics, custom-token controls, and a partial Qlib workflow adapter. Agent
workflows need a stronger layer that records external activities and artifacts, proves
which evidence supports a claim, and governs new token proposals without allowing an
agent to approve or activate its own design.

Treating that change as a v0.5 feature release would hide a fundamental product pivot.
The project therefore moves to a 1.0 alpha while preserving v0.4 as an explicit
compatibility surface.

## Decision

QST 1.0 is a deterministic strategy identity, evidence, attestation, claim-control,
customization-declaration, and token-governance layer for financial agents.

The core separation is:

1. Evidence records what was observed or produced.
2. Attestation records who makes a statement about evidence.
3. Claim policy decides whether a public claim is permitted.
4. Token resolution identifies whether current vocabulary, a recipe, a proposal, a
   reserved type, or a non-goal runtime is the correct route.
5. Token incubation separates agent authorship from human approval, publication, and
   project activation.

QST does not train models, run inference, execute backtests, run trading simulations,
execute custom Python, perform broker operations, perform exchange operations, or
conduct live trading. External systems execute their own workflows; QST adapters
collect and verify their evidence.

## Identity Model

Existing `graph_hash`, `param_hash`, and `instance_hash` remain stable for v0.4 GKR.
New identities use domain-separated material for evidence, attestation, claims,
customizations, resolver policies, and token proposals. Domain definitions are versioned
contracts and must not be changed after a stage freeze without supersession.

## Consequences

- Existing execution-oriented custom runtime APIs become legacy-only compatibility and
  cannot be exposed as QST 1.0 product capabilities.
- Adapters have no `execute` method.
- Agent output can be a draft or recommendation, never its own approval.
- Publication and project activation are separate human-authorized transitions.
- Large artifacts are content-addressed data-plane objects, not embedded control-plane
  JSON.
- The current canonical serializer remains deterministic but is not described as RFC
  8785 compliant until a dedicated audit proves that claim.
