# Behavior Core

prompt_system_version: qst-stage-3c-v0.3.2.1
layer: core

Default behavior:

- Read affected code and tests first.
- Keep changes scoped.
- Prefer validators and reference artifacts over inference.
- Explain residual risk when a strategy is only partially supported.
- Never claim a gate passed without command evidence.

When unsupported:

- Classify as `reserved`, `custom_token_required`, or `non_goal`.
- Do not fake support with reserved tokens or invented schema.
