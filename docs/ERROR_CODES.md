# Error Codes

QST diagnostics are structured objects with `code`, `severity`, `phase`,
`message`, and optional remediation fields. Stable codes are preferred for
validator and runtime boundaries.

Representative current code families:

- `QST_V2_TEMPORAL_*`: temporal rule and requirement diagnostics.
- `QST_V2_PANEL_*`: panel type-layer and panel/state boundary diagnostics.
- `QST_V2_CAPABILITY_*`: capability gating diagnostics.
- `QST_V2_LOCK_*`: current token lock metadata diagnostics.
- `QST_V2_CUSTOM_TOKEN_*`: custom-token runtime and output validation diagnostics.
- `QST_V2_EXECUTION_GRANT_*`: short-lived grant validation diagnostics.
- `QST_V2_DISTRIBUTION_*`: installed distribution integrity diagnostics.

Use exact codes in tests when behavior is part of the public boundary. Human
message text may evolve, but code, phase, and severity should remain stable
unless a change is documented.
