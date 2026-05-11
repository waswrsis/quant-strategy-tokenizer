# Agent Project Usage Guide

这份文件是给其它 agent 的“项目使用说明 + 操作提示词”。目标是让另一个 agent 不需要理解原始单体策略，也能安全地调用 `quant_strategy_tokenizer/` 里的独立模块，完成研究、模拟、风控检查、候选池筛选、信号生成和订单计划输出。
*EN: This file is a project usage guide and operating prompt for other agents. Its goal is to let another agent safely call the standalone modules in `quant_strategy_tokenizer/` for research, simulation, risk checks, candidate screening, signal generation, and order-plan output without understanding the original monolithic strategy.*

## 1. 给其它 Agent 的启动提示词
*EN: Startup Prompt for Other Agents*

```text
You are using the local `quant_strategy_tokenizer` package.

Your job is to compose small, standalone trading-strategy modules. Do not call exchanges, place orders, read live state, or modify remote systems unless the user explicitly asks for an adapter or deployment task.

Read `quant_strategy_tokenizer/agent_prompts/11_agent_project_usage_guide.md` first.

Core rules:
- Modules process caller-provided data only.
- Every module exposes a `Params`, `Request`, `Report`, and `run(request)` style interface where applicable.
- Always check `ModuleResult.ok` before using `ModuleResult.value`.
- Treat `ModuleResult.failure` as authoritative when `ok=False`.
- Do not treat empty outputs as success unless the module explicitly reports success.
- Prefer explicit field mapping through `DataFrameSpec`.
- Use `ModuleRunContext(output_dir=...)` when the user wants formatted output files.
- Compose modules in a pipeline only after each single module call works in isolation.

When answering the user:
- Explain which module you used.
- Show the input shape.
- Show the relevant output fields.
- Report warnings and failures clearly.
```

## 2. 项目地图
*EN: Project Map*

核心合同层：
*EN: Core contract layer:*

- `contracts.py`: `ModuleResult`, `ModuleFailure`, `ModuleEvent`, `DataFrameSpec`, `ExtractorSpec`, `ModuleRunContext`。
- `normalization.py`: 把 `DataFrame`、`Series`、`list[dict]`、`dict[list]`、自定义对象转换为标准表。
  *EN: `normalization.py`: converts `DataFrame`, `Series`, `list[dict]`, `dict[list]`, and custom objects into standard tables.*
- `pipeline.py`: 把多个模块按顺序串起来。
  *EN: `pipeline.py`: chains multiple modules together in sequence.*
- `reporting.py`: 输出 JSON / JSONL 报告。
  *EN: `reporting.py`: writes JSON / JSONL reports.*

指标模块：
*EN: Indicator modules:*

- `indicators/ema.py`: EMA。
- `indicators/vwap.py`: VWAP。
- `indicators/atr.py`: ATR。
- `indicators/chop.py`: CHOP。
- `indicators/spike.py`: spike / 异常波动检测。
  *EN: `indicators/spike.py`: spike / abnormal-volatility detection.*
- `indicators/rolling_return.py`: 滚动收益。
  *EN: `indicators/rolling_return.py`: rolling returns.*
- `indicators/beta_residual.py`: 相对基准残差。
  *EN: `indicators/beta_residual.py`: residuals relative to a benchmark.*
- `indicators/mrq_touch.py`: MRQ touch 诊断。
  *EN: `indicators/mrq_touch.py`: MRQ touch diagnostics.*

策略组合模块：
*EN: Strategy composition modules:*

- `universe_selector.py`: 候选 universe 选择。
  *EN: `universe_selector.py`: candidate universe selection.*
- `signal_trigger.py`: 根据 price / center / width 生成 long / short / none。
  *EN: `signal_trigger.py`: generates long / short / none from price / center / width.*
- `vote_engine.py`: 聚合多个 judge 的投票结果。
  *EN: `vote_engine.py`: aggregates voting results from multiple judges.*
