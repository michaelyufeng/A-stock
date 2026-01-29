"""
PositionMonitor 演示示例

演示PositionMonitor的各种功能：
1. 基本持仓监控
2. 止损止盈检查
3. 价格更新
4. 风险评估
5. 报告生成
6. 综合监控系统
"""

from src.risk.risk_manager import RiskManager
from src.monitoring.signal_detector import SignalDetector
from src.monitoring.position_monitor import PositionMonitor
from datetime import datetime, timedelta


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_1_basic_monitoring():
    """示例1: 基本持仓监控"""
    print_section("示例1: 基本持仓监控")

    # 创建组件
    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加持仓
    risk_mgr.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1500.0,
        entry_date=datetime.now() - timedelta(days=10)
    )

    print("已添加持仓: 600519 贵州茅台")
    print("  成本价: ¥1500.00")
    print("  持仓: 100股")
    print("  成本: ¥150,000\n")

    # 模拟价格正常波动
    quotes = {'600519': {'current_price': 1520.0}}

    print("更新价格: ¥1520.00 (+1.33%)")
    signals = monitor.monitor_positions(quotes)

    if signals:
        print(f"\n检测到 {len(signals)} 个信号:")
        for signal in signals:
            print(f"  [{signal.priority}] {signal.description}")
    else:
        print("\n状态正常，无风险信号")


def demo_2_stop_loss_check():
    """示例2: 止损检查"""
    print_section("示例2: 止损检查")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加持仓
    risk_mgr.add_position(
        '600519', '贵州茅台', '白酒', 100, 1500.0, datetime.now() - timedelta(days=10)
    )

    risk_mgr.add_position(
        '000001', '平安银行', '银行', 1000, 15.0, datetime.now() - timedelta(days=5)
    )

    print("当前持仓:")
    print("  1. 600519 贵州茅台 - 成本价: ¥1500.00")
    print("  2. 000001 平安银行 - 成本价: ¥15.00\n")

    # 模拟触发止损（下跌10%）
    quotes = {
        '600519': {'current_price': 1350.0},  # -10%
        '000001': {'current_price': 13.5}     # -10%
    }

    print("价格更新:")
    print("  600519: ¥1350.00 (-10.0%) ❌ 触发止损")
    print("  000001: ¥13.50 (-10.0%) ❌ 触发止损\n")

    # 更新价格
    monitor.update_position_prices(quotes)

    # 检查止损
    signals = monitor.check_stop_loss_all()

    print(f"止损检查结果: {len(signals)} 只股票触发止损")
    for signal in signals:
        print(f"  🔴 {signal.stock_name}: {signal.description}")


def demo_3_take_profit_check():
    """示例3: 止盈检查"""
    print_section("示例3: 止盈检查")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加持仓
    risk_mgr.add_position(
        '600519', '贵州茅台', '白酒', 100, 1500.0, datetime.now() - timedelta(days=10)
    )

    print("当前持仓:")
    print("  600519 贵州茅台 - 成本价: ¥1500.00\n")

    # 模拟触发止盈（上涨16%）
    quotes = {'600519': {'current_price': 1750.0}}

    print("价格更新:")
    print("  600519: ¥1750.00 (+16.7%) ✅ 触发止盈\n")

    monitor.update_position_prices(quotes)

    # 检查止盈
    signals = monitor.check_take_profit_all()

    print(f"止盈检查结果: {len(signals)} 只股票触发止盈")
    for signal in signals:
        print(f"  🟢 {signal.stock_name}: {signal.description}")


def demo_4_portfolio_health():
    """示例4: 组合健康评估"""
    print_section("示例4: 组合健康评估")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加多个持仓
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500.0, datetime.now() - timedelta(days=10))
    risk_mgr.add_position('000001', '平安银行', '银行', 1000, 15.0, datetime.now() - timedelta(days=5))
    risk_mgr.add_position('000002', '万科A', '房地产', 2000, 8.5, datetime.now() - timedelta(days=3))

    print("当前持仓: 3只股票\n")

    # 更新价格（混合场景）
    quotes = {
        '600519': {'current_price': 1600.0},  # +6.7%
        '000001': {'current_price': 16.0},    # +6.7%
        '000002': {'current_price': 8.0}      # -5.9%
    }

    monitor.update_position_prices(quotes)

    # 评估健康度
    health = monitor.assess_portfolio_health()

    print("组合健康评估:")
    print(f"  风险级别: {health['risk_level'].upper()}")
    print(f"  持仓数量: {health['position_count']} 只")
    print(f"  总市值: ¥{health['total_value']:,.2f}")
    print(f"  总成本: ¥{health['total_cost']:,.2f}")
    print(f"  浮动盈亏: ¥{health['total_profit_loss']:,.2f} ({health['total_profit_loss_pct']:+.2%})")

    if health['positions_at_risk'] > 0:
        print(f"\n⚠️  风险持仓: {health['positions_at_risk']} 只")
        for warning in health['warnings']:
            print(f"  - {warning}")


