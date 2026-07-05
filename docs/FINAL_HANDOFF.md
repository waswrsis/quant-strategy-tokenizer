# Final Handoff

## Entry Point

QST v0.4 is the archived compatibility baseline. QST `1.0.0a2` is a research alpha
candidate on `research/qst-1.0-agent-provenance`, published separately under
`v1.0.0a2-agent-provenance`. It is not merged into `main` or released as production.

Read in this order:

1. [Product Redefinition](rearchitecture/ADR-0001-qst-1.0-product-redefinition.md)
2. [Stage Governance](rearchitecture/STAGE_GOVERNANCE.md)
3. [Resolver Policy](rearchitecture/RESOLVER_POLICY.md)
4. [Evidence Kernel](rearchitecture/EVIDENCE_KERNEL.md)
5. [AI4Finance Adapters](rearchitecture/AI4FINANCE_ADAPTERS.md)
6. [Token Incubator](rearchitecture/TOKEN_INCUBATOR.md)
7. [Claims, Customization, and Receipts](rearchitecture/CLAIMS_CUSTOMIZATION_RECEIPTS.md)
8. [Record-Layer Workflow](agent/RECORD_LAYER_WORKFLOW.md)

## Current Truth

- Python package and CLI: `qst`.
- Candidate version: `1.0.0a2`.
- Preserved strategy schemas: `qst-ir/0.4` and `qst-canonical/0.4`.
- Primary CLI has no model, backtest, custom-code, or trading executor.
- Legacy custom runtime is isolated under `qst compat-v04 token`.
- AI4Finance adapters collect declared evidence and never launch external work.
- FinRobot is a read-only sidecar with receipt-backed admission and report review; it is
  not an upstream deployment or execution runtime.
- Agent work starts from `agent/AGENT_PLAYBOOK.md` and then loads only the task-specific
  record, authority, token, adapter, or compatibility guide.

## Repository Rule

Each rearchitecture stage is a local commit plus annotated freeze tag and passing
manifest. Do not rewrite frozen history. Do not push this branch or its tags without
explicit user approval.
