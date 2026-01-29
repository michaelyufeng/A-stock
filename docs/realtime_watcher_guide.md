# RealTimeWatcher 使用指南

## 概述

RealTimeWatcher（实时行情监控器）是A股量化交易系统监控模块的核心组件，提供实时行情数据获取和缓存功能。

### 核心功能
- ✅ 管理股票监控列表（添加/删除）
- ✅ 批量获取实时行情（优化API调用）
- ✅ 单个股票行情查询
- ✅ 行情数据缓存（可配置刷新策略）
- ✅ 异常处理（网络失败、无效代码）
- ✅ 数据验证和时间戳

## 快速开始

### 基本使用

```python
from src.monitoring.realtime_watcher import RealTimeWatcher

# 初始化监控器
watcher = RealTimeWatcher(
    stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ],
    update_interval=60  # 60秒更新间隔
)

# 更新所有行情
watcher.update_quotes()

# 获取单个股票行情
quote = watcher.get_latest_quote('600519')
print(f"贵州茅台: {quote['current_price']}元")

# 获取所有行情
all_quotes = watcher.get_all_quotes()
for code, quote in all_quotes.items():
    print(f"{quote['name']}: {quote['current_price']}元 ({quote.get('change_pct', 0)*100:.2f}%)")
```

## API 详解

### 初始化

```python
RealTimeWatcher(stock_list: List[Dict], update_interval: int = 60)
```

**参数:**
- `stock_list`: 股票列表，格式 `[{'code': 'XXX', 'name': 'YYY'}, ...]`
- `update_interval`: 更新间隔（秒），默认60秒

**示例:**
```python
# 空监控列表
watcher = RealTimeWatcher(stock_list=[], update_interval=30)

# 预填充监控列表
watcher = RealTimeWatcher(
    stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '600036', 'name': '招商银行'}
    ],
    update_interval=60
)
```

### 监控列表管理

#### add_stock()

添加股票到监控列表。

```python
watcher.add_stock(stock_code: str, stock_name: str)
```

**示例:**
```python
watcher.add_stock('000858', '五粮液')
watcher.add_stock('601318', '中国平安')

# 重复添加会更新名称
watcher.add_stock('600519', '贵州茅台酒')
```

#### remove_stock()

从监控列表移除股票。

```python
removed = watcher.remove_stock(stock_code: str) -> bool
```

**示例:**
```python
# 移除存在的股票
success = watcher.remove_stock('600519')
# → True

# 移除不存在的股票
success = watcher.remove_stock('999999')
# → False
```

#### get_watchlist()

获取当前监控列表。

```python
watchlist = watcher.get_watchlist() -> Dict[str, str]
```

**示例:**
```python
watchlist = watcher.get_watchlist()
# → {'600519': '贵州茅台', '000858': '五粮液'}

for code, name in watchlist.items():
    print(f"{code}: {name}")
```

### 行情获取

#### get_latest_quote()

获取单个股票的最新行情。

```python
quote = watcher.get_latest_quote(
    stock_code: str,
    max_age_seconds: int = None
) -> Optional[Dict]
```

**参数:**
- `stock_code`: 股票代码
- `max_age_seconds`: 缓存最大年龄（秒），超过则刷新，默认None（使用缓存）

**返回数据结构:**
```python
{
    'code': '600519',
    'name': '贵州茅台',
    'current_price': 1650.5,     # 当前价
    'open': 1645.0,               # 开盘价
    'high': 1660.0,               # 最高价
    'low': 1640.0,                # 最低价
    'volume': 1234567,            # 成交量
    'amount': 2.03e9,             # 成交额
    'change_pct': 0.0234,         # 涨跌幅（2.34%）
    'update_time': datetime(...)  # 更新时间
}
```

**示例:**
```python
# 使用缓存
quote = watcher.get_latest_quote('600519')

# 强制刷新（最多60秒缓存）
quote = watcher.get_latest_quote('600519', max_age_seconds=60)

# 检查数据
if quote:
    print(f"股价: {quote['current_price']}")
    print(f"涨跌: {quote['change_pct']*100:.2f}%")
    print(f"更新: {quote['update_time']}")
else:
    print("未找到行情数据")
```

#### get_all_quotes()

获取所有监控股票的行情。

```python
quotes = watcher.get_all_quotes() -> Dict[str, Dict]
```