- `candidate_pool.py`: 汇总过滤状态、投票状态和排序结果。
  *EN: `candidate_pool.py`: combines filter state, vote state, and ranking results.*
- `market_freeze.py`: 根据市场广度判断是否 block new risk。
  *EN: `market_freeze.py`: decides whether to block new risk based on market breadth.*
- `order_planner.py`: 生成 venue-neutral order plan，不下单。
  *EN: `order_planner.py`: generates venue-neutral order plans without placing orders.*
- `position_reconciler.py`: 对账持仓和目标状态。
  *EN: `position_reconciler.py`: reconciles observed positions against target state.*
- `state_model.py`: 状态模型校验和隔离。
  *EN: `state_model.py`: validates state schema and isolation.*

过滤器：
*EN: Filters:*

- `filters/blacklist_filter.py`
- `filters/status_filter.py`
- `filters/history_filter.py`
- `filters/cooldown_filter.py`
- `filters/backoff_filter.py`
- `filters/vwap_filter.py`
- `filters/mrq_filter.py`

## 3. 标准调用流程
*EN: Standard Calling Flow*

每个 agent 调用模块时都应按这个顺序：
*EN: Each agent should call modules in this order:*

1. 明确用户要的是研究、模拟、筛选、风控、订单计划，还是报告输出。
   *EN: Clarify whether the user wants research, simulation, screening, risk control, order planning, or report output.*
2. 选择一个最小模块先单独调用。
   *EN: Select the smallest matching module and call it in isolation first.*
3. 准备输入数据。可以是 `list[dict]`、`dict[list]`、`pandas.DataFrame` 或带 `ExtractorSpec` 的自定义对象。
   *EN: Prepare input data. It can be `list[dict]`, `dict[list]`, `pandas.DataFrame`, or a custom object with `ExtractorSpec`.*
4. 如字段名不是标准字段，用 `DataFrameSpec` 显式映射。
   *EN: If field names are not standard, map them explicitly with `DataFrameSpec`.*
5. 构造 `Params`。
   *EN: Construct `Params`.*
6. 构造 `Request`。
   *EN: Construct `Request`.*
7. 调用 `run(request)`。
   *EN: Call `run(request)`.*
8. 检查 `result.ok`。
   *EN: Check `result.ok`.*
9. 使用 `result.value` 里的结构化字段。
   *EN: Use the structured fields inside `result.value`.*
10. 如果需要落盘报告，传入 `ModuleRunContext(output_dir=...)`。
   *EN: If a report file is needed, pass `ModuleRunContext(output_dir=...)`.*

通用检查模板：
*EN: Generic checking template:*

```python
result = module.run(request)
if not result.ok:
    print(result.failure.kind, result.failure.message, result.failure.details)
else:
    report = result.value
    print(report)
```

## 4. 示例一：直接计算 EMA
*EN: Example 1: Calculate EMA Directly*

适用场景：用户传入一段价格序列，希望得到 EMA 最后值和可选序列。
*EN: Use case: the user provides a price series and wants the latest EMA value and optionally the full series.*

```python
from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.indicators.ema import EMAParams, EMARequest, run as run_ema

bars = [
    {"close": 100},
    {"close": 101},
    {"close": 103},
    {"close": 102},
    {"close": 104},
]

result = run_ema(
    EMARequest(
        data=bars,
        params=EMAParams(window=3, min_periods=3),
        context=ModuleRunContext(detail_level=DetailLevel.FULL),
    )
)

if result.ok:
    print(result.value.last_value)
    print(result.value.series)
else:
    print(result.failure.kind, result.failure.message)
```

关键输出：
*EN: Key outputs:*

- `last_value`: 最新 EMA。
  *EN: `last_value`: latest EMA.*
- `series`: `detail_level=FULL` 时返回完整序列。
  *EN: `series`: full sequence returned when `detail_level=FULL`.*
