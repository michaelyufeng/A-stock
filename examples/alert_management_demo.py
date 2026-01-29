"""
AlertManager 演示示例

演示AlertManager的各种功能：
1. 基本提醒规则配置
2. 多优先级信号处理
3. 冷却期机制
4. 提醒历史查询
5. 综合监控系统
"""

from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import Signal
from datetime import datetime, timedelta
import time


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_1_basic_usage():
    """示例1: 基本使用"""
    print_section("示例1: 基本使用")

    # 创建AlertManager
    alert_mgr = AlertManager()

    # 创建提醒规则
    rule = AlertRule(
        rule_id='ma_cross_alert',
        name='MA金叉提醒',
        stock_codes=['600519', '000001'],
        signal_types=['BUY'],
        categories=['technical'],
        min_priority='medium',
        channels=[AlertChannel.CONSOLE],
        enabled=True,
        cooldown_minutes=60
    )

    # 添加规则
    result = alert_mgr.add_rule(rule)
    print(f"添加规则: {result['message']}")

    # 创建匹配的信号
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
    print("\n处理买入信号:")
    result = alert_mgr.process_signal(signal)
    print(f"触发提醒: {result['triggered']}")
    print(f"触发规则: {result['rule_ids']}")


def demo_2_multiple_rules():
    """示例2: 多个规则和优先级"""
    print_section("示例2: 多个规则和优先级")

    alert_mgr = AlertManager()

    # 规则1: 技术信号（中等优先级）
    tech_rule = AlertRule(
        rule_id='tech_signal',
        name='技术信号提醒',
        stock_codes=[],  # 空列表 = 所有股票
        signal_types=['BUY', 'SELL'],
        categories=['technical'],
        min_priority='medium',
        channels=[AlertChannel.CONSOLE],
        enabled=True,
        cooldown_minutes=60
    )

    # 规则2: 风险预警（高优先级）
    risk_rule = AlertRule(
        rule_id='risk_alert',
        name='风险预警',
        stock_codes=[],
        signal_types=['SELL', 'WARNING'],
        categories=['risk', 'price'],
        min_priority='high',
        channels=[AlertChannel.CONSOLE, AlertChannel.LOG],
        enabled=True,
        cooldown_minutes=0  # 无冷却期
    )

    alert_mgr.add_rule(tech_rule)
    alert_mgr.add_rule(risk_rule)

    print(f"已添加 {len(alert_mgr.get_all_rules())} 个规则\n")

    # 测试不同优先级的信号
    signals = [
        Signal('600519', '贵州茅台', 'BUY', 'technical', 'MA金叉', 'low', 1680.0, datetime.now(), {}),
        Signal('000001', '平安银行', 'BUY', 'technical', 'RSI超卖', 'medium', 15.0, datetime.now(), {}),
        Signal('000002', '万科A', 'SELL', 'risk', '触发止损', 'critical', 8.5, datetime.now(), {}),
        Signal('600030', '中信证券', 'WARNING', 'price', '跌停', 'high', 20.0, datetime.now(), {}),
    ]

    for i, signal in enumerate(signals, 1):
        print(f"信号 {i}: {signal.stock_name} - {signal.description} (优先级: {signal.priority})")
        result = alert_mgr.process_signal(signal)
        if result['triggered']:
            print(f"  ✅ 触发规则: {', '.join(result['rule_ids'])}")
        else:
            print(f"  ❌ 未触发任何规则")
        print()


def demo_3_cooldown_mechanism():
    """示例3: 冷却期机制"""
    print_section("示例3: 冷却期机制")

    alert_mgr = AlertManager()

    # 创建有冷却期的规则
    rule = AlertRule(
        rule_id='cooldown_test',
        name='冷却期测试',
        stock_codes=['600519'],
        signal_types=['BUY'],
        categories=['technical'],
        min_priority='low',
        channels=[AlertChannel.CONSOLE],
        enabled=True,
        cooldown_minutes=1  # 1分钟冷却期（演示用）
    )

    alert_mgr.add_rule(rule)

    signal = Signal(
        '600519', '贵州茅台', 'BUY', 'technical',
        'MA金叉', 'medium', 1680.0, datetime.now(), {}
    )

    # 第一次触发
    print("第一次触发:")
    result1 = alert_mgr.process_signal(signal)
    print(f"  触发: {result1['triggered']}\n")

    # 立即再次触发（应该被冷却期阻止）
    print("立即再次触发（冷却期内）:")
    result2 = alert_mgr.process_signal(signal)
    print(f"  触发: {result2['triggered']}")
    print(f"  被冷却期阻止 ❌\n")

    # 模拟等待（实际应该等待61秒，这里仅演示逻辑）
    print("（实际使用中需等待冷却期过后才能再次触发）")


