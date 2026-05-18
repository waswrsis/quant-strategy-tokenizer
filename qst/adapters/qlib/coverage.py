"""Coverage builder for the Qlib partial workflow adapter."""

from __future__ import annotations

from qst.adapters.qlib.models import (
    CoverageClass,
    QlibBacktestConfig,
    QlibDatasetConfig,
    QlibImportCoverage,
    QlibModelConfig,
    QlibRecordConfig,
    QlibStrategyConfig,
    UnsupportedQlibComponent,
)


def build_coverage(
    *,
    source: str,
    model: QlibModelConfig | None,
    dataset: QlibDatasetConfig | None,
    records: list[QlibRecordConfig],
    strategy: QlibStrategyConfig | None,
    backtest: QlibBacktestConfig | None,
    unsupported: list[UnsupportedQlibComponent],
) -> QlibImportCoverage:
    tokenized_components: list[str] = []
    if dataset is not None:
        tokenized_components.append("data.qlib_dataset_record")
        if dataset.handler_class in {"Alpha158", "Alpha360"}:
            tokenized_components.append(f"feature.{dataset.handler_class.lower()}_record")
    if model is not None:
        tokenized_components.append("model.forecast_model_record")
    for record in records:
        if record.class_name == "SignalRecord":
            tokenized_components.append("record.signal_record")
        elif record.class_name == "PortAnaRecord":
            tokenized_components.append("record.portfolio_analysis_record")
    if strategy is not None:
        if strategy.class_name == "TopkDropoutStrategy":
            tokenized_components.append("selection.topk_dropout_record")
        else:
            tokenized_components.append("strategy.generic_record")
    if backtest is not None:
        tokenized_components.append("portfolio.backtest_config_record")

    classification = _classification(tokenized_components, unsupported)
    warnings = [
        "Qlib workflows are research/runtime configs.",
        "This adapter imports record-layer structure only.",
        "It does not train models, run qrun, run inference, or execute backtests.",
    ]
    return QlibImportCoverage(
        source=source,
        classification=classification,
        tokenized_components=sorted(set(tokenized_components)),
        model=model,
        dataset=dataset,
        strategy=strategy,
        backtest=backtest,
        records=records,
        unsupported_components=unsupported,
        warnings=warnings,
    )


def _classification(
    tokenized_components: list[str],
    unsupported: list[UnsupportedQlibComponent],
) -> CoverageClass:
    if tokenized_components and not unsupported:
        return "supported"
    if tokenized_components and unsupported:
        return "partially_supported"
    if unsupported:
        return "custom_token_required"
    return "non_goal"

