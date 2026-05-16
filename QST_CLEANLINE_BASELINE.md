# QST Cleanline Baseline

This file defines the post-cleanline current baseline. It is not a historical
acceptance document.

## Baseline

- Safety tag: `cleanline-pre-reset-20260516`
- Active IR: `qst-ir/0.4`
- Active canonical form: `qst-canonical/0.4`
- Historical records: `docs/archive/**`
- Cleanline inventory: `docs/cleanline/**`

## Current Code Surface

- `quant_strategy_tokenizer.ir`
- `quant_strategy_tokenizer.types`
- `quant_strategy_tokenizer.ports`
- `quant_strategy_tokenizer.tokens`
- `quant_strategy_tokenizer.hash`
- `quant_strategy_tokenizer.validation`
- `quant_strategy_tokenizer.profiles`
- `quant_strategy_tokenizer.numeric`
- `quant_strategy_tokenizer.token_evolution`
- `quant_strategy_tokenizer.decision`
- `quant_strategy_tokenizer.state`
- `quant_strategy_tokenizer.panel`
- `quant_strategy_tokenizer.custom_runtime`
- `quant_strategy_tokenizer.artifacts`
- `quant_strategy_tokenizer.frames`

## Gate Snapshot

At the time this file is written during Stage R, the focused current test suite
passes locally:

```text
python -m pytest tests -q
347 passed
```

The final Stage R gate is recorded in `docs/cleanline/PERFORMANCE_BASELINE_BEFORE_AFTER.md`.
