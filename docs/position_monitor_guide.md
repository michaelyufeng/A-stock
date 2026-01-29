# PositionMonitor 使用指南

## 概述

PositionMonitor（持仓监控器）整合了RiskManager和SignalDetector，专门用于实时监控持仓状态和风险。

### 核心功能

1. **持仓监控** - 实时跟踪所有持仓的价格变化和盈亏
2. **风险检测** - 自动检测止损止盈触发
3. **价格更新** - 批量更新持仓的当前价格
4. **风险评估** - 评估组合整体健康状况
5. **报告生成** - 生成详细的持仓监控报告

## 快速开始

### 基本使用

```python
from src.risk.risk_manager import RiskManager
from src.monitoring.signal_detector import SignalDetector
from src.monitoring.position_monitor import PositionMonitor

# 1. 创建依赖组件
risk_mgr = RiskManager(total_capital=1_000_000)
detector = SignalDetector(risk_mgr)

# 2. 创建持仓监控器
monitor = PositionMonitor(risk_mgr, detector)

# 3. 添加持仓
risk_mgr.add_position(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    shares=100,
    entry_price=1500.0,
    entry_date=datetime.now()
)

# 4. 更新实时价格并监控
quotes = {
    '600519': {'current_price': 1600.0}
}

signals = monitor.monitor_positions(quotes)

# 5. 处理检测到的信号
for signal in signals:
    print(f"{signal.signal_type}: {signal.description}")

# 6. 生成持仓报告
report = monitor.generate_position_report()
print(report)
```

## API 参考

### PositionMonitor 类

#### 初始化

```python
def __init__(
    self,
    risk_manager: RiskManager,
    signal_detector: SignalDetector
)
```

**参数**:
- `risk_manager` - RiskManager实例，管理持仓
- `signal_detector` - SignalDetector实例，检测信号

### 持仓监控

#### monitor_positions()

```python
def monitor_positions(
    self,
    quotes: Optional[Dict[str, Dict]] = None
) -> List[Signal]
```

监控所有持仓，检测风险信号。

**参数**:
- `quotes` (可选) - 实时行情数据
  ```python
  {
      '600519': {'current_price': 1600.0},
      '000001': {'current_price': 16.0}
  }
  ```

**返回**: Signal列表

**示例**:
```python
# 不提供行情（会自动获取）
signals = monitor.monitor_positions()

# 提供行情数据
quotes = {
    '600519': {'current_price': 1380.0},  # 触发止损
    '000001': {'current_price': 17.5}     # 触发止盈
}
signals = monitor.monitor_positions(quotes)

for signal in signals:
    print(f"[{signal.priority}] {signal.description}")
```

#### check_position_risks()

```python
def check_position_risks(self, stock_code: str) -> List[Signal]
```

检查单个持仓的风险。

**返回**: 该持仓的风险信号列表

**示例**:
```python
signals = monitor.check_position_risks('600519')

if signals:
    for signal in signals:
        print(f"检测到风险: {signal.description}")
```

### 价格更新

#### update_position_prices()

```python
def update_position_prices(self, quotes: Dict[str, Dict])
```

批量更新持仓的当前价格。

**参数**:
- `quotes` - 行情数据字典

**示例**:
```python
quotes = {
    '600519': {'current_price': 1600.0},
    '000001': {'current_price': 16.0},
    '000002': {'current_price': 9.5}
}

monitor.update_position_prices(quotes)
```

### 止损止盈检查

#### check_stop_loss_all()

```python
def check_stop_loss_all(self) -> List[Signal]
```

检查所有持仓的止损触发。

**返回**: 触发止损的信号列表

**示例**:
```python
# 先更新价格
monitor.update_position_prices(quotes)

# 检查止损
signals = monitor.check_stop_loss_all()

if signals:
    print(f"⚠️  {len(signals)} 只股票触发止损！")
    for signal in signals:
        print(f"  {signal.stock_name}: {signal.description}")
```

#### check_take_profit_all()

```python
def check_take_profit_all(self) -> List[Signal]
```

检查所有持仓的止盈触发。

**返回**: 触发止盈的信号列表

