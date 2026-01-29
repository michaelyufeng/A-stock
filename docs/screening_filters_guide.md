# 选股筛选器过滤器使用指南

## 概述

本文档说明如何使用选股筛选器的过滤功能来筛选符合特定条件的股票。

## 架构设计

### 核心组件

1. **filters.py** - 过滤器函数库
   - 提供5个独立的过滤函数
   - 每个函数对应一个筛选策略
   - 提供统一的`apply_filters()`接口

2. **screener.py** - 选股筛选器主类
   - 集成过滤器功能
   - 提供5个预设策略
   - 支持自定义过滤条件

### 工作流程

```
股票池 → 快速过滤(ST股等) → 获取数据 → 应用过滤器 → 评分 → 排序 → 返回TOP N
                                    ↑
                                filters.py
```

## 过滤器函数详解

### 1. filter_by_pe_roe - 低PE价值股过滤

**用途**: 筛选低估值、高盈利能力的股票

**参数**:
- `df`: 股票数据DataFrame（必须包含'PE'和'ROE'列）
- `pe_max`: PE比率最大值（例如15.0表示PE<15）
- `roe_min`: ROE最小值，单位为%（例如10.0表示ROE>10%）

**返回**: 过滤后的DataFrame

**示例**:
```python
from src.screening import filters
import pandas as pd

# 创建股票数据
stocks = pd.DataFrame({
    '代码': ['000001', '000002', '000003'],
    'PE': [8.5, 18.0, 12.0],
    'ROE': [12.0, 8.0, 15.0]
})

# 应用过滤器
result = filters.filter_by_pe_roe(stocks, pe_max=15.0, roe_min=10.0)
# 结果: 000001和000003通过，000002被拒绝（PE=18）
```

**适用场景**:
- 价值投资
- 中长期持有
- 寻找低估值蓝筹股

### 2. filter_by_dividend_yield - 高股息率过滤

**用途**: 筛选高分红收益的股票

**参数**:
- `df`: 股票数据DataFrame（必须包含'股息率'列）
- `yield_min`: 股息率最小值，单位为%（例如3.0表示股息率>=3%）

**返回**: 过滤后的DataFrame

**示例**:
```python
result = filters.filter_by_dividend_yield(stocks, yield_min=3.0)
```

**适用场景**:
- 追求稳定现金流
- 低风险偏好投资者
- 长期持有策略

### 3. filter_by_breakout - 突破新高过滤

**用途**: 筛选价格突破新高并有成交量确认的股票

**参数**:
- `df`: 股票数据DataFrame（必须包含'close'和'volume'列）
- `breakout_days`: 突破周期（20或60日，默认20）
- `volume_ratio_min`: 成交量放大倍数最小值（默认1.2）

**返回**: 过滤后的DataFrame

**筛选逻辑**:
1. 计算前N日最高价（不包括当前日）
2. 检查当前价格是否突破前N日最高价
3. 检查当前成交量是否 >= 前N日平均成交量 × volume_ratio_min
4. 仅当两个条件都满足时通过

**示例**:
```python
result = filters.filter_by_breakout(
    stocks_with_history,  # 需要有历史K线数据
    breakout_days=20,
    volume_ratio_min=1.2
)
```

**适用场景**:
- 趋势跟踪策略
- 短中期交易
- 追涨强势股

**注意事项**:
- 需要设置止损
- 注意追高风险
- 需要足够的历史数据（至少N日）

### 4. filter_by_oversold_rebound - 超卖反弹过滤

**用途**: 筛选出现超卖反弹信号的股票

**参数**:
- `df`: 股票数据DataFrame（必须包含'RSI'列）
- `rsi_oversold`: RSI超卖阈值（默认30.0）
- `rsi_rebound_min`: RSI反弹最小值（默认30.0）
- `lookback_periods`: 回看周期数（默认50）

**返回**: 过滤后的DataFrame

**筛选逻辑**:
1. 检查在lookback_periods期间内，RSI是否曾经低于oversold阈值
2. 检查当前RSI是否已经回升到rebound_min以上
3. 仅当两个条件都满足时通过（确认反弹信号）

**示例**:
```python
result = filters.filter_by_oversold_rebound(
    stocks_with_history,
    rsi_oversold=30.0,
    rsi_rebound_min=30.0,
    lookback_periods=50
)
```

