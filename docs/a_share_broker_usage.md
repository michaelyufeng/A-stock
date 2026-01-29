# A股Broker使用指南

## 概述

`AShareBroker` 是自定义的 backtrader Broker 实现，专门针对A股市场特色设计，包含：

1. **涨跌停限制**
   - 主板（沪深主板）：±10%
   - 科创板：±20%
   - 创业板：±20%

2. **交易单位限制**
   - 最小交易单位：100股（1手）
   - 自动向下取整到100股整数倍

3. **费用计算**
   - 佣金：买卖双向，0.03%，最低5元
   - 印花税：仅卖出，0.1%
   - 过户费：忽略（金额很小）

4. **T+1制度**
   - 在策略层面实现（BaseStrategy）
   - Broker负责涨跌停和交易单位限制

## 使用方法

### 基本用法

```python
from src.backtest.engine import BacktestEngine
from src.strategy.short_term.momentum import MomentumStrategy

# 创建回测引擎
engine = BacktestEngine(initial_cash=100000)

# 运行回测（传入stock_code启用A股规则）
results = engine.run_backtest(
    strategy_class=MomentumStrategy,
    data=your_data,
    stock_code='600000'  # 指定股票代码
)
```

### 板块识别

根据股票代码自动识别板块和涨跌停限制：

```python
# 主板（10%涨跌停）
engine.run_backtest(..., stock_code='600000')  # 上海主板
engine.run_backtest(..., stock_code='000001')  # 深圳主板

# 科创板（20%涨跌停）
engine.run_backtest(..., stock_code='688001')

# 创业板（20%涨跌停）
engine.run_backtest(..., stock_code='300750')

# 未指定（默认主板10%）
engine.run_backtest(..., stock_code=None)
```

### 直接使用 AShareBroker

也可以直接创建 `AShareBroker` 实例：

```python
import backtrader as bt
from src.backtest.a_share_broker import AShareBroker

# 创建 Cerebro
cerebro = bt.Cerebro()

# 使用自定义Broker
broker = AShareBroker(stock_code='688001')
cerebro.broker = broker

# 设置初始资金
cerebro.broker.setcash(100000)

# 添加数据和策略...
```

## 功能详解

### 1. 涨跌停限制

#### 买入限制

- 当买入价格接近涨停价（≥涨停价*0.99）时，订单被拒绝
- 示例：
  ```python
  # 前一日收盘价10元，主板涨停价11元
  # 尝试以11元买入 → 订单拒绝
  # 尝试以10.8元买入 → 订单允许
  ```

#### 卖出限制

- 当卖出价格接近跌停价（≤跌停价*1.01）时，订单被拒绝
- 示例：
  ```python
  # 前一日收盘价10元，主板跌停价9元
  # 尝试以9元卖出 → 订单拒绝
  # 尝试以9.2元卖出 → 订单允许
  ```

### 2. 交易单位自动调整

所有买卖订单自动调整为100股整数倍：

```python
# 买入250股 → 自动调整为200股
# 买入99股 → 订单拒绝（不足100股）
# 卖出550股 → 自动调整为500股
```

### 3. 费用计算

#### 买入费用

```python
# 买入1000股@10元
# 佣金 = 1000 * 10 * 0.0003 = 3元 → 最低5元
# 总费用 = 5元
```

#### 卖出费用

```python
# 卖出1000股@10元
# 佣金 = 1000 * 10 * 0.0003 = 3元 → 最低5元
# 印花税 = 1000 * 10 * 0.001 = 10元
# 总费用 = 5 + 10 = 15元
```

## 板块代码前缀

系统根据以下前缀识别板块：

| 板块 | 代码前缀 | 涨跌停限制 |
|------|---------|-----------|
| 上海主板 | 600, 601, 603, 605 | ±10% |
| 深圳主板 | 000, 001 | ±10% |
| 创业板 | 300 | ±20% |
| 科创板 | 688 | ±20% |
| 北交所 | 82, 83, 87 | ±10% |

## 运行示例

项目提供了完整的示例程序：

```bash
python examples/demo_a_share_broker.py
```

该示例演示了：
1. 主板股票（600000）的回测
2. 科创板股票（688001）的回测
3. 创业板股票（300750）的回测

## 测试

运行单元测试验证功能：

```bash
# 测试 AShareBroker
pytest tests/backtest/test_a_share_broker.py -v

# 测试回测引擎集成
pytest tests/backtest/test_engine.py -v

# 运行所有回测测试
pytest tests/backtest/ -v
```

## 注意事项

1. **涨跌停判断基于前一日收盘价**
   - 使用 `data.close[-1]` 获取前一日收盘价
   - 实时计算涨跌停价格

2. **容差设置**
   - 买入涨停容差：0.99（避免浮点数误差）
   - 卖出跌停容差：1.01（避免浮点数误差）

3. **T+1制度**
   - 在策略层面（BaseStrategy）实现
   - Broker只负责价格和数量限制

4. **最低佣金**
   - 每笔交易最低佣金5元
   - 适用于买入和卖出

5. **印花税**
   - 仅在卖出时收取
   - 税率0.1%（千分之一）

## 实现细节

### 核心方法

1. **`_get_limit_ratio()`**
   - 根据股票代码识别板块
   - 返回涨跌停限制比例

2. **`_get_limit_price(prev_close)`**
   - 计算涨跌停价格
   - 返回 (涨停价, 跌停价)

3. **`buy()`**
   - 覆盖父类买入方法
   - 添加涨停限制和数量调整

4. **`sell()`**
   - 覆盖父类卖出方法
   - 添加跌停限制和数量调整

5. **`_getcommission()`**
   - 覆盖父类佣金计算
   - 买入：佣金（最低5元）
   - 卖出：佣金 + 印花税

## 配置参数

所有参数在 `src/core/constants.py` 中定义：

```python
# 涨跌停限制
MAIN_BOARD_LIMIT = 0.10      # 主板±10%
STAR_MARKET_LIMIT = 0.20     # 科创板±20%
GEM_LIMIT = 0.20             # 创业板±20%

# 交易单位
MIN_LOT = 100                # 最小交易单位

# 交易费用
COMMISSION_RATE = 0.0003     # 佣金0.03%
MIN_COMMISSION = 5.0         # 最低佣金5元
STAMP_TAX_RATE = 0.001       # 印花税0.1%
```

## 扩展

如需自定义规则，可以继承 `AShareBroker` 并覆盖相应方法：

```python
from src.backtest.a_share_broker import AShareBroker

class CustomBroker(AShareBroker):
    def buy(self, *args, **kwargs):
        # 添加自定义买入逻辑
        # ...
        return super().buy(*args, **kwargs)
```

## 相关文档

- [BacktestEngine 使用指南](./backtest_engine_usage.md)
- [BaseStrategy 开发指南](./strategy_development.md)
- [技术指标计算](./technical_indicators.md)