- `used_fields`: 实际使用了哪个输入字段。
  *EN: `used_fields`: which input field was actually used.*
- `warnings`: 输入归一化时的警告。
  *EN: `warnings`: warnings from input normalization.*

## 5. 示例二：用户字段名不标准时计算 VWAP
*EN: Example 2: Calculate VWAP When User Field Names Are Nonstandard*

适用场景：用户的数据来自外部数据源，字段是 `H/L/C/V`，模块不要求用户自己改列名。
*EN: Use case: the user data comes from an external source with fields `H/L/C/V`; the module does not require the user to rename columns manually.*

```python
from quant_strategy_tokenizer.contracts import DataFrameSpec
from quant_strategy_tokenizer.indicators.vwap import VWAPParams, VWAPRequest, run as run_vwap

raw_rows = [
    {"H": 105, "L": 99, "C": 102, "V": 1200},
    {"H": 106, "L": 101, "C": 104, "V": 1500},
    {"H": 107, "L": 102, "C": 106, "V": 1700},
]

spec = DataFrameSpec(
    high_col="H",
    low_col="L",
    close_col="C",
    volume_col="V",
)

result = run_vwap(
    VWAPRequest(
        data=raw_rows,
        spec=spec,
        params=VWAPParams(window=2, price_source="typical"),
    )
)

if result.ok:
    print(result.value.last_value)
    print(result.value.last_deviation)
else:
    print(result.failure.kind, result.failure.message)
```

关键输出：
*EN: Key outputs:*

- `last_value`: 最新 VWAP。
  *EN: `last_value`: latest VWAP.*
- `last_price`: 最新价格。
  *EN: `last_price`: latest price.*
- `last_deviation`: 最新价格相对 VWAP 的偏离。
  *EN: `last_deviation`: latest price deviation from VWAP.*
- `touch_count`: 窗口中触碰 VWAP 的次数。
  *EN: `touch_count`: number of VWAP touches in the window.*
- `no_touch_run`: 最近连续未触碰长度。
  *EN: `no_touch_run`: current consecutive no-touch length.*

## 6. 示例三：用 price / center / width 生成信号
*EN: Example 3: Generate Signals from price / center / width*

适用场景：用户已经有任意指标结果，例如 EMA 是中心，ATR 或标准差是宽度，希望模块只负责触发逻辑。
*EN: Use case: the user already has indicator outputs, such as EMA as center and ATR or standard deviation as width, and wants the module to handle only trigger logic.*

```python
from quant_strategy_tokenizer.signal_trigger import (
    SignalTriggerParams,
    SignalTriggerRequest,
    run as run_signal_trigger,
)

features = [
    {"symbol": "AAA", "price": 90, "center": 100, "width": 4},
    {"symbol": "BBB", "price": 112, "center": 100, "width": 5},
    {"symbol": "CCC", "price": 101, "center": 100, "width": 3},
]

result = run_signal_trigger(
    SignalTriggerRequest(
        rows=features,
        params=SignalTriggerParams(
            price_field="price",
            center_field="center",
            width_field="width",
            upper_mult=2.0,
            lower_mult=2.0,
        ),
    )
)

if result.ok:
    print(result.value.signals)
    print(result.value.rejected)
else:
    print(result.failure.kind, result.failure.message)
```

这个模块不关心 `center` 是 EMA、VWAP、回归均值还是其它公平价值。它只做一件事：判断价格是否超过上下边界。
*EN: This module does not care whether `center` is EMA, VWAP, regression mean, or another fair-value estimate. It does one thing: decide whether price exceeds the upper or lower boundary.*

## 7. 示例四：Universe 筛选
*EN: Example 4: Universe Selection*

适用场景：用户传入候选标的、排名字段、状态、黑名单和历史长度，模块返回可交易 universe。
*EN: Use case: the user provides candidate instruments, a ranking field, status, blacklist, and history length; the module returns a tradable universe.*

