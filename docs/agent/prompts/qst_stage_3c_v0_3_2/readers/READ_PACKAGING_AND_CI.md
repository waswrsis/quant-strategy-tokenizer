# Read Packaging and CI

prompt_system_version: qst-stage-3c-v0.3.2.1
reader_type: project

Read:

- `pyproject.toml`
- `.github/`
- package `__main__` and CLI entry point

Report distribution name, import package, CLI command, test command, coverage gate, and build package inclusion. Do not confuse distribution name with import package.