**示例**:
```python
signals = monitor.check_take_profit_all()

if signals:
    print(f"✅ {len(signals)} 只股票触发止盈！")
    for signal in signals:
        print(f"  {signal.stock_name}: 盈利 {signal.metadata.get('profit_pct', 0):.2%}")
```

### 风险评估

#### assess_portfolio_health()

```python
def assess_portfolio_health(self) -> Dict
```

评估组合整体健康状况。

**返回**:
```python
{
    'risk_level': str,              # 'low', 'medium', 'high'
    'total_value': float,           # 总市值
    'total_cost': float,            # 总成本
    'total_profit_loss': float,     # 浮动盈亏
    'total_profit_loss_pct': float, # 盈亏比例
    'position_count': int,          # 持仓数量
    'positions_at_risk': int,       # 风险持仓数
    'warnings': List[str],          # 风险警告
    'portfolio_risk': Dict          # RiskManager的风险评估
}
```

**示例**:
```python
health = monitor.assess_portfolio_health()

print(f"风险级别: {health['risk_level'].upper()}")
print(f"持仓数量: {health['position_count']}")
print(f"总盈亏: ¥{health['total_profit_loss']:,.2f} ({health['total_profit_loss_pct']:.2%})")

if health['positions_at_risk'] > 0:
    print(f"\n⚠️  {health['positions_at_risk']} 只股票接近止损位：")
    for warning in health['warnings']:
        print(f"  - {warning}")
```

### 报告生成

#### generate_position_report()

```python
def generate_position_report(self) -> str
```

生成详细的持仓监控报告。

**返回**: 格式化的报告文本

**示例**:
```python
report = monitor.generate_position_report()
print(report)
```

**报告示例**:
```
============================================================
  持仓监控报告
============================================================

【组合概览】
持仓数量: 2 只
总市值: ¥176,000.00
总成本: ¥165,000.00
浮动盈亏: ¥11,000.00 (+6.67%)
风险级别: LOW

【持仓明细】

股票: 贵州茅台 (600519)
  成本价: ¥1500.00 | 现价: ¥1600.00
  持仓: 100 股 | 市值: ¥160,000.00
  盈亏: ¥10,000.00 (+6.67%)
  止损价: ¥1380.00 (距离: +13.75%)
  止盈价: ¥1725.00 (距离: +7.81%)
  持仓天数: 10 天

股票: 平安银行 (000001)
  成本价: ¥15.00 | 现价: ¥16.00
  持仓: 1000 股 | 市值: ¥16,000.00
  盈亏: ¥1,000.00 (+6.67%)
  止损价: ¥13.80 (距离: +13.75%)
  止盈价: ¥17.25 (距离: +7.81%)
  持仓天数: 5 天

报告时间: 2026-01-29 15:30:00
============================================================
```

## 使用场景

### 场景1: 实时持仓监控

```python
import time
from src.monitoring import RealTimeWatcher

# 创建实时行情监控
watcher = RealTimeWatcher([
    {'code': '600519', 'name': '贵州茅台'},
    {'code': '000001', 'name': '平安银行'}
])

# 持仓监控循环
while True:
    # 1. 更新实时行情
    watcher.update_quotes()
    quotes = watcher.get_all_quotes()

    # 2. 监控持仓风险
    signals = monitor.monitor_positions(quotes)

    # 3. 处理信号
    if signals:
        for signal in signals:
            print(f"⚠️  [{signal.priority}] {signal.description}")

    # 4. 等待下一次更新
    time.sleep(60)
```

### 场景2: 定时风险检查

```python
import schedule

def check_positions():
    """定时检查持仓风险"""
    # 检查止损
    stop_loss_signals = monitor.check_stop_loss_all()
    if stop_loss_signals:
        print(f"❌ {len(stop_loss_signals)} 只股票触发止损！")
        for signal in stop_loss_signals:
            print(f"  {signal.stock_name}: {signal.trigger_price:.2f}元")

    # 检查止盈
    take_profit_signals = monitor.check_take_profit_all()
    if take_profit_signals:
        print(f"✅ {len(take_profit_signals)} 只股票触发止盈！")
        for signal in take_profit_signals:
            print(f"  {signal.stock_name}: {signal.trigger_price:.2f}元")

# 每5分钟检查一次
schedule.every(5).minutes.do(check_positions)

while True:
    schedule.run_pending()
    time.sleep(1)
```

