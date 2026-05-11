# Strategy Decomposition Task Template

Use this prompt when asking another agent to analyze a complete trading strategy codebase and convert it into Quant Strategy Tokenizer-style modules.

```text
Task:
Analyze the following trading strategy project and decompose it into Quant Strategy Tokenizer modules.

Project path:
[INSERT LOCAL OR REPOSITORY PATH]

Primary strategy files:
[INSERT MAIN STRATEGY FILES]

Supporting files:
[INSERT README, CONFIG, BACKTEST, DEPLOYMENT, STATE, LOGGING, OR SCRIPT FILES]

Current objective:
[Choose one]
- Analysis only. Do not edit files.
- Produce a module extraction plan. Do not edit files.
- Extract pure modules only. Preserve behavior.
- Extract modules and add tests. Preserve behavior.
- Audit an existing modularization for semantic drift.

Important behavior that must be preserved:
- [INSERT DEFAULT PARAMETERS]
- [INSERT RISK SEMANTICS]
- [INSERT STATE/INSTANCE ISOLATION RULES]
- [INSERT EXECUTION OR ORDER HANDLING RULES]
- [INSERT BACKTEST OR LIVE DIFFERENCES]

Use these decomposition standards:
- Start by mapping the actual runtime path.
- Separate alpha, filters, risk, sizing, execution, state, audit, and deployment.
- Treat unknown/unavailable data as explicit state.
- Risk paths must fail closed.
- Pure modules must not call exchanges, write live state, or place orders.
- Preserve CLI and config compatibility unless explicitly instructed.
- Extract behavior mechanically before improving it.
- For each module define purpose, inputs, configuration, outputs, failure semantics, side effects, market generalization, and original code references.

Required output:
1. Executive summary of the strategy.
2. Strategy component map.
3. Proposed module/token list.
4. Original-code-to-module mapping.
5. Refactor sequence.
6. Behavior preservation checklist.
7. Test plan.
8. Red flags and semantic drift risks.
9. Any questions that block safe implementation.

If implementation is requested:
- Make small, reversible edits.
- Add or update tests where practical.
- Run compile/import/smoke checks.
- Re-audit changed paths.
- Report changed files and residual risk.

Do not:
- Place orders.
- Call live trading APIs.
- Modify remote systems.
- Delete logs or state.
- Change defaults.
- Convert unknown state into empty success.
```

## Example: Asking An Agent To Decompose A Monolithic Strategy

```text
Task:
Analyze `ema_copytreading_v2.py` and decompose it into Quant Strategy Tokenizer modules.

Project path:
C:/path/to/project

Primary strategy files:
- ema_copytreading_v2.py

Supporting files:
- README.md
- backtest_*.py
- remote/deploy scripts if relevant

Current objective:
Produce a module extraction plan. Do not edit files.

Important behavior that must be preserved:
- Existing CLI defaults.
- Existing risk fail-closed behavior.
- Existing state schema and instance isolation.
- Existing order cleanup, unknown flat, market freeze, and flatten semantics.
- Existing public/private parameter separation.

Required output:
Use the full QST decomposition format: executive summary, component map, proposed tokens, original-code-to-module mapping, refactor sequence, behavior checklist, test plan, and red flags.
```

## Example: Asking An Agent To Audit Existing Modules

```text
Task:
Audit the existing `quant_strategy_tokenizer/` implementation against Quant Strategy Tokenizer decomposition standards.

Current objective:
Analysis only. Do not edit files.

Check specifically:
- Are modules independently callable?
- Do modules accept raw or lightly processed user data?
- Are inputs and outputs documented?
- Are failures explicit?
- Is unknown state preserved?
- Are any exchange, runner, deployment, or live-state assumptions leaking into pure modules?
- Could report output leak sensitive user-provided fields?
- Can another agent safely compose these modules in a simulation?

Required output:
Findings first, ordered by severity, with file and line references. Then provide concrete fixes.
```