```python
from quant_strategy_tokenizer.universe_selector import (
    UniverseSelectorParams,
    UniverseSelectorRequest,
    run as run_universe,
)

candidates = [
    {"symbol": "AAA", "liquidity": 100},
    {"symbol": "BBB", "liquidity": 300},
    {"symbol": "CCC", "liquidity": 50},
]

result = run_universe(
    UniverseSelectorRequest(
        candidates=candidates,
        blacklist=["CCC"],
        status_by_symbol={"AAA": "ACTIVE", "BBB": "ACTIVE", "CCC": "ACTIVE"},
        history_by_symbol={"AAA": 200, "BBB": 300, "CCC": 300},
        params=UniverseSelectorParams(
            top_n=2,
            rank_field="liquidity",
            require_status_ok=True,
            accepted_status_values=("ACTIVE",),
            min_history_value=180,
            fail_closed=True,
        ),
    )
)

if result.ok:
    print(result.value.selected)
    print(result.value.rejected)
else:
    print(result.failure.kind, result.failure.message)
```

设计要点：
*EN: Design notes:*

- 空 universe 是一个有效的 fail-closed 输出，不会自动回退到默认 symbol。
  *EN: An empty universe is a valid fail-closed output and will not automatically fall back to a default symbol.*
- 缺少必要状态时，`fail_closed=True` 会拒绝对应标的。
  *EN: When required state is missing, `fail_closed=True` rejects the corresponding instrument.*

## 8. 示例五：投票系统
*EN: Example 5: Voting System*

适用场景：用户有多个外部 judge，例如趋势 judge、波动 judge、宏观 judge，希望统一成 allow/reject。
*EN: Use case: the user has multiple external judges, such as trend, volatility, or macro judges, and wants to normalize them into allow/reject decisions.*

```python
from quant_strategy_tokenizer.vote_engine import (
    VoteEngineParams,
    VoteEngineRequest,
    run as run_vote,
)

candidates = [
    {"symbol": "AAA"},
    {"symbol": "BBB"},
    {"symbol": "CCC"},
]

judge_by_symbol = {
    "AAA": {"outcome": "allow", "score": 0.82, "trend": "support"},
    "BBB": {"outcome": "reject", "score": 0.91, "trend": "veto"},
    "CCC": {"outcome": "allow", "score": 0.40},
}

result = run_vote(
    VoteEngineRequest(
        candidates=candidates,
        judge_by_symbol=judge_by_symbol,
        params=VoteEngineParams(min_score=0.70, fail_closed=True),
    )
)

if result.ok:
    print(result.value.decisions)
    print(result.value.rejected)
else:
    print(result.failure.kind, result.failure.message)
```

关键语义：
*EN: Key semantics:*

- `min_score` 是可选分数门槛。
  *EN: `min_score` is an optional score threshold.*
- 缺失 judge 时，`fail_closed=True` 会拒绝。
  *EN: When a judge is missing, `fail_closed=True` rejects.*
- judge 标签是泛化的，不绑定任何特定策略。
  *EN: Judge labels are generalized and not bound to any specific strategy.*

## 9. 示例六：候选池组合和排序
*EN: Example 6: Candidate Pool Assembly and Ranking*

适用场景：投票和过滤器已经完成，现在要形成最终候选池。
*EN: Use case: voting and filtering are complete, and the next step is to form the final candidate pool.*