def demo_4_alert_history():
    """示例4: 提醒历史管理"""
    print_section("示例4: 提醒历史管理")

    alert_mgr = AlertManager()

    rule = AlertRule(
        'history_test', '历史测试', [], ['BUY', 'SELL'],
        ['technical'], 'low', [AlertChannel.LOG], True, 0
    )
    alert_mgr.add_rule(rule)

    # 创建多个信号
    signals = [
        Signal('600519', '贵州茅台', 'BUY', 'technical', 'MA金叉', 'medium', 1680.0, datetime.now(), {}),
        Signal('000001', '平安银行', 'SELL', 'technical', 'MA死叉', 'medium', 14.5, datetime.now(), {}),
        Signal('600519', '贵州茅台', 'BUY', 'technical', 'RSI超卖', 'medium', 1675.0, datetime.now(), {}),
    ]

    # 处理所有信号
    print("处理3个信号...")
    for signal in signals:
        alert_mgr.process_signal(signal)

    # 查询所有历史
    all_history = alert_mgr.get_alert_history()
    print(f"\n总共记录: {len(all_history)} 条")

    # 查询特定股票
    stock_history = alert_mgr.get_alert_history(stock_code='600519')
    print(f"贵州茅台记录: {len(stock_history)} 条")

    # 显示历史详情
    print("\n提醒历史:")
    for record in all_history:
        print(f"  {record['timestamp'].strftime('%H:%M:%S')} - "
              f"{record['stock_name']} - {record['description']}")


def demo_5_rule_management():
    """示例5: 规则管理操作"""
    print_section("示例5: 规则管理操作")

    alert_mgr = AlertManager()

    # 添加规则
    rule = AlertRule(
        'test_rule', '测试规则', ['600519'],
        ['BUY'], ['technical'], 'medium',
        [AlertChannel.CONSOLE], True, 60
    )

    print("1. 添加规则")
    result = alert_mgr.add_rule(rule)
    print(f"   {result['message']}\n")

    # 查看所有规则
    print("2. 查看所有规则")
    rules = alert_mgr.get_all_rules()
    for r in rules:
        print(f"   - {r.rule_id}: {r.name} (启用: {r.enabled})\n")

    # 更新规则
    print("3. 更新规则（禁用）")
    result = alert_mgr.update_rule('test_rule', enabled=False, min_priority='high')
    print(f"   {result['message']}")
    updated_rule = alert_mgr.rules['test_rule']
    print(f"   新状态: 启用={updated_rule.enabled}, 最低优先级={updated_rule.min_priority}\n")

    # 删除规则
    print("4. 删除规则")
    result = alert_mgr.remove_rule('test_rule')
    print(f"   {result['message']}")
    print(f"   剩余规则数: {len(alert_mgr.get_all_rules())}")


def demo_6_integrated_monitoring():
    """示例6: 综合监控系统（概念演示）"""
    print_section("示例6: 综合监控系统（概念演示）")

    print("综合监控系统架构:")
    print("""
    ┌─────────────────┐
    │ RealTimeWatcher │ ← 实时获取行情
    └────────┬────────┘
             │
             ↓
    ┌─────────────────┐
    │ SignalDetector  │ ← 检测交易信号
    └────────┬────────┘
             │
             ↓
    ┌─────────────────┐
    │  AlertManager   │ ← 匹配规则、发送通知
    └─────────────────┘
             │
             ↓
    ┌─────────────────┐
    │ 控制台/日志/邮件 │ ← 多渠道通知
    └─────────────────┘
    """)

    # 模拟监控系统配置
    alert_mgr = AlertManager()

    # 配置多个规则
    rules = [
        AlertRule('ma_cross', 'MA交叉', [], ['BUY', 'SELL'],
                  ['technical'], 'medium', [AlertChannel.CONSOLE], True, 60),
        AlertRule('rsi_extreme', 'RSI极值', [], ['BUY', 'SELL'],
                  ['technical'], 'medium', [AlertChannel.CONSOLE], True, 60),
        AlertRule('stop_loss', '止损预警', [], ['SELL'],
                  ['risk'], 'critical', [AlertChannel.CONSOLE, AlertChannel.LOG], True, 0),
        AlertRule('limit_updown', '涨跌停', [], ['WARNING'],
                  ['price'], 'high', [AlertChannel.CONSOLE, AlertChannel.LOG], True, 1440),
    ]

    for rule in rules:
        alert_mgr.add_rule(rule)

    print(f"已配置 {len(rules)} 个监控规则:")
    for rule in alert_mgr.get_all_rules():
        print(f"  - {rule.name} (优先级: {rule.min_priority}, 冷却期: {rule.cooldown_minutes}分钟)")

    print("\n监控系统已启动，等待信号...")
    print("（实际使用中会持续监控并自动发送提醒）")


def main():
    """运行所有演示"""
    print("="*60)
    print("  AlertManager 功能演示")
    print("="*60)

    demos = [
        ("基本使用", demo_1_basic_usage),
        ("多规则和优先级", demo_2_multiple_rules),
        ("冷却期机制", demo_3_cooldown_mechanism),
        ("提醒历史", demo_4_alert_history),
        ("规则管理", demo_5_rule_management),
        ("综合监控系统", demo_6_integrated_monitoring),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ 示例 {i} 执行出错: {e}")

        if i < len(demos):
            input("\n按回车继续下一个示例...")

    print_section("演示结束")
    print("更多详细用法请参考: docs/alert_manager_guide.md")


if __name__ == '__main__':
    main()
