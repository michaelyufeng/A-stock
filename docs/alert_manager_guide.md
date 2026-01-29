# AlertManager 使用指南

## 概述

AlertManager（提醒管理器）负责管理提醒规则和发送多渠道通知。

### 核心功能

1. **提醒规则管理** - 添加、删除、更新提醒规则
2. **信号匹配检测** - 检查信号是否触发规则
3. **多渠道通知** - 支持控制台、日志、邮件、微信
4. **冷却期管理** - 防止同一股票重复提醒
5. **提醒历史** - 记录和查询提醒历史

## 快速开始

### 基本使用

```python
from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import SignalDetector, Signal
from datetime import datetime

# 1. 创建提醒管理器
alert_mgr = AlertManager()

# 2. 创建提醒规则
rule = AlertRule(
    rule_id='ma_cross_alert',
    name='MA金叉提醒',
    stock_codes=['600519', '000001'],  # 关注的股票
    signal_types=['BUY'],              # 只关注买入信号
    categories=['technical'],          # 只关注技术信号
    min_priority='medium',             # 最低优先级
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],  # 通知渠道
    enabled=True,
    cooldown_minutes=60                # 60分钟冷却期
)

# 3. 添加规则
alert_mgr.add_rule(rule)

# 4. 检测信号并发送提醒
signal = Signal(
    stock_code='600519',
    stock_name='贵州茅台',
    signal_type='BUY',
    category='technical',
    description='MA5金叉MA20',
    priority='medium',
    trigger_price=1680.50,
    timestamp=datetime.now(),
    metadata={'ma_short': 5, 'ma_long': 20}
)

# 处理信号
result = alert_mgr.process_signal(signal)
print(f"Triggered: {result['triggered']}")
print(f"Rule IDs: {result['rule_ids']}")
```

## 核心类和数据结构

### AlertChannel 枚举

```python
class AlertChannel(Enum):
    CONSOLE = "console"  # 控制台输出
    LOG = "log"          # 日志记录
    EMAIL = "email"      # 邮件通知（待实现）
    WECHAT = "wechat"    # 微信通知（待实现）
```

### AlertRule 数据类

```python
@dataclass
class AlertRule:
    rule_id: str                      # 规则唯一ID
    name: str                         # 规则名称
    stock_codes: List[str]            # 关注的股票代码列表
    signal_types: List[str]           # 关注的信号类型
    categories: List[str]             # 关注的信号类别
    min_priority: str                 # 最低优先级
    channels: List[AlertChannel]      # 通知渠道列表
    enabled: bool = True              # 是否启用
    cooldown_minutes: int = 60        # 冷却期（分钟）
```

## API 参考

### AlertManager 类

#### 初始化

```python
def __init__(self, config_path: str = 'config/risk_rules.yaml')
```

从配置文件加载默认参数。

#### 规则管理

##### add_rule()

```python
def add_rule(self, rule: AlertRule) -> Dict[str, Any]
```

添加提醒规则。

**返回**:
```python
{
    'success': bool,
    'message': str
}
```

**示例**:
```python
rule = AlertRule(
    rule_id='high_priority_alert',
    name='高优先级提醒',
    stock_codes=[],  # 空列表表示所有股票
    signal_types=['BUY', 'SELL', 'WARNING'],
    categories=['technical', 'risk'],
    min_priority='high',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    enabled=True,
    cooldown_minutes=30
)

result = alert_mgr.add_rule(rule)
```

##### remove_rule()

```python
def remove_rule(self, rule_id: str) -> Dict[str, Any]
```

移除提醒规则。

##### update_rule()

```python
def update_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]
```

更新提醒规则的字段。

**示例**:
```python
# 禁用某个规则
alert_mgr.update_rule('ma_cross_alert', enabled=False)

# 修改优先级和冷却期
alert_mgr.update_rule(
    'ma_cross_alert',
    min_priority='high',
    cooldown_minutes=120
)
```

##### get_all_rules()

```python
def get_all_rules() -> List[AlertRule]
```

获取所有提醒规则。

#### 信号处理

##### process_signal()

```python
def process_signal(self, signal: Signal) -> Dict[str, Any]
```

处理单个信号，检查所有规则并发送通知。

**返回**:
```python
{
    'triggered': bool,        # 是否触发任何规则
    'rule_ids': List[str],    # 触发的规则ID列表
    'signal': Signal          # 原始信号
}
```

##### process_signals()

```python
def process_signals(self, signals: List[Signal]) -> List[Dict[str, Any]]
```

批量处理多个信号。

**示例**:
```python
signals = detector.detect_all_signals('600519')
results = alert_mgr.process_signals(signals)

for result in results:
    if result['triggered']:
        print(f"Signal triggered {len(result['rule_ids'])} rules")
```

#### 通知发送

##### send_notification()

```python
def send_notification(self, signal: Signal, channel: AlertChannel) -> Dict[str, Any]
```

通过指定渠道发送通知。