```python
from quant_strategy_tokenizer.candidate_pool import (
    CandidatePoolParams,
    CandidatePoolRequest,
    run as run_candidate_pool,
)

candidates = [
    {"symbol": "AAA", "score": 0.82, "outcome": "allow"},
    {"symbol": "BBB", "score": 0.91, "outcome": "allow"},
    {"symbol": "CCC", "score": 0.40, "outcome": "reject"},
]

filter_state_by_symbol = {
    "AAA": {"accepted": True},
    "BBB": {"accepted": False, "reason": "cooldown"},
    "CCC": {"accepted": True},
}

result = run_candidate_pool(
    CandidatePoolRequest(
        candidates=candidates,
        filter_state_by_symbol=filter_state_by_symbol,
        params=CandidatePoolParams(
            score_field="score",
            descending=True,
            fail_closed=True,
        ),
    )
)

if result.ok:
    print(result.value.ranked_symbols)
    print(result.value.accepted_candidates)
    print(result.value.rejected_candidates)
else:
    print(result.failure.kind, result.failure.message)
```

## 10. 示例七：市场冻结判断
*EN: Example 7: Market Freeze Decision*

适用场景：用户传入一批标的的区间收益，判断是否因为市场单边过强而禁止新增风险。
*EN: Use case: the user provides interval returns for a batch of instruments to decide whether a strong one-sided market should block new risk.*

```python
from quant_strategy_tokenizer.market_freeze import (
    MarketFreezeParams,
    MarketFreezeRequest,
    run as run_market_freeze,
)

returns = [
    {"symbol": "AAA", "return": 0.05},
    {"symbol": "BBB", "return": 0.03},
    {"symbol": "CCC", "return": 0.02},
    {"symbol": "DDD", "return": -0.01},
]

result = run_market_freeze(
    MarketFreezeRequest(
        rows=returns,
        params=MarketFreezeParams(
            ratio_threshold=0.75,
            min_symbols=4,
            return_field="return",
            fail_closed_on_insufficient=True,
        ),
    )
)

if result.ok:
    print(result.value.action)
    print(result.value.direction)
    print(result.value.up_ratio, result.value.down_ratio)
else:
    print(result.failure.kind, result.failure.message)
```

关键输出：
*EN: Key outputs:*

- `freeze`: 是否触发冻结。
  *EN: `freeze`: whether freeze is triggered.*
- `action`: `allow` 或 `block_new_risk`。
  *EN: `action`: `allow` or `block_new_risk`.*
- `direction`: `up`、`down`、`none` 或 `unknown`。
  *EN: `direction`: `up`, `down`, `none`, or `unknown`.*
- `reason`: 触发原因。
  *EN: `reason`: trigger reason.*

## 11. 示例八：生成订单计划，但不下单
*EN: Example 8: Generate Order Plans Without Placing Orders*

适用场景：策略已经决定要交易，模块只生成抽象订单计划，后续由交易所 adapter 翻译执行。
*EN: Use case: the strategy has already decided to trade; the module only generates abstract order plans, which a downstream venue adapter translates and executes.*

```python
from quant_strategy_tokenizer.order_planner import (
    OrderPlannerParams,
    OrderPlannerRequest,
    run as run_order_planner,
)

decisions = [
    {
        "symbol": "AAA",
        "side": "buy",
        "price": 100.0,
        "notional": 1000.0,
        "stop_loss": 92.0,
        "take_profit": 108.0,
        "tag_prefix": "demo",
        "add_levels": [
            {"offset_pct": 0.03, "notional_fraction": 0.5},
            {"offset_pct": 0.06, "notional_fraction": 0.5},
        ],
    }
]

result = run_order_planner(
    OrderPlannerRequest(
        decisions=decisions,
        params=OrderPlannerParams(),
    )
)

if result.ok:
    plan = result.value.plans[0]
    print(plan.symbol, plan.side)
    for leg in plan.legs:
        print(leg.intent, leg.side, leg.order_type, leg.quantity, leg.price, leg.stop_price)
else:
    print(result.failure.kind, result.failure.message)
```

注意：
*EN: Notes:*

- 这个模块不会下单。
  *EN: This module does not place orders.*
- 不处理交易所精度、最小名义金额、reduce-only 真实语义。
  *EN: It does not handle venue precision, minimum notional, or real reduce-only semantics.*
