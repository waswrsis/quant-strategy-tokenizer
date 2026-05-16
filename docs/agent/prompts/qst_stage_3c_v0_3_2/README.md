# QST Stage 3C Agent Prompt Pack

prompt_system_version: qst-stage-3c-v0.3.2.1

## Purpose

This directory is the only active QST prompt system. It teaches an agent how to inspect
the repository, select current token surfaces, author or repair GKR strategies, and hand
off evidence without relying on stale project memory.

## Versioning

The directory name remains `qst_stage_3c_v0_3_2` for stable links. The active patch
prompt-system version is `qst-stage-3c-v0.3.2.1`.

## How To Use

1. Start with `core/00_FOUNDATION.md`.
2. Choose one load profile from `load_profiles/`.
3. Load only the readers required by the active task.
4. Run the task prompt and produce the report shape it requests.
5. Validate this pack with `tools/validate_prompt_set.py`.

## Boundaries

The prompt pack does not change QST token semantics, hashes, runtime behavior, demos, or
security boundaries. Reserved design token families remain non-executable.
