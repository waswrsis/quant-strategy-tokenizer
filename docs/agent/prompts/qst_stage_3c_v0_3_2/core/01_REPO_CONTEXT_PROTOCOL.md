# Repo Context Protocol

prompt_system_version: qst-stage-3c-v0.3.2.1
layer: core

Purpose: generate a current evidence-based view of the repository before reading, authoring, editing, or auditing.

Minimum inspection:

- `pwd`
- `git status --short`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `python --version`
- package and CLI metadata from `pyproject.toml`
- active docs under `docs/`
- examples under `examples/`
- conformance tests under `tests/`

CLI smoke when dependencies are available:

- `python -m qst.cli --help`
- `python -m qst.cli vocabulary --check`

The generated repo context replaces any hand-written current-state document.