- 下单细节必须由下游执行 adapter 处理。
  *EN: Order execution details must be handled by a downstream execution adapter.*

## 12. 示例九：把多个模块串成 Pipeline
*EN: Example 9: Chain Multiple Modules into a Pipeline*

适用场景：用户希望快速做模拟流程，例如 universe -> vote -> candidate pool。
*EN: Use case: the user wants to quickly build a simulation flow, such as universe -> vote -> candidate pool.*

```python
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.universe_selector import UniverseSelectorParams, UniverseSelectorRequest, run as run_universe
from quant_strategy_tokenizer.vote_engine import VoteEngineParams, VoteEngineRequest, run as run_vote
from quant_strategy_tokenizer.candidate_pool import CandidatePoolParams, CandidatePoolRequest, run as run_pool

initial_candidates = [
    {"symbol": "AAA", "liquidity": 100, "score": 0.82},
    {"symbol": "BBB", "liquidity": 300, "score": 0.91},
]

judge_by_symbol = {
    "AAA": {"outcome": "allow", "score": 0.82},
    "BBB": {"outcome": "allow", "score": 0.91},
}

steps = [
    PipelineStep(
        name="universe",
        fn=lambda payload: run_universe(
            UniverseSelectorRequest(
                candidates=payload,
                params=UniverseSelectorParams(top_n=2, rank_field="liquidity"),
            )
        ),
    ),
    PipelineStep(
        name="vote",
        fn=lambda universe_report: run_vote(
            VoteEngineRequest(
                candidates=universe_report.selected,
                judge_by_symbol=judge_by_symbol,
                params=VoteEngineParams(min_score=0.80),
            )
        ),
    ),
    PipelineStep(
        name="candidate_pool",
        fn=lambda vote_report: run_pool(
            CandidatePoolRequest(
                candidates=vote_report.decisions,
                params=CandidatePoolParams(score_field="score"),
            )
        ),
    ),
]

result = run_pipeline(initial_candidates, steps)

if result.ok:
    final_report = result.value.final_payload
    print(final_report.ranked_symbols)
else:
    print(result.failure.kind, result.failure.message)
```

## 13. 示例十：输出格式化报告文件
*EN: Example 10: Write Formatted Report Files*

适用场景：用户希望在模拟或实盘旁路观察时，直接得到可读的 JSON / JSONL 文件。
*EN: Use case: the user wants readable JSON / JSONL files during simulation or live sidecar observation.*

```python
from quant_strategy_tokenizer.contracts import ModuleRunContext
from quant_strategy_tokenizer.market_freeze import MarketFreezeParams, MarketFreezeRequest, run as run_market_freeze

result = run_market_freeze(
    MarketFreezeRequest(
        rows=[{"return": 0.01}, {"return": 0.02}, {"return": 0.03}],
        params=MarketFreezeParams(ratio_threshold=0.80, min_symbols=3),
        context=ModuleRunContext(
            run_id="example_freeze_check",
            output_dir="module_outputs",
        ),
    )
)

if result.ok:
    print(result.files)
else:
    print(result.failure.kind, result.failure.message)
```

输出文件由模块自己写入 `output_dir`，调用方只需要看 `result.files`。
*EN: Output files are written by the module into `output_dir`; the caller only needs to inspect `result.files`.*

## 14. 给其它 Agent 的选择指南
*EN: Selection Guide for Other Agents*

如果用户说：
*EN: If the user says:*

- “帮我算一下 EMA / ATR / VWAP”：使用 `indicators/*`。
  *EN: "Calculate EMA / ATR / VWAP for me": use `indicators/*`.*
- “帮我筛一批标的”：使用 `universe_selector.py` 或 `filters/*`。
  *EN: "Screen a batch of instruments for me": use `universe_selector.py` or `filters/*`.*
- “帮我判断能不能新增仓位”：使用 `market_freeze.py`、过滤器、`vote_engine.py`。
  *EN: "Tell me whether new positions can be added": use `market_freeze.py`, filters, and `vote_engine.py`.*
