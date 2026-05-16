# Architecture

QST is organized around a current typed strategy document and deterministic
metadata/reference layers.

## Core Flow

```text
strategy YAML
  -> ir.load_ir_v04_file
  -> ir.validate_ir_v04
  -> ir.canonical_bytes_v04
  -> hash.compute_hashes_v2
```

Token references point at structured TokenSpec metadata. TokenPacks group
TokenSpecs and dependencies. The registry resolves packs deterministically and
reports conflicts as diagnostics.

## Layers

- `ir`: strategy shell, canonicalization, capability validation, temporal and
  panel type-layer validation.
- `types`: TypeSpec and value type parsing.
- `ports`: InputSpec, OutputSpec, PortSignature, and temporal rules.
- `hash`: graph, parameter, instance, signature, behavior, token, pack,
  implementation, runtime, audit, and expected artifact hashes.
- `validation`: diagnostic models and validator registry.
- `profiles`: profile policy metadata.
- `numeric`: numeric policy metadata.
- `tokens`: TokenSpec, TokenPack, registry, and token lock metadata.
- `state`, `decision`, `panel`: deterministic reference semantics.
- `custom_runtime`: verify, approve, grant, execute, output validation, audit.
- `artifacts`, `frames`: current artifact and frame primitives.

## Non-Goals

QST does not provide a production trading runtime, broker integration, exchange
adapter, optimizer, or sandbox. External runtime and adapter work must use the
contracts in the active docs and remain outside the reference kernel.