**支持的渠道**:
- `AlertChannel.CONSOLE` - 彩色控制台输出（已实现）
- `AlertChannel.LOG` - 日志记录（已实现）
- `AlertChannel.EMAIL` - 邮件通知（待实现）
- `AlertChannel.WECHAT` - 微信通知（待实现）

#### 提醒历史

##### get_alert_history()

```python
def get_alert_history(
    self,
    stock_code: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[Dict[str, Any]]
```

查询提醒历史记录。

**示例**:
```python
from datetime import datetime, timedelta

# 查询所有历史
all_history = alert_mgr.get_alert_history()

# 查询特定股票
stock_history = alert_mgr.get_alert_history(stock_code='600519')

# 查询时间范围
today = datetime.now()
yesterday = today - timedelta(days=1)
recent = alert_mgr.get_alert_history(start_time=yesterday, limit=50)
```

##### clear_old_history()

```python
def clear_old_history(self, days: int = 30)
```

清理超过指定天数的历史记录。

## 使用场景

### 场景1: 技术指标提醒

```python
# 创建MA金叉提醒规则
ma_cross_rule = AlertRule(
    rule_id='ma_golden_cross',
    name='MA金叉买入提醒',
    stock_codes=['600519', '000001', '000002'],
    signal_types=['BUY'],
    categories=['technical'],
    min_priority='medium',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    enabled=True,
    cooldown_minutes=120  # 2小时内同一股票不重复提醒
)

alert_mgr.add_rule(ma_cross_rule)
```

### 场景2: 风险预警

```python
# 创建止损触发提醒
stop_loss_rule = AlertRule(
    rule_id='stop_loss_alert',
    name='止损触发紧急提醒',
    stock_codes=[],  # 所有股票
    signal_types=['SELL'],
    categories=['risk'],
    min_priority='critical',  # 只关注critical级别
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    enabled=True,
    cooldown_minutes=0  # 无冷却期，立即提醒
)

alert_mgr.add_rule(stop_loss_rule)
```

### 场景3: 涨跌停监控

```python
# 创建涨跌停提醒
limit_rule = AlertRule(
    rule_id='limit_updown_alert',
    name='涨跌停提醒',
    stock_codes=[],
    signal_types=['WARNING'],
    categories=['price'],
    min_priority='high',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    enabled=True,
    cooldown_minutes=1440  # 一天只提醒一次
)

alert_mgr.add_rule(limit_rule)
```

### 场景4: 综合监控系统

```python
from src.monitoring import RealTimeWatcher, SignalDetector, AlertManager
from src.monitoring.alert_manager import AlertRule, AlertChannel
import time

# 创建监控组件
watcher = RealTimeWatcher([
    {'code': '600519', 'name': '贵州茅台'},
    {'code': '000001', 'name': '平安银行'}
], update_interval=60)

detector = SignalDetector()
alert_mgr = AlertManager()

# 配置提醒规则
rules = [
    AlertRule('tech_signal', '技术信号', [], ['BUY', 'SELL'],
              ['technical'], 'medium', [AlertChannel.CONSOLE], True, 60),
    AlertRule('risk_signal', '风险信号', [], ['SELL', 'WARNING'],
              ['risk', 'price'], 'high', [AlertChannel.CONSOLE, AlertChannel.LOG], True, 0)
]

for rule in rules:
    alert_mgr.add_rule(rule)

# 监控循环
while True:
    # 1. 更新实时行情
    watcher.update_quotes()

    # 2. 检测所有监控股票的信号
    all_signals = []
    for stock_code in watcher.get_watchlist().keys():
        signals = detector.detect_all_signals(stock_code)
        all_signals.extend(signals)

    # 3. 处理信号并发送提醒
    if all_signals:
        results = alert_mgr.process_signals(all_signals)
        triggered_count = sum(1 for r in results if r['triggered'])
        print(f"Processed {len(all_signals)} signals, {triggered_count} triggered alerts")

    # 4. 等待下一次更新
    time.sleep(60)
```

## 配置参数

在 `config/risk_rules.yaml` 中配置默认参数：

```yaml
alerts:
  default_cooldown_minutes: 60    # 默认冷却期（分钟）
  max_history_days: 30            # 历史记录保留天数

  # 通知渠道配置
  channels:
    console:
      enabled: true
      color_output: true

    log:
      enabled: true
      level: INFO

    email:
      enabled: false
      smtp_server: smtp.example.com
      from_addr: alerts@example.com

    wechat:
      enabled: false
      webhook_url: https://qyapi.weixin.qq.com/...
```

## 优先级说明

AlertManager 支持4个优先级级别，从低到高：

| 优先级 | 说明 | 使用场景 |
|--------|------|----------|
| `low` | 低优先级 | 一般信息、非紧急提醒 |
| `medium` | 中等优先级 | 技术指标信号、常规交易提醒 |
| `high` | 高优先级 | 重要价格突破、涨跌停 |
| `critical` | 紧急 | 止损触发、严重风险预警 |

规则的 `min_priority` 决定最低匹配优先级。例如：
- `min_priority='medium'` 会匹配 medium、high、critical，但不匹配 low
- `min_priority='critical'` 只匹配 critical

