"""A股Broker使用示例 - 演示涨跌停限制和交易规则"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtest.engine import BacktestEngine
from src.strategy.short_term.momentum import MomentumStrategy
from src.core.logger import get_logger

logger = get_logger(__name__)


def create_test_data(stock_code: str = '600000') -> pd.DataFrame:
    """
    创建测试数据（模拟涨跌停场景）

    Args:
        stock_code: 股票代码

    Returns:
        测试数据DataFrame
    """
    logger.info(f"创建测试数据: {stock_code}")

    # 生成日期范围
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(20)]

    # 创建价格数据（包含涨停和跌停场景）
    base_price = 10.0
    data = []

    for i, date in enumerate(dates):
        if i == 0:
            # 第一天：正常
            open_price = base_price
            close = base_price
            high = base_price * 1.02
            low = base_price * 0.98
        elif i == 1:
            # 第二天：涨停（+10%）
            prev_close = data[-1]['close']
            close = prev_close * 1.10
            open_price = close
            high = close
            low = close
        elif i == 2:
            # 第三天：继续涨停
            prev_close = data[-1]['close']
            close = prev_close * 1.10
            open_price = close
            high = close
            low = close
        elif i == 5:
            # 第六天：跌停（-10%）
            prev_close = data[-1]['close']
            close = prev_close * 0.90
            open_price = close
            high = close
            low = close
        else:
            # 其他天：正常波动
            prev_close = data[-1]['close']
            change = np.random.uniform(-0.03, 0.03)
            close = prev_close * (1 + change)
            open_price = close * (1 + np.random.uniform(-0.01, 0.01))
            high = close * (1 + np.random.uniform(0, 0.02))
            low = close * (1 - np.random.uniform(0, 0.02))

        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(1000000, 10000000)
        })

    df = pd.DataFrame(data)
    logger.info(f"测试数据创建完成，共 {len(df)} 条")
    return df


def demo_main_board():
    """演示主板（10%涨跌停）"""
    logger.info("=" * 60)
    logger.info("演示：主板股票（600000）- 10%涨跌停限制")
    logger.info("=" * 60)

    # 创建测试数据
    data = create_test_data(stock_code='600000')

    # 创建回测引擎
    engine = BacktestEngine(initial_cash=100000)

    # 运行回测（传入stock_code以启用涨跌停限制）
    results = engine.run_backtest(
        strategy_class=MomentumStrategy,
        data=data,
        stock_code='600000'  # 主板股票
    )

    # 打印结果
    logger.info("\n回测结果:")
    logger.info(f"初始资金: {results['initial_value']:,.2f}")
    logger.info(f"最终资金: {results['final_value']:,.2f}")
    logger.info(f"总收益率: {results['total_return']:.2%}")
    logger.info(f"总交易次数: {results['total_trades']}")

    return results


def demo_star_market():
    """演示科创板（20%涨跌停）"""
    logger.info("\n" + "=" * 60)
    logger.info("演示：科创板股票（688001）- 20%涨跌停限制")
    logger.info("=" * 60)

    # 创建测试数据
    data = create_test_data(stock_code='688001')

    # 创建回测引擎
    engine = BacktestEngine(initial_cash=100000)

    # 运行回测
    results = engine.run_backtest(
        strategy_class=MomentumStrategy,
        data=data,
        stock_code='688001'  # 科创板股票
    )

    # 打印结果
    logger.info("\n回测结果:")
    logger.info(f"初始资金: {results['initial_value']:,.2f}")
    logger.info(f"最终资金: {results['final_value']:,.2f}")
    logger.info(f"总收益率: {results['total_return']:.2%}")
    logger.info(f"总交易次数: {results['total_trades']}")

    return results


def demo_gem_board():
    """演示创业板（20%涨跌停）"""
    logger.info("\n" + "=" * 60)
    logger.info("演示：创业板股票（300750）- 20%涨跌停限制")
    logger.info("=" * 60)

    # 创建测试数据
    data = create_test_data(stock_code='300750')

    # 创建回测引擎
    engine = BacktestEngine(initial_cash=100000)

    # 运行回测
    results = engine.run_backtest(
        strategy_class=MomentumStrategy,
        data=data,
        stock_code='300750'  # 创业板股票
    )

    # 打印结果
    logger.info("\n回测结果:")
    logger.info(f"初始资金: {results['initial_value']:,.2f}")
    logger.info(f"最终资金: {results['final_value']:,.2f}")
    logger.info(f"总收益率: {results['total_return']:.2%}")
    logger.info(f"总交易次数: {results['total_trades']}")

    return results


if __name__ == '__main__':
    logger.info("A股Broker演示程序")
    logger.info("展示不同板块的涨跌停限制和交易规则")
    logger.info("")

    # 演示主板
    demo_main_board()

    # 演示科创板
    demo_star_market()

    # 演示创业板
    demo_gem_board()

    logger.info("\n" + "=" * 60)
    logger.info("演示完成！")
    logger.info("=" * 60)