### 场景3: 每日持仓报告

```python
def generate_daily_report():
    """生成每日持仓报告"""
    # 更新所有持仓价格
    positions = monitor.risk_manager.get_all_positions()
    quotes = {}

    for stock_code in positions.keys():
        quote = monitor.signal_detector.provider.get_realtime_quote(stock_code)
        if quote:
            quotes[stock_code] = quote

    monitor.update_position_prices(quotes)

    # 生成报告
    report = monitor.generate_position_report()

    # 保存到文件
    filename = f"position_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"报告已保存: {filename}")

# 每天收盘后生成
schedule.every().day.at("15:05").do(generate_daily_report)
```

### 场景4: 风险预警系统

```python
from src.monitoring import AlertManager, AlertRule, AlertChannel

# 创建提醒管理器
alert_mgr = AlertManager()

# 配置风险预警规则
risk_rule = AlertRule(
    rule_id='position_risk',
    name='持仓风险预警',
    stock_codes=[],
    signal_types=['SELL'],
    categories=['risk'],
    min_priority='high',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    enabled=True,
    cooldown_minutes=0  # 立即提醒
)

alert_mgr.add_rule(risk_rule)

# 监控并提醒
def monitor_and_alert():
    signals = monitor.monitor_positions()

    if signals:
        # 发送提醒
        alert_mgr.process_signals(signals)

        # 生成报告
        health = monitor.assess_portfolio_health()

        if health['risk_level'] == 'high':
            print("🚨 组合风险级别: 高风险！")
            report = monitor.generate_position_report()
            print(report)

schedule.every(5).minutes.do(monitor_and_alert)
```

### 场景5: 组合健康评估

```python
def assess_and_rebalance():
    """评估组合健康度并提示调整"""
    health = monitor.assess_portfolio_health()

    print(f"\n组合健康评估:")
    print(f"  风险级别: {health['risk_level'].upper()}")
    print(f"  总盈亏: {health['total_profit_loss_pct']:.2%}")
    print(f"  风险持仓: {health['positions_at_risk']} 只")

    # 根据风险级别提示
    if health['risk_level'] == 'high':
        print("\n⚠️  建议操作:")
        print("  1. 检查止损触发情况")
        print("  2. 考虑减少高风险持仓")
        print("  3. 评估行业集中度")

    elif health['risk_level'] == 'medium':
        print("\n💡 建议操作:")
        print("  1. 密切关注市场动态")
        print("  2. 准备应对止损触发")

    else:
        print("\n✅ 组合状态良好")

    # 显示警告
    if health['warnings']:
        print("\n⚠️  风险警告:")
        for warning in health['warnings']:
            print(f"  - {warning}")

# 每天开盘前评估
schedule.every().day.at("09:15").do(assess_and_rebalance)
```

## 监控指标说明

### 1. 浮动盈亏

- **计算公式**: (当前价 - 成本价) × 持仓数量
- **盈亏比例**: 浮动盈亏 / 总成本
- **实时更新**: 随行情变化动态计算

### 2. 止损止盈距离

- **止损距离**: (当前价 - 止损价) / 当前价
- **止盈距离**: (止盈价 - 当前价) / 当前价
- **预警阈值**: 距离止损价2%内触发预警

### 3. 持仓天数

- **计算**: 当前日期 - 建仓日期
- **用途**: 评估持仓周期，辅助决策

### 4. 仓位占比变化

- **个股仓位**: 个股市值 / 总市值
- **行业集中度**: 从RiskManager获取
- **动态监控**: 价格变化导致的仓位漂移

### 5. 风险级别

- **低风险 (low)**:
  - 无止损触发
  - 总体盈利或小幅亏损(<2%)
  - RiskManager评估为低风险

- **中风险 (medium)**:
  - 部分持仓接近止损
  - 总体亏损2-5%
  - 或RiskManager评估为中风险

- **高风险 (high)**:
  - 多只股票触发止损
  - 总体亏损>5%
  - 或RiskManager评估为高风险

## 集成示例

### 与AlertManager集成

