# Phase 6 实施计划 - 监控提醒系统

## 当前进度总结

### ✅ 已完成阶段
- **Phase 1-3**: 基础框架、数据层、分析层 ✅
- **Phase 4**: 策略回测系统 ✅
  - BaseStrategy, MomentumStrategy, BacktestEngine, AShareBroker, BacktestMetrics
- **Phase 5**: 选股筛选和风险管理 ✅
  - StockScreener, RiskManager

### 🚧 当前阶段: Phase 6 - 监控提醒系统

---

## 一、阶段目标

### 总体目标
实现实时监控和智能提醒系统，将分析、筛选、风控能力整合到日常监控中。

### 核心价值
1. **实时监控**: 跟踪关注股票的实时行情变化
2. **信号检测**: 自动检测交易信号（买入/卖出/预警）
3. **智能提醒**: 及时通知重要事件和风险
4. **持仓跟踪**: 监控持仓止损止盈触发

### 关键特性
- 🔄 实时行情更新（可配置刷新频率）
- 🎯 多维度信号检测（技术面、基本面、资金面）
- ⚠️ 风险预警（止损触发、仓位预警、异常波动）
- 📊 持仓监控（盈亏实时计算、目标价位提醒）
- 🔔 多种通知方式（控制台、日志、可扩展邮件/微信）

---

##二、任务分解

### Task 6.1: RealTimeWatcher (实时行情监控器)

**功能描述**:
监控指定股票列表的实时行情，支持批量更新和增量刷新。

**核心方法**:
```python
class RealTimeWatcher:
    def __init__(self, stock_list: List[str], update_interval: int = 60)
    def add_stock(self, stock_code: str, stock_name: str)
    def remove_stock(self, stock_code: str)
    def start_watching(self)
    def stop_watching()
    def get_latest_quote(self, stock_code: str) -> Dict
    def get_all_quotes(self) -> Dict[str, Dict]
    def update_quotes(self)  # 手动触发更新
```

**关键特性**:
- 支持沪深A股实时行情获取
- 可配置刷新间隔（默认60秒）
- 批量获取优化（减少API调用）
- 异常处理（网络失败、数据缺失）
- 行情缓存（避免重复请求）

**数据结构**:
```python
{
    '600519': {
        'code': '600519',
        'name': '贵州茅台',
        'current_price': 1650.5,
        'open': 1645.0,
        'high': 1660.0,
        'low': 1640.0,
        'volume': 1234567,
        'amount': 2.03e9,
        'bid': 1650.0,
        'ask': 1651.0,
        'change_pct': 0.0234,  # 涨跌幅
        'update_time': datetime(2026, 1, 29, 14, 30, 0)
    }
}
```

**测试用例** (约15个):
1. 初始化监控器
2. 添加/删除股票
3. 获取单个股票行情
4. 批量获取行情
5. 更新行情数据
6. 处理网络异常
7. 处理无效股票代码
8. 验证更新时间戳
9. 测试缓存机制
10. 测试批量优化

**文件**:
- `src/monitoring/realtime_watcher.py` (~400行)
- `tests/monitoring/test_realtime_watcher.py` (~350行)

---

### Task 6.2: SignalDetector (信号检测器)

**功能描述**:
基于实时行情和历史数据，检测各类交易信号和风险预警。

**核心方法**:
```python
class SignalDetector:
    def __init__(self, risk_manager: RiskManager)

    # 技术信号检测
    def detect_technical_signals(self, stock_code: str) -> List[Signal]
    def check_ma_crossover(self, stock_code: str) -> Optional[Signal]
    def check_macd_signal(self, stock_code: str) -> Optional[Signal]
    def check_rsi_extremes(self, stock_code: str) -> Optional[Signal]
    def check_volume_breakout(self, stock_code: str) -> Optional[Signal]

    # 价格信号检测
    def check_price_breakout(self, stock_code: str) -> Optional[Signal]
    def check_support_resistance(self, stock_code: str) -> Optional[Signal]

    # 风险信号检测
    def check_stop_loss_trigger(self, stock_code: str, position: Dict) -> Optional[Signal]
    def check_take_profit_trigger(self, stock_code: str, position: Dict) -> Optional[Signal]
    def check_abnormal_volatility(self, stock_code: str) -> Optional[Signal]
    def check_limit_up_down(self, stock_code: str) -> Optional[Signal]

    # 综合检测
    def detect_all_signals(self, stock_code: str) -> List[Signal]
    def scan_watchlist(self, stock_list: List[str]) -> Dict[str, List[Signal]]
```