**适用场景**:
- 短期交易
- 逆向投资策略
- 超跌反弹机会

**注意事项**:
- 需要快进快出
- 设置止损位
- 避免抄底下跌趋势中的股票

### 5. filter_by_institutional_holding - 机构重仓过滤

**用途**: 筛选机构重仓持有的股票

**参数**:
- `df`: 股票数据DataFrame（必须包含'机构持仓比例'列）
- `ratio_min`: 机构持仓比例最小值，单位为%（例如30.0表示>=30%）

**返回**: 过滤后的DataFrame

**示例**:
```python
result = filters.filter_by_institutional_holding(stocks, ratio_min=30.0)
```

**适用场景**:
- 中长期投资
- 跟随机构策略
- 寻找高质量标的

**注意事项**:
- 机构数据可能有延迟
- 需要结合基本面分析
- 避免在机构高位减仓时追涨

### 6. apply_filters - 统一过滤接口

**用途**: 根据配置字典应用多个过滤器

**参数**:
- `df`: 股票数据DataFrame
- `filter_config`: 过滤配置字典

**配置字典格式**:
```python
filter_config = {
    'pe_max': 15.0,              # PE最大值
    'roe_min': 10.0,             # ROE最小值
    'dividend_yield_min': 3.0,   # 股息率最小值
    'breakout_days': 20,         # 突破天数
    'volume_ratio_min': 1.2,     # 成交量倍数
    'rsi_oversold': 30.0,        # RSI超卖阈值
    'rsi_rebound_min': 30.0,     # RSI反弹最小值
    'institutional_ratio_min': 30.0  # 机构持仓最小值
}
```

**返回**: 过滤后的DataFrame

**示例**:
```python
# 定义过滤条件
config = {
    'pe_max': 15.0,
    'roe_min': 10.0,
    'dividend_yield_min': 3.0
}

# 应用过滤
result = filters.apply_filters(stocks, config)
```

## 预设策略使用

### 使用StockScreener的预设策略

```python
from src.screening.screener import StockScreener

screener = StockScreener()

# 低PE价值股筛选
results = screener.screen(
    stock_pool=['600519', '000001', '600036'],
    preset='low_pe_value',  # 自动应用PE<15, ROE>10%过滤
    top_n=10,
    min_score=60
)
```

### 5种预设策略

| 策略名称 | 过滤条件 | 适用场景 |
|---------|---------|---------|
| `low_pe_value` | PE<15, ROE>10% | 价值投资，寻找低估值优质股 |
| `high_dividend` | 股息率>=3% | 追求稳定现金流，低风险投资 |
| `breakout` | 突破20日新高+成交量>1.2倍 | 趋势跟踪，追涨强势股 |
| `oversold_rebound` | RSI<30→RSI>30 | 短期交易，捕捉反弹机会 |
| `institutional_favorite` | 机构持仓>=30% | 跟随机构，寻找高质量标的 |

## 链式过滤

可以组合使用多个过滤器:

```python
# 方法1: 手动链式调用
result = stocks.copy()
result = filters.filter_by_pe_roe(result, pe_max=15.0, roe_min=10.0)
result = filters.filter_by_dividend_yield(result, yield_min=3.0)
result = filters.filter_by_institutional_holding(result, ratio_min=30.0)

# 方法2: 使用apply_filters统一接口
config = {
    'pe_max': 15.0,
    'roe_min': 10.0,
    'dividend_yield_min': 3.0,
    'institutional_ratio_min': 30.0
}
result = filters.apply_filters(stocks, config)
```

## 数据要求

### 必需的数据列

不同的过滤器需要不同的数据列:

| 过滤器 | 必需列 |
|-------|-------|
| `filter_by_pe_roe` | PE, ROE |
| `filter_by_dividend_yield` | 股息率 |
| `filter_by_breakout` | close, volume |
| `filter_by_oversold_rebound` | RSI |
| `filter_by_institutional_holding` | 机构持仓比例 |

### 数据来源

在StockScreener中，这些数据来自:
- **PE, ROE, 股息率, 机构持仓比例**: 从`get_realtime_quote()`获取
- **close, volume**: 从`get_daily_kline()`获取
- **RSI**: 从`TechnicalIndicators.calculate_all()`计算

## 错误处理

### 缺少必需列

如果DataFrame缺少必需的列，过滤器会:
- 对于基本面数据(PE/ROE/股息率/机构持仓): 抛出`KeyError`
- 对于技术数据(close/volume/RSI): 返回空DataFrame或记录警告

