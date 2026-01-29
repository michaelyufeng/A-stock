"""选股筛选器使用示例 - 展示过滤器功能

本示例展示如何使用5种预设策略进行股票筛选，
每种策略都会应用特定的过滤条件来筛选符合标准的股票。
"""
from src.screening.screener import StockScreener
from src.screening import filters
import pandas as pd


def demo_low_pe_value_screening():
    """示例1: 低PE价值股筛选

    筛选标准：
    - PE < 15
    - ROE > 10%

    适合：价值投资者，寻找被低估的优质公司
    """
    print("\n" + "=" * 60)
    print("示例1: 低PE价值股筛选")
    print("=" * 60)

    screener = StockScreener()

    # 使用预设策略
    results = screener.screen(
        stock_pool=['600519', '000001', '600036'],  # 示例股票池
        preset='low_pe_value',
        top_n=10,
        min_score=60,
        parallel=False
    )

    print(f"\n找到 {len(results)} 只符合条件的股票：")
    if len(results) > 0:
        print(results[['code', 'name', 'score', 'reason']])


def demo_high_dividend_screening():
    """示例2: 高股息率筛选

    筛选标准：
    - 股息率 >= 3%

    适合：追求稳定现金流的投资者
    """
    print("\n" + "=" * 60)
    print("示例2: 高股息率筛选")
    print("=" * 60)

    screener = StockScreener()

    results = screener.screen(
        stock_pool=['600519', '601318', '600036'],
        preset='high_dividend',
        top_n=10,
        min_score=60,
        parallel=False
    )

    print(f"\n找到 {len(results)} 只高股息股票：")
    if len(results) > 0:
        print(results[['code', 'name', 'score', 'reason']])


def demo_breakout_screening():
    """示例3: 突破新高筛选

    筛选标准：
    - 价格突破20日新高
    - 成交量放大 > 1.2倍

    适合：趋势跟踪策略，追涨强势股
    """
    print("\n" + "=" * 60)
    print("示例3: 突破新高筛选")
    print("=" * 60)

    screener = StockScreener()

    results = screener.screen(
        stock_pool=['600519', '000001'],
        preset='breakout',
        top_n=10,
        min_score=60,
        parallel=False
    )

    print(f"\n找到 {len(results)} 只突破新高的股票：")
    if len(results) > 0:
        print(results[['code', 'name', 'score', 'reason']])


def demo_oversold_rebound_screening():
    """示例4: 超卖反弹筛选

    筛选标准：
    - 曾经RSI < 30（超卖）
    - 当前RSI >= 30（反弹）

    适合：短期交易，捕捉超跌反弹机会
    """
    print("\n" + "=" * 60)
    print("示例4: 超卖反弹筛选")
    print("=" * 60)

    screener = StockScreener()

    results = screener.screen(
        stock_pool=['600519', '000001'],
        preset='oversold_rebound',
        top_n=10,
        min_score=60,
        parallel=False
    )

    print(f"\n找到 {len(results)} 只超卖反弹的股票：")
    if len(results) > 0:
        print(results[['code', 'name', 'score', 'reason']])


def demo_institutional_favorite_screening():
    """示例5: 机构重仓筛选

    筛选标准：
    - 机构持仓比例 >= 30%

    适合：跟随机构策略，寻找机构青睐的高质量标的
    """
    print("\n" + "=" * 60)
    print("示例5: 机构重仓筛选")
    print("=" * 60)

    screener = StockScreener()

    results = screener.screen(
        stock_pool=['600519', '601318', '600036'],
        preset='institutional_favorite',
        top_n=10,
        min_score=60,
        parallel=False
    )

    print(f"\n找到 {len(results)} 只机构重仓股票：")
    if len(results) > 0:
        print(results[['code', 'name', 'score', 'reason']])


def demo_direct_filter_usage():
    """示例6: 直接使用过滤器函数

    展示如何直接使用filters模块中的函数进行自定义筛选
    """
    print("\n" + "=" * 60)
    print("示例6: 直接使用过滤器函数")
    print("=" * 60)

    # 创建示例数据
    stock_data = pd.DataFrame({
        '代码': ['000001', '000002', '000003', '000004'],
        '名称': ['平安银行', '万科A', '中国平安', '招商银行'],
        'PE': [8.5, 18.0, 12.0, 10.5],
        'ROE': [12.0, 8.0, 15.0, 14.0],
        '股息率': [4.5, 2.0, 3.5, 3.8],
        '机构持仓比例': [35.0, 20.0, 40.0, 32.0]
    })

    print("\n原始股票池：")
    print(stock_data[['代码', '名称', 'PE', 'ROE', '股息率']])

    # 使用PE/ROE过滤器
    print("\n应用过滤器: PE < 15 且 ROE > 10%")
    filtered = filters.filter_by_pe_roe(stock_data, pe_max=15.0, roe_min=10.0)
    print(f"结果: {len(filtered)} 只股票")
    print(filtered[['代码', '名称', 'PE', 'ROE']])

    # 链式过滤：先过滤PE/ROE，再过滤股息率
    print("\n链式过滤: PE < 15 且 ROE > 10% 且 股息率 >= 3.5%")
    filtered = filters.filter_by_pe_roe(stock_data, pe_max=15.0, roe_min=10.0)
    filtered = filters.filter_by_dividend_yield(filtered, yield_min=3.5)
    print(f"结果: {len(filtered)} 只股票")
    print(filtered[['代码', '名称', 'PE', 'ROE', '股息率']])


def demo_custom_filter_config():
    """示例7: 使用apply_filters统一接口

    展示如何使用apply_filters函数应用多个过滤条件
    """
    print("\n" + "=" * 60)
    print("示例7: 使用apply_filters统一接口")
    print("=" * 60)

    # 创建示例数据
    stock_data = pd.DataFrame({
        '代码': ['000001', '000002', '000003'],
        'PE': [8.5, 18.0, 12.0],
        'ROE': [12.0, 8.0, 15.0],
        '股息率': [4.5, 2.0, 3.5]
    })

    print("\n原始股票池：")
    print(stock_data)

    # 定义过滤配置
    filter_config = {
        'pe_max': 15.0,
        'roe_min': 10.0,
        'dividend_yield_min': 3.0
    }

    print(f"\n过滤配置: {filter_config}")

    # 应用过滤
    filtered = filters.apply_filters(stock_data, filter_config)

    print(f"\n结果: {len(filtered)} 只股票")
    print(filtered)


if __name__ == '__main__':
    print("=" * 60)
    print("股票筛选器 - 过滤器功能示例")
    print("=" * 60)
    print("\n本示例展示如何使用5种预设筛选策略和自定义过滤器")
    print("\n注意：实际运行需要网络连接以获取AKShare数据")
    print("=" * 60)

    # 演示直接使用过滤器（不需要网络）
    demo_direct_filter_usage()
    demo_custom_filter_config()

    # 以下示例需要网络连接和真实数据
    print("\n\n" + "=" * 60)
    print("以下示例需要网络连接，已注释掉")
    print("如需运行，请取消注释")
    print("=" * 60)

    # demo_low_pe_value_screening()
    # demo_high_dividend_screening()
    # demo_breakout_screening()
    # demo_oversold_rebound_screening()
    # demo_institutional_favorite_screening()
