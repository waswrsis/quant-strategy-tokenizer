# ADR: Token System v2 P-Validate Cases

Date: 2026-05-15

Status: Accepted

## Context

Token System v2 adds major kernel capabilities: port-level temporal semantics, explicit state, panel types, decision algebra, and custom token runtime. These capabilities must be dogfooded as they are built. P-Validate gates are embedded into their owning work packages and are not deferred to final acceptance.

## Decision

Token System v2 has four required P-Validate cases:

- PV-A State-heavy strategy
- PV-B Panel / cross-sectional strategy
- PV-C Temporal safety strategy
- PV-D Custom token strategy

Each case must pass before its owning work package is accepted. If a case fails, the owning work package fails.

## PV-A: State-heavy Strategy

Owner: WP6c State Recipes.

Nature: reference strategy.

Minimum accepted subset:

- cooldown state
- market freeze state
- observe period state
- circuit breaker state
- deterministic state trace

Input fixture:

- bar-level market fixture
- event fixture containing signal triggers, trade-executed events, freeze events, and cooldown expiry events

Expected output:

- deterministic state transitions
- reproducible state trace with state before and state after
- explicit blocked / active / cooldown decisions where applicable

Failure diagnosis:

- Missing state primitive if state transition cannot be expressed.
- Missing reducer capability if accumulation cannot be represented without Python lambda.
- Missing trace support if replay cannot explain state transitions.

## PV-B: Panel / Cross-sectional Strategy

Owner: WP8d Panel Recipes / E2E.

Nature: reference strategy.

Minimum accepted subset:

- dynamic universe
- panel rank or zscore
- top-k / bottom-k selection
- BTC residualization or equivalent single-factor residual
- market-neutral weight generation

Input fixture:

- multi-symbol panel market fixture with strict time x symbol alignment
- universe membership fixture
- benchmark or factor fixture for residualization

Expected output:

- deterministic SelectionPanel
- deterministic WeightPanel
- explicit universe and axis metadata in signature material
- canonical explain output describing selection and weighting

Failure diagnosis:

- Missing Panel TypeSpec if panel data cannot be typed.
- Missing AxisSpec or UniverseSpec if universe semantics are implicit.
- Missing weight semantics if output cannot represent gross, net, or per-symbol constraints.

## PV-C: Temporal Safety Strategy

Owner: WP3 PortTemporalSpec.

Nature: reference safety case.

Minimum accepted subset:

- `shift(-1)` produces research warning and pretrade error.
- `shift(+1)` passes.
- centered rolling window is unsafe for pretrade.
- trailing rolling window carries `min_history_bars`.
- next-open prediction has explicit `available_at=next_bar_open`.
- close-price execution mismatch is surfaced as warning or error according to profile.

Input fixture:

- bar-level time series fixture
- strategies exercising safe trailing windows, unsafe future shifts, and next-open timing

Expected output:

- profile-aware validation result
- structured temporal failures or warnings
- temporal material included in signature hash

Failure diagnosis:

- Missing PortTemporalSpec if output timing is not expressible.
- Missing TemporalRule kind if parameter-driven timing cannot be resolved.
- Missing profile policy if research and pretrade cannot diverge.

## PV-D: Custom Token Strategy

Owner: WP9 Custom Token Runtime.

Nature: reference custom token case.

Minimum accepted subset:

- project or installed token pack registers `my_pack.kalman_ema`
- research validation passes with visible risk metadata
- pretrade validation fails by default
- pretrade validation can pass only with explicit `--allow-token` and `--ack-risk`
- audit records are written
- qstpkg locks token pack hash and implementation reference hash
- verify fails if the token pack is missing or mismatched

Input fixture:

- deterministic custom token pack fixture
- strategy fixture using `my_pack.kalman_ema`
- package fixture containing audit material

Expected output:

- deterministic token output under controlled fixture
- explicit profile gate behavior
- token override audit entries
- lock/package verification tied to token pack and implementation reference hashes

Failure diagnosis:

- Missing TokenPack model if pack identity cannot be locked.
- Missing implementation reference hash if code identity cannot be verified.
- Missing audit chain if risk override cannot be reconstructed.
- Missing profile gate if high-risk token can enter pretrade silently.

## Consequences

P-Validate is binding. It is not a demo suite and it is not deferred to final acceptance.

Each owning work package must include its PV case in local tests and CI before it is marked accepted.