## 冷却期机制

冷却期防止同一股票的同一规则在短时间内重复提醒：

```python
# 冷却期60分钟的规则
rule = AlertRule(
    ...,
    cooldown_minutes=60
)

# 第一次触发 - 发送通知
alert_mgr.process_signal(signal1)  # ✅ 发送

# 30分钟后再次触发 - 被冷却期阻止
alert_mgr.process_signal(signal2)  # ❌ 不发送

# 61分钟后再次触发 - 冷却期已过
alert_mgr.process_signal(signal3)  # ✅ 发送
```

**特殊值**:
- `cooldown_minutes=0` - 无冷却期，每次都提醒（用于critical级别）
- `cooldown_minutes=1440` - 一天提醒一次

## 最佳实践

### 1. 规则命名规范

```python
# ✅ 好的命名
AlertRule('ma_golden_cross', 'MA金叉买入提醒', ...)
AlertRule('stop_loss_critical', '止损紧急提醒', ...)

# ❌ 不好的命名
AlertRule('rule1', 'test', ...)
```

### 2. 合理设置冷却期

```python
# 技术指标 - 中等冷却期（避免频繁提醒）
technical_rule = AlertRule(..., cooldown_minutes=60)

# 风险预警 - 无冷却期（立即通知）
risk_rule = AlertRule(..., cooldown_minutes=0)

# 日常信息 - 长冷却期（一天一次）
info_rule = AlertRule(..., cooldown_minutes=1440)
```

### 3. 分级通知策略

```python
# Critical级别 - 所有渠道
critical_rule = AlertRule(
    ...,
    min_priority='critical',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.WECHAT],
    cooldown_minutes=0
)

# Medium级别 - 控制台和日志
medium_rule = AlertRule(
    ...,
    min_priority='medium',
    channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
    cooldown_minutes=60
)

# Low级别 - 仅日志
low_rule = AlertRule(
    ...,
    min_priority='low',
    channels=[AlertChannel.LOG],
    cooldown_minutes=120
)
```

### 4. 定期清理历史

```python
# 每天凌晨清理30天前的记录
import schedule

def cleanup_history():
    alert_mgr.clear_old_history(days=30)

schedule.every().day.at("00:00").do(cleanup_history)
```

## 注意事项

1. **规则ID唯一性** - 每个规则必须有唯一的rule_id
2. **空列表匹配所有** - stock_codes=[] 表示匹配所有股票
3. **优先级权重** - 高优先级信号总是能触发低优先级规则
4. **冷却期粒度** - 冷却期是按 (rule_id, stock_code) 对计算的
5. **未实现的渠道** - EMAIL和WECHAT渠道调用时会记录警告日志但不会报错

## 故障排查

### 问题1: 信号不触发提醒

**检查**:
1. 规则是否启用 (`enabled=True`)
2. 股票代码是否在规则的 `stock_codes` 列表中
3. 信号优先级是否满足 `min_priority` 要求
4. 是否在冷却期内

```python
# 调试方法
rule = alert_mgr.rules['your_rule_id']
matched = alert_mgr.check_signal_matches(signal, rule)
print(f"Signal matches rule: {matched}")

in_cooldown = alert_mgr._is_in_cooldown(rule.rule_id, signal.stock_code, rule.cooldown_minutes)
print(f"In cooldown: {in_cooldown}")
```

### 问题2: 重复提醒

**原因**: 冷却期设置太短或为0

**解决**:
```python
# 增加冷却期
alert_mgr.update_rule('rule_id', cooldown_minutes=60)
```

### 问题3: 历史记录过多

**解决**:
```python
# 清理旧记录
alert_mgr.clear_old_history(days=7)

# 或定期自动清理
import schedule
schedule.every().day.do(lambda: alert_mgr.clear_old_history(days=30))
```

## 扩展开发

### 添加新的通知渠道

```python
# 1. 在AlertChannel枚举中添加
class AlertChannel(Enum):
    ...
    CUSTOM = "custom"

# 2. 实现通知方法
def _send_custom_notification(self, signal: Signal):
    # 实现自定义通知逻辑
    pass

# 3. 在send_notification中添加分支
def send_notification(self, signal: Signal, channel: AlertChannel):
    ...
    elif channel == AlertChannel.CUSTOM:
        self._send_custom_notification(signal)
```

### 自定义匹配逻辑

```python
class CustomAlertManager(AlertManager):
    def check_signal_matches(self, signal: Signal, rule: AlertRule) -> bool:
        # 先调用父类的标准匹配
        if not super().check_signal_matches(signal, rule):
            return False

        # 添加自定义匹配逻辑
        # 例如：只在交易时间内提醒
        now = datetime.now()
        if not (9 <= now.hour < 15):
            return False

        return True
```

## 相关文档

- [RealTimeWatcher 使用指南](realtime_watcher_guide.md)
- [SignalDetector 使用指南](signal_detector_guide.md)
- [风险管理指南](risk_manager_guide.md)
