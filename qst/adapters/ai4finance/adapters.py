"""Project-specific field contracts for AI4Finance evidence adapters."""

from qst.adapters.ai4finance.base import DeclaredManifestAdapter
from qst.adapters.ai4finance.models import AdapterDescriptor


class FinRobotEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(
        adapter_id="qst.ai4finance.finrobot", system="finrobot", maturity="L3"
    )
    required_plan_fields = frozenset({"agents", "tools", "task"})
    required_result_fields = frozenset({"message_log", "report"})


class FinGPTEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(
        adapter_id="qst.ai4finance.fingpt", system="fingpt", maturity="L2"
    )
    required_plan_fields = frozenset(
        {"model_repo", "model_revision", "tokenizer_revision", "dataset", "task", "parameters"}
    )


class FinRLMetaEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(
        adapter_id="qst.ai4finance.finrl_meta", system="finrl_meta", maturity="L2"
    )
    required_plan_fields = frozenset(
        {"environment", "data_processor", "state", "action", "reward", "date_range", "seed"}
    )


class FinRLEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(
        adapter_id="qst.ai4finance.finrl", system="finrl", maturity="L3"
    )
    required_plan_fields = frozenset(
        {"training_activity", "testing_activity", "trading_simulation_activity", "seed"}
    )
    required_result_fields = frozenset({"checkpoint", "metrics", "simulation_result"})


class FinRLXEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(
        adapter_id="qst.ai4finance.finrl_x", system="finrl_x", maturity="L3"
    )
    required_plan_fields = frozenset(
        {"settings", "selection", "allocation", "timing", "risk", "transaction_costs"}
    )
    required_result_fields = frozenset({"target_weights", "backtest_result"})


class QlibEvidenceAdapter(DeclaredManifestAdapter):
    descriptor = AdapterDescriptor(adapter_id="qst.qlib", system="qlib", maturity="L3")
    required_plan_fields = frozenset({"model", "dataset", "records", "strategy"})
    required_result_fields = frozenset({"recorder", "metrics", "artifacts"})


ADAPTER_TYPES = {
    item.descriptor.system: item
    for item in (
        FinRobotEvidenceAdapter,
        FinGPTEvidenceAdapter,
        FinRLMetaEvidenceAdapter,
        FinRLEvidenceAdapter,
        FinRLXEvidenceAdapter,
        QlibEvidenceAdapter,
    )
}