### NaN值处理

过滤器会自动删除包含NaN值的行:
```python
# 示例: 包含NaN的数据
stocks = pd.DataFrame({
    '代码': ['000001', '000002', '000003'],
    'PE': [10.0, np.nan, 12.0],
    'ROE': [15.0, 12.0, np.nan]
})

result = filters.filter_by_pe_roe(stocks, pe_max=15.0, roe_min=10.0)
# 只有000001通过（000002和000003因为有NaN被删除）
```

## 性能优化

1. **向量化操作**: 所有过滤器使用pandas向量化操作，性能高效
2. **早期退出**: 如果数据不足，立即返回空DataFrame
3. **惰性计算**: 只在需要时计算rolling指标
4. **无前视偏差**: 使用`shift(1)`确保计算不包含当前数据

## 测试

### 运行单元测试
```bash
# 测试所有过滤器
python -m pytest tests/screening/test_filters.py -v

# 测试集成
python -m pytest tests/screening/test_screener.py -v

# 测试覆盖率
python -m pytest tests/screening/ --cov=src/screening --cov-report=term-missing
```

### 验证脚本
```bash
python verify_filters.py
```

### 示例代码
```bash
python examples/screening_with_filters_example.py
```

## 常见问题

### Q: 过滤器为什么返回空结果？

A: 可能的原因:
1. 没有股票满足过滤条件（阈值太严格）
2. 缺少必需的数据列
3. 数据中包含太多NaN值

解决方法:
- 放宽阈值条件
- 确保数据源提供所需字段
- 检查数据质量

### Q: 如何调试过滤结果？

A: 启用调试日志:
```python
import logging
logging.getLogger('src.screening.filters').setLevel(logging.DEBUG)
```

### Q: 突破过滤为什么检测不到突破？

A: 检查:
1. 是否有足够的历史数据（至少N天）
2. 当前价格是否真的突破了前N日最高价
3. 成交量是否满足放大倍数要求

### Q: 如何自定义过滤条件？

A: 两种方法:

**方法1**: 直接调用过滤函数
```python
from src.screening import filters

result = filters.filter_by_pe_roe(stocks, pe_max=12.0, roe_min=15.0)
```

**方法2**: 使用apply_filters配置
```python
config = {'pe_max': 12.0, 'roe_min': 15.0}
result = filters.apply_filters(stocks, config)
```

## 最佳实践

1. **渐进式过滤**: 先应用宽松条件，再逐步收紧
2. **组合使用**: 结合多个过滤器提高筛选质量
3. **验证数据**: 确保数据源可靠且及时
4. **回测验证**: 在历史数据上验证过滤效果
5. **动态调整**: 根据市场环境调整阈值

## 扩展开发

### 添加新的过滤器

1. 在`filters.py`中添加新函数:
```python
def filter_by_custom_metric(
    df: pd.DataFrame,
    metric_threshold: float
) -> pd.DataFrame:
    """自定义指标过滤"""
    if df.empty:
        return df

    # 检查必需列
    if 'custom_metric' not in df.columns:
        raise KeyError("缺少custom_metric列")

    # 应用过滤
    filtered = df[df['custom_metric'] > metric_threshold]

    return filtered
```

2. 在`apply_filters()`中添加支持:
```python
# 在apply_filters函数中添加
if 'custom_metric_threshold' in filter_config:
    result = filter_by_custom_metric(
        result,
        metric_threshold=filter_config['custom_metric_threshold']
    )
```

3. 添加测试:
```python
def test_filter_by_custom_metric():
    df = pd.DataFrame({
        'code': ['A', 'B'],
        'custom_metric': [10, 5]
    })
    result = filter_by_custom_metric(df, metric_threshold=8)
    assert len(result) == 1
    assert result.iloc[0]['code'] == 'A'
```

## 版本历史

### v1.0.0 (2026-01-29)
- 初始版本
- 实现5个核心过滤器
- 集成到StockScreener
- 完整测试覆盖
- 文档和示例

## 参考资料

- 源代码: `src/screening/filters.py`
- 单元测试: `tests/screening/test_filters.py`
- 集成测试: `tests/screening/test_screener.py`
- 使用示例: `examples/screening_with_filters_example.py`
- 验证脚本: `verify_filters.py`
