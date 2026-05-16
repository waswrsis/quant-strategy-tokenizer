# Market Weight Protocol

Market weight is a transparent scoring model for prioritizing coverage work. It is not a
license to inflate supported coverage.

## Scoring Model

```yaml
market_weight:
  source_frequency:
    score: 0 | 1 | 2 | 3
    meaning:
      0: rare or one-off pattern
      1: appears in at least one credible source or user request
      2: appears in at least three independent sources or repeated user requests
      3: widely repeated canonical pattern
  implementation_relevance:
    score: 0 | 1 | 2
    meaning:
      0: outside QST research-record scope
      1: recordable but niche
      2: central to QST intended use
  user_relevance:
    score: 0 | 1 | 2
    meaning:
      0: no user evidence
      1: plausible user value
      2: explicit user or project demand
  final_market_weight:
    formula: "max(0.25, source_frequency + implementation_relevance + user_relevance)"
```

If normalized weights are needed:

```text
normalized_weight = final_market_weight / average_weight
```

## Evidence Requirement

Each non-default market weight must cite at least one:

- external source
- existing QST example
- user-submitted strategy
- known project dogfood case

Matrix rows with missing evidence must be flagged by future coverage tooling and excluded
from frontier publication claims until reviewed.

## Anti-Bias Rules

- Do not increase weight only because a source is famous.
- Do not lower weight because QST cannot currently support the pattern.
- Do not combine unrelated strategies into one high-weight row.
- Report source uncertainty instead of hiding it inside the score.

