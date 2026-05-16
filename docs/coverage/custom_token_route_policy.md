# Custom Token Route Policy

`custom_token_required` is a valid record-layer route, but it must not become a loophole
for claiming built-in coverage.

## Policy

```yaml
custom_token_policy:
  max_weighted_share: 0.30
  counts_toward_routable_record_coverage: true
  counts_toward_direct_builtin_coverage: false
  requires_template: true
  requires_route_reason: true
  requires_ports: true
```

Custom-token routes must preserve verify, approve, grant, execute, and output-validation
boundaries. They do not imply custom code execution.

## Required Route Fields

```yaml
custom_token_route:
  reason:
  missing_builtin_surface:
  input_ports:
  output_ports:
  numeric_policy:
  profile_authorization:
  verification_requirements:
  approval_boundary:
  grant_boundary:
  execution_boundary:
  output_validation:
```

## Provisional Discount

Report both raw and discounted routable record coverage.

```yaml
custom_token_discount:
  value: 0.5
  status: provisional
  calibration_source: "future observed custom-route implementation rate"
```

Future calibration:

```text
custom_token_discount =
implemented_custom_routes / total_custom_token_required_routes
```

Until enough data exists, both raw and discounted routable coverage must be reported.

## Future Tool Behavior

Coverage report `--check` should fail when:

- `custom_token_route_share > custom_token_route_max`
- a `custom_token_required` pattern lacks a route reason
- a `custom_token_required` pattern lacks ports
- a `custom_token_required` pattern lacks a template or explicit deferral

