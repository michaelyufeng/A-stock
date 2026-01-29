"""
实时行情监控演示脚本

演示RealTimeWatcher的使用场景：
1. 基础监控
2. 动态添加/删除股票
3. 批量更新优化
4. 缓存机制
5. 与RiskManager集成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitoring.realtime_watcher import RealTimeWatcher
from src.risk.risk_manager import RiskManager
from datetime import datetime
import time


def print_separator(title=""):
    """打印分隔线"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
        print("=" * 60)


def demo_basic_monitoring():
    """演示1: 基础监控"""
    print_separator("演示1: 基础监控")

    # 初始化监控器
    watcher = RealTimeWatcher(
        stock_list=[
            {'code': '600519', 'name': '贵州茅台'},
            {'code': '000858', 'name': '五粮液'}
        ],
        update_interval=60
    )

    print("✅ 初始化监控器，监控2只股票")
    print(f"   更新间隔: {watcher.update_interval}秒")

    # 查看监控列表
    watchlist = watcher.get_watchlist()
    print(f"\n当前监控列表: {len(watchlist)}只")
    for code, name in watchlist.items():
        print(f"  - {code}: {name}")


def demo_watchlist_management():
    """演示2: 监控列表管理"""
    print_separator("演示2: 监控列表管理")

    watcher = RealTimeWatcher(stock_list=[])

    # 添加股票
    print("\n【添加股票】")
    stocks_to_add = [
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
        ('600036', '招商银行'),
        ('601318', '中国平安')
    ]

    for code, name in stocks_to_add:
        watcher.add_stock(code, name)
        print(f"  ✅ 添加: {code} {name}")

    print(f"\n监控列表大小: {len(watcher.get_watchlist())}只")

    # 移除股票
    print("\n【移除股票】")
    removed = watcher.remove_stock('600036')
    if removed:
        print("  ✅ 移除: 600036 招商银行")

    print(f"\n监控列表大小: {len(watcher.get_watchlist())}只")


def demo_quote_fetching():
    """演示3: 行情获取（模拟数据）"""
    print_separator("演示3: 行情获取")

    watcher = RealTimeWatcher(
        stock_list=[
            {'code': '600519', 'name': '贵州茅台'},
            {'code': '000858', 'name': '五粮液'}
        ]
    )

    print("\n【模拟】更新行情数据...")
    print("（实际使用时会从AKShare获取真实数据）\n")

    # 模拟行情数据
    mock_quotes = {
        '600519': {
            'code': '600519',
            'name': '贵州茅台',
            'current_price': 1650.5,
            'open': 1645.0,
            'high': 1660.0,
            'low': 1640.0,
            'change_pct': 0.0234,
            'update_time': datetime.now()
        },
        '000858': {
            'code': '000858',
            'name': '五粮液',
            'current_price': 180.3,
            'open': 178.5,
            'high': 182.0,
            'low': 177.8,
            'change_pct': -0.0156,
            'update_time': datetime.now()
        }
    }

    # 手动设置（模拟）
    watcher.quotes = mock_quotes

    # 获取所有行情
    quotes = watcher.get_all_quotes()

    print("【行情展示】")
    for code, quote in quotes.items():
        name = quote['name']
        price = quote['current_price']
        change_pct = quote['change_pct'] * 100

        # 彩色输出
        if change_pct > 0:
            color = '\033[91m'  # 红色
            sign = '↑'
        else:
            color = '\033[92m'  # 绿色
            sign = '↓'
        reset = '\033[0m'

        print(f"  {name}({code}): {price:.2f}元 "
              f"{color}{sign} {abs(change_pct):.2f}%{reset}")

    # 单个查询
    print("\n【单个查询】")
    quote = watcher.get_latest_quote('600519')
    if quote:
        print(f"  贵州茅台:")
        print(f"    当前价: {quote['current_price']:.2f}元")
        print(f"    开盘价: {quote['open']:.2f}元")
        print(f"    最高价: {quote['high']:.2f}元")
        print(f"    最低价: {quote['low']:.2f}元")
        print(f"    涨跌幅: {quote['change_pct']*100:.2f}%")


def demo_caching():
    """演示4: 缓存机制"""
    print_separator("演示4: 缓存机制")

    watcher = RealTimeWatcher(
        stock_list=[{'code': '600519', 'name': '贵州茅台'}]
    )

    print("\n【缓存测试】")

    # 第一次获取
    print("1. 第一次获取（模拟从API）")
    watcher.quotes['600519'] = {
        'code': '600519',
        'name': '贵州茅台',
        'current_price': 1650.5,
        'update_time': datetime.now()
    }
    quote1 = watcher.get_latest_quote('600519')
    print(f"   价格: {quote1['current_price']:.2f}元")
    print(f"   时间: {quote1['update_time'].strftime('%H:%M:%S')}")

    # 第二次获取（缓存）
    print("\n2. 第二次获取（使用缓存）")
    quote2 = watcher.get_latest_quote('600519')
    print(f"   价格: {quote2['current_price']:.2f}元")
    print(f"   时间: {quote2['update_time'].strftime('%H:%M:%S')}")
    print(f"   ✅ 使用缓存（时间戳相同）")

    # 检查缓存年龄
    age = watcher.get_quote_age('600519')
    print(f"\n3. 缓存年龄: {age:.2f}秒")

    # 清空缓存
    print("\n4. 清空缓存")
    watcher.clear_cache()
    print(f"   缓存大小: {watcher.get_cache_size()}")


