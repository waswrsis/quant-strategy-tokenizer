# Known Limitations

Date: 2026-05-15

These limitations are accepted explicitly for project-wide acceptance.

1. `qst-ir/0.4` broad runtime execution is not implemented.
2. v0.4 authoring CLI is not complete.
3. Panel recipes capability is not enabled.
4. Custom token runtime v0.1 has no sandbox.
5. Panel and Weight reference numerics are semantic float64 where applicable, not bit-exact.
6. `installed_distribution` custom-token verification depends on local installed files and RECORD metadata.
7. Real adapters are not part of qst-core acceptance.
8. Production trading engine behavior is not accepted.
9. Portfolio optimizer behavior is not accepted.
10. P5 experimental mutation and RL systems are not accepted.
11. P4b-v2 external ports are deferred.
12. qstpkg verification is structural and hash-based; it does not imply semantic or numerical equivalence.
13. Migration creates new v0.4 identity and does not claim legacy/v0.4 semantic equivalence.
14. The accepted custom-token trust boundary requires local explicit approval; approval is not portable trust.
