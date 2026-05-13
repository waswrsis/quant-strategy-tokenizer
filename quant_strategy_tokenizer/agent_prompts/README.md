# Quant Strategy Tokenizer Agent Prompt Library

This folder stores reusable prompts for other coding, strategy, audit, deployment, and research agents.

The prompts were distilled from the engineering process of building, hardening, backtesting, evaluating, and modularizing the EMA MRV trading strategy into Quant Strategy Tokenizer (QST). They are designed to be copied directly into another agent as system, developer, or task instructions.

## Files

- `01_system_prompt.md`: General senior quant engineering agent role.
- `02_strategy_engineering_principles.md`: Production strategy engineering principles.
- `03_task_prompt.md`: Generic task execution prompt.
- `04_code_review_agent.md`: Code review and risk audit prompt.
- `05_fix_implementation_agent.md`: Bug-fix implementation prompt.
- `06_modular_refactor_agent.md`: Strategy modularization prompt.
- `07_backtest_evaluation_agent.md`: Backtest realism evaluation prompt.
- `08_incident_analysis_agent.md`: Live incident analysis prompt.
- `09_pre_deployment_check_agent.md`: Deployment and restart checklist prompt.
- `10_full_agent_prompt.md`: Combined prompt for direct use.
- `11_agent_project_usage_guide.md`: Step-by-step guide for teaching another agent how to use QST modules, including the implemented trend, momentum, volatility, volume, structure, breadth, derivatives, and on-chain indicator tokens and composition examples.
- `12_strategy_code_decomposition_agent.md`: Agent prompt for analyzing and decomposing a full strategy codebase into QST modules.
- `13_strategy_decomposition_task_template.md`: Fill-in task template for applying the decomposition prompt to a concrete strategy project.

## Usage

Use the most specific prompt for the job. For example:

- For a live incident, use `08_incident_analysis_agent.md`.
- For a code audit, use `04_code_review_agent.md`.
- For implementation after review findings, use `05_fix_implementation_agent.md`.
- For a general-purpose agent, use `10_full_agent_prompt.md`.
- To onboard another agent to this module package or the indicator tokens, use `11_agent_project_usage_guide.md`.
- To analyze a complete existing strategy and split it into reusable tokens, use `12_strategy_code_decomposition_agent.md`.
- To ask another agent to perform a concrete decomposition task, use `13_strategy_decomposition_task_template.md`.

These prompts intentionally emphasize:

- preserving live semantics;
- explicit unknown state;
- fail-closed risk behavior;
- state isolation;
- public/private parameter separation;
- post-change verification and audit.
