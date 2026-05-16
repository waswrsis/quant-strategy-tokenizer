# Stage 3C Prompt Acceptance Evidence

prompt_system_version: qst-stage-3c-v0.3.2.1
construction_type: acceptance_evidence

This evidence records the required prompt-pack validation gates. It intentionally avoids current commit IDs, coverage values, token counts, branch state, or hash truth.

## Required Commands

Run these commands from the repository root:

```bash
python -m py_compile tools/validate_prompt_set.py
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
python -m pytest tests/agent_prompts -q
```

## Expected Result

- `py_compile` exits with code `0`.
- `validate_prompt_set.py` exits with code `0` and reports `"result": "pass"`.
- `tests/agent_prompts` exits with code `0`.

## Validation Coverage

The validator must check:

- required prompt files
- prompt system version consistency
- readable multi-line Markdown prompts
- stale current-state and hardcoded hash bans
- cross-reference integrity
- load-profile target existence
- strategy classification vocabulary
- custom-token verify / approve / execute separation
- reserved-design non-execution
- golden YAML parseability and minimum schema
- at least three complete golden tasks
- operator manual reference-only status

## Acceptance Decision

Stage 3C prompt pack acceptance requires both local validation and CI prompt validation to pass. CI must run the validator directly so prompt-pack regressions cannot be hidden by unrelated test success.
