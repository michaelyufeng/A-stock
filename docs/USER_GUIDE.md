# A股量化交易分析系统用户指南

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [核心功能使用](#核心功能使用)
4. [配置说明](#配置说明)
5. [常见问题FAQ](#常见问题faq)
6. [进阶使用](#进阶使用)
7. [最佳实践](#最佳实践)

---

## 系统概述

### 系统介绍

A股量化交易分析系统是一个功能完整的量化交易分析平台，专为中国A股市场设计。系统集成了数据获取、技术分析、基本面分析、资金面分析、AI评级、策略回测和实时监控等核心功能，帮助投资者做出更明智的投资决策。

### 主要功能

- **多维度分析**
  - 技术面分析：MA、MACD、RSI等20+技术指标
  - 基本面分析：财务指标、盈利能力、成长性评估
  - 资金面分析：主力资金流向、大单追踪
  - AI综合评级：基于DeepSeek的智能分析

- **策略回测**
  - 基于backtrader框架的专业回测引擎
  - 支持A股T+1交易规则
  - 完整的性能指标（收益率、夏普比率、最大回撤等）
  - 可视化回测结果

- **选股筛选**
  - 预设筛选策略（8种策略：强势动量、价值成长、资金流入、低PE价值、高股息、突破新高、超卖反弹、机构重仓）
  - 批量股票评分
  - 多条件组合过滤
  - 结果导出（CSV/Excel）

- **实时监控**
  - 持仓监控
  - 关键信号推送
  - 止损止盈提醒
  - 每日交易总结

### 技术特点

- **数据源**：AKShare（免费、稳定、实时更新）
- **AI引擎**：DeepSeek API（高性价比的AI分析）
- **回测框架**：backtrader（专业的量化回测库）
- **技术指标**：pandas_ta（丰富的技术分析指标）
- **数据存储**：SQLite（轻量级、无需配置）

### A股特色功能

- **T+1交易规则**：回测和策略完全遵循A股T+1规则
- **涨跌停限制**：
  - 主板：±10%
  - 科创板/创业板：±20%
- **交易时间识别**：自动识别开盘、收盘时间
- **市场板块识别**：自动识别主板、科创板、创业板
- **特色风险提示**：针对A股特有风险的专门提示

---

## 快速开始

### 环境要求

- **Python版本**：3.8或更高
- **操作系统**：Windows / macOS / Linux
- **网络要求**：需要访问互联网（获取市场数据和AI服务）
- **硬盘空间**：至少500MB（用于数据缓存）

### 安装步骤

#### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd A-stock
```

或直接下载ZIP包并解压。

#### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- akshare：数据获取
- pandas：数据处理
- pandas-ta：技术指标
- backtrader：回测引擎
- requests：HTTP请求
- pyyaml：配置文件解析

#### 3. 创建必要的目录

系统会自动创建以下目录（首次运行时）：
```bash
data/cache/      # 数据缓存
data/storage/    # 数据库存储
logs/            # 日志文件
```

### 基础配置

#### 1. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑`.env`文件，填入必要的配置：

```bash
# DeepSeek API Key（用于AI分析）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 调试模式（开发时可设为true）
DEBUG=false

# 数据缓存（建议启用）
CACHE_ENABLED=true
CACHE_DIR=./data/cache

# 数据库路径
DB_PATH=./data/storage/a_stock.db
```

#### 2. 获取DeepSeek API密钥

1. 访问 [DeepSeek官网](https://platform.deepseek.com)
2. 注册账号并登录
3. 在控制台创建API密钥
4. 将密钥填入`.env`文件的`DEEPSEEK_API_KEY`字段

**注意**：
- DeepSeek提供免费额度，足够日常使用
- 如果不使用AI分析功能，可以跳过此步骤，使用`--depth quick`进行快速分析

### 第一次运行

#### 测试安装

运行一个简单的股票分析来验证安装：

```bash
python scripts/analyze_stock.py --code 600519 --depth quick
```

如果看到分析报告输出，说明安装成功！

#### 预期输出

```
================================================================================
                   A股单只股票分析系统
================================================================================
股票代码: 600519
分析深度: quick
================================================================================

获取股票信息...
股票名称: 贵州茅台

开始分析，请稍候...

================================================================================
                    股票分析报告（快速模式）
================================================================================
股票代码: 600519
股票名称: 贵州茅台
分析时间: 2026-01-29 16:00:00
分析模式: 快速分析（技术面 + 资金面）
================================================================================
...
```

---

## 核心功能使用

### 1. 股票分析 (analyze_stock.py)

#### 功能说明

对单只股票进行多维度综合分析，给出买入/持有/卖出评级及具体建议。

#### 基本用法

**完整分析（推荐）**

```bash
python scripts/analyze_stock.py --code 600519
```

包含：技术面 + 基本面 + 资金面 + AI综合评级

**快速分析**

```bash
python scripts/analyze_stock.py --code 600519 --depth quick
```

仅包含：技术面 + 资金面（速度更快，但信心度较低）

#### 导出报告

```bash
python scripts/analyze_stock.py --code 600519 --output 贵州茅台分析.txt
```

支持的格式：`.txt`、`.md`、`.json`、`.csv`、`.html`

#### 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--code` | 是 | 股票代码（6位数字） | `600519` |
| `--depth` | 否 | 分析深度：`quick`或`full`（默认） | `--depth quick` |
| `--output` | 否 | 导出报告到文件 | `--output report.txt` |
| `--verbose` | 否 | 显示详细日志 | `--verbose` |

#### 分析结果解读

**评级说明**：
- **BUY（买入）**：综合得分≥70分，建议买入
- **HOLD（持有）**：综合得分45-70分，建议观望或持有
- **SELL（卖出）**：综合得分<45分，建议卖出

**信心度**：1-10分，分数越高表示评级越可靠
- 8-10分：高信心度，可以作为主要决策依据
- 5-7分：中等信心度，建议结合其他信息
- 1-4分：低信心度，仅供参考

**目标价与止损价**：
- 目标价：预期的合理价位
- 止损价：风险控制价位，建议设置止损单

#### 使用示例

**示例1：分析贵州茅台（完整分析）**

```bash
python scripts/analyze_stock.py --code 600519
```

**示例2：快速分析平安银行**

```bash
python scripts/analyze_stock.py --code 000001 --depth quick
```

**示例3：分析并导出报告**

```bash
python scripts/analyze_stock.py --code 000858 --output 五粮液分析.txt
```

#### 注意事项

1. 股票代码必须是6位数字（如600519），不需要市场后缀
2. 完整分析需要DeepSeek API密钥
3. 快速分析不需要API密钥，但准确度较低
4. 首次分析某只股票时可能需要较长时间（下载数据）
5. 分析结果仅供参考，不构成投资建议

---

### 2. 批量筛选 (run_screening.py)

#### 功能说明

根据预设条件批量筛选优质股票，支持技术面、基本面、资金面多维度过滤。

#### 预设筛选策略

系统提供8种预设策略，涵盖不同投资风格和市场环境：

**原有策略（基础策略）**

| 策略名称 | 代码 | 适用场景 | 主要指标 |
|---------|------|---------|---------|
| 强势动量股 | `strong_momentum` | 短线交易 | 技术面强势、成交量放大、资金流入 |
| 价值成长股 | `value_growth` | 价值投资 | 基本面优秀、成长性好、估值合理 |
| 资金流入股 | `capital_inflow` | 资金驱动 | 主力资金流入、大单活跃 |

**新增策略（进阶策略）**

| 策略名称 | 代码 | 适用场景 | 主要指标 | 风险等级 |
|---------|------|---------|---------|---------|
| 低PE价值股 | `low_pe_value` | 价值投资、中长期 | PE<15、ROE>10%、低估值优质股 | 低 |
| 高股息率股 | `high_dividend` | 稳健投资、长期持有 | 股息率>3%、稳定分红历史 | 低 |
| 突破新高股 | `breakout` | 趋势跟踪、短中期 | 突破20日新高、放量确认 | 中高 |
| 超卖反弹股 | `oversold_rebound` | 短期交易、逆向 | RSI<30后反弹、均值回归 | 高 |
| 机构重仓股 | `institutional_favorite` | 中长期投资、跟随聪明钱 | 机构持仓>30%、持仓增加 | 中 |

**策略选择建议**

- **保守型投资者**：推荐 `high_dividend`（高股息）、`low_pe_value`（低PE价值）
- **稳健型投资者**：推荐 `value_growth`（价值成长）、`institutional_favorite`（机构重仓）
- **激进型投资者**：推荐 `strong_momentum`（强势动量）、`breakout`（突破新高）
- **短线交易者**：推荐 `oversold_rebound`（超卖反弹）、`strong_momentum`（强势动量）
- **资金驱动型**：推荐 `capital_inflow`（资金流入）、`breakout`（突破新高）

#### 基本用法

**使用预设策略筛选**

```bash
python scripts/run_screening.py --preset strong_momentum
```

默认返回TOP 20只股票。

**自定义返回数量**

```bash
python scripts/run_screening.py --preset value_growth --top 50
```

**设置最低分数**

```bash
python scripts/run_screening.py --preset capital_inflow --min-score 70
```

#### 导出结果

**导出为CSV**

```bash
python scripts/run_screening.py --preset strong_momentum --output 筛选结果.csv
```

**导出为Excel**

```bash
python scripts/run_screening.py --preset value_growth --output 筛选结果.xlsx
```

#### 参数说明

| 参数 | 必需 | 说明 | 默认值 |
|------|------|------|--------|
| `--preset` | 是 | 预设策略名称 | - |
| `--top` | 否 | 返回TOP N只股票 | 20 |
| `--min-score` | 否 | 最低综合评分 | 0 |
| `--output` | 否 | 导出结果文件 | - |
| `--no-parallel` | 否 | 禁用并行处理 | 启用 |
| `--max-workers` | 否 | 最大并行线程数 | 5 |
| `--verbose` | 否 | 显示详细日志 | - |

#### 性能优化

**并行处理（推荐）**

```bash
python scripts/run_screening.py --preset strong_momentum --max-workers 10
```

使用更多线程加速处理（注意：线程过多可能导致API限流）

**串行处理**

```bash
python scripts/run_screening.py --preset value_growth --no-parallel
```

速度较慢，但资源占用少，适合低配置机器。

#### 使用示例

**示例1：筛选强势动量股TOP 20**

```bash
python scripts/run_screening.py --preset strong_momentum
```

**示例2：筛选价值成长股TOP 50并导出**

```bash
python scripts/run_screening.py --preset value_growth --top 50 --output 价值股.csv
```

**示例3：筛选高分资金流入股**

```bash
python scripts/run_screening.py --preset capital_inflow --min-score 75 --output 高分股.xlsx
```

**示例4：筛选低PE价值股（价值投资）**

```bash
python scripts/run_screening.py --preset low_pe_value --top 30 --output 低PE价值股.csv
```

适合寻找被市场低估的优质公司，PE<15且ROE>10%。

**示例5：筛选高股息率股（稳健投资）**

```bash
python scripts/run_screening.py --preset high_dividend --top 50 --output 高股息股.xlsx
```

适合追求稳定现金流的投资者，股息率>3%的稳定分红股。

**示例6：筛选突破新高股（趋势跟踪）**

```bash
python scripts/run_screening.py --preset breakout --top 20 --min-score 65
```

适合短中期趋势交易，捕捉突破20日新高并放量确认的强势股。

**示例7：筛选超卖反弹股（短期交易）**

```bash
python scripts/run_screening.py --preset oversold_rebound --top 15 --output 超卖反弹.csv
```

适合短期交易，捕捉RSI超卖后的反弹机会（均值回归）。

**示例8：筛选机构重仓股（跟随聪明钱）**

```bash
python scripts/run_screening.py --preset institutional_favorite --top 40 --output 机构重仓.xlsx
```

适合中长期投资，跟随机构投资方向，机构持仓比例>30%。

#### 策略组合使用建议

**组合1：稳健价值投资组合**
```bash
# 低PE价值股
python scripts/run_screening.py --preset low_pe_value --top 20 --output 组合1_低PE.csv

# 高股息率股
python scripts/run_screening.py --preset high_dividend --top 20 --output 组合1_高股息.csv

# 机构重仓股
python scripts/run_screening.py --preset institutional_favorite --top 20 --output 组合1_机构重仓.csv
```

**组合2：短线交易组合**
```bash
# 强势动量股
python scripts/run_screening.py --preset strong_momentum --top 15 --output 组合2_动量.csv

# 突破新高股
python scripts/run_screening.py --preset breakout --top 15 --output 组合2_突破.csv

# 超卖反弹股
python scripts/run_screening.py --preset oversold_rebound --top 10 --output 组合2_反弹.csv
```

#### 注意事项

1. 批量筛选耗时较长（可能需要10-30分钟），请耐心等待
2. 建议开启并行处理以提高速度
3. **新增策略的特殊注意事项**：
   - `breakout`（突破新高）：注意追高风险，建议设置止损
   - `oversold_rebound`（超卖反弹）：需要快进快出，避免抄底下跌趋势
   - `low_pe_value`（低PE价值）：需要结合基本面深入分析，避免价值陷阱
   - `high_dividend`（高股息）：注意分红的可持续性，避免股息陷阱
   - `institutional_favorite`（机构重仓）：机构数据可能有延迟，需谨慎判断
3. 筛选结果会自动按评分排序
4. 首次筛选会下载大量数据，后续运行会使用缓存

---

### 3. 策略回测 (run_backtest.py)

#### 功能说明

使用历史数据回测交易策略，评估策略的盈利能力和风险水平。

#### 支持的策略

目前支持的策略：
- **momentum**：动量策略（基于价格动量和成交量）

更多策略开发中...

#### 基本用法

**基本回测**

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01
```

默认回测到今天。

**指定结束日期**

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --end 2023-12-31
```

**自定义初始资金**

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --capital 500000
```

#### 生成图表

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --plot
```

生成回测结果可视化图表（包括资金曲线、回撤曲线等）。

#### 导出报告

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --output 回测报告.txt
```

#### 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--strategy` | 是 | 策略名称 | `momentum` |
| `--code` | 是 | 股票代码 | `600519` |
| `--start` | 是 | 开始日期（YYYY-MM-DD） | `2023-01-01` |
| `--end` | 否 | 结束日期（YYYY-MM-DD） | `2023-12-31` |
| `--capital` | 否 | 初始资金 | `100000`（默认） |
| `--plot` | 否 | 生成图表 | - |
| `--output` | 否 | 导出报告 | `report.txt` |
| `--verbose` | 否 | 详细输出 | - |

#### 回测指标说明

**基础指标**：
- **总收益率**：整个回测期间的总收益率
- **最终资金**：回测结束时的账户资金
- **总交易次数**：买卖交易的总次数
- **胜率**：盈利交易占比

**风险指标**：
- **夏普比率**：风险调整后的收益率（>1较好，>2优秀）
- **最大回撤**：资金曲线的最大下跌幅度
- **波动率**：收益率的标准差
- **索提诺比率**：下行风险调整后的收益率

**进阶指标**：
- **年化收益率**：年化后的收益率
- **Calmar比率**：年化收益率/最大回撤
- **盈亏比**：平均盈利/平均亏损
- **平均持仓天数**：单笔交易的平均持有时间

#### 使用示例

**示例1：回测贵州茅台（最近一年）**

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01
```

**示例2：回测并生成图表**

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --plot
```

**示例3：完整回测（自定义资金、导出报告、生成图表）**

```bash
python scripts/run_backtest.py \
  --strategy momentum \
  --code 600519 \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --capital 500000 \
  --plot \
  --output 贵州茅台回测.txt
```

#### 注意事项

1. 回测遵循A股T+1规则（当日买入次日才能卖出）
2. 考虑了交易费用（佣金、印花税等）
3. 回测结果不代表未来表现
4. 建议使用至少1年以上的数据进行回测
5. 数据量越大，回测越准确，但耗时也越长

---

### 4. 实时监控 (daily_monitor.py)

#### 功能说明

监控股票池中的股票，自动检测交易信号并发送提醒。

#### 基本用法

**使用默认配置**

```bash
python scripts/daily_monitor.py
```

持续监控，按Ctrl+C停止。

**运行一次后退出**

```bash
python scripts/daily_monitor.py --once
```

适合定时任务（cron/计划任务）。

**使用自定义配置**

```bash
python scripts/daily_monitor.py --config config/my_monitoring.yaml
```

#### 配置监控列表

编辑`config/monitoring.yaml`：

```yaml
monitoring:
  # 监控列表
  watchlist:
    - code: "600519"
      name: "贵州茅台"
    - code: "000858"
      name: "五粮液"
    - code: "600036"
      name: "招商银行"
```

#### 信号类型

系统会检测以下信号：

1. **MA均线交叉**：短期均线上穿/下穿长期均线
2. **RSI超买超卖**：RSI进入超买（>70）或超卖（<30）区域
3. **成交量突破**：成交量突然放大（2倍以上）
4. **止损触发**：价格触及止损位
5. **止盈触发**：价格触及止盈位

#### 提醒设置

在`config/monitoring.yaml`中配置：

```yaml
monitoring:
  alerts:
    # 最低优先级（只提醒此级别及以上的信号）
    min_priority: "medium"  # low, medium, high, critical

    # 通知渠道
    channels:
      - console  # 控制台输出
      - log      # 日志文件

    # 去重窗口（秒）
    dedup_window: 900  # 同一信号15分钟内不重复提醒
```

#### 参数说明

| 参数 | 必需 | 说明 | 默认值 |
|------|------|------|--------|
| `--config` | 否 | 配置文件路径 | `config/monitoring.yaml` |
| `--once` | 否 | 运行一次后退出 | 持续运行 |

#### 使用示例

**示例1：启动持续监控**

```bash
python scripts/daily_monitor.py
```

**示例2：定时任务（每小时运行一次）**

添加到crontab：
```bash
0 * * * * cd /path/to/A-stock && python scripts/daily_monitor.py --once
```

**示例3：使用自定义配置**

```bash
python scripts/daily_monitor.py --config config/my_stocks.yaml
```

#### 每日总结

停止监控时（Ctrl+C），系统会自动生成每日总结报告：

```
================================================================================
                           每日监控总结
================================================================================
监控时间: 2026-01-29 09:30:00 - 2026-01-29 15:00:00
监控股票: 4只

检测到的信号:
  [HIGH] 贵州茅台: MA5上穿MA20，买入信号
  [MEDIUM] 五粮液: RSI进入超卖区（28.5），反弹机会
  [HIGH] 招商银行: 成交量突破（2.3倍），资金活跃

总计: 3个信号
================================================================================
```

#### 注意事项

1. 监控服务需要持续运行，建议使用screen/tmux
2. 非交易时间也可以运行，但信号较少
3. 可以配合定时任务实现自动化监控
4. 监控列表不宜过多（建议<50只），否则影响性能

---

## 配置说明

### 配置文件概览

系统配置文件位于`config/`目录：

```
config/
├── config.yaml         # 主配置文件
├── strategies.yaml     # 策略配置
├── risk_rules.yaml     # 风控规则
└── monitoring.yaml     # 监控配置
```

### 主配置文件 (config.yaml)

#### 数据源配置

```yaml
data:
  provider: akshare
  cache:
    enabled: true          # 启用缓存
    directory: ./data/cache
    ttl:
      realtime: 60         # 实时行情缓存60秒
      daily: 3600          # 日线数据缓存1小时
      financial: 86400     # 财务数据缓存1天
```

**说明**：
- `enabled`：建议开启缓存，减少API请求
- `ttl`：根据需要调整缓存时间

#### AI配置

```yaml
ai:
  provider: deepseek
  model: deepseek-chat
  reasoning_model: deepseek-reasoner
  temperature: 0.7        # 0-1，越高越随机
  max_tokens: 4000        # 最大生成token数
  timeout: 30             # 请求超时（秒）

  rating_weights:
    technical: 0.30       # 技术面权重
    fundamental: 0.30     # 基本面权重
    capital: 0.25         # 资金面权重
    sentiment: 0.15       # 情绪面权重
```

**说明**：
- `temperature`：控制AI输出的随机性
- `rating_weights`：可根据投资风格调整各维度权重

#### 市场配置

```yaml
market:
  limit_ratio:
    main_board: 0.10      # 主板涨跌停10%
    star_market: 0.20     # 科创板涨跌停20%
    gem: 0.20             # 创业板涨跌停20%

  trading_hours:
    morning_start: "09:30"
    morning_end: "11:30"
    afternoon_start: "13:00"
    afternoon_end: "15:00"

  min_lot: 100            # 最小交易单位（1手=100股）
```

### 环境变量配置 (.env)

#### 必需配置

```bash
# DeepSeek API Key（必需，用于AI分析）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

#### 可选配置

```bash
# 调试模式
DEBUG=false

# 数据缓存
CACHE_ENABLED=true
CACHE_DIR=./data/cache

# 数据库
DB_PATH=./data/storage/a_stock.db
```

### DeepSeek API配置

#### 获取API密钥

1. 访问 [DeepSeek平台](https://platform.deepseek.com)
2. 注册并登录账号
3. 进入"API密钥"页面
4. 点击"创建新密钥"
5. 复制密钥并保存到`.env`文件

#### 免费额度

- DeepSeek提供免费额度
- 日常使用完全够用
- 超出免费额度后按使用量付费

#### API使用建议

1. 不要在代码中硬编码API密钥
2. 定期检查API使用情况
3. 使用快速分析模式可以节省API调用
4. 批量操作时注意API限流

### 策略配置 (strategies.yaml)

#### 动量策略配置

```yaml
momentum:
  parameters:
    # 技术指标
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70

    macd_fast: 12
    macd_slow: 26
    macd_signal: 9

    # 交易参数
    stop_loss: 0.08         # 止损8%
    take_profit: 0.15       # 止盈15%
    max_holding_days: 10    # 最大持仓10天
```

**参数调优建议**：
- `stop_loss`：根据风险承受能力调整（5%-15%）
- `take_profit`：根据预期收益调整（10%-30%）
- `max_holding_days`：短线5-15天，中线20-60天

### 监控配置 (monitoring.yaml)

#### 监控列表

```yaml
monitoring:
  watchlist:
    - code: "600519"
      name: "贵州茅台"
    - code: "000858"
      name: "五粮液"
```

#### 信号检测

```yaml
monitoring:
  signals:
    enabled_detectors:
      - ma_crossover      # MA均线交叉
      - rsi               # RSI超买超卖
      - volume_breakout   # 成交量突破
      - stop_loss         # 止损触发
      - take_profit       # 止盈触发

    # 参数
    ma_short: 5
    ma_long: 20
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
```

---

## 常见问题FAQ

### 数据获取问题

**Q1: 提示"未获取到数据"怎么办？**

A: 可能的原因和解决方案：
1. 检查股票代码是否正确（必须是6位数字）
2. 检查网络连接是否正常
3. 尝试清空缓存：删除`data/cache/`目录
4. 更换数据源时间段（避开交易时间高峰）

**Q2: 数据下载很慢怎么办？**

A: 优化建议：
1. 启用缓存（默认已启用）
2. 避开交易时间高峰期
3. 减小数据范围（缩短时间跨度）
4. 使用并行下载（在筛选功能中）

**Q3: 缓存数据如何更新？**

A: 缓存策略：
- 实时行情：60秒后自动更新
- 日线数据：1小时后自动更新
- 财务数据：1天后自动更新
- 手动清除：删除`data/cache/`目录

### API配置问题

**Q4: DeepSeek API密钥配置后仍提示错误？**

A: 检查清单：
1. 确认`.env`文件存在且格式正确
2. 确认API密钥无空格、换行
3. 确认API密钥未过期
4. 检查网络能否访问DeepSeek API
5. 尝试重新生成API密钥

**Q5: API调用超出限额怎么办？**

A: 应对策略：
1. 使用`--depth quick`进行快速分析（不调用API）
2. 减少分析频率
3. 升级DeepSeek付费套餐
4. 等待下个计费周期

**Q6: 不想使用AI功能可以吗？**

A: 完全可以：
- 股票分析：使用`--depth quick`模式
- 批量筛选：会自动降级为非AI模式
- 回测：不依赖AI功能
- 监控：不依赖AI功能

### 常见错误处理

**Q7: 提示"ModuleNotFoundError"？**

A: 缺少依赖包，执行：
```bash
pip install -r requirements.txt
```

**Q8: 提示"Permission denied"？**

A: 权限问题，解决方案：
1. 检查脚本是否有执行权限
2. 检查日志目录是否可写
3. 在Windows上以管理员身份运行

**Q9: 回测结果不合理？**

A: 可能原因：
1. 数据质量问题（检查数据时间范围）
2. 策略参数不合适（尝试调参）
3. 数据量太少（建议至少1年数据）
4. 复权方式问题（默认使用前复权）

**Q10: 监控服务自动停止？**

A: 原因和解决：
1. 使用screen/tmux保持后台运行
2. 检查系统资源是否充足
3. 查看日志文件排查错误
4. 配置自动重启脚本

### 性能优化

**Q11: 批量筛选很慢？**

A: 加速方法：
1. 开启并行处理（默认开启）
2. 增加并行线程数：`--max-workers 10`
3. 启用数据缓存
4. 减小筛选范围

**Q12: 内存占用过高？**

A: 优化建议：
1. 减小批量操作的数量
2. 关闭不必要的缓存
3. 定期清理日志文件
4. 减少并行线程数

---

## 进阶使用

### 自定义筛选条件

#### 创建自定义筛选器

1. 编辑`src/screening/screener.py`
2. 添加新的预设条件：

```python
PRESETS = {
    'my_custom': {
        'name': '我的策略',
        'filters': {
            'technical': {'rsi': (40, 60), 'macd': 'bullish'},
            'fundamental': {'roe': 0.15, 'pe': (0, 25)},
            'capital': {'trend': 'inflow', 'strength': 'medium'}
        }
    }
}
```

#### 使用自定义筛选器

```bash
python scripts/run_screening.py --preset my_custom
```

### 参数调优

#### 技术指标参数

常用参数调优方向：

**RSI参数**：
- 超卖阈值：20-30（越低越保守）
- 超买阈值：70-80（越高越保守）
- 周期：6-21（短期用6-14，长期用14-21）

**MACD参数**：
- 快线：8-15（常用12）
- 慢线：20-30（常用26）
- 信号线：7-12（常用9）

**均线参数**：
- 短期：3-10（常用5）
- 中期：10-30（常用20）
- 长期：50-250（常用60、120、250）

#### 止损止盈参数

**止损策略**：
- 短线：5%-8%
- 中线：8%-12%
- 长线：12%-20%

**止盈策略**：
- 短线：10%-15%
- 中线：15%-25%
- 长线：25%-50%

### 结果解读

#### 技术面得分解读

- **90-100分**：极强势，可能超买
- **70-89分**：强势，买入机会
- **50-69分**：中性，观望为主
- **30-49分**：弱势，规避风险
- **0-29分**：极弱势，可能超卖

#### 基本面得分解读

- **90-100分**：财务优秀，白马股
- **70-89分**：财务良好，质地优
- **50-69分**：财务一般，谨慎
- **30-49分**：财务欠佳，警惕
- **0-29分**：财务堪忧，避免

#### 资金面得分解读

- **90-100分**：主力强力流入
- **70-89分**：主力持续流入
- **50-69分**：资金平衡
- **30-49分**：主力流出
- **0-29分**：主力大幅流出

#### 综合评分解读

综合评分是各维度加权平均：

```
综合分 = 技术面×30% + 基本面×30% + 资金面×25% + 情绪面×15%
```

**投资建议**：
- **80分以上**：优质标的，重点关注
- **70-79分**：较好标的，可以配置
- **60-69分**：一般标的，适量参与
- **50-59分**：观望标的，等待机会
- **50分以下**：规避标的，暂不介入

---

## 最佳实践

### 股票分析最佳实践

1. **优先使用完整分析**：虽然耗时较长，但结果更准确
2. **关注信心度**：低信心度的评级仅供参考
3. **结合多个时间周期**：短期+中期+长期综合判断
4. **重视风险提示**：特别是A股特有风险
5. **设置止损止盈**：严格执行风险控制

### 批量筛选最佳实践

1. **分阶段筛选**：先用快速模式初筛，再详细分析
2. **关注筛选理由**：理解入选原因很重要
3. **定期更新筛选**：市场变化快，建议每周筛选
4. **多策略组合**：不同策略筛选结果交叉验证
5. **建立股票池**：筛选后持续跟踪观察

### 策略回测最佳实践

1. **使用充足的数据**：至少1年，最好2-3年
2. **分段回测**：牛市、熊市、震荡市分别测试
3. **避免过度优化**：不要为了好看的回测结果过度调参
4. **考虑交易成本**：系统已包含，但要理解其影响
5. **样本外测试**：用未参与调参的数据验证策略

### 实时监控最佳实践

1. **精选监控列表**：不超过20-30只，聚焦优质标的
2. **合理设置提醒**：避免信息过载
3. **定期复盘**：每日/每周总结监控结果
4. **快速响应**：收到高优先级信号及时处理
5. **结合基本面**：技术信号要结合基本面分析

### 风险管理建议

1. **仓位控制**：
   - 单只股票不超过总资金的20%
   - 单一行业不超过总资金的30%
   - 总仓位不超过总资金的95%

2. **止损纪律**：
   - 买入时设定止损价
   - 严格执行，不抱侥幸心理
   - 根据市场波动调整止损幅度

3. **分散投资**：
   - 持仓5-10只股票
   - 跨行业分散
   - 避免过度集中

4. **心态管理**：
   - 不追涨杀跌
   - 不频繁交易
   - 保持理性客观

---

## 技术支持

### 获取帮助

1. **查看文档**：详细阅读本用户指南
2. **查看日志**：`logs/`目录下的日志文件
3. **提交Issue**：在GitHub上提交问题
4. **社区讨论**：加入用户社区讨论

### 日志位置

- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 交易日志：`logs/trade.log`
- 监控日志：`logs/monitoring.log`

### 更新系统

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 免责声明

1. 本系统仅供学习和研究使用，不构成投资建议
2. 历史数据和回测结果不代表未来表现
3. 投资有风险，入市需谨慎
4. 请根据自身情况理性投资，自负盈亏
5. 系统作者不承担任何投资损失责任

---

## 附录

### A. 常用股票代码

| 代码 | 名称 | 板块 |
|------|------|------|
| 600519 | 贵州茅台 | 主板 |
| 000858 | 五粮液 | 主板 |
| 600036 | 招商银行 | 主板 |
| 000001 | 平安银行 | 主板 |
| 688036 | 传音控股 | 科创板 |
| 300750 | 宁德时代 | 创业板 |

### B. 技术指标速查

| 指标 | 超买 | 超卖 | 中性 |
|------|------|------|------|
| RSI | >70 | <30 | 40-60 |
| KDJ | >80 | <20 | 20-80 |
| CCI | >100 | <-100 | -100~100 |

### C. 系统目录结构

```
A-stock/
├── config/              # 配置文件
│   ├── config.yaml
│   ├── strategies.yaml
│   ├── risk_rules.yaml
│   └── monitoring.yaml
├── src/                 # 源代码
│   ├── core/           # 核心模块
│   ├── data/           # 数据层
│   ├── analysis/       # 分析模块
│   ├── strategy/       # 策略模块
│   ├── backtest/       # 回测模块
│   ├── screening/      # 筛选模块
│   ├── monitoring/     # 监控模块
│   └── risk/           # 风控模块
├── scripts/            # 可执行脚本
│   ├── analyze_stock.py
│   ├── run_screening.py
│   ├── run_backtest.py
│   └── daily_monitor.py
├── data/               # 数据目录
│   ├── cache/         # 缓存数据
│   └── storage/       # 数据库
├── logs/               # 日志文件
├── tests/              # 测试文件
└── docs/               # 文档
```

---

**文档版本**：v1.0
**更新日期**：2026-01-29
**适用系统版本**：A-stock v1.0+

如有疑问或建议，欢迎反馈！
