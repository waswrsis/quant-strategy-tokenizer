# Modular Refactor Agent Prompt

```text
You are modularizing a trading strategy into reusable strategy modules.

Goal:
Create modules that can be called independently by other programs, simulations, live runners, or research tools.

Module rules:
- Each module must be a standalone .py file or package unit.
- The module must not create exchange connections on import.
- The module must not place orders, read live state, or write files unless explicitly designed as an adapter/output module.
- The module should accept both lightly processed data and reasonable raw data.
- The module should normalize inputs internally when safe.
- The module should return structured, detailed output so callers can choose which fields to use.
- Do not hide errors behind empty lists or default symbols.

Each module must document:
- Module purpose
- Core idea
- Accepted inputs
- Configuration fields
- Output schema
- Failure semantics
- Market/data generalization notes

Preferred interface:
- Params dataclass
- Request dataclass
- Report dataclass
- run(request) -> ModuleResult[Report]

The runner should become orchestration only. Signal, indicators, universe, filters, voting, sizing, risk, order planning, reconciliation, reporting, and state handling should be independently callable.
```

