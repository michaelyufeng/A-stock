"""
邮件通知功能演示脚本

功能：
1. 演示如何配置和使用邮件通知
2. 展示不同类型的交易信号
3. 演示邮件发送的各种场景

使用方法：
1. 配置.env文件中的EMAIL_SENDER和EMAIL_PASSWORD
2. 修改config/monitoring.yaml中的email.recipients
3. 运行脚本: python examples/email_notification_demo.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import Signal
from datetime import datetime
import time


def create_demo_signals():
    """创建演示用的交易信号"""
    signals = [
        # 买入信号
        Signal(
            stock_code='600519',
            stock_name='贵州茅台',
            signal_type='BUY',
            category='technical',
            description='MA5金叉MA20，成交量放大，形成买入信号',
            priority='high',
            trigger_price=1680.50,
            timestamp=datetime.now(),
            metadata={
                'ma_short': 5,
                'ma_long': 20,
                'volume_ratio': 2.3,
                'rsi': 45
            }
        ),

        # 卖出信号
        Signal(
            stock_code='000858',
            stock_name='五粮液',
            signal_type='SELL',
            category='technical',
            description='MA5死叉MA20，建议考虑减仓',
            priority='medium',
            trigger_price=155.30,
            timestamp=datetime.now(),
            metadata={
                'ma_short': 5,
                'ma_long': 20,
                'volume_ratio': 1.2,
                'rsi': 65
            }
        ),

        # 风险警告
        Signal(
            stock_code='000001',
            stock_name='平安银行',
            signal_type='WARNING',
            category='risk',
            description='触发止损线，建议立即止损',
            priority='critical',
            trigger_price=12.80,
            timestamp=datetime.now(),
            metadata={
                'stop_loss': 13.20,
                'loss_percent': -8.5,
                'position_ratio': 0.15
            }
        ),

        # 信息通知
        Signal(
            stock_code='600036',
            stock_name='招商银行',
            signal_type='INFO',
            category='price',
            description='价格突破前期高点，可继续观察',
            priority='low',
            trigger_price=38.50,
            timestamp=datetime.now(),
            metadata={
                'resistance': 38.00,
                'support': 36.50
            }
        ),
    ]

    return signals


def demo_basic_email_notification():
    """演示基本的邮件通知功能"""
    print("=" * 70)
    print("邮件通知功能演示")
    print("=" * 70)

    # 1. 创建AlertManager
    print("\n1. 初始化AlertManager...")
    try:
        alert_manager = AlertManager(config_path='config/monitoring.yaml')
        print("✅ AlertManager初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 检查邮件配置
    if not alert_manager.email_config:
        print("\n⚠️  警告: 未找到邮件配置")
        print("请检查:")
        print("  1. config/monitoring.yaml中是否配置了alerts.email")
        print("  2. .env文件中是否设置了EMAIL_SENDER和EMAIL_PASSWORD")
        return

    print(f"📧 邮件配置加载完成:")
    print(f"   SMTP服务器: {alert_manager.email_config.get('smtp_server')}")
    print(f"   发件人: {alert_manager.email_config.get('sender')}")
    print(f"   收件人: {', '.join(alert_manager.email_config.get('recipients', []))}")

    # 2. 创建邮件提醒规则
    print("\n2. 创建邮件提醒规则...")

    # 规则1: 高优先级信号立即邮件通知
    rule_high_priority = AlertRule(
        rule_id='email_high_priority',
        name='高优先级邮件提醒',
        stock_codes=[],  # 空列表表示监控所有股票
        signal_types=['BUY', 'SELL', 'WARNING'],
        categories=['technical', 'risk'],
        min_priority='high',
        channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
        enabled=True,
        cooldown_minutes=5  # 演示用，设置较短的冷却期
    )

    # 规则2: 风险警告立即邮件通知
    rule_risk_alert = AlertRule(
        rule_id='email_risk_alert',
        name='风险警告邮件提醒',
        stock_codes=[],
        signal_types=['WARNING'],
        categories=['risk'],
        min_priority='medium',
        channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL],
        enabled=True,
        cooldown_minutes=5
    )

    alert_manager.add_rule(rule_high_priority)
    alert_manager.add_rule(rule_risk_alert)
    print(f"✅ 已添加 {len(alert_manager.rules)} 个提醒规则")

    # 3. 处理演示信号
    print("\n3. 处理交易信号并发送邮件...")
    signals = create_demo_signals()

    for i, signal in enumerate(signals, 1):
        print(f"\n--- 信号 {i}/{len(signals)} ---")
        print(f"股票: {signal.stock_code} {signal.stock_name}")
        print(f"类型: {signal.signal_type} | 优先级: {signal.priority}")
        print(f"描述: {signal.description}")

        result = alert_manager.process_signal(signal)

        if result['triggered']:
            print(f"✅ 触发规则: {', '.join(result['rule_ids'])}")
            print(f"📧 邮件通知已发送")
        else:
            print(f"ℹ️  未触发提醒规则（优先级不够或不匹配）")

        # 短暂延迟，避免发送过快
        if i < len(signals):
            time.sleep(1)

    # 4. 查看提醒历史
    print("\n4. 提醒历史记录:")
    history = alert_manager.get_alert_history(limit=10)

    if history:
        print(f"\n最近 {len(history)} 条提醒记录:")
        for i, record in enumerate(history, 1):
            print(f"{i}. {record['timestamp'].strftime('%H:%M:%S')} - "
                  f"{record['stock_code']} {record['stock_name']} - "
                  f"{record['signal_type']} ({record['priority']})")
    else:
        print("暂无提醒记录")

    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)
    print("\n💡 提示:")
    print("  - 检查收件箱中的邮件（可能在垃圾邮件文件夹）")
    print("  - 查看日志文件: logs/monitoring.log")
    print("  - 如需修改配置，请编辑: config/monitoring.yaml")


def demo_email_template():
    """演示邮件模板功能"""
    print("\n" + "=" * 70)
    print("邮件模板演示")
    print("=" * 70)

    alert_manager = AlertManager(config_path='config/monitoring.yaml')

    # 创建一个测试信号
    signal = Signal(
        stock_code='600519',
        stock_name='贵州茅台',
        signal_type='BUY',
        category='technical',
        description='这是一个测试信号',
        priority='high',
        trigger_price=1680.50,
        timestamp=datetime.now(),
        metadata={'test': 'demo'}
    )

    try:
        # 渲染邮件模板
        html = alert_manager._render_email_template(signal)

        print("\n✅ 邮件模板渲染成功")
        print(f"HTML长度: {len(html)} 字符")
        print("\n模板预览（前200字符）:")
        print(html[:200] + "...")

        # 可选：保存到文件查看
        output_path = 'email_preview.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n📄 完整HTML已保存到: {output_path}")
        print("   可以在浏览器中打开查看")

    except Exception as e:
        print(f"\n❌ 模板渲染失败: {e}")


def test_smtp_connection():
    """测试SMTP连接"""
    print("\n" + "=" * 70)
    print("SMTP连接测试")
    print("=" * 70)

    from dotenv import load_dotenv
    import smtplib

    load_dotenv()

    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')

    if not sender or not password:
        print("\n❌ 未配置EMAIL_SENDER或EMAIL_PASSWORD")
        print("请在.env文件中配置这些环境变量")
        return

    print(f"\n测试配置:")
    print(f"发件人: {sender}")
    print(f"密码: {'*' * len(password)}")

    # 尝试连接
    smtp_configs = [
        ('Gmail', 'smtp.gmail.com', 587, True),
        ('QQ', 'smtp.qq.com', 587, True),
        ('163', 'smtp.163.com', 25, False),
    ]

    for name, server, port, use_tls in smtp_configs:
        try:
            print(f"\n尝试连接 {name} ({server}:{port})...")
            smtp = smtplib.SMTP(server, port, timeout=10)

            if use_tls:
                smtp.starttls()

            smtp.login(sender, password)
            smtp.quit()

            print(f"✅ {name} 连接成功!")
            break

        except Exception as e:
            print(f"❌ {name} 连接失败: {e}")

    print("\n提示: 如果所有连接都失败，请检查:")
    print("  1. 邮箱是否开启了SMTP服务")
    print("  2. 是否使用了正确的密码类型（应用密码/授权码）")
    print("  3. 防火墙是否阻止了SMTP端口")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("A股监控系统 - 邮件通知功能演示")
    print("=" * 70)

    print("\n请选择演示功能:")
    print("1. 基本邮件通知演示（推荐）")
    print("2. 邮件模板预览")
    print("3. SMTP连接测试")
    print("4. 运行所有演示")
    print("0. 退出")

    choice = input("\n请输入选项 (0-4): ").strip()

    if choice == '1':
        demo_basic_email_notification()
    elif choice == '2':
        demo_email_template()
    elif choice == '3':
        test_smtp_connection()
    elif choice == '4':
        test_smtp_connection()
        demo_email_template()
        demo_basic_email_notification()
    elif choice == '0':
        print("退出演示")
    else:
        print("无效的选项")


if __name__ == '__main__':
    main()
