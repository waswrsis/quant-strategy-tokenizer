# Agent Methodology

- Read implementation and tests before proposing abstractions.
- Prefer deterministic repository evidence over remembered current-state facts.
- Keep project memory concise and load detailed guidance only for the active task.
- Preserve `qst-ir/0.4`, `qst-canonical/0.4`, and hash boundaries unless an explicit ADR
  changes them.
- Treat evidence, receipt, claim, authority, publication, activation, and execution as
  separate layers.
- Use the least authority appropriate to the use case; never weaken a mode to hide a
  failing gate.
- Add stable diagnostic codes and negative tests when introducing a new rejection path.
- Keep generated and local audit output outside committed product artifacts.
- Use current `qst` imports, `.gkr.yaml` examples, and content-addressed references.
- Challenge unsupported runtime or profitability claims instead of encoding them as
  record-layer support.