**示例:**
```python
# 更新后获取
watcher.update_quotes()
quotes = watcher.get_all_quotes()

for code, quote in quotes.items():
    name = quote.get('name', code)
    price = quote.get('current_price', 0)
    change = quote.get('change_pct', 0) * 100

    print(f"{name}({code}): {price:.2f}元 {change:+.2f}%")
```

#### update_quotes()

批量更新所有股票行情。

```python
watcher.update_quotes(force: bool = False)
```

**参数:**
- `force`: 是否强制刷新（忽略缓存），默认False

**示例:**
```python
# 正常更新
watcher.update_quotes()

# 强制刷新
watcher.update_quotes(force=True)
```

## 缓存机制

### 缓存策略

RealTimeWatcher 使用智能缓存减少API调用：

1. **默认缓存**: `get_latest_quote()` 默认返回缓存数据
2. **年龄检查**: 可设置 `max_age_seconds` 自动刷新过期缓存
3. **强制刷新**: `update_quotes(force=True)` 忽略缓存

### 缓存示例

```python
watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

# 第1次调用 - 从API获取
quote1 = watcher.get_latest_quote('600519')

# 第2次调用 - 使用缓存（快速）
quote2 = watcher.get_latest_quote('600519')

# 强制刷新 - 重新获取
watcher.update_quotes(force=True)
quote3 = watcher.get_latest_quote('600519')

# 仅当缓存超过60秒才刷新
quote4 = watcher.get_latest_quote('600519', max_age_seconds=60)
```

### 辅助方法

```python
# 获取缓存年龄
age = watcher.get_quote_age('600519')  # 秒

# 清空缓存
watcher.clear_cache()

# 缓存大小
size = watcher.get_cache_size()  # 缓存条目数
```

## 异常处理

RealTimeWatcher 优雅处理各类异常：

### 网络异常

```python
try:
    watcher.update_quotes()
except Exception as e:
    # 内部已处理，不会抛出异常
    pass

# 检查是否成功
quotes = watcher.get_all_quotes()
if not quotes:
    print("更新失败或无数据")
```

### 无效股票代码

```python
watcher.add_stock('INVALID', '无效股票')

quote = watcher.get_latest_quote('INVALID')
# → None (不会报错)
```

### 部分失败

```python
# 即使部分股票失败，其他股票仍可获取
watcher.add_stock('600519', '贵州茅台')
watcher.add_stock('INVALID', '无效')

watcher.update_quotes()

# 成功的股票仍可用
quote = watcher.get_latest_quote('600519')
# → 有效数据

quote = watcher.get_latest_quote('INVALID')
# → None
```

## 完整使用示例

### 示例1: 基础监控

```python
from src.monitoring.realtime_watcher import RealTimeWatcher
import time

# 初始化
watcher = RealTimeWatcher(stock_list=[], update_interval=60)

# 添加监控股票
watchlist = [
    ('600519', '贵州茅台'),
    ('000858', '五粮液'),
    ('600036', '招商银行'),
    ('601318', '中国平安')
]

for code, name in watchlist:
    watcher.add_stock(code, name)

# 循环监控
for i in range(5):
    print(f"\n=== 第{i+1}次更新 ===")

    # 更新行情
    watcher.update_quotes()

    # 显示行情
    quotes = watcher.get_all_quotes()
    for code, quote in quotes.items():
        name = quote.get('name', code)
        price = quote.get('current_price', 0)
        change = quote.get('change_pct', 0) * 100

        # 彩色输出
        color = '\033[91m' if change < 0 else '\033[92m'
        reset = '\033[0m'

        print(f"{name}({code}): {price:.2f}元 {color}{change:+.2f}%{reset}")

    # 等待
    if i < 4:
        time.sleep(60)
```

### 示例2: 与RiskManager集成

```python
from src.monitoring.realtime_watcher import RealTimeWatcher
from src.risk.risk_manager import RiskManager

# 初始化
risk_mgr = RiskManager(total_capital=1_000_000)
watcher = RealTimeWatcher(stock_list=[])

# 监控持仓
for code, position in risk_mgr.get_all_positions().items():
    watcher.add_stock(code, position['stock_name'])

# 更新持仓价格
watcher.update_quotes()

for code, quote in watcher.get_all_quotes().items():
    current_price = quote.get('current_price')
    if current_price:
        # 更新持仓
        risk_mgr.update_position(code, current_price)

        # 检查止损
        position = risk_mgr.get_position(code)
        if current_price <= position['stop_loss_price']:
            print(f"⚠️ {position['stock_name']} 触发止损！")
            print(f"   当前价: {current_price:.2f}")
            print(f"   止损价: {position['stop_loss_price']:.2f}")
```

