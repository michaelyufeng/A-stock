# 风险管理器使用指南

## 概述

RiskManager（风险管理器）是A股量化交易系统的核心风控模块，提供全方位的风险管理功能：

- ✅ 仓位管理（单一股票、行业、总仓位限制）
- ✅ 止损止盈计算（固定、移动、ATR三种方式）
- ✅ 交易限制检查（ST股、退市风险股、交易频率）
- ✅ 持仓管理（添加、移除、更新）
- ✅ 组合风险评估
- ✅ A股特色功能（连续涨跌停检查、T+1流动性管理）

## 快速开始

### 基本使用

```python
from src.risk.risk_manager import RiskManager
from datetime import datetime

# 初始化风险管理器（总资金100万）
risk_mgr = RiskManager(total_capital=1_000_000)

# 1. 建仓前检查
result = risk_mgr.check_position_limit(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    position_value=150_000  # 拟建仓15万
)

if result['allowed']:
    print("✅ 可以建仓")
    print(f"最大可建仓: {result['max_position_value']}元")
else:
    print(f"❌ 不允许建仓: {result['reason']}")

# 2. 检查交易限制
trade_check = risk_mgr.check_trade_restrictions('600519', '贵州茅台')
if not trade_check['allowed']:
    print(f"❌ 交易受限: {trade_check['reason']}")

# 3. 建仓
risk_mgr.add_position(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    shares=100,
    entry_price=1500.0,
    entry_date=datetime.now()
)

# 4. 查看持仓
position = risk_mgr.get_position('600519')
print(f"止损价: {position['stop_loss_price']:.2f}")
print(f"止盈价: {position['take_profit_price']:.2f}")

# 5. 更新市值
risk_mgr.update_position('600519', current_price=1600)

# 6. 评估风险
risk_assessment = risk_mgr.assess_portfolio_risk()
print(f"风险等级: {risk_assessment['risk_level']}")
print(f"总仓位: {risk_assessment['total_position_pct']*100:.1f}%")
```

## 核心功能详解

### 1. 仓位限制检查

#### check_position_limit()

检查是否允许建仓，考虑三个维度的限制：

**参数:**
- `stock_code`: 股票代码（如'600519'）
- `stock_name`: 股票名称（如'贵州茅台'）
- `sector`: 所属行业（如'白酒'）
- `position_value`: 拟建仓金额（元）

**返回:**
```python
{
    'allowed': True/False,           # 是否允许建仓
    'reason': '原因说明',             # 不允许的原因
    'max_position_value': 200000,    # 单一持仓最大金额
    'warnings': ['警告信息1', ...]    # 预警信息列表
}
```

**限制规则（来自 `config/risk_rules.yaml`）:**
- 单一持仓 ≤ 20%（可配置）
- 单一行业 ≤ 30%（可配置）
- 总仓位 ≤ 95%（可配置）
- 最小建仓金额 ≥ 10,000元（可配置）

**示例:**
```python
# 案例1: 正常建仓
result = risk_mgr.check_position_limit('600519', '贵州茅台', '白酒', 150_000)
# → {'allowed': True, 'max_position_value': 200000, ...}

# 案例2: 超过单一持仓限制
result = risk_mgr.check_position_limit('600519', '贵州茅台', '白酒', 250_000)
# → {'allowed': False, 'reason': '单一持仓超过限制20%', ...}

# 案例3: 行业集中度过高
risk_mgr.add_position('600519', '贵州茅台', '白酒', 133, 1500, datetime.now())
result = risk_mgr.check_position_limit('000858', '五粮液', '白酒', 200_000)
# → {'allowed': False, 'reason': '行业集中度超过限制30%', ...}
```

### 2. 交易限制检查

#### check_trade_restrictions()

检查是否允许交易该股票。

**参数:**
- `stock_code`: 股票代码
- `stock_name`: 股票名称

**返回:**
```python
{
    'allowed': True/False,
    'reason': '原因说明'
}
```

**限制规则:**
1. **ST股票过滤**: 自动拒绝ST、*ST、SST、S*ST股票
2. **交易频率限制**: 每日最多5次交易（可配置）
3. **冷却期机制**: 平仓后5天内不能再次交易同一股票（可配置）