def demo_5_position_report():
    """示例5: 持仓报告生成"""
    print_section("示例5: 持仓报告生成")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加持仓
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500.0, datetime.now() - timedelta(days=10))
    risk_mgr.add_position('000001', '平安银行', '银行', 1000, 15.0, datetime.now() - timedelta(days=5))

    # 更新价格
    quotes = {
        '600519': {'current_price': 1600.0},
        '000001': {'current_price': 16.0}
    }
    monitor.update_position_prices(quotes)

    # 生成报告
    report = monitor.generate_position_report()
    print(report)


def demo_6_empty_portfolio():
    """示例6: 空持仓处理"""
    print_section("示例6: 空持仓处理")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    print("测试空持仓场景:")

    # 监控空持仓
    signals = monitor.monitor_positions()
    print(f"  监控信号: {len(signals)} 个")

    # 评估健康度
    health = monitor.assess_portfolio_health()
    print(f"  风险级别: {health['risk_level']}")
    print(f"  持仓数量: {health['position_count']}")
    print(f"  总市值: ¥{health['total_value']:,.2f}\n")

    # 生成报告
    report = monitor.generate_position_report()
    print(report)


def demo_7_monitoring_cycle():
    """示例7: 完整监控周期"""
    print_section("示例7: 完整监控周期")

    risk_mgr = RiskManager(total_capital=1_000_000)
    detector = SignalDetector(risk_mgr)
    monitor = PositionMonitor(risk_mgr, detector)

    # 添加持仓
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500.0, datetime.now() - timedelta(days=10))
    risk_mgr.add_position('000001', '平安银行', '银行', 1000, 15.0, datetime.now() - timedelta(days=5))

    print("模拟3个监控周期:\n")

    scenarios = [
        # 场景1: 正常波动
        {
            'name': '场景1: 正常波动',
            'quotes': {
                '600519': {'current_price': 1520.0},
                '000001': {'current_price': 15.3}
            }
        },
        # 场景2: 触发止损
        {
            'name': '场景2: 触发止损',
            'quotes': {
                '600519': {'current_price': 1350.0},  # 触发止损
                '000001': {'current_price': 15.0}
            }
        },
        # 场景3: 触发止盈
        {
            'name': '场景3: 触发止盈',
            'quotes': {
                '600519': {'current_price': 1750.0},  # 触发止盈
                '000001': {'current_price': 17.5}     # 触发止盈
            }
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"--- {scenario['name']} ---")

        # 监控
        signals = monitor.monitor_positions(scenario['quotes'])

        # 显示结果
        print(f"检测到信号: {len(signals)} 个")
        for signal in signals:
            icon = '🔴' if signal.signal_type == 'SELL' and '止损' in signal.description else '🟢'
            print(f"  {icon} [{signal.priority}] {signal.stock_name}: {signal.description}")

        # 评估健康度
        health = monitor.assess_portfolio_health()
        print(f"风险级别: {health['risk_level'].upper()}")
        print(f"总盈亏: ¥{health['total_profit_loss']:,.2f} ({health['total_profit_loss_pct']:+.2%})")
        print()


def demo_8_integrated_system():
    """示例8: 综合监控系统（概念演示）"""
    print_section("示例8: 综合监控系统（概念演示）")

    print("综合持仓监控系统架构:")
    print("""
    ┌────────────────┐
    │ RiskManager    │ ← 管理持仓
    └───────┬────────┘
            │
            ↓
    ┌────────────────┐
    │SignalDetector  │ ← 检测信号
    └───────┬────────┘
            │
            ↓
    ┌────────────────┐
    │PositionMonitor │ ← 监控持仓
    └───────┬────────┘
            │
            ├─→ 更新价格
            ├─→ 检查止损止盈
            ├─→ 评估风险
            └─→ 生成报告
    """)

    print("典型监控流程:")
    print("  1. 实时获取行情 (RealTimeWatcher)")
    print("  2. 更新持仓价格 (PositionMonitor.update_position_prices)")
    print("  3. 监控持仓风险 (PositionMonitor.monitor_positions)")
    print("  4. 检测交易信号 (SignalDetector)")
    print("  5. 发送风险提醒 (AlertManager)")
    print("  6. 生成监控报告 (PositionMonitor.generate_position_report)")


def main():
    """运行所有演示"""
    print("="*60)
    print("  PositionMonitor 功能演示")
    print("="*60)

    demos = [
        ("基本持仓监控", demo_1_basic_monitoring),
        ("止损检查", demo_2_stop_loss_check),
        ("止盈检查", demo_3_take_profit_check),
        ("组合健康评估", demo_4_portfolio_health),
        ("持仓报告生成", demo_5_position_report),
        ("空持仓处理", demo_6_empty_portfolio),
        ("完整监控周期", demo_7_monitoring_cycle),
        ("综合监控系统", demo_8_integrated_system),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ 示例 {i} 执行出错: {e}")

        if i < len(demos):
            input("\n按回车继续下一个示例...")

    print_section("演示结束")
    print("更多详细用法请参考: docs/position_monitor_guide.md")


if __name__ == '__main__':
    main()