### 示例3: 批量监控优化

```python
from src.monitoring.realtime_watcher import RealTimeWatcher

# 监控大量股票
stock_list = []
for i in range(100):
    stock_list.append({
        'code': f'60{i:04d}',
        'name': f'股票{i}'
    })

watcher = RealTimeWatcher(stock_list=stock_list, update_interval=60)

# 批量更新（单次API调用）
watcher.update_quotes()

# 快速查询（从缓存）
for code in [s['code'] for s in stock_list[:10]]:
    quote = watcher.get_latest_quote(code)
    if quote:
        print(f"{quote['name']}: {quote.get('current_price', 'N/A')}")
```

## 性能优化

### 批量获取优化

```python
# ❌ 低效：多次API调用
for code in ['600519', '000858', '600036']:
    quote = watcher.get_latest_quote(code)  # 每次调用API

# ✅ 高效：单次批量获取
watcher.update_quotes()  # 一次性获取所有
quotes = watcher.get_all_quotes()  # 从缓存读取
```

### 缓存利用

```python
# 设置合理的刷新间隔
watcher = RealTimeWatcher(stock_list=stocks, update_interval=60)

# 频繁查询使用缓存
for _ in range(10):
    quote = watcher.get_latest_quote('600519')  # 使用缓存，快速

# 定期刷新
import time
while True:
    watcher.update_quotes()  # 批量刷新
    time.sleep(60)  # 60秒后再刷新
```

## 数据字段说明

### 行情数据字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | str | 股票代码 | '600519' |
| `name` | str | 股票名称 | '贵州茅台' |
| `current_price` | float | 当前价 | 1650.5 |
| `open` | float | 开盘价 | 1645.0 |
| `high` | float | 最高价 | 1660.0 |
| `low` | float | 最低价 | 1640.0 |
| `volume` | int | 成交量（股） | 1234567 |
| `amount` | float | 成交额（元） | 2.03e9 |
| `change_pct` | float | 涨跌幅 | 0.0234 (2.34%) |
| `update_time` | datetime | 更新时间 | datetime(...) |

**注意**: 实际字段可能因数据源而异，建议使用 `.get()` 安全访问。

## 常见问题

### Q1: 如何调整更新频率？

A: 在初始化时设置 `update_interval`：
```python
watcher = RealTimeWatcher(stock_list=[], update_interval=30)  # 30秒
```

### Q2: 如何强制刷新缓存？

A: 使用 `force=True` 或设置 `max_age_seconds`：
```python
# 方法1
watcher.update_quotes(force=True)

# 方法2
quote = watcher.get_latest_quote('600519', max_age_seconds=0)
```

### Q3: 如何处理大量股票监控？

A: 使用批量更新和缓存：
```python
# 添加大量股票
for code, name in large_stock_list:
    watcher.add_stock(code, name)

# 批量更新（单次API调用）
watcher.update_quotes()

# 从缓存快速查询
quotes = watcher.get_all_quotes()
```

### Q4: 如何判断数据是否新鲜？

A: 检查 `update_time` 或使用 `get_quote_age()`：
```python
quote = watcher.get_latest_quote('600519')
age = watcher.get_quote_age('600519')

if age > 300:  # 超过5分钟
    watcher.update_quotes(force=True)
```

### Q5: 如何处理API限流？

A: 合理使用缓存，减少更新频率：
```python
# 设置较长的更新间隔
watcher = RealTimeWatcher(stock_list=stocks, update_interval=120)

# 利用缓存，避免频繁调用
quote = watcher.get_latest_quote('600519')  # 优先使用缓存
```

## 相关文件

- **实现**: `src/monitoring/realtime_watcher.py`
- **测试**: `tests/monitoring/test_realtime_watcher.py` (25个测试用例)
- **示例**: `examples/realtime_monitoring_demo.py`

## 下一步

- **Task 6.2**: SignalDetector（信号检测器）- 检测交易信号和风险预警
- **Task 6.3**: AlertManager（提醒管理器）- 管理和发送提醒通知
- **Task 6.4**: PositionMonitor（持仓监控器）- 监控持仓止损止盈