**示例:**
```python
# 案例1: ST股被拒绝
result = risk_mgr.check_trade_restrictions('600000', 'ST海航')
# → {'allowed': False, 'reason': 'ST股禁止交易'}

# 案例2: 超过每日交易次数
# (假设今日已交易5次)
result = risk_mgr.check_trade_restrictions('600519', '贵州茅台')
# → {'allowed': False, 'reason': '每日交易次数超过限制'}

# 案例3: 冷却期内
# (假设3天前刚卖出该股票)
result = risk_mgr.check_trade_restrictions('600519', '贵州茅台')
# → {'allowed': False, 'reason': '冷却期内，需等待5天'}
```

### 3. 止损止盈计算

#### calculate_stop_loss()

计算止损价格，支持三种方式。

**参数:**
- `entry_price`: 入场价格
- `method`: 止损方式（'fixed'/'trailing'/'atr'）
- `atr`: ATR值（仅method='atr'时需要）

**止损方式对比:**

| 方式 | 说明 | 适用场景 | 配置参数 |
|------|------|----------|----------|
| fixed | 固定比例止损 | 趋势明确，快速止损 | fixed_ratio: 0.08 (8%) |
| trailing | 移动止损 | 持续盈利，保护利润 | trailing_ratio: 0.05 (5%) |
| atr | ATR倍数止损 | 波动较大，动态止损 | atr_multiplier: 2.0 |

**示例:**
```python
# 固定止损（默认8%）
stop_loss = risk_mgr.calculate_stop_loss(100.0, method='fixed')
# → 92.0

# 移动止损（默认5%）
stop_loss = risk_mgr.calculate_stop_loss(100.0, method='trailing')
# → 95.0

# ATR止损（ATR=3.0，倍数2.0）
stop_loss = risk_mgr.calculate_stop_loss(100.0, method='atr', atr=3.0)
# → 94.0  (100 - 3*2)
```

#### calculate_take_profit()

计算止盈价格，支持两种方式。

**参数:**
- `entry_price`: 入场价格
- `method`: 止盈方式（'fixed'/'dynamic'）

**示例:**
```python
# 固定止盈（默认15%）
take_profit = risk_mgr.calculate_take_profit(100.0, method='fixed')
# → 115.0

# 动态止盈（1.5倍固定止盈）
take_profit = risk_mgr.calculate_take_profit(100.0, method='dynamic')
# → 122.5
```

### 4. 持仓管理

#### add_position()

添加新持仓，自动计算止损止盈位。

**参数:**
- `stock_code`: 股票代码
- `stock_name`: 股票名称
- `sector`: 所属行业
- `shares`: 股数
- `entry_price`: 入场价格
- `entry_date`: 入场日期

**示例:**
```python
risk_mgr.add_position(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    shares=100,
    entry_price=1500.0,
    entry_date=datetime.now()
)
```

#### remove_position()

移除持仓并计算盈亏。

**参数:**
- `stock_code`: 股票代码
- `exit_price`: 卖出价格
- `exit_date`: 卖出日期

**返回:** 盈亏金额（浮点数）

**示例:**
```python
# 盈利案例
pnl = risk_mgr.remove_position('600519', exit_price=1650, exit_date=datetime.now())
# → 15000.0  ((1650-1500) * 100)

# 亏损案例
pnl = risk_mgr.remove_position('600519', exit_price=1380, exit_date=datetime.now())
# → -12000.0  ((1380-1500) * 100)
```

#### update_position()

更新持仓当前价格和市值。

**参数:**
- `stock_code`: 股票代码
- `current_price`: 当前价格

**示例:**
```python
risk_mgr.update_position('600519', current_price=1600)

position = risk_mgr.get_position('600519')
print(position['current_value'])    # 160000
print(position['unrealized_pnl'])   # 10000
```

#### get_position() / get_all_positions()

查询持仓信息。

**示例:**
```python
# 查询单个持仓
position = risk_mgr.get_position('600519')
if position:
    print(f"股数: {position['shares']}")
    print(f"成本: {position['entry_price']}")
    print(f"现价: {position['current_price']}")
    print(f"浮盈: {position['unrealized_pnl']}")

# 查询所有持仓
all_positions = risk_mgr.get_all_positions()
for code, pos in all_positions.items():
    print(f"{code}: {pos['stock_name']}")
```

