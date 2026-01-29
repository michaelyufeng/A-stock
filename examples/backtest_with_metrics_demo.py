"""
回测指标计算演示

展示如何使用 BacktestMetrics 进行详细的性能分析
"""
import pandas as pd
import numpy as np
from datetime import datetime
from src.backtest import BacktestEngine, BacktestMetrics
from src.strategy.base_strategy import BaseStrategy
from src.core.constants import SignalType


class DemoStrategy(BaseStrategy):
    """演示策略 - 简单的动量策略"""

    def __init__(self):
        self.strategy_name = 'demo_momentum'
        self.params = {
            'stop_loss': 0.05,
            'take_profit': 0.10,
            'max_holding_days': 10
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号

        简单规则：
        - 5日均线上穿10日均线 -> 买入
        - 5日均线下穿10日均线 -> 卖出
        """
        df = df.copy()

        # 计算均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()

        # 初始化信号
        df['signal'] = SignalType.HOLD.value

        # 生成信号
        for i in range(1, len(df)):
            # 金叉 - 买入
            if df['ma5'].iloc[i] > df['ma10'].iloc[i] and df['ma5'].iloc[i-1] <= df['ma10'].iloc[i-1]:
                df.loc[df.index[i], 'signal'] = SignalType.BUY.value
            # 死叉 - 卖出
            elif df['ma5'].iloc[i] < df['ma10'].iloc[i] and df['ma5'].iloc[i-1] >= df['ma10'].iloc[i-1]:
                df.loc[df.index[i], 'signal'] = SignalType.SELL.value

        return df


def create_sample_data(days: int = 252) -> pd.DataFrame:
    """创建模拟数据"""
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

    # 生成有趋势的价格数据
    np.random.seed(42)
    trend = np.linspace(0, 10, days)
    noise = np.random.randn(days) * 2
    close_prices = 50 + trend + noise.cumsum()

    df = pd.DataFrame({
        'date': dates,
        'open': close_prices + np.random.randn(days) * 0.5,
        'high': close_prices + np.abs(np.random.randn(days) * 1.5),
        'low': close_prices - np.abs(np.random.randn(days) * 1.5),
        'close': close_prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })

    return df


def main():
    """主函数"""
    print("=" * 80)
    print("回测指标计算演示")
    print("=" * 80)

    # 1. 创建模拟数据
    print("\n1. 创建模拟数据（252个交易日）...")
    data = create_sample_data(days=252)
    print(f"   数据量: {len(data)} 行")
    print(f"   日期范围: {data['date'].min()} 至 {data['date'].max()}")

    # 2. 创建回测引擎
    print("\n2. 创建回测引擎...")
    engine = BacktestEngine(
        initial_cash=1000000,  # 100万初始资金
        commission=0.0003,     # 0.03% 佣金
        stamp_tax=0.001        # 0.1% 印花税
    )

    # 3. 运行回测
    print("\n3. 运行回测...")
    results = engine.run_backtest(
        strategy_class=DemoStrategy,
        data=data,
        stock_code='600000'  # 浦发银行（主板，10%涨跌停）
    )

    # 4. 查看详细指标
    print("\n4. 详细指标分析:")
    print("-" * 80)

    if 'metrics' in results and results['metrics']:
        metrics = results['metrics']

        print("\n收益指标:")
        print(f"  总收益率: {metrics['total_return']:.2%}")
        print(f"  年化收益率: {metrics['annual_return']:.2%}")

        print("\n风险指标:")
        print(f"  最大回撤: {metrics['max_drawdown']['drawdown_pct']:.2%}")
        print(f"  波动率: {metrics['volatility']:.2%}")
        print(f"  夏普比率: {metrics['sharpe_ratio']:.4f}")
        print(f"  索提诺比率: {metrics['sortino_ratio']:.4f}")
        print(f"  Calmar比率: {metrics['calmar_ratio']:.4f}")

        print("\n交易指标:")
        print(f"  总交易次数: {metrics['total_trades']}")
        print(f"  胜率: {metrics['win_rate']:.2%}")
        print(f"  盈亏比: {metrics['profit_loss_ratio']:.2f}")
        print(f"  平均持仓天数: {metrics['avg_holding_days']:.1f}")
        print(f"  最大连胜: {metrics['max_consecutive_wins']} 次")
        print(f"  最大连亏: {metrics['max_consecutive_losses']} 次")

        print("\nA股特色指标:")
        print(f"  总费用: ¥{metrics['total_fees']:,.2f}")
        print(f"  费用占比: {metrics['fee_percentage']:.2%}")

    # 5. 交易明细
    if 'trades' in results and len(results['trades']) > 0:
        print("\n5. 交易明细（前5笔）:")
        print("-" * 80)
        trades_df = pd.DataFrame(results['trades'])
        print(trades_df.head().to_string())

    print("\n" + "=" * 80)
    print("演示完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
