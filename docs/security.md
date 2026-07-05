# Security Boundary

QST separates record validation from code execution.

## Custom Tokens

Custom-token integrity verification checks TokenSpec, TokenPack, implementation references, runtime environment metadata, dependency hashes, and audit material without importing or executing user code. It does not call entry-point loaders, inspect custom modules, or perform dynamic package introspection.

Execution requires:

1. Integrity verification.
2. Authorization under the selected profile.
3. A local approval record with explicit risk acknowledgement and token allowance.
4. A short-lived execution grant bound to token, pack, implementation, runtime, profile, approval, and run id.
5. Output validation against declared TokenSpec ports and numeric policy.

There is no sandbox here. Approved custom-token execution runs local Python code.

## Non-Portable Trust

Approval records and execution grants are local security state. They are not canonical strategy material and are not portable trust. Receiving a package or source tree never implies approval to execute code.

## External Systems

QST does not provide broker, exchange, custody, order-routing, or production trading controls. Integrations must enforce their own risk checks, credentials, throttles, and operational approvals.

## Agent and Report Inputs

FinRobot strategy inputs are bounded and parsed as data; they are not imported or
executed. Financial-report provenance rejects credential-bearing parameter keys and
credential-like values. Report review checks source artifacts, ticker/period consistency,
workspace paths, evidence bindings, retries, fallbacks, failures, truncation, and
valuation-change reasons.

Audit JSONL stores record references, hashes, and bounded summaries. It rejects common
credential fields and uses a single-writer lock plus sequence and previous-line hashes.
The export is tamper-evident, not a substitute for signatures or remote immutable
storage.

## Agent Tool Permissions

Coding-agent or orchestrator permissions do not replace QST authority. Read access,
editing, command execution, commit, push, token approval, activation, custom-code
execution, and external financial workflow execution are distinct permissions. Use the
least authority appropriate to the task and record any override explicitly.
