# Agent Project Usage Guide

本文件是给其它 agent 使用 Quant Strategy Tokenizer 的操作指南。
EN: This file is an operating guide for other agents using Quant Strategy Tokenizer.

目标是让 agent 能够安全调用项目中的独立策略 token，完成研究、模拟、筛选、指标计算、信号组合和非执行型订单规划。
EN: The goal is to let agents safely call standalone strategy tokens for research, simulation, screening, indicator calculation, signal composition, and non-executing order planning.

## 1. Agent 启动提示词

EN: Agent startup prompt.

```text
You are using the local `quant_strategy_tokenizer` package.

Your job is to compose small, standalone trading-strategy modules from caller-provided data.

Hard rules:
- Do not fetch market data unless the user explicitly asks for a separate data adapter.
- Do not call exchanges, place orders, cancel orders, read live account state, or modify deployments.
- Every module call must check `ModuleResult.ok` before reading `ModuleResult.value`.
- If `ok=False`, treat `ModuleResult.failure` as authoritative and stop or report the failure.
- Do not convert unknown, unavailable, invalid, or missing data into empty successful output.
- Use `DataFrameSpec` or `ExtractorSpec` when user data fields are nonstandard.
- Use `ModuleRunContext(output_dir=...)` only when the user wants formatted files.
- Test one module in isolation before composing it into a pipeline.

When replying to the user:
- Name the module used.
- Describe the input shape and field mapping.
- Show the key report fields.
- Surface warnings and failures clearly.
- Say explicitly that QST modules do not execute trades.
```

## 2. 公共调用标准

EN: Common calling standard.

多数 QST 模块遵循同一种接口。
EN: Most QST modules follow the same interface.

```text
Params / Request / Report / normalize_input(request) / run(request)
```

标准流程如下。
EN: Use the following standard flow.

1. 明确用户要的是指标、筛选、投票、风控、候选池、订单计划，还是报告文件。
   EN: Identify whether the user wants indicators, filters, voting, risk control, candidate pools, order plans, or report files.
2. 选择最小可用模块。
   EN: Select the smallest module that can answer the request.
3. 准备用户传入的数据，不让模块自己拉数据。
   EN: Prepare caller-provided data and do not let the module fetch data.
4. 用 `DataFrameSpec` 或 `ExtractorSpec` 显式映射非标准字段。
   EN: Use `DataFrameSpec` or `ExtractorSpec` for nonstandard fields.
5. 构造 `Params` 和 `Request`。
   EN: Construct `Params` and `Request`.
6. 调用 `run(request)`。
   EN: Call `run(request)`.
7. 先检查 `result.ok`，再读取 `result.value`。
   EN: Check `result.ok` before reading `result.value`.
8. 需要落盘时，在 `ModuleRunContext` 中设置 `output_dir`。
   EN: Set `output_dir` in `ModuleRunContext` only when file output is needed.

通用失败处理模板。
EN: Generic failure handling template.

```python
result = run_module(request)

if not result.ok:
    failure = result.failure
    response = {
        "status": "failed",
        "kind": failure.kind,
        "message": failure.message,
        "field": failure.field,
        "details": failure.details,
        "warnings": result.warnings,
    }
else:
    report = result.value
```

## 3. 项目地图

EN: Project map.

核心基础层。
EN: Core foundation layer.

- `contracts.py`: `ModuleResult`, `ModuleFailure`, `ModuleEvent`, `DataFrameSpec`, `ExtractorSpec`, `ModuleRunContext`。
  EN: Shared result, failure, event, schema, extractor, and runtime context contracts.
- `normalization.py`: 把 raw data 归一化为模块可计算的表格。
  EN: Normalizes raw data into tables that modules can calculate on.
- `pipeline.py`: 用小型数据总线组合多个模块。
  EN: Composes modules through a small data bus.
- `reporting.py`: 写入 redacted JSON / JSONL 报告。
  EN: Writes redacted JSON / JSONL reports.

指标层。
EN: Indicator layer.

- `indicators/ema.py`, `atr.py`, `vwap.py`, `chop.py`: 基础指标。
  EN: Base indicators.
- `indicators/spike.py`, `rolling_return.py`, `beta_residual.py`, `mrq_touch.py`: 特征和诊断指标。
  EN: Feature and diagnostic indicators.
- `indicators/trend_common.py`: 趋势指标共享归一化、后端、计算和报告逻辑。
  EN: Shared normalization, backend, calculation, and report logic for trend indicators.
- `indicators/<trend_token>.py`: 一个趋势指标一个独立 token。
  EN: One independent token per trend indicator.
- `indicators/momentum_common.py`: 动量指标共享归一化、后端、计算和报告逻辑。
  EN: Shared normalization, backend, calculation, and report logic for momentum indicators.
- `indicators/<momentum_token>.py`: 一个动量指标一个独立 token。
  EN: One independent token per momentum indicator.
- `indicators/volatility_common.py`: 波动指标共享归一化、后端、计算和报告逻辑。
  EN: Shared normalization, backend, calculation, and report logic for volatility indicators.
- `indicators/<volatility_token>.py`: 一个波动指标一个独立 token。
  EN: One independent token per volatility indicator.
- `indicators/volume_common.py`: 成交量指标共享归一化、后端、计算和报告逻辑。
  EN: Shared normalization, backend, calculation, and report logic for volume indicators.
- `indicators/<volume_token>.py`: 一个成交量指标一个独立 token。
  EN: One independent token per volume indicator.
- `indicators/structure_common.py`: 结构指标共享归一化、局部极值、水平聚类、突破检测、profile 近似和报告逻辑。
  EN: Shared normalization, local extrema, level clustering, breakout detection, profile approximation, and report logic for structure indicators.
- `indicators/<structure_token>.py`: 一个结构指标一个独立 token。
  EN: One independent token per structure indicator.
- `indicators/breadth_common.py`: 宽度指标共享面板/宽表/聚合序列归一化、市场内部参与度计算和报告逻辑。
  EN: Shared normalization, market-internal participation calculation, and report logic for breadth indicators from panels, wide matrices, or aggregate rows.
- `indicators/<breadth_token>.py`: 一个宽度指标一个独立 token。
  EN: One independent token per breadth indicator.
- `indicators/derivatives_common.py`: 衍生品指标共享期货/永续、期权链和聚合诊断序列的归一化、压力计算和报告逻辑。
  EN: Shared normalization, pressure calculation, and report logic for futures/perpetuals, option chains, and aggregate derivatives diagnostics.
- `indicators/<derivatives_token>.py`: 一个衍生品指标一个独立 token。
  EN: One independent token per derivatives indicator.
- `indicators/onchain_common.py`: 链上指标共享网络、交易所流、持有人、稳定币、矿工/验证者、费用和 age-bucket 数据的归一化、压力计算和报告逻辑。
  EN: Shared normalization, pressure calculation, and report logic for network, exchange-flow, holder, stablecoin, miner/validator, fee, and age-bucket on-chain data.
- `indicators/<onchain_token>.py`: 一个链上指标一个独立 token。
  EN: One independent token per on-chain indicator.

策略组合层。
EN: Strategy composition layer.

- `universe_selector.py`: 候选池 universe 选择。
  EN: Candidate universe selection.
- `signal_trigger.py`: 基于 price / center / width 生成 long / short / none。
  EN: Generates long / short / none from price / center / width.
- `vote_engine.py`: 聚合多个 judge。
  EN: Aggregates multiple judges.
- `candidate_pool.py`: 组合筛选、投票和排序结果。
  EN: Combines filtering, voting, and ranking results.
- `market_freeze.py`: 根据市场宽度决定是否 block new risk。
  EN: Blocks or allows new risk from market breadth.
- `order_planner.py`: 生成 venue-neutral order plan，不执行交易。
  EN: Produces venue-neutral order plans without executing trades.
- `position_reconciler.py`: 对比观察仓位和目标仓位。
  EN: Reconciles observed positions with target state.
- `state_model.py`: 状态 schema 和实例隔离检查。
  EN: State schema and instance isolation checks.

## 4. 趋势指标 Token 总览

EN: Trend indicator token overview.

趋势指标 token 已经实现为独立模块。
EN: Trend indicators are implemented as independent modules.

每个趋势 token 都接受用户传入的数据，不拉行情、不连接交易所、不下单。
EN: Every trend token processes caller-provided data only; it does not fetch data, connect to venues, or place orders.

