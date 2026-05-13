from __future__ import annotations

P1_PRETRADE_READY_YAML = """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: p1_pretrade_ready
strategy_version: 1
form: surface
externals:
  state:
    type: State
    required: true
  sizing:
    type: Number
    required: true
recipes: []
graph:
  - id: risk
    token: risk.position_cap
    v: 1
    params:
      max_position: 5
      symbol_key: current_symbol
    inputs:
      decision:
        kind: accept
        reason: entry
      state: state
  - id: plan
    token: plan.order_intent
    v: 1
    params:
      side: long
    inputs:
      decision: risk.decision
      sizing: sizing
outputs:
  plan: plan
"""

P1_MISSING_RISK_PATH_YAML = """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: p1_missing_risk_path
strategy_version: 1
form: surface
externals:
  sizing:
    type: Number
    required: true
recipes: []
graph:
  - id: plan
    token: plan.order_intent
    v: 1
    params:
      side: long
    inputs:
      decision:
        kind: accept
        reason: entry
      sizing: sizing
outputs:
  plan: plan
"""
