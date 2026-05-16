# Stage 3C Prompt Acceptance Evidence

prompt_system_version: qst-stage-3c-v0.3.2.1
construction_type: acceptance_evidence

This evidence records the Stage 3C prompt-pack validation gates.

The directory name `qst_stage_3c_v0_3_2` is the stable pack directory.
The internal `qst-stage-3c-v0.3.2.1` value is the patch prompt-system version inside that pack.

## Local Command Evidence

Recorded command results:

| Command | Exit code | Stdout excerpt | Stderr excerpt | Verdict |
| --- | ---: | --- | --- | --- |
| `python -m py_compile tools/validate_prompt_set.py` | `0` | no output | no output | pass |
| `python -m py_compile tests/agent_prompts/test_validate_prompt_set.py` | `0` | no output | no output | pass |
| `python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2` | `0` | `"result": "pass"`; all prompt checks pass | no output | pass |
| `python tools/verify_prompt_remote_artifacts.py docs/agent/prompts/qst_stage_3c_v0_3_2` | `0` | `"result": "pass"`; local artifact format checks pass | no output | pass |
| `python -m pytest tests/agent_prompts -q` | `0` | prompt validator tests pass | no output | pass |

## CI Evidence

The CI workflow includes a dedicated `prompt-validation` job. It runs:

```bash
python -m py_compile tools/validate_prompt_set.py
python -m py_compile tests/agent_prompts/test_validate_prompt_set.py
python tools/validate_prompt_set.py docs/agent/prompts/qst_stage_3c_v0_3_2
python tools/verify_prompt_remote_artifacts.py docs/agent/prompts/qst_stage_3c_v0_3_2
python -m pytest tests/agent_prompts -q
```

CI must pass this job before Stage 3C prompt-pack acceptance is considered complete.

## Raw Artifact Evidence

The raw-artifact verifier can be run against a commit-SHA raw URL after push:

```bash
python tools/verify_prompt_remote_artifacts.py docs/agent/prompts/qst_stage_3c_v0_3_2 --raw-base https://raw.githubusercontent.com/waswrsis/Quant-Strategy-Tokenizer/<commit-sha>
```

The verifier records byte count, line count, compile/parse checks, and verdict for:

- `tools/validate_prompt_set.py`
- `tests/agent_prompts/test_validate_prompt_set.py`
- prompt-pack `README.md`
- `core/00_FOUNDATION.md`
- `tasks/CLASSIFY_STRATEGY_INTENT.md`
- `validation/VALIDATE_PROMPT_SET.md`
- Stage 3C acceptance docs
- the three complete golden task YAML files

## Acceptance Decision

Stage 3C prompt pack acceptance requires all local prompt gates, CI prompt gates, and raw-artifact evidence checks to pass.

This file records the required evidence format.
CI enforces the local gate.
The raw commit-SHA gate is used as post-push evidence for public repository review.
