# Validate Prompt Set

prompt_system_version: qst-stage-3c-v0.3.2.1
validation_type: prompt_set

Run:

```bash
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
```

Required checks:

- version consistency
- readable multi-line Markdown prompt structure
- no stale current-state facts
- no hardcoded hash truth
- cross-reference integrity
- load profile validity
- classification vocabulary consistency
- custom token separation
- reserved-design non-execution
- golden YAML parseability and minimum schema
- at least 3 complete golden tasks
