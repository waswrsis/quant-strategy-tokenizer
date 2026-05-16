# Stage 3B Decision

Stage 3B accepts the Stage 3A token surface as `token surface accepted and gap-classified`.

## Chosen Next Stage

**Stage 3C: Agent Strategy Authoring Profile**.

The evidence shows the main near-term gap is not missing primitive coverage. Users and agents need a disciplined way to combine accepted tokens, avoid reserved-design traps, and choose between accepted, experimental, custom, and metadata-only surfaces.

## Rejected Alternatives

- **Extended TypeSpec Stage**: valid future work for EventStream, Distribution, and Instrument metadata, but not required before agent authoring because the public demos and common scalar/panel/state patterns are already expressible.
- **Token Surface Patch**: useful for `indicator.macd` and `weight.inverse_vol`, but these are P1 convenience gaps rather than acceptance blockers.
- **Strategy Pattern Demonstrations**: useful as part of agent authoring, but insufficient alone because agents also need profile, maturity, and execution-support rules.

## Acceptance Criteria for Stage 3C

- Agent-facing docs explain how to select accepted tokens and when to stop at custom/reserved boundaries.
- Authoring guidance preserves hash/canonical visibility and does not imply broad runtime execution.
- Reserved-design and experimental gates remain enforced by validator tests.

## Risk

The main risk is confusing `accepted` with executable. Stage 3C must continue to treat `execution_support` as the execution boundary.