### 5. 组合风险评估

#### assess_portfolio_risk()

评估整个组合的风险水平。

**返回:**
```python
{
    'risk_level': 'low'|'medium'|'high',  # 风险等级
    'warnings': ['警告信息1', ...],        # 风险警告列表
    'total_position_pct': 0.85,           # 总仓位比例
    'sector_exposure': {                   # 行业分布
        '白酒': 0.30,
        '银行': 0.15,
        ...
    },
    'position_count': 5                    # 持仓数量
}
```

**风险等级判断逻辑:**
- **Low**: 总仓位<70%，无集中度警告
- **Medium**: 总仓位≥70% 或 有预警
- **High**: 行业集中度>24%（30%*0.8）或 个股集中度>20%

**示例:**
```python
risk = risk_mgr.assess_portfolio_risk()

print(f"风险等级: {risk['risk_level']}")
print(f"总仓位: {risk['total_position_pct']*100:.1f}%")
print(f"持仓数量: {risk['position_count']}")

# 行业分布
for sector, pct in risk['sector_exposure'].items():
    print(f"  {sector}: {pct*100:.1f}%")

# 风险警告
if risk['warnings']:
    print("⚠️ 风险警告:")
    for warning in risk['warnings']:
        print(f"  - {warning}")
```

### 6. A股特色功能

#### check_continuous_limit()

检查连续涨跌停情况。

**参数:**
- `stock_code`: 股票代码
- `kline_df`: K线DataFrame（需包含open, close, high, low列）

**返回:**
```python
{
    'continuous_limit_up': 3,      # 连续涨停次数
    'continuous_limit_down': 0,    # 连续跌停次数
    'warning': True                # 是否预警
}
```

**示例:**
```python
import pandas as pd

# 准备K线数据
kline_df = pd.DataFrame({
    'open': [100, 110, 121, 133.1, 146.4],
    'close': [110, 121, 133.1, 146.4, 146.4],
    'high': [110, 121, 133.1, 146.4, 146.4],
    'low': [100, 110, 121, 133.1, 146.4],
})

result = risk_mgr.check_continuous_limit('600519', kline_df)

if result['warning']:
    if result['continuous_limit_up'] >= 3:
        print(f"⚠️ 连续{result['continuous_limit_up']}个涨停，注意风险！")
    if result['continuous_limit_down'] >= 3:
        print(f"⚠️ 连续{result['continuous_limit_down']}个跌停，注意风险！")
```

## 配置说明

所有风控参数在 `config/risk_rules.yaml` 中配置：

```yaml
# 仓位管理
position:
  max_single_position: 0.20      # 单一持仓≤20%
  max_sector_exposure: 0.30      # 单一行业≤30%
  max_total_position: 0.95       # 总仓位≤95%
  min_position_value: 10000      # 最小建仓1万元

# 止损止盈
stop_loss:
  method: "fixed"                # fixed/trailing/atr
  fixed_ratio: 0.08              # 固定止损8%
  trailing_ratio: 0.05           # 移动止损5%
  atr_multiplier: 2.0            # ATR倍数

take_profit:
  method: "fixed"                # fixed/dynamic
  fixed_ratio: 0.15              # 固定止盈15%

# 交易限制
trading_limits:
  max_trades_per_day: 5          # 每日最多5次
  cooling_period: 5              # 冷却期5天

# 风险预警
alerts:
  position_concentration:
    warning: 0.15                # 15%预警
    critical: 0.20               # 20%严重
```

## 完整使用示例

