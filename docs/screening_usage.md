# 选股筛选器使用指南

## 概述

StockScreener（选股筛选器）是 A-stock 项目的核心组件之一，用于从大量股票中筛选出符合条件的优质股票。它支持多维度筛选、预设方案、自定义权重和并行处理。

## 主要功能

### 1. 数据源支持

- **全市场筛选**: 从沪深A股所有股票中筛选
- **指定股票池**: 从给定的股票代码列表中筛选
- **自动过滤**: 自动过滤ST股、退市风险股

### 2. 筛选维度

- **技术面**: RSI、MACD、均线、成交量等技术指标
- **基本面**: ROE、毛利率、净利率、成长性等财务指标
- **资金面**: 主力资金流向、净流入趋势

### 3. 预设方案

#### strong_momentum (强势动量股)
- 重点关注技术面和资金面
- 权重配置: 技术60% + 资金20% + 基本面20%
- 适合短期交易

#### value_growth (价值成长股)
- 重点关注基本面
- 权重配置: 基本面60% + 技术30% + 资金10%
- 适合中长期投资

#### capital_inflow (资金流入股)
- 重点关注主力资金动向
- 权重配置: 资金40% + 技术40% + 基本面20%
- 适合捕捉热点

## 快速开始

### 基本用法

```python
from src.screening.screener import StockScreener

# 创建筛选器
screener = StockScreener()

# 使用预设方案筛选
results = screener.screen(
    stock_pool=['600519', '000001', '600036'],  # 指定股票池
    preset='strong_momentum',                    # 使用预设方案
    top_n=10,                                    # 返回TOP 10
    min_score=60                                 # 最低60分
)

# 查看结果
print(results[['code', 'name', 'score', 'reason']])
```

### 自定义筛选

```python
# 自定义筛选条件
custom_filters = {
    'use_fundamental': True,  # 启用基本面分析
    'use_capital': True,      # 启用资金面分析
    'weights': {
        'technical': 0.4,     # 技术面权重40%
        'fundamental': 0.4,   # 基本面权重40%
        'capital': 0.2        # 资金面权重20%
    }
}

results = screener.screen(
    stock_pool=['600519', '000001', '600036'],
    filters=custom_filters,
    top_n=5
)
```

### 全市场筛选（并行处理）

```python
# 全市场筛选，使用并行处理
results = screener.screen(
    stock_pool=None,          # None表示全市场
    preset='value_growth',
    top_n=20,
    min_score=70,
    parallel=True,            # 启用并行处理
    max_workers=5             # 5个工作线程
)
```

## 返回结果

筛选器返回一个 pandas DataFrame，包含以下列：

| 列名 | 说明 | 类型 |
|------|------|------|
| code | 股票代码 | str |
| name | 股票名称 | str |
| score | 综合评分（0-100） | float |
| tech_score | 技术面评分（0-100） | float |
| fundamental_score | 基本面评分（0-100） | float |
| capital_score | 资金面评分（0-100） | float |
| current_price | 当前价格 | float |
| reason | 入选理由 | str |

## 评分规则

### 技术面评分 (0-100分)

基础分: 50分

**加分项**:
- RSI在40-70之间: +10分
- RSI超卖(<30): +15分
- MACD金叉: +15分
- 价格站上MA20: +10分
- 成交量放大(>MA5*1.5): +10分

**减分项**:
- RSI超买(>80): -10分
- MACD死叉: -10分

### 基本面评分

使用 `FinancialMetrics.get_overall_score()` 计算，综合考虑：
- 盈利能力（ROE、毛利率）
- 成长性（营收增长、利润增长）
- 财务健康度（负债率、流动比率）

### 资金面评分

- 主力资金流入: 70分
- 主力资金流出: 30分
- 资金平衡: 50分

## 性能优化

### 并行处理

对于大股票池（>10只），建议使用并行处理：

```python
results = screener.screen(
    stock_pool=large_pool,
    parallel=True,
    max_workers=5  # 根据CPU核心数调整
)
```

### 控制分析深度

通过筛选条件控制是否启用基本面和资金面分析：

```python
# 只使用技术面（最快）
filters = {
    'use_fundamental': False,
    'use_capital': False
}

# 使用技术面+资金面（中等速度）
filters = {
    'use_fundamental': False,
    'use_capital': True
}

# 全面分析（最慢但最准确）
filters = {
    'use_fundamental': True,
    'use_capital': True
}
```

## 注意事项

### API 调用限制

- 全市场筛选需要大量API调用，注意akshare的速率限制
- 建议测试时使用小股票池（<20只）
- 利用缓存机制减少重复调用

### 数据要求

- 股票至少需要60天的K线数据
- 数据不足的股票会被自动过滤

### ST股过滤

- 自动过滤股票代码或名称中包含"ST"的股票
- 自动过滤*ST退市风险股

## 实际案例

### 案例1: 寻找强势突破股

```python
screener = StockScreener()

# 从沪深300成分股中筛选
hs300_codes = ['600519', '000001', '600036', ...]  # 沪深300代码

results = screener.screen(
    stock_pool=hs300_codes,
    preset='strong_momentum',
    top_n=20,
    min_score=70,
    parallel=True,
    max_workers=5
)

# 筛选出技术面强势的股票
strong_stocks = results[results['tech_score'] >= 75]
print(strong_stocks[['code', 'name', 'tech_score', 'reason']])
```

### 案例2: 价值投资选股

```python
# 重视基本面的价值投资
value_filters = {
    'use_fundamental': True,
    'use_capital': False,
    'weights': {
        'technical': 0.2,
        'fundamental': 0.7,
        'capital': 0.1
    }
}

results = screener.screen(
    stock_pool=None,  # 全市场
    filters=value_filters,
    top_n=30,
    min_score=75,
    parallel=True
)

# 筛选基本面优秀的股票
value_stocks = results[results['fundamental_score'] >= 80]
```

### 案例3: 资金热点追踪

```python
# 追踪主力资金流向
results = screener.screen(
    stock_pool=None,
    preset='capital_inflow',
    top_n=50,
    min_score=65,
    parallel=True
)

# 查看资金流入最强的股票
top_inflow = results.nlargest(10, 'capital_score')
print(top_inflow[['code', 'name', 'capital_score', 'current_price']])
```

## 错误处理

筛选器内置了完善的错误处理机制：

- 单个股票分析失败不影响整体流程
- 网络错误自动重试（通过缓存机制）
- 数据不足自动跳过
- 所有错误都会记录日志

## 运行示例

项目提供了完整的使用示例：

```bash
# 运行示例脚本
python examples/screening_example.py
```

## 测试

运行测试套件：

```bash
# 运行所有测试
pytest tests/screening/test_screener.py -v

# 运行特定测试
pytest tests/screening/test_screener.py::TestStockScreener::test_screen_with_preset -v
```

## 后续优化建议

1. **增加更多筛选维度**: 行业、市值、市盈率等
2. **机器学习评分**: 使用ML模型替代简单加权
3. **实时监控**: 定时筛选并推送结果
4. **回测验证**: 验证筛选策略的历史表现
5. **数据库存储**: 存储筛选历史便于分析

## 技术支持

如有问题，请查看：
- 项目文档: `/docs`
- 测试用例: `/tests/screening`
- 示例代码: `/examples/screening_example.py`
