"""回测引擎测试"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.backtest.engine import BacktestEngine
from src.strategy.base_strategy import BaseStrategy
from src.strategy.short_term.momentum import MomentumStrategy
from src.core.constants import SignalType, DEFAULT_CAPITAL, COMMISSION_RATE, STAMP_TAX_RATE


class TestBacktestEngine(unittest.TestCase):
    """回测引擎测试类"""

    def setUp(self):
        """测试前准备"""
        self.engine = BacktestEngine()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self) -> pd.DataFrame:
        """创建测试用的K线数据"""
        # 创建100天的模拟数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        # 生成上涨趋势的价格数据
        np.random.seed(42)
        close_prices = 10 + np.cumsum(np.random.randn(100) * 0.2)

        df = pd.DataFrame({
            'date': dates,
            'open': close_prices + np.random.randn(100) * 0.1,
            'high': close_prices + np.abs(np.random.randn(100) * 0.3),
            'low': close_prices - np.abs(np.random.randn(100) * 0.3),
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        })

        return df

    def test_01_initialization(self):
        """测试1: 初始化测试 - 正确设置初始资金和费率"""
        # 默认参数初始化
        engine = BacktestEngine()
        self.assertEqual(engine.initial_cash, DEFAULT_CAPITAL)
        self.assertEqual(engine.commission, COMMISSION_RATE)
        self.assertEqual(engine.stamp_tax, STAMP_TAX_RATE)
        self.assertIsNone(engine.cerebro)

        # 自定义参数初始化
        custom_engine = BacktestEngine(
            initial_cash=500000,
            commission=0.0005,
            stamp_tax=0.002
        )
        self.assertEqual(custom_engine.initial_cash, 500000)
        self.assertEqual(custom_engine.commission, 0.0005)
        self.assertEqual(custom_engine.stamp_tax, 0.002)

    def test_02_standardize_columns(self):
        """测试2: 列名标准化 - 中文列名转英文"""
        # 创建中文列名的数据
        chinese_df = pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=5),
            '开盘': [10, 11, 12, 13, 14],
            '收盘': [10.5, 11.5, 12.5, 13.5, 14.5],
            '最高': [11, 12, 13, 14, 15],
            '最低': [9.5, 10.5, 11.5, 12.5, 13.5],
            '成交量': [1000000, 1500000, 2000000, 1800000, 1200000]
        })

        standardized = self.engine._standardize_columns(chinese_df)

        # 验证列名已转换
        expected_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
        for col in expected_columns:
            self.assertIn(col, standardized.columns)

        # 验证数据未改变
        self.assertEqual(len(standardized), 5)
        self.assertEqual(standardized['open'].iloc[0], 10)

    def test_03_prepare_data(self):
        """测试3: 数据准备测试 - DataFrame转backtrader数据源"""
        # 准备数据
        bt_data = self.engine._prepare_data(
            self.sample_data,
            start_date='2024-01-10',
            end_date='2024-02-28'
        )

        # 验证数据源已创建
        self.assertIsNotNone(bt_data)
        # backtrader数据源应该有正确的列映射
        self.assertEqual(bt_data.params.dataname.columns.tolist(),
                        ['open', 'high', 'low', 'close', 'volume'])

    def test_04_prepare_data_date_filter(self):
        """测试4: 数据准备日期过滤测试"""
        # 测试日期过滤
        bt_data = self.engine._prepare_data(
            self.sample_data,
            start_date='2024-02-01',
            end_date='2024-02-29'
        )

        # 获取过滤后的数据
        filtered_df = bt_data.params.dataname

        # 验证日期范围
        self.assertTrue((filtered_df.index >= '2024-02-01').all())
        self.assertTrue((filtered_df.index <= '2024-02-29').all())

    def test_05_extract_results_structure(self):
        """测试5: 结果提取结构测试"""
        # 创建模拟的策略分析器结果
        class MockAnalyzer:
            def __init__(self):
                self.sharperatio = None
                self.max = type('obj', (object,), {'drawdown': 10.0})()
                self.total = type('obj', (object,), {'closed': 10})()
                self.won = type('obj', (object,), {'total': 6})()

            def get_analysis(self):
                if hasattr(self, 'sharperatio'):
                    return {'sharperatio': 1.5}
                if hasattr(self, 'max'):
                    return self
                if hasattr(self, 'total'):
                    return self
                return {}

        class MockStrategy:
            def __init__(self):
                self.analyzers = type('obj', (object,), {
                    'sharpe': MockAnalyzer(),
                    'drawdown': MockAnalyzer(),
                    'returns': MockAnalyzer(),
                    'trades': MockAnalyzer()
                })()

        # 提取结果
        results = self.engine._extract_results(
            MockStrategy(),
            initial_value=1000000,
            final_value=1150000
        )

        # 验证结果结构
        required_keys = [
            'initial_value', 'final_value', 'total_return',
            'sharpe_ratio', 'max_drawdown', 'total_trades', 'win_rate'
        ]
        for key in required_keys:
            self.assertIn(key, results)

        # 验证计算正确性
        self.assertEqual(results['initial_value'], 1000000)
        self.assertEqual(results['final_value'], 1150000)
        self.assertAlmostEqual(results['total_return'], 0.15, places=2)

    def test_06_simple_strategy_conversion(self):
        """测试6: 简单策略转换测试"""
        # 创建一个简单的测试策略
        class SimpleStrategy(BaseStrategy):
            def __init__(self):
                # 手动设置属性,避免配置文件依赖
                self.strategy_name = 'test_strategy'
                self.params = {
                    'stop_loss': 0.08,
                    'take_profit': 0.15,
                    'max_holding_days': 10
                }

            def generate_signals(self, df):
                df = df.copy()
                df['signal'] = SignalType.HOLD.value
                # 在第5天买入
                if len(df) > 5:
                    df.iloc[5, df.columns.get_loc('signal')] = SignalType.BUY.value
                # 在第15天卖出
                if len(df) > 15:
                    df.iloc[15, df.columns.get_loc('signal')] = SignalType.SELL.value
                return df

        # 生成信号
        signals_df = self.sample_data.copy()
        signals_df['signal'] = SignalType.HOLD.value

        # 转换策略
        bt_strategy_class = self.engine._convert_strategy(SimpleStrategy, signals_df)

        # 验证转换后的类是backtrader策略
        self.assertIsNotNone(bt_strategy_class)
        self.assertTrue(hasattr(bt_strategy_class, '__init__'))

    def test_07_run_backtest_basic(self):
        """测试7: 基本回测运行测试"""
        # 创建简单策略
        class SimpleStrategy(BaseStrategy):
            def __init__(self):
                self.strategy_name = 'test_strategy'
                self.params = {
                    'stop_loss': 0.08,
                    'take_profit': 0.15,
                    'max_holding_days': 10
                }

            def generate_signals(self, df):
                df = df.copy()
                df['signal'] = SignalType.HOLD.value
                return df

        # 运行回测
        try:
            results = self.engine.run_backtest(
                strategy_class=SimpleStrategy,
                data=self.sample_data,
                start_date='2024-01-01',
                end_date='2024-03-31'
            )

            # 验证结果
            self.assertIsNotNone(results)
            self.assertIn('initial_value', results)
            self.assertIn('final_value', results)
            self.assertIn('total_return', results)

            # 验证初始资金
            self.assertAlmostEqual(
                results['initial_value'],
                DEFAULT_CAPITAL,
                places=2
            )

        except Exception as e:
            self.fail(f"回测运行失败: {e}")

    def test_08_run_backtest_with_momentum_strategy(self):
        """测试8: 使用动量策略的回测测试"""
        # 跳过如果配置不存在
        try:
            # 使用动量策略运行回测
            results = self.engine.run_backtest(
                strategy_class=MomentumStrategy,
                data=self.sample_data,
                start_date='2024-01-01',
                end_date='2024-03-31'
            )

            # 验证结果
            self.assertIsNotNone(results)
            self.assertIsInstance(results['total_return'], float)
            self.assertIsInstance(results['sharpe_ratio'], (int, float))
            self.assertIsInstance(results['max_drawdown'], float)

        except ValueError as e:
            if "策略" in str(e) and "不存在" in str(e):
                self.skipTest("动量策略配置不存在")
            else:
                raise

    def test_09_multiple_backtests(self):
        """测试9: 多次回测测试 - 验证引擎可重用"""
        class SimpleStrategy(BaseStrategy):
            def __init__(self):
                self.strategy_name = 'test_strategy'
                self.params = {'stop_loss': 0.08}

            def generate_signals(self, df):
                df = df.copy()
                df['signal'] = SignalType.HOLD.value
                return df

        # 运行第一次回测
        results1 = self.engine.run_backtest(
            strategy_class=SimpleStrategy,
            data=self.sample_data
        )

        # 运行第二次回测
        results2 = self.engine.run_backtest(
            strategy_class=SimpleStrategy,
            data=self.sample_data
        )

        # 验证两次结果应该相同
        self.assertEqual(results1['initial_value'], results2['initial_value'])
        self.assertEqual(results1['final_value'], results2['final_value'])

    def test_10_empty_data_handling(self):
        """测试10: 空数据处理测试"""
        class SimpleStrategy(BaseStrategy):
            def __init__(self):
                self.strategy_name = 'test_strategy'
                self.params = {}

            def generate_signals(self, df):
                return df

        # 空DataFrame
        empty_df = pd.DataFrame()

        # 应该抛出异常或安全处理
        with self.assertRaises(Exception):
            self.engine.run_backtest(
                strategy_class=SimpleStrategy,
                data=empty_df
            )


class TestBacktestEngineIntegration(unittest.TestCase):
    """回测引擎集成测试"""

    def test_full_backtest_workflow(self):
        """完整回测工作流测试"""
        # 1. 创建引擎
        engine = BacktestEngine(initial_cash=1000000)

        # 2. 准备数据
        dates = pd.date_range('2024-01-01', periods=100)
        data = pd.DataFrame({
            'date': dates,
            'open': 10 + np.random.randn(100) * 0.5,
            'high': 11 + np.random.randn(100) * 0.5,
            'low': 9 + np.random.randn(100) * 0.5,
            'close': 10 + np.random.randn(100) * 0.5,
            'volume': np.random.randint(1000000, 5000000, 100)
        })

        # 3. 创建策略
        class TestStrategy(BaseStrategy):
            def __init__(self):
                self.strategy_name = 'test'
                self.params = {'stop_loss': 0.05}

            def generate_signals(self, df):
                df = df.copy()
                df['signal'] = SignalType.HOLD.value
                return df

        # 4. 运行回测
        results = engine.run_backtest(
            strategy_class=TestStrategy,
            data=data
        )

        # 5. 验证结果
        self.assertIsNotNone(results)
        self.assertGreater(results['initial_value'], 0)


if __name__ == '__main__':
    unittest.main()