- “帮我形成最终候选列表”：使用 `candidate_pool.py`。
  *EN: "Create the final candidate list": use `candidate_pool.py`.*
- “帮我把交易想法变成订单”：使用 `order_planner.py`，但不要下单。
  *EN: "Turn a trade idea into orders": use `order_planner.py`, but do not place orders.*
- “帮我看持仓是否和目标一致”：使用 `position_reconciler.py`。
  *EN: "Check whether positions match the target": use `position_reconciler.py`.*
- “帮我把一套流程串起来”：使用 `pipeline.py`。
  *EN: "Chain a workflow together": use `pipeline.py`.*
- “帮我生成输出文件”：在 `ModuleRunContext` 中传 `output_dir`。
  *EN: "Generate output files": pass `output_dir` in `ModuleRunContext`.*

## 15. 失败处理规范
*EN: Failure Handling Rules*

其它 agent 必须这样处理失败：
*EN: Other agents must handle failures like this:*

```python
if not result.ok:
    failure = result.failure
    return {
        "status": "failed",
        "kind": failure.kind,
        "message": failure.message,
        "field": failure.field,
        "details": failure.details,
        "warnings": result.warnings,
    }
```

不要这样做：
*EN: Do not do this:*

```python
# Bad: 把失败当作空结果继续跑
# Bad: Treating a failure as an empty result and continuing
rows = result.value.selected if result.value else []
```

原因：这个项目的核心约定是 unknown / unavailable / invalid 必须显式保留，不允许被空列表吞掉。
*EN: Reason: the core convention of this project is that unknown / unavailable / invalid states must be preserved explicitly and must not be swallowed by empty lists.*

## 16. 常见坑
*EN: Common Pitfalls*

1. 不要让模块自己拉数据。
   *EN: Do not let modules fetch data themselves.*
   数据源由用户或上层程序配置，模块只处理传入数据。
   *EN: The data source is configured by the user or upper-level program; modules only process passed-in data.*

2. 不要绕过 `DataFrameSpec`。
   *EN: Do not bypass `DataFrameSpec`.*
   如果字段不标准，显式映射字段，而不是提前改坏原始数据。
   *EN: If fields are nonstandard, map them explicitly instead of mutating the raw data prematurely.*

3. 不要把 `result.value` 当作永远存在。
   *EN: Do not assume `result.value` always exists.*
   先检查 `result.ok`。
   *EN: Check `result.ok` first.*

4. 不要把 `order_planner` 当交易执行器。
   *EN: Do not treat `order_planner` as a trade executor.*
   它只生成计划，不负责交易所精度、下单、撤单或确认。
   *EN: It only generates plans and does not handle venue precision, order placement, cancellation, or confirmation.*

5. 不要把空 universe 自动替换成默认标的。
   *EN: Do not automatically replace an empty universe with a default instrument.*
   空 universe 是重要的 fail-closed 信号。
   *EN: An empty universe is an important fail-closed signal.*

6. 不要在 pipeline 中吞掉失败。
   *EN: Do not swallow failures in a pipeline.*
   默认让 pipeline 在失败处停止。只有探索性分析才设置 `continue_on_failure=True`。
   *EN: By default, let the pipeline stop at the failure. Set `continue_on_failure=True` only for exploratory analysis.*

## 17. 最小可用工作流
*EN: Minimum Usable Workflow*

给其它 agent 的最小工作流可以这样写：
*EN: A minimum workflow for other agents can be written as follows:*

```text
1. Ask the user what data they have and what output they want.
2. Select the smallest module that matches the request.
3. Map input fields using DataFrameSpec or module Params.
4. Call run(request).
5. If ok=False, report ModuleFailure and stop.
6. If ok=True, show the key fields from report.
7. Only compose multiple modules after each individual module works.
```

