# Security Boundary

QST separates metadata verification from code execution.

## Custom Token Flow

1. `verify_integrity`: checks TokenPack, TokenSpec, implementation reference,
   runtime reference, dependency metadata, and audit chain. It does not import,
   inspect, load, or execute custom code.
2. `check_authorization`: checks profile policy and local approval state.
3. `approve_token_pack`: writes a local approval record only when the user has
   explicitly acknowledged risk and allowed the token.
4. `issue_execution_grant`: creates a short-lived grant bound to hashes,
   approval, profile, and run id.
5. `execute_custom_token`: re-checks integrity, authorization, grant validity,
   then imports and calls the declared Python entrypoint.
6. Output validation checks declared output ports, structured types, canonical
   JSON compatibility, finite numerics, and numeric policy diagnostics.

## Trust Model

Approval is local security state. It is not stored in strategy hashes and is not
portable through TokenPacks or package artifacts.

## Known Boundary

This baseline has no sandbox. Executing a custom token means running approved
local Python code in the current environment.