```python
from src.risk.risk_manager import RiskManager
from datetime import datetime

# 初始化
risk_mgr = RiskManager(total_capital=1_000_000)

# ========== 建仓流程 ==========

# 1. 检查仓位限制
position_check = risk_mgr.check_position_limit(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    position_value=150_000
)

if not position_check['allowed']:
    print(f"❌ 仓位限制: {position_check['reason']}")
    exit()

# 2. 检查交易限制
trade_check = risk_mgr.check_trade_restrictions('600519', '贵州茅台')

if not trade_check['allowed']:
    print(f"❌ 交易限制: {trade_check['reason']}")
    exit()

# 3. 建仓
risk_mgr.add_position(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    shares=100,
    entry_price=1500.0,
    entry_date=datetime.now()
)

print("✅ 建仓成功")

# ========== 持仓监控 ==========

# 更新市价
risk_mgr.update_position('600519', current_price=1600)

# 查看持仓
position = risk_mgr.get_position('600519')
print(f"当前市值: {position['current_value']:,.0f}元")
print(f"浮动盈亏: {position['unrealized_pnl']:,.0f}元")
print(f"止损价: {position['stop_loss_price']:.2f}元")
print(f"止盈价: {position['take_profit_price']:.2f}元")

# 风险评估
risk = risk_mgr.assess_portfolio_risk()
print(f"\n风险等级: {risk['risk_level']}")
print(f"总仓位: {risk['total_position_pct']*100:.1f}%")

# ========== 平仓流程 ==========

# 达到止盈目标，平仓
if position['current_price'] >= position['take_profit_price']:
    pnl = risk_mgr.remove_position(
        stock_code='600519',
        exit_price=position['current_price'],
        exit_date=datetime.now()
    )
    print(f"✅ 止盈平仓，盈利: {pnl:,.0f}元")
```

## 最佳实践

### 1. 建仓前双重检查

```python
# ✅ 推荐做法
position_ok = risk_mgr.check_position_limit(...)
trade_ok = risk_mgr.check_trade_restrictions(...)

if position_ok['allowed'] and trade_ok['allowed']:
    risk_mgr.add_position(...)
```

### 2. 定期风险评估

```python
# 每日收盘后评估风险
def daily_risk_check():
    risk = risk_mgr.assess_portfolio_risk()

    if risk['risk_level'] == 'high':
        print("⚠️ 高风险警告，建议减仓！")
        for warning in risk['warnings']:
            print(f"  - {warning}")
```

### 3. 动态调整止损

```python
# 盈利后移动止损
position = risk_mgr.get_position('600519')
if position['unrealized_pnl'] > 0:
    # 重新计算移动止损
    new_stop_loss = risk_mgr.calculate_stop_loss(
        position['current_price'],
        method='trailing'
    )
    # 更新止损位（手动实现）
    position['stop_loss_price'] = max(
        position['stop_loss_price'],
        new_stop_loss
    )
```

### 4. 行业分散投资

```python
# 检查行业分布
risk = risk_mgr.assess_portfolio_risk()

# 避免单一行业过于集中
if max(risk['sector_exposure'].values()) > 0.25:
    print("⚠️ 行业过于集中，建议分散投资")
```

## 常见问题

### Q1: 如何修改风控参数？

A: 编辑 `config/risk_rules.yaml` 文件，修改后重新初始化RiskManager即可。

### Q2: 止损被触发后如何处理？

A: RiskManager只负责计算止损价，不会自动平仓。需要在策略层判断并调用 `remove_position()`。

### Q3: 如何处理涨跌停股票？

A: 使用 `check_continuous_limit()` 检查连续涨跌停，避免追高杀跌。

### Q4: T+1限制如何处理？

A: 持仓记录包含 `entry_date`，可以判断是否满足T+1要求：
```python
from datetime import timedelta

position = risk_mgr.get_position('600519')
holding_days = (datetime.now() - position['entry_date']).days

if holding_days >= 1:
    # 可以卖出
    pass
```

### Q5: 如何实现分批止盈？

A: 根据配置中的 `partial_take_profit` 参数：
```python
position = risk_mgr.get_position('600519')
entry_price = position['entry_price']
current_price = position['current_price']

# 第一目标：盈利10%，减仓50%
if current_price >= entry_price * 1.10:
    partial_shares = int(position['shares'] * 0.5)
    # 部分平仓逻辑
```

## 相关文件

- `src/risk/risk_manager.py` - 主实现文件
- `config/risk_rules.yaml` - 配置文件
- `tests/risk/test_risk_manager.py` - 测试文件（35个测试用例）
- `examples/risk_management_demo.py` - 完整示例

## 下一步扩展

计划中的功能：
- [ ] 动态仓位调整（根据市场波动）
- [ ] 风险预算分配（按风险分配仓位）
- [ ] 历史风控记录（保存所有决策）
- [ ] 风险报告生成（每日风险摘要）
- [ ] 支撑位/压力位止损