公共输出是 `ModuleResult[TrendReport]`。
EN: The common output is `ModuleResult[TrendReport]`.

`TrendReport` 的关键字段如下。
EN: Key `TrendReport` fields are listed below.

- `quality`: 计算质量，例如 `ok`。
  EN: Calculation quality, for example `ok`.
- `indicator`: 指标名称。
  EN: Indicator name.
- `last_value`: 主输出的最新有效值。
  EN: Latest valid value of the primary output.
- `last_values`: 多线指标的最新值字典。
  EN: Dictionary of latest values for multi-line indicators.
- `trend_direction`: `bullish`, `bearish`, `neutral`, `mixed`, `trend`, `cycle`, or `unknown`。
  EN: Direction label such as `bullish`, `bearish`, `neutral`, `mixed`, `trend`, `cycle`, or `unknown`.
- `trend_strength`: 趋势强度或距离度量。
  EN: Trend strength or distance measure.
- `signal`: 交叉、方向或状态信号。
  EN: Cross, direction, or state signal.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.
- `summary`: 行数、后端、输入类型和指标摘要。
  EN: Rows, backend, input kind, and indicator summary.
- `used_fields`: 实际使用的输入字段映射。
  EN: Actual input field mapping used.
- `warnings` / `diagnostics`: 警告和诊断信息。
  EN: Warnings and diagnostics.

后端规则。
EN: Backend rules.

- `backend="native"`: 默认值，使用 `numpy` / `pandas`。
  EN: Default backend using `numpy` / `pandas`.
- `backend="talib"`: 要求安装 TA-Lib；不可用时返回 `unavailable_backend`。
  EN: Requires TA-Lib; returns `unavailable_backend` when unavailable.
- `backend="auto"`: 只在 TA-Lib 已安装且该 token 支持时使用 TA-Lib，否则使用 native。
  EN: Uses TA-Lib only when installed and supported for the token; otherwise uses native.

## 5. 趋势指标清单

EN: Trend indicator list.

| Family | Tokens |
| --- | --- |
| Moving averages | `sma`, `wma`, `smma`, `dema`, `tema`, `trima`, `t3`, `hma`, `kama`, `zlema`, `mcginley_dynamic`, `vwma` |
| Trend / momentum hybrids | `macd`, `ppo`, `apo` |
| Direction and strength | `adx`, `adxr`, `dmi`, `aroon`, `aroon_oscillator`, `vortex` |
| Stops and channels | `parabolic_sar`, `supertrend`, `donchian_channel`, `keltner_channel`, `chandelier_exit`, `atr_trailing_stop` |
| Structured trend systems | `ichimoku_cloud`, `alligator`, `ma_cross`, `ma_ribbon`, `gmma` |
| Linear regression trend | `linear_regression`, `linear_regression_slope`, `linear_regression_angle`, `linear_regression_r2`, `least_squares_moving_average`, `time_series_forecast` |
| Hilbert / MESA / Ehlers | `mama`, `ht_trendline`, `ht_trendmode`, `ht_sinewave`, `ht_phasor`, `ht_dominant_cycle_period`, `ht_dominant_cycle_phase` |
| Composite trend scoring | `trend_strength_index`, `chande_trend_meter` |

## 6. 动量指标 Token 总览

EN: Momentum indicator token overview.

动量指标 token 已经实现为独立模块。
EN: Momentum indicators are implemented as independent modules.

每个动量 token 都接受用户传入的数据，不拉行情、不连接交易所、不下单。
EN: Every momentum token processes caller-provided data only; it does not fetch data, connect to venues, or place orders.

公共输出是 `ModuleResult[MomentumReport]`。
EN: The common output is `ModuleResult[MomentumReport]`.

`MomentumReport` 的关键字段如下。
EN: Key `MomentumReport` fields are listed below.

- `quality`: 计算质量，例如 `ok`。
  EN: Calculation quality, for example `ok`.
- `indicator`: 指标名称。
  EN: Indicator name.
- `last_value`: 主输出的最新有效值。
  EN: Latest valid value of the primary output.
- `last_values`: 多线指标的最新值字典。
  EN: Dictionary of latest values for multi-line indicators.
- `momentum_direction`: `bullish`, `bearish`, `neutral`, `mixed`, or `unknown`。
  EN: Direction label such as `bullish`, `bearish`, `neutral`, `mixed`, or `unknown`.
- `momentum_strength`: 动量强度、距离或标准化强度。
  EN: Momentum strength, distance, or normalized strength.
- `signal`: 交叉、方向、超买超卖或状态信号。
  EN: Cross, direction, overbought/oversold, or state signal.
- `zone`: `overbought`, `oversold`, `neutral`, `bullish`, `bearish`, or `unknown`。
  EN: Zone label such as `overbought`, `oversold`, `neutral`, `bullish`, `bearish`, or `unknown`.
- `overbought` / `oversold`: 当前报告使用的阈值。
  EN: Thresholds used by the current report.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.

## 7. 动量指标清单

EN: Momentum indicator list.

| Family | Tokens |
| --- | --- |
| Bounded oscillators | `rsi`, `stochastic_oscillator`, `stochastic_fast`, `stochastic_rsi`, `cci`, `cmo`, `williams_r`, `ultimate_oscillator`, `mfi`, `demarker`, `relative_momentum_index` |
| Rate-of-change | `momentum`, `roc`, `rocp`, `rocr`, `rocr100`, `trix`, `dpo`, `chande_forecast_oscillator` |
| Multi-line momentum | `kst`, `true_strength_index`, `relative_vigor_index`, `fisher_transform`, `stochastic_momentum_index`, `kdj` |
| Price/volume pressure | `bop`, `awesome_oscillator`, `accelerator_oscillator`, `elder_ray`, `qstick`, `coppock_curve`, `connors_rsi` |

## 8. 波动指标 Token 总览

EN: Volatility indicator token overview.

波动指标 token 已经实现为独立模块。
EN: Volatility indicators are implemented as independent modules.

每个波动 token 都只处理用户传入的数据，不拉行情、不连接交易所、不读账户、不下单。
EN: Every volatility token processes caller-provided data only; it does not fetch data, connect to venues, read accounts, or place orders.

公共输出是 `ModuleResult[VolatilityReport]`。
EN: The common output is `ModuleResult[VolatilityReport]`.

`VolatilityReport` 的关键字段如下。
EN: Key `VolatilityReport` fields are listed below.

- `quality`: 计算质量，例如 `ok`。
  EN: Calculation quality, for example `ok`.
- `indicator`: 指标名称。
  EN: Indicator name.
- `last_value`: 主输出的最新有效值。
  EN: Latest valid value of the primary output.
- `last_values`: 多线指标的最新值字典。
  EN: Dictionary of latest values for multi-line indicators.
- `volatility_direction`: `expanding`, `contracting`, `stable`, or `unknown`。
  EN: Volatility direction label such as `expanding`, `contracting`, `stable`, or `unknown`.
- `volatility_level`: `low`, `normal`, `high`, `extreme`, or `unknown`。
  EN: Volatility level label such as `low`, `normal`, `high`, `extreme`, or `unknown`.
- `signal`: 压缩、扩张、风险升高或状态信号。
  EN: Compression, expansion, risk, or state signal.
- `regime`: 波动状态标签。
  EN: Volatility regime label.
- `normalized_value`: 通常是 0-100 的滚动百分位或标准化强度。
  EN: Usually a 0-100 rolling percentile or normalized intensity.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.

## 9. 波动指标清单

EN: Volatility indicator list.

| Family | Tokens |
| --- | --- |
| Range / ATR | `true_range`, `natr`, `high_low_range`, `rolling_range`, `average_range`, `gap_range`, `range_percent`, `range_expansion` |
| Statistical volatility | `rolling_stddev`, `rolling_variance`, `historical_volatility`, `realized_volatility`, `ewma_volatility`, `parkinson_volatility`, `garman_klass_volatility`, `rogers_satchell_volatility`, `yang_zhang_volatility`, `downside_volatility`, `volatility_of_volatility` |
| Bands and squeeze | `bollinger_bands`, `bollinger_bandwidth`, `percent_b`, `zscore`, `zscore_bands`, `ttm_squeeze`, `bollinger_keltner_squeeze` |
| Regime and special | `chaikin_volatility`, `mass_index`, `ulcer_index`, `relative_volatility_index`, `inertia`, `vertical_horizontal_filter`, `volatility_ratio`, `volatility_regime` |

