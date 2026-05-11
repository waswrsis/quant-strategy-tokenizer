# Submission Notes

This folder contains the recommended clean submission set for Quant Strategy Tokenizer.

Included:

- `README.md`: public project README with no remote deployment paths.
- `pyproject.toml`: Python project metadata.
- `.gitignore`: excludes credentials, logs, backups, remote snapshots, generated state, and local caches.
- `quant_strategy_tokenizer/`: source package and agent prompts.
- `docs/PROJECT_EXPERIENCE.md`: your project experience write-up.
- `docs/PROJECT_EXPERIENCE_TEMPLATE.md`: optional backup template for future revisions.

Intentionally excluded from the clean submission set:

- live trading strategy files such as `ema_copytreading_v2.py`;
- remote deployment scripts and snapshots;
- remote logs;
- backups;
- state files;
- `.env` files or credentials;
- backtest output folders;
- personal or unrelated local projects.

Before publishing:

- review `quant_strategy_tokenizer/agent_prompts/` for wording you want public;
- review `docs/PROJECT_EXPERIENCE.md` for personal details you want public;
- add a license if the repository will be public;
- run a final secret scan.
