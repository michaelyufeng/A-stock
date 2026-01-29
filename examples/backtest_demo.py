"""
回测引擎演示脚本

展示如何使用BacktestEngine进行策略回测
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, '/Users/zhuyufeng/Documents/A-stock')

from src.backtest.engine import BacktestEngine
from src.strategy.short_term.momentum import MomentumStrategy
from src.core.logger import get_logger

logger = get_logger(__name__)


def create_sample_data(days=252, start_price=100):
    """
    创建模拟的K线数据

    Args:
        days: 天数
        start_price: 起始价格

    Returns:
        DataFrame: 模拟的K线数据
    """
    logger.info(f"创建 {days} 天的模拟数据...")

    # 生成日期序列
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # 生成带趋势的价格数据
    np.random.seed(42)

    # 价格趋势（上涨）
    trend = np.linspace(0, 20, days)

    # 随机波动
    noise = np.random.randn(days) * 2

    # 合成收盘价
    close = start_price + trend + np.cumsum(noise)

    # 生成OHLC数据
    df = pd.DataFrame({
        'date': dates,
        'open': close + np.random.randn(days) * 0.5,
        'high': close + np.abs(np.random.randn(days) * 1.5),
        'low': close - np.abs(np.random.randn(days) * 1.5),
        'close': close,
        'volume': np.random.randint(10000000, 50000000, days)
    })

    logger.info(f"数据创建完成 - 价格范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")

    return df


def main():
    """主函数"""
    logger.info("=" * 70)
    logger.info("回测引擎演示")
    logger.info("=" * 70)

    # 1. 创建模拟数据
    data = create_sample_data(days=252, start_price=100)

    # 2. 创建回测引擎
    logger.info("\n创建回测引擎...")
    engine = BacktestEngine(
        initial_cash=1_000_000,  # 100万初始资金
        commission=0.0003,        # 0.03%佣金
        stamp_tax=0.001          # 0.1%印花税
    )

    # 3. 运行回测
    logger.info("\n使用动量策略进行回测...")
    try:
        results = engine.run_backtest(
            strategy_class=MomentumStrategy,
            data=data
        )

        # 4. 打印结果
        logger.info("\n" + "=" * 70)
        logger.info("回测结果详情")
        logger.info("=" * 70)

        print(f"\n初始资金: ¥{results['initial_value']:,.2f}")
        print(f"最终资金: ¥{results['final_value']:,.2f}")
        print(f"盈亏金额: ¥{results['final_value'] - results['initial_value']:,.2f}")
        print(f"总收益率: {results['total_return']:.2%}")
        print(f"夏普比率: {results['sharpe_ratio']:.4f}")
        print(f"最大回撤: {results['max_drawdown']:.2%}")
        print(f"总交易次数: {results['total_trades']}")
        print(f"胜率: {results['win_rate']:.2%}")

        # 5. 评估结果
        logger.info("\n" + "=" * 70)
        logger.info("策略评估")
        logger.info("=" * 70)

        if results['total_return'] > 0:
            print("✓ 策略盈利")
        else:
            print("✗ 策略亏损")

        if results['sharpe_ratio'] > 1:
            print("✓ 夏普比率优秀（>1）")
        elif results['sharpe_ratio'] > 0.5:
            print("○ 夏普比率一般（0.5-1）")
        else:
            print("✗ 夏普比率较差（<0.5）")

        if results['max_drawdown'] < 0.1:
            print("✓ 最大回撤较小（<10%）")
        elif results['max_drawdown'] < 0.2:
            print("○ 最大回撤适中（10%-20%）")
        else:
            print("✗ 最大回撤较大（>20%）")

        logger.info("\n回测演示完成!")

    except Exception as e:
        logger.error(f"回测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