## 10. 示例：调用一个波动指标
EN: Example: call one volatility indicator.

适用场景：用户传入价格序列，希望判断当前波动处在历史百分位的哪个状态。
EN: Use case: the user provides price rows and wants the current volatility percentile regime.

```python
from quant_strategy_tokenizer.indicators.volatility_regime import (
    VolatilityRegimeParams,
    VolatilityRegimeRequest,
    run as run_volatility_regime,
)

result = run_volatility_regime(
    VolatilityRegimeRequest(
        data=bars,
        params=VolatilityRegimeParams(window=20, regime_window=100),
    )
)

if result.ok:
    report = result.value
    print(report.regime, report.normalized_value, report.volatility_direction)
else:
    print(result.failure.kind, result.failure.message)
```

## 11. 示例：组合多个波动 token
EN: Example: compose multiple volatility tokens.

多个波动指标通常都需要原始行情，因此在 pipeline 中使用 `input_key="initial"`。
EN: Multiple volatility indicators usually need the original market data, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.atr import ATRParams, ATRRequest, run as run_atr
from quant_strategy_tokenizer.indicators.bollinger_bandwidth import (
    BollingerBandwidthParams,
    BollingerBandwidthRequest,
    run as run_bandwidth,
)
from quant_strategy_tokenizer.indicators.volatility_regime import (
    VolatilityRegimeParams,
    VolatilityRegimeRequest,
    run as run_regime,
)

