# Stage 3C Prompt Acceptance

prompt_system_version: qst-stage-3c-v0.3.2.1
construction_type: acceptance

Evidence:

- `construction/STAGE_3C_PROMPT_ACCEPTANCE_EVIDENCE.md`

Checklist:

- [x] One active prompt system exists.
- [x] Repo context is generated dynamically.
- [x] Reader prompts are read-only.
- [x] Strategy authoring starts with classification.
- [x] Token selection requires current vocabulary evidence.
- [x] Custom token execution is forbidden by default.
- [x] Golden task schema exists.
- [x] At least 3 complete golden tasks exist.
- [x] `tools/validate_prompt_set.py` exists and passes.
- [x] Cross-reference integrity passes.
- [x] Load profiles resolve to real files.
- [x] Prompt set validation passes.

CI Requirement:

- [x] CI must run `python -m py_compile tools/validate_prompt_set.py`.
- [x] CI must run `python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2`.
- [x] CI must run `python -m pytest tests/agent_prompts -q`.
