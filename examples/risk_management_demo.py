"""
风险管理器演示脚本

演示RiskManager的完整使用流程：
1. 初始化和配置
2. 建仓前检查
3. 添加持仓
4. 持仓监控和更新
5. 风险评估
6. 止损止盈
7. 平仓
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.risk.risk_manager import RiskManager
from datetime import datetime, timedelta
import pandas as pd


def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
        print("=" * 60)


def demo_basic_usage():
    """演示基本使用流程"""
    print_separator("演示1: 基本使用流程")

    # 初始化风险管理器（总资金100万）
    risk_mgr = RiskManager(total_capital=1_000_000)
    print("✅ 初始化风险管理器，总资金: 1,000,000元")

    # 1. 建仓前检查
    print("\n【步骤1】建仓前检查")
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=150_000
    )

    print(f"  允许建仓: {result['allowed']}")
    print(f"  最大可建仓: {result['max_position_value']:,.0f}元")
    if result['warnings']:
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")

    # 2. 检查交易限制
    print("\n【步骤2】检查交易限制")
    trade_check = risk_mgr.check_trade_restrictions('600519', '贵州茅台')
    print(f"  允许交易: {trade_check['allowed']}")
    if not trade_check['allowed']:
        print(f"  ❌ 原因: {trade_check['reason']}")

    # 3. 建仓
    print("\n【步骤3】建仓")
    risk_mgr.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1500.0,
        entry_date=datetime.now()
    )
    print("  ✅ 建仓成功: 600519 贵州茅台")
    print("     数量: 100股")
    print("     价格: 1500.0元/股")
    print("     金额: 150,000元")

    # 4. 查看持仓详情
    print("\n【步骤4】查看持仓详情")
    position = risk_mgr.get_position('600519')
    print(f"  股票代码: {position['stock_code']}")
    print(f"  股票名称: {position['stock_name']}")
    print(f"  持有数量: {position['shares']}股")
    print(f"  成本价格: {position['entry_price']:.2f}元")
    print(f"  当前价格: {position['current_price']:.2f}元")
    print(f"  持仓市值: {position['current_value']:,.0f}元")
    print(f"  止损价格: {position['stop_loss_price']:.2f}元")
    print(f"  止盈价格: {position['take_profit_price']:.2f}元")


def demo_position_limits():
    """演示仓位限制检查"""
    print_separator("演示2: 仓位限制检查")

    risk_mgr = RiskManager(total_capital=1_000_000)

    # 案例1: 单一持仓限制
    print("\n【案例1】单一持仓限制（20%）")
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=250_000  # 25%，超过限制
    )
    print(f"  拟建仓: 250,000元 (25%)")
    print(f"  ❌ 允许建仓: {result['allowed']}")
    print(f"  原因: {result['reason']}")

    # 案例2: 行业集中度限制
    print("\n【案例2】行业集中度限制（30%）")
    # 先建一个20%的白酒仓位
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 133, 1500, datetime.now())
    print("  已有仓位: 600519 贵州茅台 (白酒) 20%")

    # 尝试再建15%的白酒仓位（总共35%，超限）
    result = risk_mgr.check_position_limit(
        stock_code='000858',
        stock_name='五粮液',
        sector='白酒',
        position_value=150_000
    )
    print(f"  拟建仓: 000858 五粮液 (白酒) 15%")
    print(f"  ❌ 允许建仓: {result['allowed']}")
    print(f"  原因: {result['reason']}")

    # 案例3: 最小建仓金额
    print("\n【案例3】最小建仓金额（10,000元）")
    result = risk_mgr.check_position_limit(
        stock_code='600036',
        stock_name='招商银行',
        sector='银行',
        position_value=5_000  # 低于最小金额
    )
    print(f"  拟建仓: 5,000元")
    print(f"  ❌ 允许建仓: {result['allowed']}")
    print(f"  原因: {result['reason']}")


def demo_trade_restrictions():
    """演示交易限制检查"""
    print_separator("演示3: 交易限制检查")

    risk_mgr = RiskManager(total_capital=1_000_000)

    # 案例1: ST股过滤
    print("\n【案例1】ST股过滤")
    st_stocks = ['ST海航', '*ST凯迪', 'SST前锋', 'S*ST昌鱼']
    for stock_name in st_stocks:
        result = risk_mgr.check_trade_restrictions('600000', stock_name)
        print(f"  {stock_name}: {'❌ 禁止' if not result['allowed'] else '✅ 允许'}")

    # 案例2: 交易频率限制
    print("\n【案例2】交易频率限制（每日5次）")
    today = datetime.now()

    # 模拟5次交易
    for i in range(5):
        code = f'60000{i}'
        risk_mgr.add_position(code, f'股票{i}', '电子', 100, 10, today)
        risk_mgr.remove_position(code, 11, today)
        print(f"  交易{i+1}: {code}")

    # 尝试第6次交易
    result = risk_mgr.check_trade_restrictions('600006', '第六只股票')
    print(f"\n  第6次交易: {'❌ 禁止' if not result['allowed'] else '✅ 允许'}")
    if not result['allowed']:
        print(f"  原因: {result['reason']}")

    # 案例3: 冷却期
    print("\n【案例3】冷却期（5天）")
    risk_mgr2 = RiskManager(total_capital=1_000_000)

    # 3天前交易过
    past_date = datetime.now() - timedelta(days=3)
    risk_mgr2.add_position('600519', '贵州茅台', '白酒', 100, 1500, past_date)
    risk_mgr2.remove_position('600519', 1600, past_date)

    result = risk_mgr2.check_trade_restrictions('600519', '贵州茅台')
    print(f"  上次交易: 3天前")
    print(f"  ❌ 允许交易: {result['allowed']}")
    print(f"  原因: {result['reason']}")


def demo_stop_loss_take_profit():
    """演示止损止盈计算"""
    print_separator("演示4: 止损止盈计算")

    risk_mgr = RiskManager(total_capital=1_000_000)
    entry_price = 100.0

    # 1. 固定止损
    print("\n【方法1】固定止损（8%）")
    stop_loss = risk_mgr.calculate_stop_loss(entry_price, method='fixed')
    print(f"  入场价: {entry_price:.2f}元")
    print(f"  止损价: {stop_loss:.2f}元")
    print(f"  止损幅度: {(entry_price - stop_loss) / entry_price * 100:.1f}%")

    # 2. 移动止损
    print("\n【方法2】移动止损（5%）")
    stop_loss = risk_mgr.calculate_stop_loss(entry_price, method='trailing')
    print(f"  入场价: {entry_price:.2f}元")
    print(f"  止损价: {stop_loss:.2f}元")
    print(f"  止损幅度: {(entry_price - stop_loss) / entry_price * 100:.1f}%")

    # 3. ATR止损
    print("\n【方法3】ATR止损（2倍ATR）")
    atr = 3.0
    stop_loss = risk_mgr.calculate_stop_loss(entry_price, method='atr', atr=atr)
    print(f"  入场价: {entry_price:.2f}元")
    print(f"  ATR值: {atr:.2f}")
    print(f"  止损价: {stop_loss:.2f}元 ({entry_price} - 2*{atr})")

    # 4. 固定止盈
    print("\n【方法4】固定止盈（15%）")
    take_profit = risk_mgr.calculate_take_profit(entry_price, method='fixed')
    print(f"  入场价: {entry_price:.2f}元")
    print(f"  止盈价: {take_profit:.2f}元")
    print(f"  止盈幅度: {(take_profit - entry_price) / entry_price * 100:.1f}%")

    # 5. 动态止盈
    print("\n【方法5】动态止盈（22.5%）")
    take_profit = risk_mgr.calculate_take_profit(entry_price, method='dynamic')
    print(f"  入场价: {entry_price:.2f}元")
    print(f"  止盈价: {take_profit:.2f}元")
    print(f"  止盈幅度: {(take_profit - entry_price) / entry_price * 100:.1f}%")


def demo_position_management():
    """演示持仓管理"""
    print_separator("演示5: 持仓管理")

    risk_mgr = RiskManager(total_capital=1_000_000)

    # 1. 添加多个持仓
    print("\n【步骤1】添加多个持仓")
    positions_to_add = [
        ('600519', '贵州茅台', '白酒', 100, 1500),
        ('600036', '招商银行', '银行', 1000, 35),
        ('000858', '五粮液', '白酒', 67, 1500),
    ]

    for code, name, sector, shares, price in positions_to_add:
        risk_mgr.add_position(code, name, sector, shares, price, datetime.now())
        print(f"  ✅ {code} {name}: {shares}股 @ {price}元")

    # 2. 查看所有持仓
    print("\n【步骤2】查看所有持仓")
    all_positions = risk_mgr.get_all_positions()
    print(f"  总持仓数: {len(all_positions)}")

    total_value = 0
    for code, pos in all_positions.items():
        print(f"\n  {code} {pos['stock_name']}")
        print(f"    持仓: {pos['shares']}股 @ {pos['entry_price']:.2f}元")
        print(f"    市值: {pos['current_value']:,.0f}元")
        total_value += pos['current_value']

    print(f"\n  总市值: {total_value:,.0f}元")

    # 3. 更新市值
    print("\n【步骤3】更新市值")
    updates = [
        ('600519', 1600),  # 上涨
        ('600036', 34),    # 下跌
        ('000858', 1550),  # 上涨
    ]

    for code, new_price in updates:
        risk_mgr.update_position(code, new_price)
        pos = risk_mgr.get_position(code)
        pnl_pct = (new_price - pos['entry_price']) / pos['entry_price'] * 100
        print(f"  {code}: {pos['entry_price']:.2f} → {new_price:.2f} "
              f"({'+'if pnl_pct > 0 else ''}{pnl_pct:.1f}%)")

    # 4. 平仓
    print("\n【步骤4】平仓")
    pnl = risk_mgr.remove_position('600519', exit_price=1600, exit_date=datetime.now())
    print(f"  平仓 600519 @ 1600元")
    print(f"  盈亏: {'+' if pnl > 0 else ''}{pnl:,.0f}元")


def demo_risk_assessment():
    """演示风险评估"""
    print_separator("演示6: 风险评估")

    risk_mgr = RiskManager(total_capital=1_000_000)

    # 场景1: 空仓
    print("\n【场景1】空仓")
    risk = risk_mgr.assess_portfolio_risk()
    print(f"  风险等级: {risk['risk_level']}")
    print(f"  总仓位: {risk['total_position_pct']*100:.1f}%")

    # 场景2: 低风险
    print("\n【场景2】低风险（单一10%持仓）")
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 67, 1500, datetime.now())
    risk = risk_mgr.assess_portfolio_risk()
    print(f"  风险等级: {risk['risk_level']}")
    print(f"  总仓位: {risk['total_position_pct']*100:.1f}%")
    print(f"  持仓数: {risk['position_count']}")

    # 场景3: 中等风险
    print("\n【场景3】中等风险（多持仓，高仓位）")
    risk_mgr.add_position('600036', '招商银行', '银行', 5000, 35, datetime.now())
    risk_mgr.add_position('000858', '五粮液', '白酒', 200, 1500, datetime.now())
    risk = risk_mgr.assess_portfolio_risk()
    print(f"  风险等级: {risk['risk_level']}")
    print(f"  总仓位: {risk['total_position_pct']*100:.1f}%")
    print(f"  持仓数: {risk['position_count']}")

    print("\n  行业分布:")
    for sector, pct in risk['sector_exposure'].items():
        print(f"    {sector}: {pct*100:.1f}%")

    if risk['warnings']:
        print("\n  ⚠️  风险警告:")
        for warning in risk['warnings']:
            print(f"    - {warning}")

    # 场景4: 高风险
    print("\n【场景4】高风险（行业集中）")
    risk_mgr2 = RiskManager(total_capital=1_000_000)
    risk_mgr2.add_position('600519', '贵州茅台', '白酒', 133, 1500, datetime.now())
    risk_mgr2.add_position('000858', '五粮液', '白酒', 133, 1500, datetime.now())

    risk = risk_mgr2.assess_portfolio_risk()
    print(f"  风险等级: {risk['risk_level']}")
    print(f"  总仓位: {risk['total_position_pct']*100:.1f}%")

    print("\n  行业分布:")
    for sector, pct in risk['sector_exposure'].items():
        print(f"    {sector}: {pct*100:.1f}%")

    if risk['warnings']:
        print("\n  ⚠️  风险警告:")
        for warning in risk['warnings']:
            print(f"    - {warning}")


def demo_continuous_limit():
    """演示连续涨跌停检查"""
    print_separator("演示7: 连续涨跌停检查")

    risk_mgr = RiskManager(total_capital=1_000_000)

    # 案例1: 连续涨停
    print("\n【案例1】连续涨停（3个涨停）")
    dates = pd.date_range(end=datetime.now(), periods=5)
    kline_df = pd.DataFrame({
        'open': [100, 110, 121, 133.1, 146.4],
        'close': [110, 121, 133.1, 146.4, 146.4],
        'high': [110, 121, 133.1, 146.4, 146.4],
        'low': [100, 110, 121, 133.1, 146.4],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)
    print(f"  连续涨停: {result['continuous_limit_up']}次")
    print(f"  连续跌停: {result['continuous_limit_down']}次")
    print(f"  ⚠️  预警: {result['warning']}")

    # 案例2: 连续跌停
    print("\n【案例2】连续跌停（3个跌停）")
    kline_df = pd.DataFrame({
        'open': [100, 90, 81, 72.9, 65.6],
        'close': [90, 81, 72.9, 65.6, 65.6],
        'high': [100, 90, 81, 72.9, 65.6],
        'low': [90, 81, 72.9, 65.6, 65.6],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)
    print(f"  连续涨停: {result['continuous_limit_up']}次")
    print(f"  连续跌停: {result['continuous_limit_down']}次")
    print(f"  ⚠️  预警: {result['warning']}")

    # 案例3: 正常交易
    print("\n【案例3】正常交易（无连续涨跌停）")
    kline_df = pd.DataFrame({
        'open': [100, 102, 101, 103, 104],
        'close': [102, 101, 103, 104, 105],
        'high': [103, 103, 104, 105, 106],
        'low': [99, 100, 100, 102, 103],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)
    print(f"  连续涨停: {result['continuous_limit_up']}次")
    print(f"  连续跌停: {result['continuous_limit_down']}次")
    print(f"  ⚠️  预警: {result['warning']}")


def demo_complete_workflow():
    """演示完整交易流程"""
    print_separator("演示8: 完整交易流程")

    risk_mgr = RiskManager(total_capital=1_000_000)

    print("\n=== 第1天: 建仓 ===")

    # 建仓前检查
    position_ok = risk_mgr.check_position_limit('600519', '贵州茅台', '白酒', 150_000)
    trade_ok = risk_mgr.check_trade_restrictions('600519', '贵州茅台')

    if position_ok['allowed'] and trade_ok['allowed']:
        risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())
        print("✅ 建仓成功: 100股 @ 1500元")

        position = risk_mgr.get_position('600519')
        print(f"止损价: {position['stop_loss_price']:.2f}元")
        print(f"止盈价: {position['take_profit_price']:.2f}元")

    print("\n=== 第5天: 监控 ===")

    # 更新价格
    current_price = 1380  # 下跌8.2%
    risk_mgr.update_position('600519', current_price)

    position = risk_mgr.get_position('600519')
    print(f"当前价格: {current_price}元")
    print(f"浮动盈亏: {position['unrealized_pnl']:,.0f}元")

    # 检查止损
    if current_price <= position['stop_loss_price']:
        print(f"⚠️  触发止损! ({position['stop_loss_price']:.2f}元)")
        pnl = risk_mgr.remove_position('600519', current_price, datetime.now())
        print(f"❌ 止损平仓，亏损: {pnl:,.0f}元")
    else:
        print("✅ 未触发止损")

    print("\n=== 第10天: 止盈 ===")

    # 重新建仓演示止盈
    risk_mgr2 = RiskManager(total_capital=1_000_000)
    risk_mgr2.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())

    # 价格上涨到止盈位
    current_price = 1725  # 上涨15%
    risk_mgr2.update_position('600519', current_price)

    position = risk_mgr2.get_position('600519')
    print(f"当前价格: {current_price}元")
    print(f"浮动盈亏: {position['unrealized_pnl']:,.0f}元")

    # 检查止盈
    if current_price >= position['take_profit_price']:
        print(f"✅ 触发止盈! ({position['take_profit_price']:.2f}元)")
        pnl = risk_mgr2.remove_position('600519', current_price, datetime.now())
        print(f"✅ 止盈平仓，盈利: {pnl:,.0f}元")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" 风险管理器演示脚本")
    print(" A股量化交易系统 - RiskManager")
    print("=" * 60)

    demos = [
        ("基本使用流程", demo_basic_usage),
        ("仓位限制检查", demo_position_limits),
        ("交易限制检查", demo_trade_restrictions),
        ("止损止盈计算", demo_stop_loss_take_profit),
        ("持仓管理", demo_position_management),
        ("风险评估", demo_risk_assessment),
        ("连续涨跌停检查", demo_continuous_limit),
        ("完整交易流程", demo_complete_workflow),
    ]

    for i, (title, demo_func) in enumerate(demos, 1):
        print(f"\n运行演示 {i}/{len(demos)}: {title}")
        input("按Enter继续...")
        demo_func()

    print_separator("演示完成")
    print("\n所有演示已完成！")
    print("\n相关文档:")
    print("  - 使用指南: docs/risk_manager_guide.md")
    print("  - 测试文件: tests/risk/test_risk_manager.py")
    print("  - 配置文件: config/risk_rules.yaml")


if __name__ == "__main__":
    main()
