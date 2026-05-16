# QST Stage 3C Prompt Pack

prompt_system_version: qst-stage-3c-v0.3.2.1
layer: index

This is the only active QST prompt system. It is repo-first, evidence-driven, and bounded to GKR reading, authoring, validation, repair, audit, and documentation.

Load a task-specific profile from `load_profiles/` instead of loading every reader by default.

Core rules:

- Inspect the current repository before asserting project facts.
- Use current token vocabulary and validators.
- Do not invent tokens, schema fields, ports, capabilities, or runtime support.
- Do not use reserved-design tokens as executable behavior.
- Treat custom-token verify, approve, and execute as separate trust steps.