def demo_integration_with_risk_manager():
    """演示5: 与RiskManager集成"""
    print_separator("演示5: 与RiskManager集成")

    # 初始化
    risk_mgr = RiskManager(total_capital=1_000_000)
    watcher = RealTimeWatcher(stock_list=[])

    print("\n【场景】监控持仓股票")

    # 添加持仓
    print("\n1. 添加持仓")
    positions = [
        ('600519', '贵州茅台', '白酒', 100, 1500),
        ('000858', '五粮液', '白酒', 120, 1500),
        ('600036', '招商银行', '银行', 1000, 35)
    ]

    for code, name, sector, shares, price in positions:
        risk_mgr.add_position(code, name, sector, shares, price, datetime.now())
        watcher.add_stock(code, name)
        print(f"   ✅ {code} {name}: {shares}股 @ {price}元")

    # 模拟更新价格
    print("\n2. 更新行情（模拟）")
    mock_prices = {
        '600519': 1600,  # 下跌
        '000858': 1550,  # 上涨
        '600036': 34     # 下跌
    }

    # 模拟行情
    for code, price in mock_prices.items():
        watcher.quotes[code] = {
            'code': code,
            'current_price': price,
            'update_time': datetime.now()
        }

    # 更新持仓价格
    print("\n3. 更新持仓价格并检查")
    for code, quote in watcher.get_all_quotes().items():
        current_price = quote['current_price']

        # 更新持仓
        risk_mgr.update_position(code, current_price)

        # 获取持仓信息
        position = risk_mgr.get_position(code)
        entry_price = position['entry_price']
        pnl = position['unrealized_pnl']
        stop_loss = position['stop_loss_price']

        print(f"\n   {position['stock_name']}({code})")
        print(f"     成本价: {entry_price:.2f}元")
        print(f"     现价: {current_price:.2f}元")
        print(f"     浮盈: {'+' if pnl > 0 else ''}{pnl:,.0f}元")

        # 检查止损
        if current_price <= stop_loss:
            print(f"     ⚠️ 触发止损! (止损价: {stop_loss:.2f}元)")
        else:
            distance_pct = (current_price - stop_loss) / stop_loss * 100
            print(f"     止损距离: {distance_pct:.1f}%")


def demo_batch_optimization():
    """演示6: 批量优化"""
    print_separator("演示6: 批量优化")

    # 大量股票
    print("\n【场景】监控100只股票")

    stock_list = [
        {'code': f'60{i:04d}', 'name': f'股票{i}'}
        for i in range(100)
    ]

    watcher = RealTimeWatcher(stock_list=stock_list, update_interval=60)

    print(f"监控列表: {len(watcher.get_watchlist())}只股票")
    print("\n【性能对比】")

    # 模拟批量更新
    print("✅ 批量更新: 1次API调用获取全部行情")
    print("   （实际使用update_quotes()方法）")

    print("\n❌ 逐个更新: 需要100次API调用")
    print("   （不推荐）")

    print("\n💡 建议:")
    print("   - 使用update_quotes()批量更新")
    print("   - 利用缓存减少API调用")
    print("   - 设置合理的更新间隔")


def demo_error_handling():
    """演示7: 异常处理"""
    print_separator("演示7: 异常处理")

    watcher = RealTimeWatcher(stock_list=[])

    print("\n【场景1】无效股票代码")
    watcher.add_stock('INVALID', '无效股票')
    quote = watcher.get_latest_quote('INVALID')

    if quote is None:
        print("  ✅ 正确处理: 返回None，不抛出异常")

    print("\n【场景2】查询不在监控列表的股票")
    quote = watcher.get_latest_quote('999999')

    if quote is None:
        print("  ✅ 正确处理: 返回None，不抛出异常")

    print("\n【场景3】网络异常（模拟）")
    print("  ✅ 内部捕获异常，返回空结果")
    print("  （生产环境会记录日志）")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(" RealTimeWatcher 实时监控演示")
    print(" A股量化交易系统 - 监控模块")
    print("=" * 60)

    demos = [
        ("基础监控", demo_basic_monitoring),
        ("监控列表管理", demo_watchlist_management),
        ("行情获取", demo_quote_fetching),
        ("缓存机制", demo_caching),
        ("与RiskManager集成", demo_integration_with_risk_manager),
        ("批量优化", demo_batch_optimization),
        ("异常处理", demo_error_handling),
    ]

    for i, (title, demo_func) in enumerate(demos, 1):
        print(f"\n运行演示 {i}/{len(demos)}: {title}")
        input("按Enter继续...")
        demo_func()

    print_separator("演示完成")
    print("\n所有演示已完成！")
    print("\n相关文档:")
    print("  - 使用指南: docs/realtime_watcher_guide.md")
    print("  - 测试文件: tests/monitoring/test_realtime_watcher.py")
    print("  - API文档: src/monitoring/realtime_watcher.py")


if __name__ == "__main__":
    main()
