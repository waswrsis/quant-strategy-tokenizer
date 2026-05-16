# Custom Token Guide

Custom tokens are described by TokenSpec metadata and grouped into TokenPacks.
Execution is intentionally gated.

## Verify

```bash
python -m quant_strategy_tokenizer.cli token verify path/to/tokenpack --token-ref namespace.name/v1/bv1
```

Verification reports integrity and authorization separately.

## Approve

```bash
python -m quant_strategy_tokenizer.cli token approve path/to/tokenpack \
  --token-ref namespace.name/v1/bv1 \
  --approved-by local-user \
  --allow-token \
  --ack-risk
```

Approval is local and hash-bound.

## Execute

```bash
python -m quant_strategy_tokenizer.cli token execute path/to/tokenpack \
  --token-ref namespace.name/v1/bv1 \
  --current-time-utc 2026-05-16T00:00:00Z \
  --inputs-file inputs.json
```

Execution validates outputs against the TokenSpec contract.