**Signal数据结构**:
```python
@dataclass
class Signal:
    stock_code: str
    stock_name: str
    signal_type: str  # 'BUY', 'SELL', 'WARNING', 'INFO'
    category: str     # 'technical', 'risk', 'price', 'volume'
    description: str
    priority: str     # 'low', 'medium', 'high', 'critical'
    trigger_price: float
    timestamp: datetime
    metadata: Dict    # 额外信息
```

**信号类型**:
1. **买入信号**:
   - MA金叉 (5日均线上穿20日均线)
   - MACD金叉
   - RSI超卖反弹 (RSI < 30后回升)
   - 放量突破

2. **卖出信号**:
   - MA死叉
   - MACD死叉
   - RSI超买 (RSI > 70)

3. **风险预警**:
   - 止损触发
   - 异常波动 (单日波动>5%)
   - 连续涨跌停
   - 成交量异常

4. **信息提示**:
   - 接近止盈位
   - 突破支撑/压力位
   - 成交量放大

**测试用例** (约20个):
1. MA金叉/死叉检测
2. MACD信号检测
3. RSI超买超卖检测
4. 放量突破检测
5. 止损触发检测
6. 止盈触发检测
7. 涨跌停检测
8. 异常波动检测
9. 支撑位检测
10. 压力位检测
11. 综合信号检测
12. 批量扫描
13. 优先级判断
14. 信号去重

**文件**:
- `src/monitoring/signal_detector.py` (~500行)
- `tests/monitoring/test_signal_detector.py` (~450行)

---

### Task 6.3: AlertManager (提醒管理器)

**功能描述**:
管理和发送各类提醒通知，支持多种输出方式和优先级过滤。

**核心方法**:
```python
class AlertManager:
    def __init__(self, config: Dict)

    # 提醒发送
    def send_alert(self, alert: Alert)
    def send_batch_alerts(self, alerts: List[Alert])

    # 提醒管理
    def add_alert(self, signal: Signal) -> Alert
    def dismiss_alert(self, alert_id: str)
    def get_active_alerts(self) -> List[Alert]
    def get_alert_history(self, hours: int = 24) -> List[Alert]

    # 通知渠道
    def notify_console(self, alert: Alert)
    def notify_log(self, alert: Alert)
    def notify_email(self, alert: Alert)  # 可选
    def notify_wechat(self, alert: Alert)  # 可选

    # 过滤和规则
    def should_notify(self, alert: Alert) -> bool
    def filter_by_priority(self, alerts: List[Alert], min_priority: str) -> List[Alert]
    def deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]
```

**Alert数据结构**:
```python
@dataclass
class Alert:
    alert_id: str
    signal: Signal
    status: str       # 'active', 'dismissed', 'expired'
    created_at: datetime
    notified_at: Optional[datetime]
    notification_channels: List[str]  # ['console', 'log', 'email']
```

