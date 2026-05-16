# Golden Task Schema

prompt_system_version: qst-stage-3c-v0.3.2.1
schema_type: prompt_schema

Each complete golden task YAML must include:

- `golden_task.id`
- `golden_task.name`
- `golden_task.target_profile`
- `golden_task.intent`
- `golden_task.expected.classification`
- `golden_task.expected.required_token_families`
- `golden_task.expected.validation_outcome`
- `golden_task.forbidden_behavior`
- `golden_task.acceptance`

Skeleton tasks must set `golden_task.status: skeleton`.
