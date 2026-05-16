# False Supported Protocol

A false `supported` classification is worse than an honest `reserved`,
`custom_token_required`, or `non_goal` classification.

## False-Supported Classes

```yaml
false_supported:
  mechanical:
    description: "Pattern is marked supported but lacks a valid example that passes validate/hash/canonicalize."
  semantic:
    description: "Example passes mechanically but omits a required strategy component."
  boundary:
    description: "Example hides reserved or non-goal runtime behavior inside supported metadata."
```

## Mechanical Review

Every fully supported pattern must have a strategy source and command evidence:

```text
examples/strategies/<case>/strategy.gkr.yaml
qst validate examples/strategies/<case>/strategy.gkr.yaml
qst hash examples/strategies/<case>/strategy.gkr.yaml
qst canonicalize examples/strategies/<case>/strategy.gkr.yaml --output /tmp/<case>.canonical.json
```

If any command fails, record:

```yaml
false_supported:
  mechanical_status: "fail"
```

A supported row without mechanical evidence is provisional and must not be counted as
fully supported.

## Semantic Review

For v0.3, semantic review may be manual, but it must be explicitly tracked.

```yaml
semantic_review:
  status: "pending | pass | fail | uncertain"
  reviewer:
  reviewer_relation: "author | independent | llm_assisted"
  review_date:
  required_components_checked:
  omitted_components:
  notes:
```

Rules:

- A mechanically valid supported pattern with `semantic_review.status = pending` is
  reported separately from fully reviewed supported coverage.
- A supported pattern with `semantic_review.status = fail` counts as semantic false
  support.
- If `reviewer_relation = author`, the result is lower-confidence internal review.

## Boundary Review

Fail boundary review if a supported pattern requires:

- broker
- exchange
- live execution
- order routing
- HFT runtime
- EventStream runtime
- full backtest engine
- portfolio optimizer solver

Boundary false support must be reported separately from mechanical and semantic false
support.