```python
from src.monitoring import PositionMonitor, AlertManager, AlertRule, AlertChannel

# 创建组件
monitor = PositionMonitor(risk_mgr, detector)
alert_mgr = AlertManager()

# 配置提醒规则
alert_mgr.add_rule(AlertRule(
    'position_alert', '持仓预警', [],
    ['SELL', 'WARNING'], ['risk'],
    'high', [AlertChannel.CONSOLE], True, 30
))

# 监控循环
while True:
    # 监控持仓
    signals = monitor.monitor_positions()

    # 发送提醒
    if signals:
        alert_mgr.process_signals(signals)

    time.sleep(300)  # 5分钟
```

### 与RealTimeWatcher集成

```python
from src.monitoring import RealTimeWatcher, PositionMonitor

watcher = RealTimeWatcher([...])
monitor = PositionMonitor(risk_mgr, detector)

# 同步监控
while True:
    # 1. 更新行情
    watcher.update_quotes()

    # 2. 获取持仓股票的行情
    positions = monitor.risk_manager.get_all_positions()
    quotes = {}

    for stock_code in positions.keys():
        quote = watcher.get_latest_quote(stock_code)
        if quote:
            quotes[stock_code] = quote

    # 3. 监控持仓
    signals = monitor.monitor_positions(quotes)

    # 4. 处理信号
    for signal in signals:
        print(signal.description)

    time.sleep(60)
```

## 最佳实践

### 1. 定期更新价格

```python
# ✅ 好的做法 - 定期批量更新
quotes = get_all_quotes_batch()  # 批量获取
monitor.update_position_prices(quotes)

# ❌ 不好的做法 - 每次单独获取
for stock_code in positions:
    quote = get_quote(stock_code)  # 多次API调用
    monitor.update_position_prices({stock_code: quote})
```

### 2. 合理设置检查频率

```python
# 交易时间内 - 高频检查（5分钟）
if is_trading_hours():
    interval = 300

# 非交易时间 - 低频检查（30分钟）
else:
    interval = 1800

schedule.every(interval).seconds.do(check_positions)
```

### 3. 分级处理信号

```python
signals = monitor.monitor_positions()

for signal in signals:
    if signal.priority == 'critical':
        # 立即处理
        handle_critical(signal)
    elif signal.priority == 'high':
        # 重点关注
        log_high_priority(signal)
    else:
        # 记录即可
        log_signal(signal)
```

### 4. 定期生成报告

```python
# 每日收盘后
schedule.every().day.at("15:05").do(generate_daily_report)

# 每周总结
schedule.every().monday.at("09:00").do(generate_weekly_summary)

# 每月复盘
schedule.every().day.at("00:00").do(monthly_review)
```

## 注意事项

1. **价格更新时机** - 确保在检查止损止盈前更新价格
2. **网络异常处理** - 行情获取失败时使用上次价格或跳过检查
3. **持仓同步** - RiskManager中的持仓变化会立即反映到监控中
4. **性能考虑** - 大量持仓时考虑分批处理或异步更新
5. **时区问题** - 确保持仓天数计算使用正确的时区

## 故障排查

### 问题1: 检测不到止损触发

**检查**:
1. 价格是否已更新
2. 止损价是否正确设置
3. SignalDetector的止损检查逻辑

```python
position = monitor.risk_manager.get_position('600519')
print(f"当前价: {position.get('current_price')}")
print(f"止损价: {position.get('stop_loss_price')}")

# 手动检查
if position['current_price'] <= position['stop_loss_price']:
    print("应该触发止损")
```

### 问题2: 报告中盈亏计算错误

**原因**: current_price未更新

**解决**:
```python
# 确保先更新价格
quotes = {...}
monitor.update_position_prices(quotes)

# 再生成报告
report = monitor.generate_position_report()
```

### 问题3: 风险级别评估不准确

**原因**: RiskManager的风险评估参数需要调整

**解决**:
```python
# 查看详细的风险评估
health = monitor.assess_portfolio_health()
print(health['portfolio_risk'])  # RiskManager的评估结果

# 根据实际情况调整config/risk_rules.yaml中的参数
```

## 相关文档

- [RiskManager 使用指南](risk_manager_guide.md)
- [SignalDetector 使用指南](signal_detector_guide.md)
- [AlertManager 使用指南](alert_manager_guide.md)
- [RealTimeWatcher 使用指南](realtime_watcher_guide.md)
