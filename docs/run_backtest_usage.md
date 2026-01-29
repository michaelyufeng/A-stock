# run_backtest.py 使用说明

## 概述

`run_backtest.py` 是一个命令行工具，用于对A股策略进行历史回测。它使用 BacktestEngine 和策略模块来模拟历史交易，评估策略表现。

## 功能特性

- 支持多种策略回测（当前支持：momentum）
- 自定义回测时间范围
- 自定义初始资金
- 详细的性能指标报告
- 结果导出为文本文件
- 可选的可视化图表生成

## 基本用法

### 最简单的回测

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01
```

这将使用动量策略回测贵州茅台（600519）从2023年1月1日至今天的表现。

### 指定结束日期

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --end 2023-12-31
```

### 自定义初始资金

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --capital 500000
```

### 显示详细信息

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --verbose
```

详细模式会显示更多指标，包括：
- 年化收益率
- 波动率
- 索提诺比率
- Calmar比率
- 盈亏比
- 平均持仓天数
- 最大连胜/连亏次数
- 交易费用统计

### 导出结果报告

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --output report.txt
```

这会将详细的回测结果保存到 `report.txt` 文件中。

### 生成可视化图表

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --plot
```

这会生成 `backtest_chart.png` 图表文件，显示：
- 价格走势
- 买卖点标记
- 资金曲线

### 组合使用

```bash
python scripts/run_backtest.py \
    --strategy momentum \
    --code 600519 \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --capital 1000000 \
    --verbose \
    --output results/backtest_600519.txt \
    --plot
```

## 命令行参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy` | 是 | 无 | 策略名称（momentum/value/breakout等） |
| `--code` | 是 | 无 | 股票代码（如：600519） |
| `--start` | 是 | 无 | 回测开始日期（YYYY-MM-DD） |
| `--end` | 否 | 今天 | 回测结束日期（YYYY-MM-DD） |
| `--capital` | 否 | 1000000 | 初始资金（元） |
| `--verbose` | 否 | false | 显示详细输出 |
| `--output` | 否 | 无 | 导出结果到文件 |
| `--plot` | 否 | false | 生成可视化图表 |

## 输出说明

### 基本输出

```
======================================================================
                        回测结果摘要
======================================================================
初始资金: ¥1,000,000.00
最终资金: ¥1,150,000.00
总收益率: 15.00%
----------------------------------------------------------------------
夏普比率: 1.5000
最大回撤: 8.00%
----------------------------------------------------------------------
总交易次数: 10
胜率: 60.00%
======================================================================
```

### 详细输出（--verbose）

额外包含：
- 年化收益率
- 波动率
- 索提诺比率
- Calmar比率
- 盈亏比
- 平均持仓天数
- 最大连胜/连亏次数
- 总费用和费用占比

## 支持的策略

### momentum - 动量策略

基于技术指标的短线交易策略。

**买入条件**（满足3个或以上）：
1. RSI从超卖区回升
2. MACD金叉
3. 成交量放大
4. 价格突破MA20

**卖出条件**（任意满足）：
1. RSI超买
2. MACD死叉
3. 触及止损（-8%）
4. 触及止盈（+15%）
5. 超过最大持仓天数（10天）

**配置参数**：
- RSI周期：14
- RSI超卖：30
- RSI超买：70
- MACD参数：12/26/9
- 成交量放大倍数：2.0
- 止损：8%
- 止盈：15%
- 最大持仓：10天

## 注意事项

### 日期格式

日期必须使用 `YYYY-MM-DD` 格式，例如：
- ✓ 正确：`2023-01-01`
- ✗ 错误：`2023/01/01`、`20230101`

### 数据量要求

- 建议使用至少30天以上的数据进行回测
- 数据量过少会影响回测准确性
- 系统会在数据不足时发出警告

### A股特色

回测引擎考虑了A股的特殊规则：
- **T+1交易**：当日买入的股票次日才能卖出
- **涨跌停限制**：主板/中小板 ±10%，科创板/创业板 ±20%
- **交易费用**：
  - 佣金：0.03%（双向）
  - 印花税：0.1%（仅卖出）
- **交易单位**：按手交易（1手=100股）

### 回测的局限性

1. **历史数据不代表未来**：过去的表现不能保证未来收益
2. **滑点影响**：真实交易中可能无法按回测价格成交
3. **流动性考虑**：回测假设可以按任意数量交易
4. **心理因素**：实盘交易会受到情绪影响
5. **市场环境变化**：策略在不同市场环境下表现可能差异很大

## 故障排查

### 错误：股票代码不存在

```
✗ 数据获取失败: 股票代码不存在
```

**解决方案**：
- 检查股票代码是否正确（6位数字）
- 确认该股票在指定日期范围内有交易数据

### 错误：开始日期必须早于结束日期

```
✗ 参数错误: 开始日期必须早于结束日期
```

**解决方案**：
- 确保 `--start` 日期早于 `--end` 日期
- 检查日期格式是否正确

### 警告：数据量较少

```
⚠ 数据量较少（22条），可能影响回测准确性
```

**解决方案**：
- 扩大回测日期范围
- 这只是警告，回测仍会继续执行

## 示例场景

### 1. 快速测试策略

测试最近一个月的表现：

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2024-01-01 --end 2024-01-31
```

### 2. 完整年度回测

评估全年表现：

```bash
python scripts/run_backtest.py \
    --strategy momentum \
    --code 600519 \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --verbose \
    --output reports/2023_backtest.txt \
    --plot
```

### 3. 小资金测试

测试小额资金表现：

```bash
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --capital 100000
```

### 4. 批量回测多只股票

使用shell脚本批量回测：

```bash
#!/bin/bash
for code in 600519 000001 000002; do
    python scripts/run_backtest.py \
        --strategy momentum \
        --code $code \
        --start 2023-01-01 \
        --output reports/backtest_${code}.txt
done
```

## 进阶使用

### 添加新策略

1. 在 `src/strategy/` 下创建策略类，继承 `BaseStrategy`
2. 在 `config/strategies.yaml` 中添加策略配置
3. 在 `scripts/run_backtest.py` 的 `STRATEGY_MAP` 中注册策略
4. 运行回测：`--strategy your_strategy_name`

### 自定义策略参数

修改 `config/strategies.yaml` 中的参数配置，无需修改代码。

## 相关文档

- [BacktestEngine API](../src/backtest/engine.py)
- [Strategy Development Guide](./strategy_development.md)
- [Performance Metrics](./backtest_metrics.md)

## 技术支持

如有问题，请查看：
1. 日志文件：`logs/backtest_YYYYMMDD.log`
2. 测试用例：`tests/scripts/test_run_backtest.py`
3. 源代码：`scripts/run_backtest.py`