**通知格式**:
```
[2026-01-29 14:30:15] 🔴 CRITICAL - 止损触发
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
股票: 600519 贵州茅台
类型: 风险预警
触发价: 1380.00元
止损价: 1380.00元 (8% 固定止损)
建议: 立即平仓止损
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**提醒规则**:
1. **优先级过滤**: 只通知high/critical级别
2. **去重**: 同一信号15分钟内不重复提醒
3. **时间窗口**: 交易时间内实时提醒，盘后汇总
4. **分组**: 按股票/类型分组显示

**测试用例** (约15个):
1. 创建提醒
2. 发送单个提醒
3. 批量发送提醒
4. 控制台通知格式
5. 日志记录
6. 优先级过滤
7. 去重逻辑
8. 获取活跃提醒
9. 获取历史提醒
10. 提醒状态管理
11. 多渠道通知
12. 时间窗口过滤

**文件**:
- `src/monitoring/alert_manager.py` (~400行)
- `tests/monitoring/test_alert_manager.py` (~350行)

---

### Task 6.4: PositionMonitor (持仓监控器)

**功能描述**:
整合RiskManager和SignalDetector，专门监控持仓状态和风险。

**核心方法**:
```python
class PositionMonitor:
    def __init__(self, risk_manager: RiskManager, signal_detector: SignalDetector)

    # 持仓监控
    def monitor_positions(self) -> List[Signal]
    def check_position_risks(self, stock_code: str) -> List[Signal]
    def update_position_prices(self, quotes: Dict[str, Dict])

    # 止损止盈检查
    def check_stop_loss_all(self) -> List[Signal]
    def check_take_profit_all(self) -> List[Signal]

    # 风险评估
    def assess_portfolio_health(self) -> Dict
    def generate_position_report(self) -> str
```

**监控指标**:
1. 浮动盈亏实时更新
2. 止损止盈距离
3. 持仓天数
4. 个股仓位占比变化
5. 行业集中度变化

**测试用例** (约12个):
1. 持仓监控
2. 批量价格更新
3. 止损检查
4. 止盈检查
5. 风险评估
6. 报告生成

**文件**:
- `src/monitoring/position_monitor.py` (~300行)
- `tests/monitoring/test_position_monitor.py` (~250行)

---

### Task 6.5: MonitoringService (监控服务整合)

**功能描述**:
整合所有监控组件，提供统一的监控服务接口。

**核心方法**:
```python
class MonitoringService:
    def __init__(self, config_path: str)

    # 服务控制
    def start(self)
    def stop()
    def reload_config()

    # 监控管理
    def add_to_watchlist(self, stock_code: str, stock_name: str)
    def remove_from_watchlist(self, stock_code: str)
    def get_watchlist(self) -> List[str]

    # 主循环
    def run_monitoring_cycle(self)
    def scan_and_alert(self)

    # 报告
    def generate_daily_summary(self) -> str
    def get_active_signals(self) -> List[Signal]
```

**监控流程**:
```
1. 更新实时行情 (RealTimeWatcher)
   ↓
2. 检测交易信号 (SignalDetector)
   ↓
3. 更新持仓价格 (PositionMonitor)
   ↓
4. 检查止损止盈 (PositionMonitor)
   ↓
5. 生成提醒 (AlertManager)
   ↓
6. 发送通知 (AlertManager)
   ↓
7. 等待下一周期
```

**配置文件**: `config/monitoring.yaml`
```yaml
monitoring:
  # 更新频率
  update_interval: 60  # 秒

  # 监控列表
  watchlist:
    - code: "600519"
      name: "贵州茅台"
    - code: "000858"
      name: "五粮液"

  # 信号检测
  signals:
    enabled_detectors:
      - ma_crossover
      - macd
      - rsi
      - volume_breakout
      - stop_loss
      - take_profit

    # 参数
    ma_short: 5
    ma_long: 20
    rsi_oversold: 30
    rsi_overbought: 70
    volume_multiplier: 2.0

  # 提醒设置
  alerts:
    min_priority: "medium"  # low/medium/high/critical
    channels:
      - console
      - log

    # 去重
    dedup_window: 900  # 秒 (15分钟)

    # 时间窗口
    trading_hours_only: true

  # 持仓监控
  position_monitoring:
    enabled: true
    check_interval: 300  # 5分钟
