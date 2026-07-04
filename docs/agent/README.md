# Agent Guidance

Agents working in this repository should treat QST as a deterministic record and validation system. The agent should prefer small scoped edits, explicit command evidence, and no hidden trust transitions.

## QST 1.0 Alpha Guidance

For current architecture work, read `docs/rearchitecture/` and
`docs/FINAL_HANDOFF.md` first. The prompt set below is preserved for v0.4 strategy
authoring compatibility; it is not authority for QST 1.0 execution or governance.

## Compatibility Prompt System

The preserved v0.4 prompt system is:

- [qst_stage_3c_v0_3_2](prompts/qst_stage_3c_v0_3_2/README.md)

Validate it with:

```bash
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
```

There is no separate QST 1.0 generative prompt system in this tree.

Read these documents first:

- [Methodology](methodology.md)
- [Workflow](workflow.md)
- [Conformance](conformance.md)
- [Task Contract](task_contract.md)
- [Agent Takeover Prompt](AGENT_TAKEOVER_PROMPT.md)
- [Agent Playbook](AGENT_PLAYBOOK.md)
- [Usage Guide](USAGE_GUIDE.md)

Secondary development references:

- [Token Registration Guide](TOKEN_REGISTRATION_GUIDE.md)
- [Recipe Authoring Guide](RECIPE_AUTHORING_GUIDE.md)
- [Custom Token Guide](CUSTOM_TOKEN_GUIDE.md)
- [Secondary Development Guide](SECONDARY_DEVELOPMENT_GUIDE.md)
