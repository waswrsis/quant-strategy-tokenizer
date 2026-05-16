# Custom Token Routing

prompt_system_version: qst-stage-3c-v0.3.2.1
task_type: security
foundation: core/00_FOUNDATION.md

Use when required behavior cannot be expressed with accepted built-in tokens.

Separation:

- verify checks metadata and integrity and must not execute code.
- approve is explicit local trust.
- execute runs approved local code and is forbidden by default.

Never auto-approve or auto-execute custom token code.
