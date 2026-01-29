# 回测指标计算指南

## 概述

`BacktestMetrics` 模块提供了全面的回测性能评估指标，帮助您深入分析交易策略的表现。

## 功能特性

### 1. 收益指标
- **总收益率**: 整个回测期间的收益率
- **年化收益率**: 按年化计算的收益率
- **月度收益**: 每月的收益率分布

### 2. 风险指标
- **最大回撤**: 资产净值的最大回撤百分比和金额
- **波动率**: 年化波动率（标准差）
- **夏普比率**: 风险调整后的收益率
- **索提诺比率**: 只考虑下行风险的收益率
- **Calmar比率**: 年化收益率与最大回撤的比值

### 3. 交易指标
- **总交易次数**: 完成的交易对数
- **胜率**: 盈利交易占总交易的比例
- **盈亏比**: 平均盈利与平均亏损的比值
- **平均持仓天数**: 平均每笔交易的持仓时间
- **最大连续盈利/亏损**: 连续盈利或亏损的最大次数

### 4. A股特色指标
- **总费用**: 所有交易的手续费和印花税总和
- **费用占比**: 费用占初始资金的百分比

## 使用方法

### 基本使用

```python
from src.backtest import BacktestEngine
from src.strategy.your_strategy import YourStrategy

# 1. 创建回测引擎
engine = BacktestEngine(
    initial_cash=1000000,
    commission=0.0003,
    stamp_tax=0.001
)

# 2. 运行回测
results = engine.run_backtest(
    strategy_class=YourStrategy,
    data=your_data,
    stock_code='600000'
)

# 3. 查看详细指标
print(results['summary'])  # 格式化的摘要
metrics = results['metrics']  # 详细指标字典
```

### 单独使用 BacktestMetrics

```python
from src.backtest import BacktestMetrics
import pandas as pd

# 准备数据
portfolio_values = pd.Series([100000, 101000, 99000, 102000, ...],
                             index=pd.date_range('2024-01-01', periods=100))

trades = [
    {
        'entry_date': '2024-01-05',
        'exit_date': '2024-01-15',
        'pnl': 800,
        'commission': 100,
        'status': 'closed'
    },
    # ... 更多交易
]

# 创建指标计算器
metrics = BacktestMetrics(
    portfolio_values=portfolio_values,
    trades=trades,
    initial_capital=100000
)

# 计算所有指标
all_metrics = metrics.calculate_all_metrics()

# 或单独计算特定指标
sharpe = metrics.calculate_sharpe_ratio()
max_dd = metrics.calculate_max_drawdown()
win_rate = metrics.calculate_win_rate()
```

### 生成可视化数据

```python
# 权益曲线数据
equity_curve = metrics.generate_equity_curve_data()
# 包含: date, value, return, cumulative_return

# 回撤曲线数据
drawdown_curve = metrics.generate_drawdown_curve_data()
# 包含: date, drawdown

# 可以使用matplotlib绘图
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(equity_curve['date'], equity_curve['value'])
plt.title('Portfolio Value Over Time')
plt.xlabel('Date')
plt.ylabel('Value')
plt.show()
```

## 指标详解

### 夏普比率 (Sharpe Ratio)
衡量每单位风险获得的超额收益。

**计算公式**: `(年化收益率 - 无风险利率) / 年化波动率`

**解读**:
- > 1: 表现良好
- > 2: 表现优秀
- > 3: 表现卓越
- < 0: 策略表现不如无风险资产

### 索提诺比率 (Sortino Ratio)
类似夏普比率，但只考虑下行波动（负收益的波动）。

**优势**: 更适合评估风险厌恶型策略，不惩罚上行波动。

### Calmar比率
年化收益率与最大回撤的比值。

**解读**:
- 数值越大越好
- > 0.5: 表现良好
- > 1.0: 表现优秀

### 最大回撤
从峰值到谷值的最大跌幅。

**重要性**:
- 评估策略的最坏情况
- 判断资金管理是否合理
- 一般建议控制在20%以内

## 输出示例

```
╔══════════════════════════════════════════════════════════════╗
║                      回测结果摘要                              ║
╠══════════════════════════════════════════════════════════════╣
║ 初始资金: ¥1,000,000.00
║ 最终资金: ¥1,150,000.00
║ 总收益率: 15.00%
║ 年化收益: 20.50%
╠══════════════════════════════════════════════════════════════╣
║ 最大回撤: 8.50%
║ 波动率: 12.30%
║ 夏普比率: 1.4228
║ 索提诺比率: 2.1450
║ Calmar比率: 2.4118
╠══════════════════════════════════════════════════════════════╣
║ 总交易次数: 25
║ 胜率: 60.00%
║ 盈亏比: 1.85
║ 平均持仓: 5.2天
║ 最大连胜: 5次
║ 最大连亏: 3次
╠══════════════════════════════════════════════════════════════╣
║ 总费用: ¥1,250.00
║ 费用占比: 0.13%
╚══════════════════════════════════════════════════════════════╝
```

## 注意事项

1. **数据质量**: 确保输入的资产价值序列完整且按时间排序
2. **交易记录**: 必须包含 `pnl`, `commission`, `status` 字段
3. **年化计算**: 默认使用252个交易日
4. **无风险利率**: 默认3%，可以根据实际情况调整

## 最佳实践

1. **综合评估**: 不要只看单一指标，要综合多个维度评估
2. **风险优先**: 在追求收益的同时，更要关注风险指标（回撤、波动率）
3. **样本外测试**: 使用未参与优化的数据进行测试
4. **多周期验证**: 在不同市场环境下测试策略稳定性

## 常见问题

**Q: 为什么我的夏普比率是负数？**
A: 说明策略的年化收益率低于无风险利率，建议优化策略。

**Q: 盈亏比很高但胜率很低，是好策略吗？**
A: 这是"小亏大赚"型策略，可以盈利，但需要承受较长的亏损期，心理压力大。

**Q: 如何降低最大回撤？**
A: 可以通过设置止损、分散投资、降低仓位等方式控制回撤。

## 参考资源

- [夏普比率详解](https://en.wikipedia.org/wiki/Sharpe_ratio)
- [索提诺比率详解](https://en.wikipedia.org/wiki/Sortino_ratio)
- [最大回撤计算](https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp)
