# Agent Workflow

1. **Orient:** inspect Git state, package version, affected public contracts, and user
   changes.
2. **Load narrowly:** read the playbook, one task-specific guide, owned code, and relevant
   tests. Avoid loading the whole compatibility prompt pack for unrelated work.
3. **Classify impact:** state whether the task changes identity, evidence, receipt, claim,
   authority, token governance, adapter extraction, compatibility, or execution.
4. **Plan gates:** identify positive, negative, tamper, and boundary tests before editing.
5. **Implement:** use existing canonical and model APIs; keep facts, approvals, and side
   effects separate.
6. **Verify:** run focused tests first, then shared gates for public or cross-layer changes.
7. **Audit:** inspect the final diff for stale claims, accidental authority escalation,
   hidden execution, secret material, and unsupported compatibility promises.
8. **Handoff:** report exact evidence and perform Git/remote actions only when requested.
