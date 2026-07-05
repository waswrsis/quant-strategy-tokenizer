# Agent Guidance

Agents working in this repository should treat QST as a deterministic record and validation system. The agent should prefer small scoped edits, explicit command evidence, and no hidden trust transitions.

Tool-specific project memory is available in the root `CLAUDE.md`. It is a concise
entrypoint, not a replacement for typed QST policy or this documentation.

## QST 1.0 Alpha Guidance

The single operational prompt for current work is:

- [QST 1.0 Agent Prompt](QST_1_0_AGENT_PROMPT.md)

Use it with the playbook and one task-specific guide. It is repository guidance, not QST
authority and not permission to execute external work.

## Compatibility Prompt System

The preserved v0.4 prompt system is:

- [qst_stage_3c_v0_3_2](prompts/qst_stage_3c_v0_3_2/README.md)

Validate it with:

```bash
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
```

The compatibility prompt pack does not govern QST 1.0 receipts, claims, authority, or
FinRobot admission.

Read these documents first:

- [Methodology](methodology.md)
- [Workflow](workflow.md)
- [Conformance](conformance.md)
- [Task Contract](task_contract.md)
- [Agent Takeover Prompt](AGENT_TAKEOVER_PROMPT.md)
- [QST 1.0 Agent Prompt](QST_1_0_AGENT_PROMPT.md)
- [Agent Playbook](AGENT_PLAYBOOK.md)
- [Usage Guide](USAGE_GUIDE.md)
- [Record-Layer Workflow](RECORD_LAYER_WORKFLOW.md)

Secondary development references:

- [Token Registration Guide](TOKEN_REGISTRATION_GUIDE.md)
- [Recipe Authoring Guide](RECIPE_AUTHORING_GUIDE.md)
- [Custom Token Guide](CUSTOM_TOKEN_GUIDE.md)
- [Secondary Development Guide](SECONDARY_DEVELOPMENT_GUIDE.md)
