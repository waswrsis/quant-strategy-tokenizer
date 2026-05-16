# Kernel Gap Decision Protocol

This protocol prevents coverage work from becoming a large token inventory that hides
missing core abstractions.

## Decision Table

| Gap type | Preferred solution |
| --- | --- |
| Same port/type issue repeats across many patterns | kernel/type-system improvement |
| Same temporal/state issue repeats | temporal type or FSM semantics |
| Single common indicator | token |
| Proprietary or long-tail model | custom token |
| Event-time runtime | reserved |
| Broker/live execution | non_goal |

## Kernel Gap Categories

```text
port_temporal_type_gap
panel_type_gap
fsm_state_gap
numeric_determinism_gap
reducer_semantics_gap
diagnostic_precision_gap
canonical_hash_boundary_gap
```

## Trigger Rules

A kernel review is mandatory when any of the following is true:

- `implementation_cost >= 3` for a proposed token family
- the same `kernel_gap` category appears in at least 3 active patterns
- a token proposal repeats the same port/type/temporal workaround across multiple families
- a proposed state/gate token implies FSM semantics
- a proposed panel/factor token requires Panel[T] semantics not currently proven
- a proposed record risks changing canonical/hash semantics

## Review Output

```yaml
kernel_review:
  trigger:
  affected_patterns:
  gap_category:
  options:
    - new_token
    - kernel_type_system_change
    - custom_token_template
    - reserved_design
    - non_goal
  decision:
  rationale:
  deferred_until:
```

No high-cost token family may merge without a kernel review record.

## Matrix Integration

Each pattern may include:

```yaml
gaps:
  kernel_gaps:
    - category:
      description:
      affected_components:
      preferred_solution:
```

The coverage report must include `kernel_gap_count`.

