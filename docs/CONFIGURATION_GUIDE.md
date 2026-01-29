# A股量化交易系统配置指南

## 目录
1. [配置概述](#配置概述)
2. [主配置文件 (config.yaml)](#主配置文件-configyaml)
3. [策略配置 (strategies.yaml)](#策略配置-strategiesyaml)
4. [风险规则配置 (risk_rules.yaml)](#风险规则配置-risk_rulesyaml)
5. [监控配置 (monitoring.yaml)](#监控配置-monitoringyaml)
6. [A股特色配置说明](#a股特色配置说明)
7. [常见配置场景](#常见配置场景)
8. [配置最佳实践](#配置最佳实践)

---

## 配置概述

### 配置文件结构

本系统采用YAML格式的配置文件，位于 `config/` 目录下：

```
config/
├── config.yaml          # 主配置文件（系统、数据、AI、日志）
├── strategies.yaml      # 策略配置（各类交易策略参数）
├── risk_rules.yaml      # 风险规则配置（仓位、止损、风控）
└── monitoring.yaml      # 监控配置（实时监控、信号检测、提醒）
```

### 配置加载机制

配置文件由 `ConfigManager` 单例管理，系统启动时自动加载：

```python
from src.core.config_manager import ConfigManager

config = ConfigManager()
value = config.get('data.provider')  # 支持点号分隔的嵌套键
```

### 配置优先级

1. 环境变量（如有）
2. YAML配置文件
3. 代码中的默认值

---

## 主配置文件 (config.yaml)

### 完整示例

```yaml
# A股量化交易系统配置文件

data:
  provider: akshare                # 数据提供商
  cache:
    enabled: true                  # 启用数据缓存
    directory: ./data/cache        # 缓存目录
    ttl:
      realtime: 60                 # 实时行情缓存时间（秒）
      daily: 3600                  # 日线数据缓存时间（秒）
      financial: 86400             # 财务数据缓存时间（秒）

  sources:                         # AKShare数据源接口名称
    stock_list: "stock_zh_a_spot"
    realtime_quote: "stock_zh_a_spot_em"
    daily_kline: "stock_zh_a_hist"
    financial: "stock_financial_analysis_indicator"
    money_flow: "stock_individual_fund_flow"

ai:
  provider: deepseek               # AI服务提供商
  model: deepseek-chat             # 聊天模型
  reasoning_model: deepseek-reasoner  # 推理模型
  temperature: 0.7                 # 生成温度
  max_tokens: 4000                 # 最大生成令牌数
  timeout: 30                      # 请求超时（秒）

  rating_weights:                  # AI评级权重分配
    technical: 0.30                # 技术面权重
    fundamental: 0.30              # 基本面权重
    capital: 0.25                  # 资金面权重
    sentiment: 0.15                # 情绪面权重

logging:
  level: INFO                      # 日志级别
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  files:
    app: ./logs/app.log            # 应用日志
    error: ./logs/error.log        # 错误日志
    trade: ./logs/trade.log        # 交易日志
  rotation: "100 MB"               # 日志轮转大小
  retention: "30 days"             # 日志保留时间

market:
  limit_ratio:                     # A股涨跌停限制
    main_board: 0.10               # 主板涨跌停±10%
    star_market: 0.20              # 科创板涨跌停±20%
    gem: 0.20                      # 创业板涨跌停±20%

  trading_hours:                   # 交易时间
    morning_start: "09:30"         # 早盘开盘
    morning_end: "11:30"           # 早盘收盘
    afternoon_start: "13:00"       # 午盘开盘
    afternoon_end: "15:00"         # 午盘收盘

  min_lot: 100                     # 最小交易单位（1手=100股）

database:
  path: ./data/storage/a_stock.db  # 数据库路径
  echo: false                      # 是否打印SQL语句
  pool_size: 5                     # 连接池大小
  max_overflow: 10                 # 最大溢出连接数
```

### 配置项详解

#### data - 数据源配置

| 配置项 | 类型 | 默认值 | 说明 | 推荐值 |
|-------|------|--------|------|--------|
| `provider` | string | akshare | 数据提供商 | akshare（唯一支持） |
| `cache.enabled` | boolean | true | 是否启用缓存 | true（提升性能） |
| `cache.directory` | string | ./data/cache | 缓存目录 | 建议使用绝对路径 |
| `cache.ttl.realtime` | int | 60 | 实时行情缓存秒数 | 30-120秒 |
| `cache.ttl.daily` | int | 3600 | 日线数据缓存秒数 | 3600-7200秒 |
| `cache.ttl.financial` | int | 86400 | 财务数据缓存秒数 | 86400秒（1天） |

**注意事项：**
- 实时行情缓存时间不宜过长，建议30-120秒
- 财务数据更新频率低，可使用较长缓存时间
- 缓存目录需确保有写入权限

#### ai - AI服务配置

| 配置项 | 类型 | 默认值 | 说明 | 推荐值 |
|-------|------|--------|------|--------|
| `provider` | string | deepseek | AI提供商 | deepseek |
| `model` | string | deepseek-chat | 聊天模型 | deepseek-chat |
| `reasoning_model` | string | deepseek-reasoner | 推理模型 | deepseek-reasoner |
| `temperature` | float | 0.7 | 生成随机性（0-2） | 0.5-0.9 |
| `max_tokens` | int | 4000 | 最大生成令牌数 | 2000-8000 |
| `timeout` | int | 30 | 请求超时秒数 | 30-60 |

**AI评级权重说明：**
- `technical`: 技术分析权重（K线、指标）
- `fundamental`: 基本面权重（财务、估值）
- `capital`: 资金流向权重（主力资金）
- `sentiment`: 市场情绪权重（涨跌幅、成交量）

**权重配置要求：** 四项之和必须等于1.0

#### logging - 日志配置

| 配置项 | 类型 | 默认值 | 说明 | 可选值 |
|-------|------|--------|------|--------|
| `level` | string | INFO | 日志级别 | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `rotation` | string | 100 MB | 日志文件大小限制 | "10 MB"/"100 MB"/"1 GB" |
| `retention` | string | 30 days | 日志保留时间 | "7 days"/"30 days"/"90 days" |

**日志级别选择：**
- **DEBUG**: 开发调试时使用（日志量大）
- **INFO**: 生产环境推荐（正常运行信息）
- **WARNING**: 仅记录警告和错误
- **ERROR**: 仅记录错误

#### market - 市场规则配置

| 配置项 | 类型 | 说明 | A股规则 |
|-------|------|------|---------|
| `limit_ratio.main_board` | float | 主板涨跌停限制 | ±10% |
| `limit_ratio.star_market` | float | 科创板涨跌停限制 | ±20% |
| `limit_ratio.gem` | float | 创业板涨跌停限制 | ±20% |
| `min_lot` | int | 最小交易单位 | 100股（1手） |

**注意：** 这些是A股市场的硬性规则，不建议修改。

#### database - 数据库配置

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `path` | string | ./data/storage/a_stock.db | SQLite数据库路径 |
| `echo` | boolean | false | 是否打印SQL（调试用） |
| `pool_size` | int | 5 | 连接池大小 |
| `max_overflow` | int | 10 | 最大溢出连接数 |

---

## 策略配置 (strategies.yaml)

本文件定义了多种交易策略的参数配置。

### 短线动量策略 (momentum)

```yaml
momentum:
  type: short_term
  description: "基于价格动量和成交量的短线策略"

  parameters:
    # 技术指标参数
    rsi_period: 14              # RSI计算周期
    rsi_oversold: 30            # RSI超卖阈值
    rsi_overbought: 70          # RSI超买阈值

    macd_fast: 12               # MACD快线周期
    macd_slow: 26               # MACD慢线周期
    macd_signal: 9              # MACD信号线周期

    volume_ma_period: 5         # 成交量均线周期
    volume_surge_ratio: 2.0     # 成交量放大倍数

    # 交易参数
    stop_loss: 0.08             # 止损比例（8%）
    take_profit: 0.15           # 止盈比例（15%）
    max_holding_days: 10        # 最大持仓天数

  entry_conditions:             # 入场条件
    - "RSI从超卖区回升"
    - "MACD金叉"
    - "成交量放大"
    - "价格突破短期阻力"

  exit_conditions:              # 出场条件
    - "RSI进入超买区"
    - "MACD死叉"
    - "触及止盈止损"
    - "持仓超过最大天数"
```

#### 参数说明

| 参数 | 范围 | 推荐值 | 说明 |
|-----|------|--------|------|
| `rsi_period` | 5-30 | 14 | RSI周期，值越小越敏感 |
| `rsi_oversold` | 20-40 | 30 | 超卖线，低于此值视为超卖 |
| `rsi_overbought` | 60-80 | 70 | 超买线，高于此值视为超买 |
| `macd_fast` | 5-20 | 12 | 快线周期，标准值12 |
| `macd_slow` | 15-40 | 26 | 慢线周期，标准值26 |
| `macd_signal` | 5-15 | 9 | 信号线周期，标准值9 |
| `volume_surge_ratio` | 1.5-3.0 | 2.0 | 成交量放大倍数 |
| `stop_loss` | 0.03-0.15 | 0.08 | 止损比例（短线建议5-10%） |
| `take_profit` | 0.10-0.30 | 0.15 | 止盈比例（盈亏比至少1:1.5） |
| `max_holding_days` | 3-15 | 10 | 短线最大持仓天数 |

**策略特点：**
- 适合波动性较大的股票
- 持仓时间短，换手率高
- 需密切关注盘面变化

### 价值投资策略 (value_investing)

```yaml
value_investing:
  type: long_term
  description: "基于基本面的价值投资策略"

  parameters:
    # 基本面筛选条件
    min_roe: 0.15               # 最低ROE（净资产收益率）
    max_pe: 30                  # 最高PE（市盈率）
    max_pb: 3                   # 最高PB（市净率）
    min_gross_margin: 0.30      # 最低毛利率

    # 财务健康度
    max_debt_ratio: 0.60        # 最高资产负债率
    min_current_ratio: 1.5      # 最低流动比率

    # 成长性
    min_revenue_growth: 0.10    # 最低营收增长率
    min_profit_growth: 0.10     # 最低净利润增长率

    # 持仓参数
    stop_loss: 0.15             # 止损比例（15%）
    take_profit: 0.50           # 止盈比例（50%）
    max_holding_days: 365       # 最大持仓天数（1年）

  entry_conditions:
    - "ROE稳定在15%以上"
    - "PE低于行业平均"
    - "连续盈利且增长"
    - "资产负债率健康"

  exit_conditions:
    - "基本面恶化"
    - "估值过高"
    - "触及止盈止损"
```

#### 参数说明

| 参数 | 范围 | 推荐值 | 说明 |
|-----|------|--------|------|
| `min_roe` | 0.10-0.20 | 0.15 | ROE越高越好，15%以上为优质 |
| `max_pe` | 10-50 | 30 | PE要结合行业比较 |
| `max_pb` | 1-5 | 3 | PB<1可能被低估 |
| `min_gross_margin` | 0.20-0.40 | 0.30 | 毛利率体现竞争力 |
| `max_debt_ratio` | 0.40-0.70 | 0.60 | 负债率越低越安全 |
| `min_current_ratio` | 1.0-2.0 | 1.5 | >1表示流动性健康 |
| `min_revenue_growth` | 0.05-0.20 | 0.10 | 营收增长体现成长性 |
| `min_profit_growth` | 0.05-0.20 | 0.10 | 利润增长更重要 |
| `stop_loss` | 0.10-0.25 | 0.15 | 长线止损可宽松些 |
| `take_profit` | 0.30-1.00 | 0.50 | 长线目标更高 |

**策略特点：**
- 适合长期投资
- 注重企业基本面和成长性
- 换手率低，适合稳健投资者

### 突破策略 (breakout)

```yaml
breakout:
  type: short_term
  description: "价格突破策略"

  parameters:
    # 突破参数
    breakout_period: 20         # 突破周期（20日高点）
    breakout_threshold: 0.03    # 突破幅度（3%）
    volume_confirm: true        # 是否需要成交量确认

    # 交易参数
    stop_loss: 0.05             # 止损比例（5%）
    take_profit: 0.20           # 止盈比例（20%）
    trailing_stop: 0.03         # 移动止损（3%）

  entry_conditions:
    - "突破N日高点"
    - "成交量放大确认"
    - "无明显阻力位"

  exit_conditions:
    - "跌破关键支撑"
    - "触及止盈止损"
    - "成交量萎缩"
```

#### 参数说明

| 参数 | 范围 | 推荐值 | 说明 |
|-----|------|--------|------|
| `breakout_period` | 10-60 | 20 | 周期越长，突破越有效 |
| `breakout_threshold` | 0.01-0.05 | 0.03 | 突破幅度，防止假突破 |
| `volume_confirm` | true/false | true | 建议开启，提高成功率 |
| `stop_loss` | 0.03-0.08 | 0.05 | 突破策略止损要快 |
| `take_profit` | 0.15-0.30 | 0.20 | 突破后目标空间 |
| `trailing_stop` | 0.02-0.05 | 0.03 | 移动止损锁定利润 |

**策略特点：**
- 适合趋势性行情
- 对时机要求高
- 假突破风险需防范

---

## 风险规则配置 (risk_rules.yaml)

风险管理是量化交易的核心，本配置文件定义了完整的风控规则。

### 完整示例

```yaml
# 风险管理配置

# 仓位管理
position:
  max_single_position: 0.20      # 单一持仓最大20%
  max_sector_exposure: 0.30      # 单一行业最大30%
  max_total_position: 0.95       # 总仓位最大95%
  min_position_value: 10000      # 最小建仓金额1万元

# 交易限制
trade_restrictions:
  禁止ST股: true                  # 禁止ST、*ST、ST*等股票
  禁止退市风险股: true            # 禁止有退市风险的股票
  min_listing_days: 30           # 最少上市30天（避免次新股）
  min_market_cap: 2000000000     # 最小市值20亿（流动性要求）
  min_daily_volume: 10000000     # 最小日成交额1000万

  # A股特色限制
  avoid_continuous_limit_up: true      # 避免连续涨停股
  avoid_continuous_limit_down: true    # 避免连续跌停股
  max_continuous_limit: 3              # 最多连续涨跌停天数

# 止损止盈
stop_loss:
  enabled: true                  # 启用止损
  method: "fixed"                # 止损方式：fixed/trailing/atr
  fixed_ratio: 0.08              # 固定止损8%
  trailing_ratio: 0.05           # 移动止损5%
  atr_multiplier: 2.0            # ATR止损倍数

take_profit:
  enabled: true                  # 启用止盈
  method: "fixed"                # 止盈方式：fixed/dynamic
  fixed_ratio: 0.15              # 固定止盈15%
  partial_take_profit:           # 分批止盈
    enabled: true                # 启用分批止盈
    first_target: 0.10           # 第一目标10%
    first_size: 0.50             # 第一次减仓50%

# A股特色风控
a_share_specific:
  t1_settlement: true            # T+1交易制度
  check_limit_price: true        # 检查涨跌停

  # 涨跌停处理
  limit_up_action: "hold"        # 涨停处理：hold（持有）/sell（卖出）
  limit_down_action: "hold"      # 跌停处理：hold（持有）/emergency_sell（紧急卖出）

  # 特殊时段
  avoid_before_holiday: false    # 避免节前买入
  avoid_year_end: false          # 避免年末买入

# 风险预警
alerts:
  position_concentration:        # 仓位集中度预警
    warning: 0.15                # 单一持仓15%预警
    critical: 0.20               # 单一持仓20%严重预警

  drawdown:                      # 回撤预警
    warning: 0.05                # 5%回撤预警
    critical: 0.10               # 10%回撤严重预警

  volatility:                    # 波动率预警
    warning: 0.30                # 30%波动率预警
    critical: 0.50               # 50%波动率严重预警

# 交易限制
trading_limits:
  max_trades_per_day: 5          # 每日最多交易5次
  max_trades_per_week: 15        # 每周最多交易15次
  min_holding_period: 1          # 最短持仓1天（T+1限制）
  cooling_period: 5              # 同一股票冷却期5天
```

### 配置项详解

#### position - 仓位管理

| 配置项 | 类型 | 推荐值 | 说明 |
|-------|------|--------|------|
| `max_single_position` | float | 0.15-0.25 | 单股最大仓位，防止过度集中 |
| `max_sector_exposure` | float | 0.25-0.35 | 行业最大暴露，分散行业风险 |
| `max_total_position` | float | 0.85-0.95 | 总仓位上限，保留现金应对风险 |
| `min_position_value` | int | 10000-50000 | 最小建仓金额，避免碎片化 |

**仓位管理原则：**
1. **单股仓位**: 不超过20%，避免"一股定乾坤"
2. **行业分散**: 不超过30%，防止行业黑天鹅
3. **总仓位**: 保留5-15%现金，应对突发机会或风险
4. **最小仓位**: 建议不低于1万元，否则交易成本过高

#### trade_restrictions - 交易限制

| 配置项 | 类型 | 推荐值 | 说明 |
|-------|------|--------|------|
| `禁止ST股` | boolean | true | 强烈建议，ST股风险极高 |
| `禁止退市风险股` | boolean | true | 强烈建议 |
| `min_listing_days` | int | 30-90 | 避免次新股，建议30天以上 |
| `min_market_cap` | int | 20-50亿 | 流动性要求，小市值风险高 |
| `min_daily_volume` | int | 1000-5000万 | 日成交额要求，确保能顺利买卖 |
| `avoid_continuous_limit_up` | boolean | true | 避免追高连板股 |
| `avoid_continuous_limit_down` | boolean | true | 避免接飞刀 |
| `max_continuous_limit` | int | 2-3 | 连续涨跌停天数限制 |

**A股特色限制说明：**
- **ST股**: 包括ST、*ST、ST*、SST等，代表财务异常或退市风险
- **连续涨停**: 避免追高，特别是3连板以上
- **连续跌停**: 避免抄底，可能存在重大利空

#### stop_loss - 止损配置

| 配置项 | 类型 | 说明 | 推荐值 |
|-------|------|------|--------|
| `enabled` | boolean | 是否启用止损 | true（必须开启） |
| `method` | string | 止损方式 | fixed/trailing/atr |
| `fixed_ratio` | float | 固定止损比例 | 0.05-0.10（短线）<br>0.10-0.20（长线） |
| `trailing_ratio` | float | 移动止损比例 | 0.03-0.08 |
| `atr_multiplier` | float | ATR倍数 | 1.5-3.0 |

**止损方式对比：**

| 方式 | 优点 | 缺点 | 适用场景 |
|-----|------|------|----------|
| **fixed** | 简单明确 | 不够灵活 | 震荡市、新手 |
| **trailing** | 锁定利润 | 可能过早止损 | 趋势市、盈利后 |
| **atr** | 适应波动 | 计算复杂 | 波动大的股票 |

**止损比例建议：**
- **短线**: 5-8%（快进快出）
- **中线**: 8-12%（给予空间）
- **长线**: 15-20%（容忍波动）

#### take_profit - 止盈配置

| 配置项 | 类型 | 说明 | 推荐值 |
|-------|------|------|--------|
| `enabled` | boolean | 是否启用止盈 | true |
| `method` | string | 止盈方式 | fixed/dynamic |
| `fixed_ratio` | float | 固定止盈比例 | 0.15-0.30 |
| `partial_take_profit.enabled` | boolean | 是否分批止盈 | true（推荐） |
| `partial_take_profit.first_target` | float | 第一目标 | 0.08-0.12 |
| `partial_take_profit.first_size` | float | 第一次减仓比例 | 0.30-0.50 |

**分批止盈策略：**
1. 达到第一目标（如10%）时，减仓50%
2. 剩余仓位继续持有，追求更大收益
3. 设置移动止损保护剩余仓位

**盈亏比要求：**
- 止盈 : 止损 应至少为 1.5:1
- 示例：止损8%，止盈至少12%

#### a_share_specific - A股特色风控

| 配置项 | 类型 | 说明 | A股规则 |
|-------|------|------|---------|
| `t1_settlement` | boolean | T+1制度 | true（固定规则） |
| `check_limit_price` | boolean | 检查涨跌停 | true（必须开启） |
| `limit_up_action` | string | 涨停处理 | hold（持有）/sell（卖出） |
| `limit_down_action` | string | 跌停处理 | hold（持有）/emergency_sell（紧急卖） |
| `avoid_before_holiday` | boolean | 避免节前买入 | 可选 |
| `avoid_year_end` | boolean | 避免年末买入 | 可选 |

**T+1制度影响：**
- 当天买入的股票，当天不能卖出
- 需要更谨慎的买入决策
- 建议设置更严格的买入条件

**涨跌停处理建议：**
- **涨停**: 一般持有，除非放量打开
- **跌停**: 视情况而定，重大利空应紧急卖出

#### alerts - 风险预警

| 预警类型 | warning阈值 | critical阈值 | 说明 |
|---------|-------------|--------------|------|
| 仓位集中度 | 15% | 20% | 单股仓位占比 |
| 回撤 | 5% | 10% | 从最高点回撤 |
| 波动率 | 30% | 50% | 年化波动率 |

**预警级别：**
- **warning**: 黄色预警，注意观察
- **critical**: 红色预警，需立即处理

#### trading_limits - 交易频率限制

| 配置项 | 推荐值 | 说明 |
|-------|--------|------|
| `max_trades_per_day` | 3-5 | 防止过度交易 |
| `max_trades_per_week` | 10-20 | 控制换手率 |
| `min_holding_period` | 1 | T+1限制 |
| `cooling_period` | 3-7天 | 同一股票冷却期 |

**过度交易的危害：**
1. 交易成本高（佣金+印花税）
2. 容易情绪化决策
3. 策略难以发挥效果

---

## 监控配置 (monitoring.yaml)

实时监控配置，用于盘中监控和信号检测。

### 完整示例

```yaml
# 监控服务配置文件

monitoring:
  # 更新频率（秒）
  update_interval: 60          # 每60秒更新一次行情

  # 监控列表
  watchlist:
    - code: "600519"
      name: "贵州茅台"
    - code: "000858"
      name: "五粮液"
    - code: "000001"
      name: "平安银行"
    - code: "600036"
      name: "招商银行"

  # 信号检测配置
  signals:
    # 启用的检测器
    enabled_detectors:
      - ma_crossover            # MA均线交叉
      - rsi                     # RSI超买超卖
      - volume_breakout         # 成交量突破
      - stop_loss               # 止损触发
      - take_profit             # 止盈触发

    # 技术指标参数
    ma_short: 5                 # 短期均线周期
    ma_long: 20                 # 长期均线周期
    rsi_period: 14              # RSI周期
    rsi_oversold: 30            # RSI超卖阈值
    rsi_overbought: 70          # RSI超买阈值
    volume_multiplier: 2.0      # 成交量放大倍数

  # 提醒设置
  alerts:
    # 最低优先级（只提醒此级别及以上的信号）
    min_priority: "medium"      # low/medium/high/critical

    # 通知渠道
    channels:
      - console                 # 控制台输出
      - log                     # 日志文件
      # - email                 # 邮件（需配置）
      # - wechat                # 微信（需配置）

    # 去重窗口（秒）- 同一股票同一信号在此窗口内不重复提醒
    dedup_window: 900           # 15分钟

    # 交易时间限制
    trading_hours_only: false   # 是否仅在交易时间提醒

  # 持仓监控
  position_monitoring:
    enabled: true               # 是否启用持仓监控
    check_interval: 300         # 检查间隔（秒）- 5分钟

# 风险管理配置
risk:
  # 总资金
  total_capital: 1000000        # 100万初始资金

  # 仓位限制
  position:
    max_single_position: 0.20   # 单一持仓≤20%
    max_sector_exposure: 0.30   # 单一行业≤30%
    max_total_position: 0.95    # 总仓位≤95%

  # 止损止盈
  stop_loss:
    method: "fixed"             # fixed, trailing, atr
    fixed_ratio: 0.08           # 固定止损8%
    trailing_ratio: 0.05        # 移动止损5%
    atr_multiplier: 2.0         # ATR倍数

  take_profit:
    method: "fixed"             # fixed, dynamic
    fixed_ratio: 0.15           # 固定止盈15%
```

### 配置项详解

#### monitoring - 监控服务

| 配置项 | 类型 | 推荐值 | 说明 |
|-------|------|--------|------|
| `update_interval` | int | 30-120秒 | 行情更新间隔 |
| `watchlist` | list | - | 监控股票列表 |

**更新间隔选择：**
- **30秒**: 适合日内交易，实时性高
- **60秒**: 一般监控，平衡性能和实时性
- **120秒**: 长线监控，降低API调用频率

#### signals - 信号检测

| 配置项 | 类型 | 推荐值 | 说明 |
|-------|------|--------|------|
| `ma_short` | int | 5-10 | 短期均线，常用5/10 |
| `ma_long` | int | 20-60 | 长期均线，常用20/30/60 |
| `rsi_period` | int | 14 | RSI周期，标准值14 |
| `rsi_oversold` | int | 25-35 | RSI超卖线 |
| `rsi_overbought` | int | 65-75 | RSI超买线 |
| `volume_multiplier` | float | 1.5-2.5 | 成交量放大倍数 |

**常用均线组合：**
- **5/20**: 超短线，信号频繁
- **10/30**: 短线，比较灵敏
- **20/60**: 中线，信号可靠
- **60/120**: 长线，趋势明确

#### alerts - 提醒设置

| 配置项 | 类型 | 说明 | 可选值 |
|-------|------|------|--------|
| `min_priority` | string | 最低优先级 | low/medium/high/critical |
| `channels` | list | 通知渠道 | console/log/email/wechat |
| `dedup_window` | int | 去重窗口（秒） | 300-1800 |
| `trading_hours_only` | boolean | 仅交易时间提醒 | true/false |

**优先级说明：**
- **low**: 一般信号，可选择性关注
- **medium**: 重要信号，建议关注
- **high**: 紧急信号，需立即查看
- **critical**: 严重预警，必须处理

**通知渠道：**
- **console**: 控制台输出（开发测试）
- **log**: 写入日志文件（生产环境）
- **email**: 邮件通知（需配置SMTP）
- **wechat**: 微信通知（需配置企业微信）

**去重窗口建议：**
- 短线监控：5-10分钟（300-600秒）
- 中长线监控：15-30分钟（900-1800秒）

#### position_monitoring - 持仓监控

| 配置项 | 类型 | 推荐值 | 说明 |
|-------|------|--------|------|
| `enabled` | boolean | true | 是否启用持仓监控 |
| `check_interval` | int | 300-600秒 | 持仓检查间隔 |

**持仓监控功能：**
1. 实时更新持仓市值
2. 检测止损止盈触发
3. 监控风险指标变化
4. 评估组合健康度

#### risk - 风险配置

此部分与 `risk_rules.yaml` 中的配置相同，在监控服务中使用。

---

## A股特色配置说明

### T+1交易制度

```yaml
a_share_specific:
  t1_settlement: true           # 必须开启
  min_holding_period: 1         # 最短持仓1天
```

**影响：**
- 当天买入不能卖出，需持有至少1天
- 买入决策需更谨慎
- 日内止损无法执行

**应对策略：**
1. 提高买入标准
2. 设置更严格的入场条件
3. 考虑隔夜风险

### 涨跌停限制

```yaml
market:
  limit_ratio:
    main_board: 0.10            # 主板±10%
    star_market: 0.20           # 科创板±20%
    gem: 0.20                   # 创业板±20%

a_share_specific:
  check_limit_price: true       # 检查涨跌停
  limit_up_action: "hold"       # 涨停持有
  limit_down_action: "hold"     # 跌停持有
```

**板块识别：**
- 6开头（60/68）: 主板，涨跌停±10%
- 688开头: 科创板，涨跌停±20%
- 300开头: 创业板（注册制后），涨跌停±20%
- 000/001/002开头: 深市主板/中小板/创业板

**涨跌停处理：**
1. **涨停**:
   - 封单量大：继续持有
   - 放量打开：考虑减仓

2. **跌停**:
   - 重大利空：emergency_sell（紧急卖出）
   - 技术性回调：hold（持有观察）

### ST股票限制

```yaml
trade_restrictions:
  禁止ST股: true                 # 强烈建议
  max_continuous_limit: 3       # 连续涨跌停限制
```

**ST股类型：**
- **ST**: 连续两年亏损
- ***ST**: 连续三年亏损（退市预警）
- **ST***: 其他异常情况
- **SST**: 连续两年亏损且股改未完成

**风险：**
1. 涨跌停±5%（主板）
2. 退市风险高
3. 业绩持续恶化

### 连续涨跌停限制

```yaml
trade_restrictions:
  avoid_continuous_limit_up: true      # 避免追高连板
  avoid_continuous_limit_down: true    # 避免接飞刀
  max_continuous_limit: 3              # 最多3连板
```

**策略：**
- 不追3连板以上的股票
- 不接连续跌停的股票
- 等待市场稳定后再介入

### 特殊时段控制

```yaml
a_share_specific:
  avoid_before_holiday: false   # 节前避险
  avoid_year_end: false         # 年末避险
```

**特殊时段：**
1. **节前**: 长假前1-2天，市场偏谨慎
2. **年末**: 12月下旬，机构调仓
3. **季末**: 季度最后一周，考核压力

**是否开启：**
- 保守型投资者：建议开启
- 激进型投资者：可关闭

---

## 常见配置场景

### 场景1: 稳健型长线投资

```yaml
# config.yaml
data:
  cache:
    ttl:
      realtime: 300             # 5分钟缓存
      daily: 7200               # 2小时缓存

# risk_rules.yaml
position:
  max_single_position: 0.15     # 单股最多15%
  max_sector_exposure: 0.25     # 行业最多25%
  max_total_position: 0.85      # 保留15%现金

stop_loss:
  method: "fixed"
  fixed_ratio: 0.15             # 止损15%

take_profit:
  method: "fixed"
  fixed_ratio: 0.50             # 止盈50%

trading_limits:
  max_trades_per_day: 2         # 每天最多2次交易
  cooling_period: 10            # 冷却期10天

# strategies.yaml - 使用价值投资策略
value_investing:
  parameters:
    min_roe: 0.15
    max_pe: 25
    max_debt_ratio: 0.50
```

**特点：**
- 低换手率
- 高安全边际
- 注重基本面

### 场景2: 激进型短线交易

```yaml
# config.yaml
data:
  cache:
    ttl:
      realtime: 30              # 30秒缓存

# risk_rules.yaml
position:
  max_single_position: 0.20     # 单股最多20%
  max_sector_exposure: 0.35     # 行业可放宽到35%
  max_total_position: 0.95      # 几乎满仓

stop_loss:
  method: "trailing"
  trailing_ratio: 0.03          # 移动止损3%

take_profit:
  method: "fixed"
  fixed_ratio: 0.12             # 止盈12%
  partial_take_profit:
    enabled: true
    first_target: 0.08          # 8%减仓一半
    first_size: 0.50

trading_limits:
  max_trades_per_day: 5         # 每天最多5次
  cooling_period: 3             # 冷却期3天

# strategies.yaml - 使用动量或突破策略
momentum:
  parameters:
    rsi_oversold: 35
    rsi_overbought: 65
    volume_surge_ratio: 2.5
    stop_loss: 0.05
    take_profit: 0.12
    max_holding_days: 5
```

**特点：**
- 高换手率
- 快进快出
- 技术分析为主

### 场景3: 均衡型中线交易

```yaml
# config.yaml
data:
  cache:
    ttl:
      realtime: 60              # 1分钟缓存

# risk_rules.yaml
position:
  max_single_position: 0.18     # 单股18%
  max_sector_exposure: 0.28     # 行业28%
  max_total_position: 0.90      # 保留10%现金

stop_loss:
  method: "fixed"
  fixed_ratio: 0.10             # 止损10%

take_profit:
  method: "fixed"
  fixed_ratio: 0.25             # 止盈25%
  partial_take_profit:
    enabled: true
    first_target: 0.15          # 15%减仓一半
    first_size: 0.50

trading_limits:
  max_trades_per_day: 3
  max_trades_per_week: 12
  cooling_period: 5

# strategies.yaml - 结合技术面和基本面
# 可同时使用momentum和value_investing，分配不同仓位
```

**特点：**
- 技术+基本面结合
- 适度换手
- 风险收益平衡

### 场景4: 盘中监控配置

```yaml
# monitoring.yaml
monitoring:
  update_interval: 30           # 30秒更新（交易时段）

  watchlist:                    # 精选10-20只股票
    - code: "600519"
      name: "贵州茅台"
    # ... 更多股票

  signals:
    enabled_detectors:
      - ma_crossover
      - rsi
      - volume_breakout
      - stop_loss
      - take_profit

    ma_short: 5
    ma_long: 20
    rsi_oversold: 30
    rsi_overbought: 70

  alerts:
    min_priority: "medium"      # 只提醒中等以上信号
    channels:
      - console                 # 实时看盘
      - log                     # 记录日志
    dedup_window: 300           # 5分钟去重
    trading_hours_only: true    # 仅交易时间提醒

  position_monitoring:
    enabled: true
    check_interval: 60          # 1分钟检查持仓

risk:
  total_capital: 1000000        # 根据实际资金调整
```

**适用场景：**
- 日内盯盘
- 及时发现买卖点
- 监控持仓风险

---

## 配置最佳实践

### 1. 配置文件管理

**版本控制：**
```bash
# 将配置文件纳入Git版本控制
git add config/*.yaml
git commit -m "Update risk rules"

# 敏感信息使用环境变量
# 不要将API密钥写入配置文件
```

**配置备份：**
```bash
# 定期备份配置
cp -r config/ config_backup_$(date +%Y%m%d)/
```

**多环境配置：**
```
config/
├── config.yaml              # 生产环境
├── config.dev.yaml          # 开发环境
├── config.test.yaml         # 测试环境
└── strategies.yaml
```

### 2. 参数优化流程

**步骤：**
1. **初始配置**: 使用推荐默认值
2. **回测验证**: 用历史数据回测
3. **参数扫描**: 遍历参数组合
4. **样本外测试**: 验证泛化能力
5. **实盘小仓**: 小资金实盘验证
6. **逐步放大**: 确认有效后放大资金

**避免过度优化：**
- 不要针对单一股票调优
- 避免在同一数据集上反复优化
- 保持策略简单性

### 3. 风险参数设置

**基本原则：**
1. **先紧后松**: 初期设置较严格，逐步放宽
2. **分散为王**: 控制单一持仓和行业集中度
3. **止损为先**: 宁可少赚，不能多亏
4. **逐步加仓**: 不要一次性满仓

**资金管理建议：**

| 资金规模 | max_single_position | max_total_position | min_position_value |
|---------|---------------------|--------------------|--------------------|
| 10万 | 0.25 | 0.85 | 5,000 |
| 50万 | 0.20 | 0.90 | 10,000 |
| 100万+ | 0.15 | 0.90 | 20,000 |
| 500万+ | 0.10 | 0.95 | 50,000 |

### 4. 监控配置建议

**交易时段：**
```yaml
# 盘中实时监控
update_interval: 30-60秒
trading_hours_only: true
min_priority: "medium"
```

**非交易时段：**
```yaml
# 盘后分析
update_interval: 300-600秒
trading_hours_only: false
min_priority: "high"
```

**资源消耗考虑：**
- update_interval越小，API调用越频繁
- watchlist不宜超过50只股票
- 合理设置cache.ttl降低请求频率

### 5. 策略组合配置

**单策略：**
```yaml
# 适合新手，专注一个策略
strategies:
  - momentum               # 只用动量策略
```

**多策略：**
```yaml
# 适合有经验的投资者
strategies:
  - momentum: 50%         # 50%资金用于动量
  - value_investing: 30%  # 30%资金用于价值
  - breakout: 20%         # 20%资金用于突破
```

**策略组合优势：**
1. 分散策略风险
2. 适应不同市场环境
3. 提高稳定性

### 6. 配置检查清单

**部署前检查：**
- [ ] 所有必填参数已设置
- [ ] 仓位限制之和不超过100%
- [ ] 止损止盈比例合理（盈亏比>1.5）
- [ ] 数据缓存目录存在且可写
- [ ] 日志目录存在且可写
- [ ] 数据库路径正确
- [ ] API密钥已配置（环境变量）
- [ ] 监控股票代码格式正确
- [ ] 交易限制符合T+1规则

**定期审查：**
- 每月审查一次配置参数
- 根据市场环境调整
- 根据回测结果优化
- 记录配置变更和原因

### 7. 常见错误和解决

**错误1: 仓位限制不合理**
```yaml
# 错误示例
max_single_position: 0.30
max_sector_exposure: 0.25   # 小于单股限制，不合理

# 正确示例
max_single_position: 0.20
max_sector_exposure: 0.30   # 行业限制应大于单股
```

**错误2: 止盈止损比例不当**
```yaml
# 错误示例（盈亏比过低）
stop_loss: 0.10
take_profit: 0.12           # 盈亏比1.2:1，扣除成本后不划算

# 正确示例
stop_loss: 0.08
take_profit: 0.15           # 盈亏比1.875:1，合理
```

**错误3: 缓存时间设置不当**
```yaml
# 错误示例
cache:
  ttl:
    realtime: 3600          # 1小时缓存，实时性差

# 正确示例
cache:
  ttl:
    realtime: 60            # 1分钟缓存，平衡性能和实时性
```

**错误4: 监控列表过大**
```yaml
# 错误示例
watchlist: 100只股票       # 过多，性能问题

# 正确示例
watchlist: 10-30只股票     # 精选，便于管理
```

### 8. 性能优化建议

**缓存优化：**
```yaml
# 根据数据更新频率设置TTL
cache:
  ttl:
    realtime: 60           # 行情1分钟变化
    daily: 3600            # 日线1小时内不变
    financial: 86400       # 财报1天内不变
```

**监控优化：**
```yaml
# 非交易时段降低频率
monitoring:
  update_interval: 60      # 交易时段60秒
  # 盘后可手动调整为300秒
```

**数据库优化：**
```yaml
database:
  pool_size: 5             # 根据并发需求
  max_overflow: 10         # 峰值连接数
```

### 9. 安全配置建议

**敏感信息保护：**
```bash
# 使用环境变量
export DEEPSEEK_API_KEY="your_api_key"
export EMAIL_PASSWORD="your_password"

# 配置文件中引用
ai:
  api_key: ${DEEPSEEK_API_KEY}
```

**配置文件权限：**
```bash
# 限制配置文件权限
chmod 600 config/*.yaml
```

**Git忽略：**
```gitignore
# .gitignore
config/config.local.yaml
.env
*.key
```

---

## 附录

### A. 配置参数速查表

| 参数 | 文件 | 推荐值 | 说明 |
|-----|------|--------|------|
| max_single_position | risk_rules.yaml | 0.15-0.20 | 单股仓位 |
| max_total_position | risk_rules.yaml | 0.85-0.95 | 总仓位 |
| stop_loss.fixed_ratio | risk_rules.yaml | 0.05-0.15 | 止损比例 |
| take_profit.fixed_ratio | risk_rules.yaml | 0.12-0.30 | 止盈比例 |
| update_interval | monitoring.yaml | 30-120 | 监控频率（秒） |
| rsi_oversold | strategies.yaml | 25-35 | RSI超卖 |
| rsi_overbought | strategies.yaml | 65-75 | RSI超买 |

### B. A股市场规则速查

| 规则 | 说明 | 配置影响 |
|-----|------|----------|
| T+1 | 当天买入次日才能卖 | min_holding_period: 1 |
| 涨跌停 | 主板±10%，创业板/科创板±20% | check_limit_price: true |
| ST限制 | ST股涨跌停±5% | 禁止ST股: true |
| 交易时间 | 9:30-11:30, 13:00-15:00 | trading_hours配置 |
| 最小单位 | 1手=100股 | min_lot: 100 |

### C. 技术指标参数参考

| 指标 | 参数 | 常用值 | 说明 |
|-----|------|--------|------|
| MA | 周期 | 5/10/20/30/60 | 均线周期 |
| RSI | 周期 | 14 | 相对强弱指标 |
| RSI | 超卖 | 30 | 低于此值超卖 |
| RSI | 超买 | 70 | 高于此值超买 |
| MACD | 快线 | 12 | 快速EMA |
| MACD | 慢线 | 26 | 慢速EMA |
| MACD | 信号线 | 9 | 信号线EMA |
| ATR | 周期 | 14 | 真实波幅 |

### D. 风险等级对照表

| 风险等级 | 单股仓位 | 总仓位 | 止损 | 适合人群 |
|---------|---------|--------|------|----------|
| 保守 | ≤15% | ≤80% | 10-15% | 新手、稳健型 |
| 稳健 | ≤20% | ≤85% | 8-12% | 有经验投资者 |
| 平衡 | ≤20% | ≤90% | 6-10% | 积极投资者 |
| 激进 | ≤25% | ≤95% | 5-8% | 专业交易者 |

---

## 总结

配置文件是量化交易系统的核心，合理的配置可以：

1. **控制风险**: 通过仓位、止损等限制
2. **提高效率**: 通过缓存、监控优化
3. **适应市场**: 通过策略参数调整
4. **保障安全**: 通过A股特色规则

**配置原则：**
- 安全第一，收益第二
- 从严到松，逐步放宽
- 定期审查，持续优化
- 记录变更，总结经验

**下一步：**
- 阅读 [USER_GUIDE.md](USER_GUIDE.md) 了解系统使用
- 参考 [常见配置场景](#常见配置场景) 选择合适配置
- 通过回测验证配置有效性
- 小仓位实盘验证后再放大

祝您交易顺利！
