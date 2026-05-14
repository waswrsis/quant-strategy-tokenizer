# ADR: P2c-extended Kernel Substitution Spike

Date: 2026-05-14
Status: accepted

## Decision

QST P2c-extended introduces an opt-in kernel substitution spike for `indicator.ewm/v1`.

The default runtime path remains unchanged. Kernel substitution only runs when explicitly requested through `execute_strategy(..., kernel_substitution=True)` or `qst execute --kernel-substitution`.

## Rules

- Only `indicator.ewm/v1` has a built-in spike kernel.
- A node is eligible only when it carries `indicator.ewm/v1` provenance.
- The matching TagSpec must verify as `fully_verified=True`.
- The TagSpec must explicitly list the kernel in `allowed_kernels`.
- Kernel substitution is runtime behavior only.
- Kernel substitution does not enter canonical IR, three-layer hash material, Merkle fingerprint material, mutation output, or recipe registry.

## Rationale

P2c-core already introduced execution-plan CSE without changing canonical IR. Kernel substitution follows the same boundary: it is an execution-plan/runtime optimization, not strategy semantics.

The opt-in gate keeps P0/P1/P2 default behavior stable while proving that verified semantic provenance can safely select an alternative executor.

## Consequences

- Default execution remains backward compatible.
- Opt-in execution can emit trace evidence with `kernel_substituted=true`.
- The spike is not a production kernel framework.
- Additional kernels require a later ADR and their own verification evidence.