steps = [
    PipelineStep(
        name="atr",
        input_key="initial",
        output_key="atr_last",
        take="last_value",
        fn=lambda data: run_atr(ATRRequest(data=data, params=ATRParams())),
    ),
    PipelineStep(
        name="bandwidth",
        input_key="initial",
        output_key="bandwidth_last",
        take="last_value",
        fn=lambda data: run_bandwidth(BollingerBandwidthRequest(data=data, params=BollingerBandwidthParams())),
    ),
    PipelineStep(
        name="regime",
        input_key="initial",
        output_key="vol_regime",
        take="regime",
        fn=lambda data: run_regime(VolatilityRegimeRequest(data=data, params=VolatilityRegimeParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "atr": state.get("atr_last"),
                "bandwidth": state.get("bandwidth_last"),
                "regime": state.get("vol_regime"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=bars, steps=steps)
```

## 12. 成交量指标 Token 总览

EN: Volume indicator token overview.

成交量指标 token 已经实现为独立模块。
EN: Volume indicators are implemented as independent modules.

每个成交量 token 都只处理用户传入的数据，不拉行情、不连接交易所、不读账户、不下单。
EN: Every volume token processes caller-provided data only; it does not fetch data, connect to venues, read accounts, or place orders.

公共输出是 `ModuleResult[VolumeReport]`。
EN: The common output is `ModuleResult[VolumeReport]`.

`VolumeReport` 的关键字段如下。
EN: Key `VolumeReport` fields are listed below.

- `quality`: 计算质量，例如 `ok`。
  EN: Calculation quality, for example `ok`.
- `indicator`: 指标名称。
  EN: Indicator name.
- `last_value`: 主输出的最新有效值。
  EN: Latest valid value of the primary output.
- `last_values`: 多线指标的最新值字典。
  EN: Dictionary of latest values for multi-line indicators.
- `volume_direction`: `increasing`, `decreasing`, `stable`, `mixed`, or `unknown`。
  EN: Volume direction label such as `increasing`, `decreasing`, `stable`, `mixed`, or `unknown`.
- `volume_level`: `dry_up`, `low`, `normal`, `high`, `extreme`, or `unknown`。
  EN: Volume level label such as `dry_up`, `low`, `normal`, `high`, `extreme`, or `unknown`.
- `flow_direction`: `accumulation`, `distribution`, `neutral`, or `unknown`。
  EN: Flow direction label such as `accumulation`, `distribution`, `neutral`, or `unknown`.
- `signal`: 放量、缩量、资金流或确认状态信号。
  EN: Expansion, dry-up, flow, or confirmation signal.
- `regime`: 成交量状态标签。
  EN: Volume regime label.
- `normalized_value`: 通常是 0-100 的滚动百分位或标准化强度。
  EN: Usually a 0-100 rolling percentile or normalized intensity.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.

## 13. 成交量指标清单

EN: Volume indicator list.

| Family | Tokens |
| --- | --- |
| Raw volume / regime | `volume_sma`, `volume_ema`, `volume_roc`, `volume_zscore`, `relative_volume`, `volume_percentile`, `volume_spike`, `volume_dry_up`, `volume_trend`, `volume_oscillator` |
| Accumulation / distribution | `obv`, `accumulation_distribution_line`, `chaikin_money_flow`, `chaikin_oscillator`, `volume_price_trend`, `positive_volume_index`, `negative_volume_index` |
| Flow / pressure | `force_index`, `ease_of_movement`, `intraday_intensity`, `money_flow_volume`, `klinger_oscillator`, `volume_flow_indicator`, `demand_index` |
| Proxy diagnostics | `signed_volume_proxy`, `cumulative_signed_volume_proxy`, `price_volume_divergence`, `volume_confirmation` |
| Existing price-volume tokens | `mfi`, `vwma`, `vwap` |

## 14. 示例：调用一个成交量指标
EN: Example: call one volume indicator.

适用场景：用户传入 OHLCV 行情，希望判断当前成交量相对近期均量是否异常。
EN: Use case: the user provides OHLCV rows and wants to judge whether current volume is abnormal versus recent average volume.

```python
from quant_strategy_tokenizer.indicators.relative_volume import (
    RelativeVolumeParams,
    RelativeVolumeRequest,
    run as run_relative_volume,
)

result = run_relative_volume(
    RelativeVolumeRequest(
        data=bars,
        params=RelativeVolumeParams(window=20, spike_multiplier=2.5),
    )
)

if result.ok:
    report = result.value
    print(report.last_value, report.volume_level, report.signal)
else:
    print(result.failure.kind, result.failure.message)
```

## 15. 示例：组合多个成交量 token
EN: Example: compose multiple volume tokens.

多个成交量指标通常都需要原始行情，因此在 pipeline 中使用 `input_key="initial"`。
EN: Multiple volume indicators usually need the original market data, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.relative_volume import RelativeVolumeParams, RelativeVolumeRequest, run as run_relative_volume
from quant_strategy_tokenizer.indicators.obv import OBVParams, OBVRequest, run as run_obv
from quant_strategy_tokenizer.indicators.volume_confirmation import (
    VolumeConfirmationParams,
    VolumeConfirmationRequest,
    run as run_confirmation,
)

steps = [
    PipelineStep(
        name="relative_volume",
        input_key="initial",
        output_key="rv_last",
        take="last_value",
        fn=lambda data: run_relative_volume(RelativeVolumeRequest(data=data, params=RelativeVolumeParams())),
    ),
    PipelineStep(
        name="obv",
        input_key="initial",
        output_key="obv_flow",
        take="flow_direction",
        fn=lambda data: run_obv(OBVRequest(data=data, params=OBVParams())),
    ),
    PipelineStep(
        name="confirmation",
        input_key="initial",
        output_key="confirmation_signal",
        take="signal",
        fn=lambda data: run_confirmation(VolumeConfirmationRequest(data=data, params=VolumeConfirmationParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "relative_volume": state.get("rv_last"),
                "obv_flow": state.get("obv_flow"),
                "confirmation": state.get("confirmation_signal"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=bars, steps=steps)
```

## 16. 结构类指标 Token 总览

EN: Structure indicator token overview.

结构类指标 token 已经实现为独立模块。
EN: Structure indicators are implemented as independent modules.

每个结构 token 都只处理用户传入的数据，不拉行情、不连接交易所、不读账户、不下单。
EN: Every structure token processes caller-provided data only; it does not fetch data, connect to venues, read accounts, or place orders.

公共输出是 `ModuleResult[StructureReport]`。
EN: The common output is `ModuleResult[StructureReport]`.

`StructureReport` 的关键字段如下。
EN: Key `StructureReport` fields are listed below.

- `quality`: 计算质量，例如 `ok`。
  EN: Calculation quality, for example `ok`.
- `indicator`: 指标名称。
  EN: Indicator name.
- `last_value`: 主输出的最新有效值。
  EN: Latest valid value of the primary output.
- `last_values`: 多输出结构指标的最新值字典。
  EN: Dictionary of latest values for multi-output structure indicators.
- `structure_bias`: `bullish`, `bearish`, `range`, `mixed`, or `unknown`。
  EN: Structure bias label such as `bullish`, `bearish`, `range`, `mixed`, or `unknown`.
- `structure_state`: `breakout`, `breakdown`, `retest`, `sweep`, `consolidation`, `expansion`, `neutral`, or `unknown`。
  EN: Structure state label such as `breakout`, `breakdown`, `retest`, `sweep`, `consolidation`, `expansion`, `neutral`, or `unknown`.
- `nearest_support` / `nearest_resistance`: 离当前价格最近的支撑和阻力。
  EN: Nearest support and resistance around the current price.
- `levels`: 结构化水平列表，包含 `price`, `kind`, `strength`, `touch_count`, `last_touch_index`。
  EN: Structured level list with `price`, `kind`, `strength`, `touch_count`, and `last_touch_index`.
- `zones`: 结构化区域列表，包含 `lower`, `upper`, `kind`, `strength`。
  EN: Structured zone list with `lower`, `upper`, `kind`, and `strength`.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.
- `warnings` / `diagnostics`: 警告和诊断；profile 与 order-block proxy 会明确标注为 OHLCV 近似。
  EN: Warnings and diagnostics; profile and order-block proxies explicitly mark OHLCV approximation.

## 17. 结构类指标清单

EN: Structure indicator list.

| Family | Tokens |
| --- | --- |
| Swing / market structure | `swing_points`, `fractal_pivots`, `zigzag_structure`, `higher_high_lower_low`, `market_structure_shift`, `break_of_structure`, `change_of_character`, `trendline_structure` |
| Support / resistance | `pivot_points`, `rolling_support_resistance`, `support_resistance_zones`, `nearest_support_resistance`, `level_touch_count`, `breakout_detector`, `retest_detector`, `false_breakout_detector` |
| Range / consolidation | `range_box`, `consolidation_zone`, `inside_bar`, `outside_bar`, `narrow_range`, `wide_range`, `range_position`, `range_breakout_strength` |
| Gaps / liquidity proxies | `price_gap`, `fair_value_gap`, `liquidity_sweep`, `equal_highs_lows`, `order_block_proxy`, `supply_demand_zone` |
| Profile approximation | `volume_profile`, `market_profile`, `point_of_control`, `value_area`, `profile_acceptance` |

## 18. 示例：组合多个结构 token

EN: Example: compose multiple structure tokens.

多数结构类模块都需要原始 OHLC 或 OHLCV 行情，因此在 pipeline 中使用 `input_key="initial"`。
EN: Most structure tokens need the original OHLC or OHLCV data, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.swing_points import SwingPointsParams, SwingPointsRequest, run as run_swings
from quant_strategy_tokenizer.indicators.support_resistance_zones import (
    SupportResistanceZonesParams,
    SupportResistanceZonesRequest,
    run as run_zones,
)
from quant_strategy_tokenizer.indicators.breakout_detector import (
    BreakoutDetectorParams,
    BreakoutDetectorRequest,
    run as run_breakout,
)

steps = [
    PipelineStep(
        name="swing_points",
        input_key="initial",
        output_key="swing_bias",
        take="structure_bias",
        fn=lambda data: run_swings(SwingPointsRequest(data=data, params=SwingPointsParams())),
    ),
    PipelineStep(
        name="zones",
        input_key="initial",
        output_key="nearest_resistance",
        take="nearest_resistance",
        fn=lambda data: run_zones(SupportResistanceZonesRequest(data=data, params=SupportResistanceZonesParams())),
    ),
    PipelineStep(
        name="breakout",
        input_key="initial",
        output_key="breakout_state",
        take="structure_state",
        fn=lambda data: run_breakout(BreakoutDetectorRequest(data=data, params=BreakoutDetectorParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "swing_bias": state.get("swing_bias"),
                "nearest_resistance": state.get("nearest_resistance"),
                "breakout_state": state.get("breakout_state"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=bars, steps=steps)
```

## 19. 宽度类指标 Token 总览

EN: Breadth indicator token overview.

宽度类指标 token 已经实现为独立模块。
EN: Breadth indicators are implemented as independent modules.

每个宽度 token 都只处理用户传入的数据，不拉行情、不连接交易所、不读账户、不下单。
EN: Every breadth token processes caller-provided data only; it does not fetch data, connect to venues, read accounts, or place orders.

公共输出是 `ModuleResult[BreadthReport]`。
EN: The common output is `ModuleResult[BreadthReport]`.

宽度 token 支持三类输入：long panel rows/DataFrame、wide close matrix、aggregate breadth rows。
EN: Breadth tokens support long panel rows/DataFrames, wide close matrices, and aggregate breadth rows.

- long panel 默认字段：`ts`, `symbol`, `close`，可选 `volume`, `weight`, `index_close`。
  EN: Long panels default to `ts`, `symbol`, and `close`, with optional `volume`, `weight`, and `index_close`.
- aggregate 默认字段：`advances`, `declines`, `unchanged`, `up_volume`, `down_volume`, `new_highs`, `new_lows`, `index_close`。
  EN: Aggregate rows default to `advances`, `declines`, `unchanged`, `up_volume`, `down_volume`, `new_highs`, `new_lows`, and `index_close`.

`BreadthReport` 的关键字段如下。
EN: Key `BreadthReport` fields are listed below.

- `breadth_direction`: `bullish`, `bearish`, `neutral`, or `unknown`。
  EN: Breadth direction label such as `bullish`, `bearish`, `neutral`, or `unknown`.
- `breadth_state`: `broad_up`, `broad_down`, `mixed`, `thrust`, `divergence`, `freeze_pressure`, or `neutral` 等状态。
  EN: Breadth state labels such as `broad_up`, `broad_down`, `mixed`, `thrust`, `divergence`, `freeze_pressure`, or `neutral`.
- `participation_rate`: 有方向变化的成分占有效样本的比例。
  EN: Fraction of valid constituents with directional movement.
- `advance_count` / `decline_count` / `unchanged_count`: 上涨、下跌、无变化数量。
  EN: Advance, decline, and unchanged counts.
- `sample_count` / `coverage`: 有效样本数量和覆盖率。
  EN: Valid sample count and coverage ratio.
- `up_volume` / `down_volume`: 上涨成分和下跌成分对应成交量。
  EN: Volume associated with advancing and declining constituents.

## 20. 宽度类指标清单

EN: Breadth indicator list.

| Family | Tokens |
| --- | --- |
| Advance / decline | `advance_decline_line`, `advance_decline_ratio`, `advance_decline_percent`, `net_advances`, `absolute_breadth_index`, `breadth_thrust` |
| McClellan | `mcclellan_oscillator`, `mcclellan_summation_index`, `mcclellan_ratio_adjusted_oscillator` |
| New high / new low | `new_highs`, `new_lows`, `net_new_highs`, `new_high_new_low_ratio`, `high_low_index`, `cumulative_new_highs_new_lows` |
| Percent participation | `percent_positive_return`, `percent_above_ma`, `percent_above_ema`, `percent_above_threshold`, `percent_near_high`, `percent_near_low` |
| Volume breadth | `up_down_volume_ratio`, `up_down_volume_line`, `volume_advance_decline_percent`, `arms_index`, `trin`, `volume_breadth_thrust` |
| Cross-sectional diagnostics | `cross_sectional_dispersion`, `cross_sectional_correlation_proxy`, `equal_weighted_return`, `cap_weighted_breadth`, `breadth_momentum`, `breadth_regime` |
| Divergence / confirmation | `index_breadth_divergence`, `breadth_confirmation`, `breadth_freeze_pressure` |

## 21. 示例：组合多个宽度 token

EN: Example: compose multiple breadth tokens.

宽度类模块通常需要同一份跨标的行情或聚合宽度序列，因此在 pipeline 中使用 `input_key="initial"`。
EN: Breadth modules usually share the same cross-sectional market data or aggregate breadth rows, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.advance_decline_percent import (
    AdvanceDeclinePercentParams,
    AdvanceDeclinePercentRequest,
    run as run_ad_percent,
)
from quant_strategy_tokenizer.indicators.percent_above_ma import (
    PercentAboveMaParams,
    PercentAboveMaRequest,
    run as run_above_ma,
)
from quant_strategy_tokenizer.indicators.breadth_regime import (
    BreadthRegimeParams,
    BreadthRegimeRequest,
    run as run_breadth_regime,
)

steps = [
    PipelineStep(
        name="ad_percent",
        input_key="initial",
        output_key="ad_percent",
        take="last_value",
        fn=lambda data: run_ad_percent(AdvanceDeclinePercentRequest(data=data, params=AdvanceDeclinePercentParams())),
    ),
    PipelineStep(
        name="above_ma",
        input_key="initial",
        output_key="above_ma",
        take="last_value",
        fn=lambda data: run_above_ma(PercentAboveMaRequest(data=data, params=PercentAboveMaParams())),
    ),
    PipelineStep(
        name="regime",
        input_key="initial",
        output_key="breadth_regime",
        take="breadth_state",
        fn=lambda data: run_breadth_regime(BreadthRegimeRequest(data=data, params=BreadthRegimeParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "ad_percent": state.get("ad_percent"),
                "above_ma": state.get("above_ma"),
                "breadth_regime": state.get("breadth_regime"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=cross_sectional_rows, steps=steps)
```

## 22. 示例：调用一个动量指标

EN: Example: call one momentum indicator.

适用场景：用户传入价格序列，希望判断 RSI 动量状态。
EN: Use case: the user provides price rows and wants the RSI momentum state.

```python
from quant_strategy_tokenizer.indicators.rsi import RSIParams, RSIRequest, run as run_rsi

result = run_rsi(
    RSIRequest(
        data=bars,
        params=RSIParams(window=14, overbought=70, oversold=30),
    )
)

if result.ok:
    report = result.value
    print(report.last_value, report.momentum_direction, report.zone)
else:
    print(result.failure.kind, result.failure.message)
```

## 23. 示例：组合多个动量 token

EN: Example: compose multiple momentum tokens.

如果多个动量指标都需要原始行情，使用 `input_key="initial"`。
EN: If multiple momentum indicators need the original market data, use `input_key="initial"`.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.rsi import RSIParams, RSIRequest, run as run_rsi
from quant_strategy_tokenizer.indicators.mfi import MFIParams, MFIRequest, run as run_mfi

steps = [
    PipelineStep(
        name="rsi",
        input_key="initial",
        output_key="rsi_last",
        take="last_value",
        fn=lambda data: run_rsi(RSIRequest(data=data, params=RSIParams())),
    ),
    PipelineStep(
        name="mfi",
        input_key="initial",
        output_key="mfi_zone",
        take="zone",
        fn=lambda data: run_mfi(MFIRequest(data=data, params=MFIParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "rsi_last": state.get("rsi_last"),
                "mfi_zone": state.get("mfi_zone"),
                "rsi_direction": state.get("rsi.momentum_direction"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=bars, steps=steps)
```

## 24. 示例：调用一个趋势指标

EN: Example: call one trend indicator.

适用场景：用户传入 OHLC 行情，希望判断 Supertrend 方向。
EN: Use case: the user provides OHLC rows and wants the Supertrend direction.

```python
from quant_strategy_tokenizer.indicators.supertrend import (
    SupertrendParams,
    SupertrendRequest,
    run as run_supertrend,
)

bars = [
    {"open": 100, "high": 102, "low": 99, "close": 101},
    {"open": 101, "high": 104, "low": 100, "close": 103},
    # provide enough rows for the selected ATR window
]

result = run_supertrend(
    SupertrendRequest(
        data=bars,
        params=SupertrendParams(atr_window=10, multiplier=3.0),
    )
)

if result.ok:
    report = result.value
    print(report.trend_direction, report.signal, report.last_value)
else:
    print(result.failure.kind, result.failure.message)
```

## 25. 示例：非标准字段映射

EN: Example: nonstandard field mapping.

适用场景：用户的数据字段来自外部数据源，例如 `H/L/C/V`。
EN: Use case: user data comes from an external vendor with fields such as `H/L/C/V`.

```python
from quant_strategy_tokenizer.contracts import DataFrameSpec
from quant_strategy_tokenizer.indicators.vwma import VWMAParams, VWMARequest, run as run_vwma

rows = [
    {"C": 100, "V": 1200},
    {"C": 101, "V": 1500},
    {"C": 103, "V": 1800},
]

spec = DataFrameSpec(close_col="C", volume_col="V")

result = run_vwma(
    VWMARequest(
        data=rows,
        spec=spec,
        params=VWMAParams(window=3),
    )
)

if result.ok:
    print(result.value.last_value)
    print(result.value.used_fields)
else:
    print(result.failure.kind, result.failure.message)
```

## 26. 示例：请求完整序列

EN: Example: request full series.

默认情况下趋势 token 不返回大序列，避免输出膨胀。
EN: By default, trend tokens do not return large series to avoid bloated output.

需要完整序列时设置 `DetailLevel.FULL`。
EN: Set `DetailLevel.FULL` when full series are needed.

```python
from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.indicators.macd import MACDParams, MACDRequest, run as run_macd

ctx = ModuleRunContext(module="macd", detail_level=DetailLevel.FULL)

result = run_macd(
    MACDRequest(
        data=bars,
        params=MACDParams(fast_window=12, slow_window=26, signal_window=9),
        context=ctx,
    )
)

if result.ok:
    print(result.value.last_values)
    print(result.value.series_by_name["histogram"])
else:
    print(result.failure.kind, result.failure.message)
```

## 27. 示例：组合多个趋势 token

EN: Example: compose multiple trend tokens.

pipeline 不是隐藏 runner，它只是一个小型数据总线。
EN: The pipeline is not a hidden runner; it is only a small data bus.

如果多个指标都需要原始行情，使用 `input_key="initial"`。
EN: If multiple indicators need the original market data, use `input_key="initial"`.

```python
from quant_strategy_tokenizer.contracts import ModuleResult
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.sma import SMAParams, SMARequest, run as run_sma
from quant_strategy_tokenizer.indicators.macd import MACDParams, MACDRequest, run as run_macd

steps = [
    PipelineStep(
        name="sma",
        input_key="initial",
        output_key="sma_last",
        take="last_value",
        fn=lambda data: run_sma(SMARequest(data=data, params=SMAParams(window=20))),
    ),
    PipelineStep(
        name="macd",
        input_key="initial",
        output_key="macd_hist",
        take="last_values.histogram",
        fn=lambda data: run_macd(MACDRequest(data=data, params=MACDParams())),
    ),
    PipelineStep(
        name="summary",
        pass_state=True,
        fn=lambda state: ModuleResult.success(
            {
                "sma_last": state.get("sma_last"),
                "macd_hist": state.get("macd_hist"),
                "macd_direction": state.get("macd.trend_direction"),
            }
        ),
    ),
]

result = run_pipeline(initial_payload=bars, steps=steps)

if result.ok:
    print(result.value.final_payload)
else:
    print(result.failure.kind, result.failure.message)
```

## 28. 示例：写入标准报告文件

EN: Example: write standard report files.

适用场景：用户希望模拟或研究过程直接生成 JSON / JSONL 文件。
EN: Use case: the user wants JSON / JSONL files during simulation or research.

```python
from quant_strategy_tokenizer.contracts import DetailLevel, ModuleRunContext
from quant_strategy_tokenizer.indicators.trend_strength_index import (
    TrendStrengthIndexParams,
    TrendStrengthIndexRequest,
    run as run_tsi,
)

ctx = ModuleRunContext(
    module="trend_strength_index",
    run_id="example_trend_scan",
    detail_level=DetailLevel.FULL,
    output_dir="module_outputs",
)

result = run_tsi(
    TrendStrengthIndexRequest(
        data=bars,
        params=TrendStrengthIndexParams(window=20),
        context=ctx,
    )
)

if result.ok:
    print(result.files.summary_json)
    print(result.files.events_jsonl)
    print(result.files.data_json)
else:
    print(result.failure.kind, result.failure.message)
```

## 29. 衍生品类指标 Token 总览
EN: Derivatives indicator token overview.

衍生品指标被实现为独立模块。
EN: Derivatives indicators are implemented as independent modules.

每个衍生品 token 只处理用户传入的数据；它不拉取 funding、OI、清算、期权链或账户数据。
EN: Every derivatives token processes caller-provided data only; it does not fetch funding, OI, liquidation, option-chain, or account data.

公共输出是 `ModuleResult[DerivativesReport]`。
EN: The common output is `ModuleResult[DerivativesReport]`.

衍生品 token 支持三类输入：期货/永续单合约时间序列、期权链 long rows、用户已聚合的衍生品诊断序列。
EN: Derivatives tokens support futures/perpetual time series, option-chain long rows, and user-aggregated derivatives diagnostic rows.

`DerivativesReport` 的关键字段如下。
EN: Key `DerivativesReport` fields are listed below.

- `derivative_direction`: 衍生品指标方向，例如 `bullish`, `bearish`, `expanding`, `contracting`, `neutral`, or `unknown`。
  EN: Derivatives direction label such as `bullish`, `bearish`, `expanding`, `contracting`, `neutral`, or `unknown`.
- `risk_state`: 风险状态，例如 `low`, `normal`, `high`, `extreme`, or `unknown`。
  EN: Risk state such as `low`, `normal`, `high`, `extreme`, or `unknown`.
- `crowding_state`: 拥挤状态，例如 `long_crowded`, `short_crowded`, `balanced`, or `unknown`。
  EN: Crowding state such as `long_crowded`, `short_crowded`, `balanced`, or `unknown`.
- `term_structure_state`: 期限结构状态，例如 `contango`, `backwardation`, `normal`, `inverted`, or `unknown`。
  EN: Term-structure state such as `contango`, `backwardation`, `normal`, `inverted`, or `unknown`.
- `leverage_pressure`, `funding_pressure`, `oi_pressure`, `liquidation_pressure`: 杠杆、资金费率、持仓和清算压力诊断。
  EN: Leverage, funding, open-interest, and liquidation pressure diagnostics.
- `skew_state`: 期权偏斜状态，例如 `put_skew`, `call_skew`, or `flat`。
  EN: Options skew state such as `put_skew`, `call_skew`, or `flat`.
- `series` / `series_by_name`: 仅在 `DetailLevel.FULL` 或更高时返回完整序列。
  EN: Full series output, returned only at `DetailLevel.FULL` or above.
- `diagnostics`: proxy 模块会明确标注 `proxy=True`。
  EN: Proxy modules explicitly mark `proxy=True` in diagnostics.

## 30. 衍生品指标清单
EN: Derivatives indicator list.

| Family | Tokens |
| --- | --- |
| Funding | `funding_rate`, `funding_rate_zscore`, `funding_momentum`, `funding_regime`, `funding_crowding_score` |
| Open interest | `open_interest_change`, `open_interest_roc`, `open_interest_zscore`, `price_oi_divergence`, `oi_volume_ratio` |
| Basis / premium | `basis_rate`, `basis_zscore`, `basis_momentum`, `premium_index`, `mark_index_deviation`, `perp_spot_deviation` |
| Positioning / flow | `long_short_ratio`, `long_short_ratio_zscore`, `taker_buy_sell_ratio`, `taker_flow_imbalance`, `leverage_pressure_index` |
| Liquidation | `liquidation_imbalance`, `liquidation_pressure`, `long_liquidation_ratio`, `short_liquidation_ratio`, `liquidation_cascade_risk` |
| Composite futures diagnostics | `derivatives_crowding_index`, `perp_risk_regime`, `futures_curve_pressure` |
| IV level / term structure | `implied_volatility`, `iv_rank`, `iv_percentile`, `iv_term_structure`, `front_back_iv_spread` |
| Skew / smile | `put_call_iv_skew`, `risk_reversal`, `butterfly_skew`, `smile_curvature`, `atm_iv_skew` |
| Put-call / activity | `put_call_volume_ratio`, `put_call_open_interest_ratio`, `option_volume_oi_ratio` |
| Greeks exposure proxies | `gamma_exposure`, `delta_exposure`, `vega_exposure`, `theta_exposure`, `dealer_gamma_proxy` |
| Composite options diagnostics | `options_crowding_index`, `volatility_risk_premium_proxy`, `max_pain_proxy` |

## 31. 示例：组合多个衍生品 token
EN: Example: compose multiple derivatives tokens.

多个衍生品指标通常需要同一份期货/永续序列或期权链，因此在 pipeline 中使用 `input_key="initial"`。
EN: Multiple derivatives indicators usually need the same futures/perpetual series or option chain, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.funding_rate_zscore import FundingRateZScoreRequest, run as run_funding
from quant_strategy_tokenizer.indicators.open_interest_change import OpenInterestChangeRequest, run as run_oi
from quant_strategy_tokenizer.indicators.basis_rate import BasisRateRequest, run as run_basis
from quant_strategy_tokenizer.indicators.derivatives_crowding_index import DerivativesCrowdingIndexRequest, run as run_crowding

steps = [
    PipelineStep(
        name="funding",
        input_key="initial",
        output_key="funding_z",
        take="last_value",
        fn=lambda data: run_funding(FundingRateZScoreRequest(data=data)),
    ),
    PipelineStep(
        name="oi",
        input_key="initial",
        output_key="oi_change",
        take="last_value",
        fn=lambda data: run_oi(OpenInterestChangeRequest(data=data)),
    ),
    PipelineStep(
        name="basis",
        input_key="initial",
        output_key="basis_rate",
        take="last_value",
        fn=lambda data: run_basis(BasisRateRequest(data=data)),
    ),
    PipelineStep(
        name="crowding",
        input_key="initial",
        output_key="risk_state",
        take="risk_state",
        fn=lambda data: run_crowding(DerivativesCrowdingIndexRequest(data=data)),
    ),
]

result = run_pipeline(initial_payload=perp_rows, steps=steps)
```

## 32. 链上类指标 Token 总览
EN: On-chain indicator token overview.

链上指标被实现为独立模块。
EN: On-chain indicators are implemented as independent modules.

每个链上 token 只处理用户传入的数据；它不连接链节点、不读取钱包、不拉取第三方数据、不读账户、不执行交易。
EN: Every on-chain token processes caller-provided data only; it does not connect to nodes, read wallets, fetch third-party data, read accounts, or execute trades.

公共输出是 `ModuleResult[OnChainReport]`。
EN: The common output is `ModuleResult[OnChainReport]`.

链上 token 支持三类输入：aggregate network series、UTXO/age-bucket rows、account/token-style rows。
EN: On-chain tokens support aggregate network series, UTXO/age-bucket rows, and account/token-style rows.

`OnChainReport` 的关键字段如下。
EN: Key `OnChainReport` fields are listed below.

- `network_activity_state`: 网络活跃状态，例如 `high_activity`, `normal_activity`, `low_activity`, or `unknown`。
  EN: Network activity state such as `high_activity`, `normal_activity`, `low_activity`, or `unknown`.
- `flow_state`: 交易所流状态，例如 `exchange_inflow_pressure`, `exchange_outflow_accumulation`, or `neutral`。
  EN: Exchange-flow state such as `exchange_inflow_pressure`, `exchange_outflow_accumulation`, or `neutral`.
- `holder_state`: 持有人行为状态，例如 `accumulation`, `distribution`, or `neutral`。
  EN: Holder behavior state such as `accumulation`, `distribution`, or `neutral`.
- `valuation_state`: 估值状态，例如 `undervalued`, `fair`, or `overvalued`。
  EN: Valuation state such as `undervalued`, `fair`, or `overvalued`.
- `liquidity_state`: 稳定币或流动性状态，例如 `expanding`, `contracting`, or `stable`。
  EN: Stablecoin or liquidity state such as `expanding`, `contracting`, or `stable`.
- `miner_validator_state`: 矿工或验证者压力状态，例如 `pressure`, `accumulation`, or `stable`。
  EN: Miner or validator pressure state such as `pressure`, `accumulation`, or `stable`.
- `diagnostics`: proxy 模块会明确标注 `proxy=True`。
  EN: Proxy modules explicitly mark `proxy=True` in diagnostics.

## 33. 链上指标清单
EN: On-chain indicator list.

| Family | Tokens |
| --- | --- |
| Network activity | `active_addresses`, `new_addresses`, `transaction_count`, `transaction_volume`, `transfer_volume_adjusted`, `network_activity_index`, `address_growth_rate`, `transaction_growth_rate` |
| Valuation / cost basis | `nvt_ratio`, `nvt_signal`, `mvrv_ratio`, `mvrv_zscore`, `realized_price`, `market_realized_gradient`, `supply_in_profit_proxy`, `realized_cap_change` |
| Exchange flows | `exchange_netflow`, `exchange_inflow_zscore`, `exchange_outflow_zscore`, `exchange_balance_change`, `exchange_reserve_ratio`, `exchange_flow_pressure`, `stablecoin_exchange_balance_change` |
| Holder behavior | `sopr`, `sopr_zscore`, `holder_age_trend`, `long_term_holder_supply_proxy`, `short_term_holder_supply_proxy`, `hodl_wave_proxy`, `whale_balance_change`, `retail_balance_change`, `whale_retail_divergence` |
| Liquidity / stablecoin | `stablecoin_supply_change`, `stablecoin_supply_ratio`, `stablecoin_liquidity_index`, `stablecoin_exchange_pressure` |
| Miner / validator | `miner_reserve_change`, `miner_flow_pressure`, `miner_capitulation_proxy`, `staking_deposit_withdrawal_ratio`, `staking_balance_change`, `validator_exit_pressure` |
| Fees / usage | `fee_pressure`, `gas_usage_trend`, `gas_price_zscore`, `fee_burn_pressure` |
| Composite diagnostics | `onchain_risk_regime`, `onchain_liquidity_regime`, `onchain_valuation_regime`, `onchain_accumulation_distribution`, `cycle_pressure_index` |

## 34. 示例：组合多个链上 token
EN: Example: compose multiple on-chain tokens.

多个链上指标通常需要同一份链上聚合序列或 age-bucket 行，因此在 pipeline 中使用 `input_key="initial"`。
EN: Multiple on-chain indicators usually need the same aggregate series or age-bucket rows, so use `input_key="initial"` in pipelines.

```python
from quant_strategy_tokenizer.pipeline import PipelineStep, run_pipeline
from quant_strategy_tokenizer.indicators.mvrv_zscore import MVRVZScoreRequest, run as run_mvrv
from quant_strategy_tokenizer.indicators.exchange_netflow import ExchangeNetflowRequest, run as run_netflow
from quant_strategy_tokenizer.indicators.stablecoin_liquidity_index import StablecoinLiquidityIndexRequest, run as run_stable
from quant_strategy_tokenizer.indicators.onchain_risk_regime import OnchainRiskRegimeRequest, run as run_risk

steps = [
    PipelineStep(
        name="mvrv",
        input_key="initial",
        output_key="mvrv_z",
        take="last_value",
        fn=lambda data: run_mvrv(MVRVZScoreRequest(data=data)),
    ),
    PipelineStep(
        name="netflow",
        input_key="initial",
        output_key="exchange_netflow",
        take="last_value",
        fn=lambda data: run_netflow(ExchangeNetflowRequest(data=data)),
    ),
    PipelineStep(
        name="stablecoin",
        input_key="initial",
        output_key="stablecoin_liquidity",
        take="last_value",
        fn=lambda data: run_stable(StablecoinLiquidityIndexRequest(data=data)),
    ),
    PipelineStep(
        name="risk",
        input_key="initial",
        output_key="risk_state",
        take="risk_state",
        fn=lambda data: run_risk(OnchainRiskRegimeRequest(data=data)),
    ),
]

result = run_pipeline(initial_payload=onchain_rows, steps=steps)
```

## 35. Agent 选择指南

EN: Agent selection guide.

如果用户说“帮我判断趋势方向”，优先使用 `supertrend`, `ma_cross`, `ma_ribbon`, `gmma`, `ichimoku_cloud`。
EN: If the user asks for trend direction, prefer `supertrend`, `ma_cross`, `ma_ribbon`, `gmma`, or `ichimoku_cloud`.

如果用户说“帮我算均线或平滑线”，使用 `sma`, `ema`, `wma`, `smma`, `dema`, `tema`, `trima`, `t3`, `hma`, `kama`, `zlema`, `mcginley_dynamic`, `vwma`。
EN: If the user asks for moving averages or smoothing, use `sma`, `ema`, `wma`, `smma`, `dema`, `tema`, `trima`, `t3`, `hma`, `kama`, `zlema`, `mcginley_dynamic`, or `vwma`.

如果用户说“帮我看趋势强度”，使用 `adx`, `adxr`, `dmi`, `vortex`, `trend_strength_index`, `chande_trend_meter`。
EN: If the user asks for trend strength, use `adx`, `adxr`, `dmi`, `vortex`, `trend_strength_index`, or `chande_trend_meter`.

如果用户说“帮我找趋势止损或通道”，使用 `parabolic_sar`, `supertrend`, `donchian_channel`, `keltner_channel`, `chandelier_exit`, `atr_trailing_stop`。
EN: If the user asks for trend stops or channels, use `parabolic_sar`, `supertrend`, `donchian_channel`, `keltner_channel`, `chandelier_exit`, or `atr_trailing_stop`.

如果用户说“帮我做趋势打分”，使用 `trend_strength_index` 或 `chande_trend_meter`，必要时再用 `pipeline.py` 聚合其它 token。
EN: If the user asks for trend scoring, use `trend_strength_index` or `chande_trend_meter`, and aggregate additional tokens through `pipeline.py` if needed.

如果用户说“帮我判断超买超卖”，优先使用 `rsi`, `stochastic_oscillator`, `stochastic_rsi`, `williams_r`, `mfi`, `demarker`。
EN: If the user asks for overbought/oversold state, prefer `rsi`, `stochastic_oscillator`, `stochastic_rsi`, `williams_r`, `mfi`, or `demarker`.

如果用户说“帮我判断速度或动量变化”，使用 `momentum`, `roc`, `rocp`, `trix`, `true_strength_index`, `kst`。
EN: If the user asks for speed or momentum change, use `momentum`, `roc`, `rocp`, `trix`, `true_strength_index`, or `kst`.

如果用户说“帮我看量价动量”，使用 `mfi`；如果只需要价格/蜡烛压力，使用 `bop`, `elder_ray`, `qstick`, `awesome_oscillator`。
EN: If the user asks for volume-price momentum, use `mfi`; for price/candle pressure, use `bop`, `elder_ray`, `qstick`, or `awesome_oscillator`.

如果用户说“帮我看波动、止损距离或风险区间”，使用 `atr`, `natr`, `true_range`, `historical_volatility`, `realized_volatility`。
EN: If the user asks for volatility, stop distance, or risk range, use `atr`, `natr`, `true_range`, `historical_volatility`, or `realized_volatility`.

如果用户说“帮我判断波动压缩或突破前的挤压”，使用 `bollinger_bandwidth`, `ttm_squeeze`, `bollinger_keltner_squeeze`, `range_expansion`。
EN: If the user asks for compression or pre-breakout squeeze, use `bollinger_bandwidth`, `ttm_squeeze`, `bollinger_keltner_squeeze`, or `range_expansion`.

如果用户说“帮我判断波动 regime”，使用 `volatility_regime`, `volatility_ratio`, `volatility_of_volatility`, `ulcer_index`。
EN: If the user asks for volatility regime, use `volatility_regime`, `volatility_ratio`, `volatility_of_volatility`, or `ulcer_index`.

如果用户说“帮我看放量、缩量或相对成交量”，使用 `relative_volume`, `volume_spike`, `volume_dry_up`, `volume_percentile`, `volume_oscillator`。
EN: If the user asks for volume expansion, dry-up, or relative volume, use `relative_volume`, `volume_spike`, `volume_dry_up`, `volume_percentile`, or `volume_oscillator`.

如果用户说“帮我看资金流、吸筹或派发”，使用 `obv`, `accumulation_distribution_line`, `chaikin_money_flow`, `chaikin_oscillator`, `volume_price_trend`。
EN: If the user asks for money flow, accumulation, or distribution, use `obv`, `accumulation_distribution_line`, `chaikin_money_flow`, `chaikin_oscillator`, or `volume_price_trend`.

如果用户说“帮我判断量价背离或成交量确认”，使用 `price_volume_divergence`, `volume_confirmation`；如果用户只有 OHLCV 而没有订单流，可使用 `signed_volume_proxy` 并明确这是代理估计。
EN: If the user asks for price-volume divergence or volume confirmation, use `price_volume_divergence` or `volume_confirmation`; if only OHLCV is available without order flow, use `signed_volume_proxy` and state that it is a proxy estimate.

如果用户说“帮我找支撑、阻力、关键价位或触碰次数”，使用 `support_resistance_zones`, `nearest_support_resistance`, `level_touch_count`, `pivot_points`。
EN: If the user asks for support, resistance, key levels, or touch counts, use `support_resistance_zones`, `nearest_support_resistance`, `level_touch_count`, or `pivot_points`.

如果用户说“帮我看市场结构、HH/LL、BOS 或 CHoCH”，使用 `higher_high_lower_low`, `market_structure_shift`, `break_of_structure`, `change_of_character`, `swing_points`。
EN: If the user asks for market structure, HH/LL, BOS, or CHoCH, use `higher_high_lower_low`, `market_structure_shift`, `break_of_structure`, `change_of_character`, or `swing_points`.

如果用户说“帮我判断箱体、盘整、突破、回踩或假突破”，使用 `range_box`, `consolidation_zone`, `breakout_detector`, `retest_detector`, `false_breakout_detector`, `range_breakout_strength`。
EN: If the user asks for ranges, consolidation, breakout, retest, or false breakout, use `range_box`, `consolidation_zone`, `breakout_detector`, `retest_detector`, `false_breakout_detector`, or `range_breakout_strength`.

如果用户说“帮我看缺口、流动性扫点、等高等低或 profile”，使用 `price_gap`, `fair_value_gap`, `liquidity_sweep`, `equal_highs_lows`, `volume_profile`, `point_of_control`, `value_area`；对 `order_block_proxy` 和 profile 模块必须说明它们只是 OHLCV 近似。
EN: If the user asks for gaps, liquidity sweeps, equal highs/lows, or profile, use `price_gap`, `fair_value_gap`, `liquidity_sweep`, `equal_highs_lows`, `volume_profile`, `point_of_control`, or `value_area`; for `order_block_proxy` and profile modules, state that they are OHLCV approximations.

如果用户说“帮我看市场宽度、上涨下跌家数、内部参与度”，使用 `advance_decline_percent`, `advance_decline_line`, `net_advances`, `percent_positive_return`, `breadth_regime`。
EN: If the user asks for market breadth, advance/decline counts, or internal participation, use `advance_decline_percent`, `advance_decline_line`, `net_advances`, `percent_positive_return`, or `breadth_regime`.

如果用户说“帮我看新高新低或市场领导力”，使用 `new_highs`, `new_lows`, `net_new_highs`, `high_low_index`, `cumulative_new_highs_new_lows`。
EN: If the user asks for new highs/lows or market leadership, use `new_highs`, `new_lows`, `net_new_highs`, `high_low_index`, or `cumulative_new_highs_new_lows`.

如果用户说“帮我看量能宽度或 TRIN”，使用 `up_down_volume_ratio`, `volume_advance_decline_percent`, `arms_index`, `trin`, `volume_breadth_thrust`；缺少 volume 时不要静默降级。
EN: If the user asks for volume breadth or TRIN, use `up_down_volume_ratio`, `volume_advance_decline_percent`, `arms_index`, `trin`, or `volume_breadth_thrust`; do not silently downgrade when volume is missing.

如果用户说“帮我看指数上涨但内部变弱、宽度背离或确认”，使用 `index_breadth_divergence`, `breadth_confirmation`，并要求输入包含 `index_close`。
EN: If the user asks whether an index move is weakening internally, diverging, or confirmed by breadth, use `index_breadth_divergence` or `breadth_confirmation`, and require `index_close`.

如果用户说“帮我看市场冻结压力或系统风险宽度输入”，使用 `breadth_freeze_pressure` 做诊断；真正的 freeze 决策仍使用 `market_freeze.py`。
EN: If the user asks for market-freeze pressure or system-risk breadth input, use `breadth_freeze_pressure` for diagnostics; actual freeze decisions still belong to `market_freeze.py`.

如果用户说“帮我看资金费率、OI、期现价差、永续拥挤或清算压力”，使用 `funding_rate_zscore`, `open_interest_change`, `basis_rate`, `derivatives_crowding_index`, `liquidation_pressure`, or `perp_risk_regime`。
EN: If the user asks for funding, OI, basis, perpetual crowding, or liquidation pressure, use `funding_rate_zscore`, `open_interest_change`, `basis_rate`, `derivatives_crowding_index`, `liquidation_pressure`, or `perp_risk_regime`.

如果用户说“帮我看期权 IV、期限结构、偏斜、put-call 或 Greeks 暴露”，使用 `implied_volatility`, `iv_rank`, `iv_term_structure`, `put_call_iv_skew`, `put_call_volume_ratio`, `gamma_exposure`, or `options_crowding_index`。
EN: If the user asks for option IV, term structure, skew, put-call activity, or Greeks exposure, use `implied_volatility`, `iv_rank`, `iv_term_structure`, `put_call_iv_skew`, `put_call_volume_ratio`, `gamma_exposure`, or `options_crowding_index`.

如果用户说“帮我估算 dealer gamma、VRP 或 max pain”，使用 `dealer_gamma_proxy`, `volatility_risk_premium_proxy`, or `max_pain_proxy`，并明确说明这些只是 proxy。
EN: If the user asks for dealer gamma, VRP, or max pain, use `dealer_gamma_proxy`, `volatility_risk_premium_proxy`, or `max_pain_proxy`, and explicitly state that these are proxies.


如果用户说“帮我看链上活跃度、地址增长或交易增长”，使用 `active_addresses`, `new_addresses`, `network_activity_index`, `address_growth_rate`, or `transaction_growth_rate`。
EN: If the user asks for on-chain activity, address growth, or transaction growth, use `active_addresses`, `new_addresses`, `network_activity_index`, `address_growth_rate`, or `transaction_growth_rate`.

如果用户说“帮我看 MVRV、NVT、realized price 或链上估值”，使用 `mvrv_ratio`, `mvrv_zscore`, `nvt_ratio`, `nvt_signal`, `realized_price`, or `onchain_valuation_regime`。
EN: If the user asks for MVRV, NVT, realized price, or on-chain valuation, use `mvrv_ratio`, `mvrv_zscore`, `nvt_ratio`, `nvt_signal`, `realized_price`, or `onchain_valuation_regime`.

如果用户说“帮我看交易所流入流出、稳定币流动性、矿工或验证者压力”，使用 `exchange_netflow`, `exchange_flow_pressure`, `stablecoin_liquidity_index`, `miner_flow_pressure`, `miner_capitulation_proxy`, or `validator_exit_pressure`。
EN: If the user asks for exchange flows, stablecoin liquidity, miner pressure, or validator pressure, use `exchange_netflow`, `exchange_flow_pressure`, `stablecoin_liquidity_index`, `miner_flow_pressure`, `miner_capitulation_proxy`, or `validator_exit_pressure`.

如果用户说“帮我看长期持有人、短期持有人、HODL wave 或 whale/retail 分歧”，使用 `long_term_holder_supply_proxy`, `short_term_holder_supply_proxy`, `hodl_wave_proxy`, `whale_retail_divergence`，并明确说明 proxy 语义。
EN: If the user asks for long-term holders, short-term holders, HODL wave, or whale/retail divergence, use `long_term_holder_supply_proxy`, `short_term_holder_supply_proxy`, `hodl_wave_proxy`, or `whale_retail_divergence`, and explicitly state proxy semantics.

## 36. 常见坑

EN: Common pitfalls.

不要让 indicator token 自己拉行情。
EN: Do not let indicator tokens fetch market data.

不要把 `backend="talib"` 的失败静默降级。
EN: Do not silently downgrade a failed `backend="talib"` request.

不要假设 `series_by_name` 一定存在。
EN: Do not assume `series_by_name` exists.

不要在 `result.ok=False` 时读取 `result.value`。
EN: Do not read `result.value` when `result.ok=False`.

不要把 pipeline 当成自动策略 runner。
EN: Do not treat the pipeline as an automatic strategy runner.

不要把 `order_planner.py` 当成下单器。
EN: Do not treat `order_planner.py` as an order executor.

不要把空 universe 自动替换成默认标的。
EN: Do not replace an empty universe with a default instrument.
