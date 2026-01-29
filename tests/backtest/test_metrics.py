"""回测指标计算测试"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.backtest.metrics import BacktestMetrics


class TestBacktestMetrics(unittest.TestCase):
    """回测指标计算测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建模拟的每日资产价值数据（100天，初始10万，最终12万）
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        # 模拟一个有波动的上涨曲线
        np.random.seed(42)
        values = 100000 + np.cumsum(np.random.randn(100) * 1000 + 200)

        self.portfolio_values = pd.Series(values, index=dates)
        self.initial_capital = 100000

        # 创建模拟的交易记录
        self.trades = [
            {
                'entry_date': '2024-01-05',
                'exit_date': '2024-01-15',
                'entry_price': 10.0,
                'exit_price': 11.0,
                'size': 1000,
                'pnl': 800,  # 1000 - 佣金和印花税
                'commission': 200,
                'status': 'closed'
            },
            {
                'entry_date': '2024-01-20',
                'exit_date': '2024-01-30',
                'entry_price': 12.0,
                'exit_price': 11.5,
                'size': 1000,
                'pnl': -600,  # -500 - 佣金和印花税
                'commission': 100,
                'status': 'closed'
            },
            {
                'entry_date': '2024-02-01',
                'exit_date': '2024-02-10',
                'entry_price': 11.0,
                'exit_price': 12.5,
                'size': 1000,
                'pnl': 1300,
                'commission': 200,
                'status': 'closed'
            },
            {
                'entry_date': '2024-02-15',
                'exit_date': '2024-02-25',
                'entry_price': 13.0,
                'exit_price': 14.5,
                'size': 1000,
                'pnl': 1200,
                'commission': 300,
                'status': 'closed'
            },
        ]

    def test_01_initialization(self):
        """测试1: 初始化测试"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        self.assertEqual(metrics.initial_capital, 100000)
        self.assertEqual(len(metrics.portfolio_values), 100)
        self.assertEqual(len(metrics.trades), 4)
        self.assertIsNotNone(metrics.final_capital)

    def test_02_calculate_total_return(self):
        """测试2: 总收益率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        total_return = metrics.calculate_total_return()

        # 验证收益率是浮点数
        self.assertIsInstance(total_return, float)

        # 验证公式正确性
        expected_return = (metrics.final_capital - self.initial_capital) / self.initial_capital
        self.assertAlmostEqual(total_return, expected_return, places=6)

    def test_03_calculate_annual_return(self):
        """测试3: 年化收益率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        annual_return = metrics.calculate_annual_return()

        # 验证是浮点数
        self.assertIsInstance(annual_return, float)

        # 年化收益应该与总收益相关
        total_return = metrics.calculate_total_return()
        days = (self.portfolio_values.index[-1] - self.portfolio_values.index[0]).days
        years = days / 365.0
        expected_annual = (1 + total_return) ** (1 / years) - 1

        self.assertAlmostEqual(annual_return, expected_annual, places=6)

    def test_04_calculate_monthly_returns(self):
        """测试4: 月度收益率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        monthly_returns = metrics.calculate_monthly_returns()

        # 验证返回Series
        self.assertIsInstance(monthly_returns, pd.Series)

        # 验证有月度数据
        self.assertGreater(len(monthly_returns), 0)

        # 验证每个值都是浮点数
        for ret in monthly_returns:
            self.assertIsInstance(ret, (float, np.floating))

    def test_05_calculate_max_drawdown(self):
        """测试5: 最大回撤计算"""
        # 创建一个有明显回撤的曲线
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        values = pd.Series([100000, 110000, 105000, 102000, 98000, 103000, 108000, 106000, 111000, 115000], index=dates)

        metrics = BacktestMetrics(
            portfolio_values=values,
            trades=[],
            initial_capital=100000
        )

        max_dd = metrics.calculate_max_drawdown()

        # 验证返回字典结构
        self.assertIn('drawdown_pct', max_dd)
        self.assertIn('drawdown_amount', max_dd)
        self.assertIn('start_date', max_dd)
        self.assertIn('end_date', max_dd)

        # 验证回撤百分比和金额
        self.assertGreater(max_dd['drawdown_pct'], 0)
        self.assertGreater(max_dd['drawdown_amount'], 0)

        # 最大回撤应该是从110000到98000
        expected_dd_pct = (110000 - 98000) / 110000
        self.assertAlmostEqual(max_dd['drawdown_pct'], expected_dd_pct, places=4)

    def test_06_calculate_volatility(self):
        """测试6: 波动率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        volatility = metrics.calculate_volatility()

        # 验证是浮点数
        self.assertIsInstance(volatility, (float, np.floating))

        # 波动率应该大于0
        self.assertGreater(volatility, 0)

    def test_07_calculate_sharpe_ratio(self):
        """测试7: 夏普比率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        # 使用默认无风险利率
        sharpe_ratio = metrics.calculate_sharpe_ratio()

        self.assertIsInstance(sharpe_ratio, (float, np.floating))

        # 使用自定义无风险利率
        sharpe_ratio_custom = metrics.calculate_sharpe_ratio(risk_free_rate=0.05)
        self.assertIsInstance(sharpe_ratio_custom, (float, np.floating))

    def test_08_calculate_sortino_ratio(self):
        """测试8: 索提诺比率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        sortino_ratio = metrics.calculate_sortino_ratio()

        self.assertIsInstance(sortino_ratio, (float, np.floating))

        # 索提诺比率通常应该高于夏普比率（因为只考虑下行风险）
        sharpe_ratio = metrics.calculate_sharpe_ratio()
        # 这个关系不总是成立，所以只验证都是数字
        self.assertIsInstance(sharpe_ratio, (float, np.floating))

    def test_09_calculate_calmar_ratio(self):
        """测试9: Calmar比率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        calmar_ratio = metrics.calculate_calmar_ratio()

        self.assertIsInstance(calmar_ratio, (float, np.floating))

    def test_10_calculate_total_trades(self):
        """测试10: 总交易次数计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        total_trades = metrics.calculate_total_trades()

        self.assertEqual(total_trades, 4)

    def test_11_calculate_win_rate(self):
        """测试11: 胜率计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        win_rate = metrics.calculate_win_rate()

        # 4笔交易，3笔盈利，1笔亏损
        self.assertAlmostEqual(win_rate, 0.75, places=2)

    def test_12_calculate_profit_loss_ratio(self):
        """测试12: 盈亏比计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        pl_ratio = metrics.calculate_profit_loss_ratio()

        # 验证是数字
        self.assertIsInstance(pl_ratio, (float, np.floating))

        # 平均盈利 = (800 + 1300 + 1200) / 3 = 1100
        # 平均亏损 = 600
        # 盈亏比 = 1100 / 600 = 1.833...
        expected_ratio = 1100 / 600
        self.assertAlmostEqual(pl_ratio, expected_ratio, places=2)

    def test_13_calculate_avg_holding_days(self):
        """测试13: 平均持仓天数计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        avg_days = metrics.calculate_avg_holding_days()

        # 验证是数字
        self.assertIsInstance(avg_days, (float, np.floating))

        # 验证合理性（应该是10天左右）
        self.assertGreater(avg_days, 0)
        self.assertLess(avg_days, 30)

    def test_14_calculate_max_consecutive_wins(self):
        """测试14: 最大连续盈利次数"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        max_wins = metrics.calculate_max_consecutive_wins()

        # 验证是整数
        self.assertIsInstance(max_wins, (int, np.integer))

        # 交易序列: 盈利, 亏损, 盈利, 盈利
        # 最大连续盈利应该是2
        self.assertEqual(max_wins, 2)

    def test_15_calculate_max_consecutive_losses(self):
        """测试15: 最大连续亏损次数"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        max_losses = metrics.calculate_max_consecutive_losses()

        # 验证是整数
        self.assertIsInstance(max_losses, (int, np.integer))

        # 只有1次连续亏损
        self.assertEqual(max_losses, 1)

    def test_16_calculate_total_fees(self):
        """测试16: 总费用计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        total_fees = metrics.calculate_total_fees()

        # 总费用 = 200 + 100 + 200 + 300 = 800
        self.assertEqual(total_fees, 800)

    def test_17_calculate_fee_percentage(self):
        """测试17: 费用占比计算"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        fee_pct = metrics.calculate_fee_percentage()

        # 费用占比 = 800 / 100000 = 0.008
        self.assertAlmostEqual(fee_pct, 0.008, places=4)

    def test_18_calculate_all_metrics(self):
        """测试18: 计算所有指标"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        all_metrics = metrics.calculate_all_metrics()

        # 验证返回字典
        self.assertIsInstance(all_metrics, dict)

        # 验证包含所有关键指标
        required_keys = [
            'total_return', 'annual_return', 'monthly_returns',
            'max_drawdown', 'volatility', 'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'total_trades', 'win_rate', 'profit_loss_ratio',
            'avg_holding_days', 'max_consecutive_wins', 'max_consecutive_losses',
            'total_fees', 'fee_percentage'
        ]

        for key in required_keys:
            self.assertIn(key, all_metrics)

    def test_19_generate_equity_curve_data(self):
        """测试19: 生成权益曲线数据"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        equity_curve = metrics.generate_equity_curve_data()

        # 验证返回DataFrame
        self.assertIsInstance(equity_curve, pd.DataFrame)

        # 验证包含必要的列
        self.assertIn('date', equity_curve.columns)
        self.assertIn('value', equity_curve.columns)
        self.assertIn('return', equity_curve.columns)
        self.assertIn('cumulative_return', equity_curve.columns)

        # 验证数据量
        self.assertEqual(len(equity_curve), 100)

    def test_20_generate_drawdown_curve_data(self):
        """测试20: 生成回撤曲线数据"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        drawdown_curve = metrics.generate_drawdown_curve_data()

        # 验证返回DataFrame
        self.assertIsInstance(drawdown_curve, pd.DataFrame)

        # 验证包含必要的列
        self.assertIn('date', drawdown_curve.columns)
        self.assertIn('drawdown', drawdown_curve.columns)

        # 验证数据量
        self.assertEqual(len(drawdown_curve), 100)

    def test_21_format_summary(self):
        """测试21: 格式化摘要输出"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=self.trades,
            initial_capital=self.initial_capital
        )

        summary = metrics.format_summary()

        # 验证返回字符串
        self.assertIsInstance(summary, str)

        # 验证包含关键信息
        self.assertIn('回测结果摘要', summary)
        self.assertIn('初始资金', summary)
        self.assertIn('最终资金', summary)
        self.assertIn('总收益率', summary)
        self.assertIn('年化收益', summary)
        self.assertIn('最大回撤', summary)
        self.assertIn('夏普比率', summary)

    def test_22_empty_trades(self):
        """测试22: 空交易记录"""
        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=[],
            initial_capital=self.initial_capital
        )

        # 验证不会报错
        self.assertEqual(metrics.calculate_total_trades(), 0)
        self.assertEqual(metrics.calculate_win_rate(), 0.0)
        self.assertEqual(metrics.calculate_total_fees(), 0.0)

    def test_23_single_day_data(self):
        """测试23: 单日数据"""
        dates = pd.date_range(start='2024-01-01', periods=1, freq='D')
        values = pd.Series([100000], index=dates)

        metrics = BacktestMetrics(
            portfolio_values=values,
            trades=[],
            initial_capital=100000
        )

        # 验证不会报错
        self.assertEqual(metrics.calculate_annual_return(), 0.0)
        self.assertEqual(metrics.calculate_volatility(), 0.0)

    def test_24_zero_return_case(self):
        """测试24: 零收益情况"""
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        values = pd.Series([100000] * 10, index=dates)

        metrics = BacktestMetrics(
            portfolio_values=values,
            trades=[],
            initial_capital=100000
        )

        # 验证零收益
        self.assertEqual(metrics.calculate_total_return(), 0.0)
        self.assertEqual(metrics.calculate_annual_return(), 0.0)

        # 波动率应该为0
        self.assertEqual(metrics.calculate_volatility(), 0.0)

    def test_25_all_winning_trades(self):
        """测试25: 全部盈利交易"""
        winning_trades = [
            {
                'entry_date': '2024-01-05',
                'exit_date': '2024-01-15',
                'pnl': 800,
                'commission': 200,
                'status': 'closed'
            },
            {
                'entry_date': '2024-01-20',
                'exit_date': '2024-01-30',
                'pnl': 600,
                'commission': 100,
                'status': 'closed'
            },
        ]

        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=winning_trades,
            initial_capital=self.initial_capital
        )

        # 胜率应该是100%
        self.assertEqual(metrics.calculate_win_rate(), 1.0)

        # 盈亏比应该是inf（没有亏损）
        self.assertEqual(metrics.calculate_profit_loss_ratio(), float('inf'))

    def test_26_all_losing_trades(self):
        """测试26: 全部亏损交易"""
        losing_trades = [
            {
                'entry_date': '2024-01-05',
                'exit_date': '2024-01-15',
                'pnl': -800,
                'commission': 200,
                'status': 'closed'
            },
            {
                'entry_date': '2024-01-20',
                'exit_date': '2024-01-30',
                'pnl': -600,
                'commission': 100,
                'status': 'closed'
            },
        ]

        metrics = BacktestMetrics(
            portfolio_values=self.portfolio_values,
            trades=losing_trades,
            initial_capital=self.initial_capital
        )

        # 胜率应该是0%
        self.assertEqual(metrics.calculate_win_rate(), 0.0)

        # 盈亏比应该是0（没有盈利）
        self.assertEqual(metrics.calculate_profit_loss_ratio(), 0.0)


if __name__ == '__main__':
    unittest.main()
