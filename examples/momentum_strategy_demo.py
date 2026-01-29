"""动量策略使用示例"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategy.short_term.momentum import MomentumStrategy
from src.core.constants import SignalType


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """
    创建模拟K线数据

    Args:
        days: 数据天数

    Returns:
        包含K线数据的DataFrame
    """
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')

    # 创建一个有趋势的价格序列
    base_price = 10.0
    trend = np.linspace(0, 5, days)  # 上涨趋势
    noise = np.random.normal(0, 0.3, days)  # 随机噪声
    close_prices = base_price + trend + noise

    data = {
        'date': dates,
        'open': close_prices * 0.99,
        'high': close_prices * 1.02,
        'low': close_prices * 0.98,
        'close': close_prices,
        'volume': np.random.uniform(1000000, 5000000, days),
    }

    return pd.DataFrame(data)


def main():
    """主函数"""
    print("=" * 60)
    print("动量策略 (MomentumStrategy) 示例")
    print("=" * 60)

    # 1. 创建策略实例
    print("\n1. 初始化策略...")
    strategy = MomentumStrategy()
    print(f"   策略名称: {strategy.strategy_name}")
    print(f"   策略参数:")
    print(f"     - RSI周期: {strategy.get_param('rsi_period')}")
    print(f"     - RSI超卖: {strategy.get_param('rsi_oversold')}")
    print(f"     - RSI超买: {strategy.get_param('rsi_overbought')}")
    print(f"     - 成交量放大倍数: {strategy.get_param('volume_surge_ratio')}")
    print(f"     - 止损: {strategy.get_param('stop_loss') * 100}%")
    print(f"     - 止盈: {strategy.get_param('take_profit') * 100}%")
    print(f"     - 最大持仓天数: {strategy.get_param('max_holding_days')}")

    # 2. 创建模拟数据
    print("\n2. 生成模拟K线数据...")
    df = create_sample_data(days=100)
    print(f"   数据量: {len(df)} 天")
    print(f"   日期范围: {df['date'].min()} 至 {df['date'].max()}")

    # 3. 生成交易信号
    print("\n3. 生成交易信号...")
    result = strategy.generate_signals(df)
    print(f"   信号生成完成")

    # 4. 分析信号
    print("\n4. 信号统计:")
    buy_signals = result[result['signal'] == SignalType.BUY.value]
    sell_signals = result[result['signal'] == SignalType.SELL.value]
    hold_signals = result[result['signal'] == SignalType.HOLD.value]

    print(f"   买入信号: {len(buy_signals)} 次")
    print(f"   卖出信号: {len(sell_signals)} 次")
    print(f"   持有信号: {len(hold_signals)} 次")

    # 5. 展示部分买入信号
    if len(buy_signals) > 0:
        print("\n5. 买入信号示例（前3个）:")
        print("   日期         收盘价    RSI     MACD    成交量")
        print("   " + "-" * 55)
        for idx, row in buy_signals.head(3).iterrows():
            print(f"   {row['date'].strftime('%Y-%m-%d')}  "
                  f"{row['close']:7.2f}  "
                  f"{row['RSI']:6.2f}  "
                  f"{row['MACD']:7.2f}  "
                  f"{row['volume']:,.0f}")

    # 6. 展示部分卖出信号
    if len(sell_signals) > 0:
        print("\n6. 卖出信号示例（前3个）:")
        print("   日期         收盘价    RSI     MACD    成交量")
        print("   " + "-" * 55)
        for idx, row in sell_signals.head(3).iterrows():
            print(f"   {row['date'].strftime('%Y-%m-%d')}  "
                  f"{row['close']:7.2f}  "
                  f"{row['RSI']:6.2f}  "
                  f"{row['MACD']:7.2f}  "
                  f"{row['volume']:,.0f}")

    # 7. 测试止损止盈
    print("\n7. 止损止盈测试:")
    entry_price = 100.0

    # 止损测试
    stop_loss_price = 91.0  # 9% 亏损
    is_stop_loss = strategy.check_stop_loss(entry_price, stop_loss_price)
    print(f"   买入价: {entry_price}, 当前价: {stop_loss_price}")
    print(f"   触发止损: {is_stop_loss}")

    # 止盈测试
    take_profit_price = 116.0  # 16% 盈利
    is_take_profit = strategy.check_take_profit(entry_price, take_profit_price)
    print(f"   买入价: {entry_price}, 当前价: {take_profit_price}")
    print(f"   触发止盈: {is_take_profit}")

    # 8. 测试最大持仓天数
    print("\n8. 最大持仓天数测试:")
    buy_date = datetime(2024, 1, 1)
    current_date = datetime(2024, 1, 12)  # 11天后
    is_max_holding = strategy.check_max_holding_days(buy_date, current_date)
    print(f"   买入日期: {buy_date.date()}, 当前日期: {current_date.date()}")
    print(f"   持仓天数: {(current_date - buy_date).days} 天")
    print(f"   超过最大持仓天数: {is_max_holding}")

    # 9. 测试T+1规则
    print("\n9. T+1交易规则测试:")
    buy_date = datetime(2024, 1, 1)
    same_day = datetime(2024, 1, 1)
    next_day = datetime(2024, 1, 2)

    can_sell_same_day = strategy.can_sell_today(buy_date, same_day)
    can_sell_next_day = strategy.can_sell_today(buy_date, next_day)

    print(f"   买入日期: {buy_date.date()}")
    print(f"   当天可以卖出: {can_sell_same_day}")
    print(f"   次日可以卖出: {can_sell_next_day}")

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