```

**文件**:
- `src/monitoring/service.py` (~400行)
- `tests/monitoring/test_service.py` (~300行)

---

## 三、实施顺序

### 阶段1: 基础监控 (Task 6.1)
1. 实现RealTimeWatcher
2. 测试行情获取功能
3. 验证批量更新优化

**时间**: 2-3小时

### 阶段2: 信号检测 (Task 6.2)
1. 实现Signal数据类
2. 实现技术指标信号检测
3. 实现风险信号检测
4. 测试各类信号准确性

**时间**: 3-4小时

### 阶段3: 提醒管理 (Task 6.3)
1. 实现Alert数据类
2. 实现AlertManager核心功能
3. 实现控制台/日志通知
4. 测试去重和过滤逻辑

**时间**: 2-3小时

### 阶段4: 持仓监控 (Task 6.4)
1. 实现PositionMonitor
2. 集成RiskManager
3. 测试持仓风险检测

**时间**: 2小时

### 阶段5: 服务整合 (Task 6.5)
1. 实现MonitoringService
2. 创建配置文件
3. 测试完整监控流程
4. 创建命令行脚本

**时间**: 2-3小时

**总计**: 11-15小时

---

## 四、测试策略

### 单元测试
- RealTimeWatcher: 15个测试
- SignalDetector: 20个测试
- AlertManager: 15个测试
- PositionMonitor: 12个测试
- MonitoringService: 10个测试

**总计**: ~72个测试用例

### 集成测试
1. 完整监控流程测试
2. 多股票并发监控
3. 信号检测准确性验证
4. 提醒及时性测试

### 性能测试
- 100只股票监控性能
- 信号检测延迟
- 内存占用

---

## 五、交付标准

### 代码质量
- [ ] 所有测试用例通过
- [ ] 代码覆盖率 >95%
- [ ] 无严重性能问题
- [ ] 异常处理完善

### 功能完整性
- [ ] 实时行情获取正常
- [ ] 信号检测准确
- [ ] 提醒及时发送
- [ ] 持仓监控有效
- [ ] 配置系统灵活

### 文档完整性
- [ ] API文档清晰
- [ ] 使用指南完整
- [ ] 配置说明详细
- [ ] 示例脚本可运行

---

## 六、示例脚本

### scripts/daily_monitor.py
```python
"""每日监控脚本"""
from src.monitoring.service import MonitoringService

def main():
    # 初始化监控服务
    service = MonitoringService('config/monitoring.yaml')

    # 启动监控
    print("开始监控...")
    service.start()

    try:
        # 持续运行
        service.run()
    except KeyboardInterrupt:
        print("\n停止监控...")
        service.stop()

        # 生成每日总结
        summary = service.generate_daily_summary()
        print(summary)

if __name__ == "__main__":
    main()
```

### scripts/check_positions.py
```python
"""检查持仓脚本"""
from src.monitoring.position_monitor import PositionMonitor
from src.risk.risk_manager import RiskManager
from src.monitoring.signal_detector import SignalDetector

def main():
    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 检查持仓
    signals = monitor.monitor_positions()

    if signals:
        print(f"发现 {len(signals)} 个信号:")
        for signal in signals:
            print(f"  [{signal.priority}] {signal.description}")
    else:
        print("持仓状态正常")

    # 生成报告
    report = monitor.generate_position_report()
    print(report)

if __name__ == "__main__":
    main()
```

---

## 七、后续扩展

### 短期
- [ ] 微信/邮件通知集成
- [ ] Web界面（实时监控面板）
- [ ] 更多技术指标信号

### 中期
- [ ] 机器学习信号预测
- [ ] 自动化交易执行（谨慎）
- [ ] 回测验证信号有效性

### 长期
- [ ] 多账户监控
- [ ] 组合优化建议
- [ ] 风险预算动态调整

---

## 八、风险和挑战

| 风险 | 应对措施 |
|------|----------|
| API限流 | 批量请求优化，缓存机制 |
| 数据延迟 | 明确标注更新时间 |
| 信号误报 | 多指标交叉验证，优先级过滤 |
| 性能问题 | 异步处理，分批扫描 |
| 通知轰炸 | 去重机制，优先级过滤 |

---

## 九、成功标准

✅ **功能完整性**:
- 能监控100+只股票实时行情
- 能检测10+种交易信号
- 能及时发送风险预警
- 能生成每日监控报告

✅ **性能指标**:
- 行情更新延迟 <5秒
- 信号检测延迟 <10秒
- 提醒发送延迟 <3秒
- 100股票监控内存 <100MB

✅ **可靠性**:
- 异常处理覆盖率 100%
- 7x24小时稳定运行
- 网络异常自动恢复

---

**准备开始实施 Phase 6 - Task 6.1: RealTimeWatcher**

预计完成时间: 2-3小时
实施方法: TDD (Test-Driven Development)
