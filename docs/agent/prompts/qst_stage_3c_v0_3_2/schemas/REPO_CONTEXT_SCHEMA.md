# Repo Context Schema

prompt_system_version: qst-stage-3c-v0.3.2.1
schema_type: prompt_schema

Repo context output must include:

- working directory
- branch and HEAD from inspection
- package and CLI identity from current files
- active docs and examples
- relevant tests
- contradictions
- commands run

Do not treat generated context as reusable across sessions.
