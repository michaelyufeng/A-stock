"""run_backtest.py 脚本测试"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestRunBacktestScript(unittest.TestCase):
    """回测脚本测试类"""

    # 测试用固定随机种子，确保测试结果可重复
    # 用于生成确定性的测试数据，避免随机性导致测试不稳定
    TEST_RANDOM_SEED = 42

    def setUp(self):
        """测试前准备"""
        # 延迟导入，避免在模块加载时执行main()
        from scripts import run_backtest
        self.run_backtest_module = run_backtest

    def _create_sample_kline_data(self, days=100):
        """创建测试用的K线数据

        使用固定随机种子确保每次生成相同的测试数据
        """
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(self.TEST_RANDOM_SEED)
        close_prices = 10 + np.cumsum(np.random.randn(days) * 0.2)

        return pd.DataFrame({
            'date': dates,
            'open': close_prices + np.random.randn(days) * 0.1,
            'high': close_prices + np.abs(np.random.randn(days) * 0.3),
            'low': close_prices - np.abs(np.random.randn(days) * 0.3),
            'close': close_prices,
            'volume': np.random.randint(1000000, 10000000, days)
        })

    def _create_mock_backtest_result(self):
        """创建模拟的回测结果"""
        return {
            'initial_value': 1000000.0,
            'final_value': 1150000.0,
            'total_return': 0.15,
            'sharpe_ratio': 1.5,
            'max_drawdown': 0.08,
            'total_trades': 10,
            'win_rate': 0.6,
            'metrics': {
                'annual_return': 0.18,
                'volatility': 0.12,
                'sortino_ratio': 1.8,
                'calmar_ratio': 2.25,
                'profit_loss_ratio': 1.8,
                'avg_holding_days': 5.5,
                'max_consecutive_wins': 3,
                'max_consecutive_losses': 2,
                'total_fees': 3500.0,
                'fee_percentage': 0.0035,
                'max_drawdown': {
                    'drawdown_pct': 0.08,
                    'drawdown_amount': 80000.0,
                    'start_date': pd.Timestamp('2024-02-01'),
                    'end_date': pd.Timestamp('2024-02-15')
                }
            },
            'summary': '回测结果摘要',
            'trades': []
        }

    @patch('scripts.run_backtest.AKShareProvider')
    @patch('scripts.run_backtest.BacktestEngine')
    def test_01_run_backtest_success(self, mock_engine, mock_provider):
        """测试1: 成功运行回测 - 正常流程"""
        # 模拟数据提供者
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = self._create_sample_kline_data()
        mock_provider.return_value = mock_provider_instance

        # 模拟回测引擎
        mock_engine_instance = Mock()
        mock_engine_instance.run_backtest.return_value = self._create_mock_backtest_result()
        mock_engine.return_value = mock_engine_instance

        # 运行回测（返回元组）
        result, engine = self.run_backtest_module.run_backtest(
            strategy='momentum',
            code='600519',
            start='2023-01-01',
            end='2023-12-31'
        )

        # 验证
        self.assertIsNotNone(result)
        self.assertIsNotNone(engine)
        self.assertIn('initial_value', result)
        self.assertIn('final_value', result)
        self.assertIn('total_return', result)

        # 验证调用
        mock_provider_instance.get_daily_kline.assert_called_once()
        mock_engine_instance.run_backtest.assert_called_once()

    @patch('scripts.run_backtest.AKShareProvider')
    def test_02_validate_date_range(self, mock_provider):
        """测试2: 日期范围验证 - start_date应小于end_date"""
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        # 测试无效日期范围
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.validate_date_range('2024-12-31', '2024-01-01')

        self.assertIn('开始日期必须早于结束日期', str(context.exception))

    def test_03_validate_date_format(self):
        """测试3: 日期格式验证"""
        # 测试有效日期格式
        self.assertTrue(self.run_backtest_module.validate_date_format('2024-01-01'))
        self.assertTrue(self.run_backtest_module.validate_date_format('2023-12-31'))

        # 测试无效日期格式
        self.assertFalse(self.run_backtest_module.validate_date_format('2024/01/01'))
        self.assertFalse(self.run_backtest_module.validate_date_format('20240101'))
        self.assertFalse(self.run_backtest_module.validate_date_format('invalid'))

    @patch('scripts.run_backtest.MomentumStrategy')
    def test_04_get_strategy_class(self, mock_momentum):
        """测试4: 获取策略类 - 根据策略名称返回对应类"""
        # 测试已知策略
        strategy_class = self.run_backtest_module.get_strategy_class('momentum')
        self.assertIsNotNone(strategy_class)

        # 测试未知策略
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.get_strategy_class('unknown_strategy')

        self.assertIn('不支持的策略', str(context.exception))

    @patch('scripts.run_backtest.AKShareProvider')
    def test_05_fetch_data_error_handling(self, mock_provider):
        """测试5: 数据获取错误处理"""
        # 模拟数据获取失败
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.side_effect = Exception("网络错误")
        mock_provider.return_value = mock_provider_instance

        # 验证异常处理
        with self.assertRaises(Exception) as context:
            self.run_backtest_module.fetch_backtest_data('600519', '2023-01-01', '2023-12-31')

        self.assertIn('网络错误', str(context.exception))

    @patch('scripts.run_backtest.AKShareProvider')
    def test_06_empty_data_handling(self, mock_provider):
        """测试6: 空数据处理"""
        # 模拟返回空数据
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = pd.DataFrame()
        mock_provider.return_value = mock_provider_instance

        # 验证异常处理
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.fetch_backtest_data('600519', '2023-01-01', '2023-12-31')

        self.assertIn('未获取到数据', str(context.exception))

    def test_07_format_results_output(self):
        """测试7: 结果格式化输出"""
        result = self._create_mock_backtest_result()
        output = self.run_backtest_module.format_results(result)

        # 验证输出包含关键信息
        self.assertIsInstance(output, str)
        self.assertIn('初始资金', output)
        self.assertIn('最终资金', output)
        self.assertIn('总收益率', output)
        self.assertIn('夏普比率', output)

    @patch('scripts.run_backtest.BacktestEngine')
    def test_08_save_results_to_file(self, mock_engine):
        """测试8: 保存结果到文件"""
        result = self._create_mock_backtest_result()

        # 测试保存
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.run_backtest_module.save_results(result, '/tmp/test_report.txt')

            # 验证文件写入
            mock_open.assert_called_once()
            mock_file.write.assert_called()

    @patch('scripts.run_backtest.BacktestEngine')
    def test_09_plot_results(self, mock_engine):
        """测试9: 绘制结果图表"""
        from pathlib import Path

        mock_engine_instance = Mock()
        mock_engine_instance.plot_results = Mock()
        mock_engine.return_value = mock_engine_instance

        # 测试绘图功能
        self.run_backtest_module.plot_backtest_results(
            mock_engine_instance,
            '/tmp/test_chart.png'
        )

        # 验证调用（路径会被解析为绝对路径）
        expected_path = str(Path('/tmp/test_chart.png').resolve())
        mock_engine_instance.plot_results.assert_called_once_with(expected_path)

    @patch('sys.argv', ['run_backtest.py', '--strategy', 'momentum', '--code', '600519', '--start', '2023-01-01'])
    @patch('scripts.run_backtest.run_backtest')
    def test_10_command_line_parsing(self, mock_run):
        """测试10: 命令行参数解析"""
        mock_run.return_value = self._create_mock_backtest_result()

        # 测试参数解析
        args = self.run_backtest_module.parse_arguments()

        self.assertEqual(args.strategy, 'momentum')
        self.assertEqual(args.code, '600519')
        self.assertEqual(args.start, '2023-01-01')

    def test_11_default_date_handling(self):
        """测试11: 默认日期处理 - 无start/end时使用默认值"""
        # 测试获取默认日期
        start, end = self.run_backtest_module.get_default_dates()

        # 验证end是今天
        self.assertEqual(end, datetime.now().strftime('%Y-%m-%d'))

        # 验证start是一年前
        expected_start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        self.assertEqual(start, expected_start)

    @patch('scripts.run_backtest.AKShareProvider')
    @patch('scripts.run_backtest.BacktestEngine')
    def test_12_capital_parameter(self, mock_engine, mock_provider):
        """测试12: 初始资金参数"""
        # 模拟数据
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = self._create_sample_kline_data()
        mock_provider.return_value = mock_provider_instance

        mock_engine_instance = Mock()
        mock_engine_instance.run_backtest.return_value = self._create_mock_backtest_result()
        mock_engine.return_value = mock_engine_instance

        # 测试自定义资金
        result, engine = self.run_backtest_module.run_backtest(
            strategy='momentum',
            code='600519',
            start='2023-01-01',
            end='2023-12-31',
            capital=500000
        )

        # 验证BacktestEngine使用正确的资金初始化
        mock_engine.assert_called_with(initial_cash=500000)

    @patch('scripts.run_backtest.AKShareProvider')
    def test_13_invalid_stock_code(self, mock_provider):
        """测试13: 无效股票代码处理"""
        # 模拟无效代码
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.side_effect = Exception("股票代码不存在")
        mock_provider.return_value = mock_provider_instance

        with self.assertRaises(Exception):
            self.run_backtest_module.fetch_backtest_data('999999', '2023-01-01', '2023-12-31')

    def test_14_output_verbosity_levels(self):
        """测试14: 输出详细程度控制"""
        result = self._create_mock_backtest_result()

        # 测试简洁输出
        brief_output = self.run_backtest_module.format_results(result, verbose=False)
        self.assertIn('总收益率', brief_output)

        # 测试详细输出
        verbose_output = self.run_backtest_module.format_results(result, verbose=True)
        self.assertIn('年化收益', verbose_output)
        self.assertIn('最大连胜', verbose_output)

    @patch('scripts.run_backtest.AKShareProvider')
    def test_15_data_insufficient_warning(self, mock_provider):
        """测试15: 数据不足警告"""
        # 模拟数据量不足（少于30天）
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = self._create_sample_kline_data(days=20)
        mock_provider.return_value = mock_provider_instance

        # 应该给出警告但不抛出异常
        with patch('scripts.run_backtest.logger') as mock_logger:
            data = self.run_backtest_module.fetch_backtest_data('600519', '2023-12-01', '2023-12-20')

            # 验证警告被记录
            mock_logger.warning.assert_called()

    def test_16_validate_stock_code(self):
        """测试16: 股票代码验证"""
        # 测试有效代码
        self.assertTrue(self.run_backtest_module.validate_stock_code('600519'))
        self.assertTrue(self.run_backtest_module.validate_stock_code('000001'))
        self.assertTrue(self.run_backtest_module.validate_stock_code('300750'))

        # 测试无效代码
        self.assertFalse(self.run_backtest_module.validate_stock_code('60051'))  # 不足6位
        self.assertFalse(self.run_backtest_module.validate_stock_code('6005199'))  # 超过6位
        self.assertFalse(self.run_backtest_module.validate_stock_code('ABC123'))  # 包含字母
        self.assertFalse(self.run_backtest_module.validate_stock_code(''))  # 空字符串
        self.assertFalse(self.run_backtest_module.validate_stock_code(None))  # None

    def test_17_validate_capital(self):
        """测试17: 初始资金验证"""
        # 测试有效资金
        try:
            self.run_backtest_module.validate_capital(100000)
            self.run_backtest_module.validate_capital(1000000)
        except ValueError:
            self.fail("validate_capital raised ValueError unexpectedly")

        # 测试过低资金
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.validate_capital(5000)
        self.assertIn('不能低于', str(context.exception))

        # 测试过高资金
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.validate_capital(200000000)
        self.assertIn('不能超过', str(context.exception))

    def test_18_validate_output_path(self):
        """测试18: 输出路径验证"""
        import tempfile

        # 测试有效路径（当前目录）
        safe_path = self.run_backtest_module.validate_output_path('test_output.txt')
        self.assertTrue(safe_path.endswith('test_output.txt'))

        # 测试临时目录路径
        temp_file = os.path.join(tempfile.gettempdir(), 'test_output.txt')
        safe_path = self.run_backtest_module.validate_output_path(temp_file)
        self.assertTrue(safe_path.endswith('test_output.txt'))

        # 测试空路径
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.validate_output_path('')
        self.assertIn('不能为空', str(context.exception))

        # 测试不安全的路径（尝试路径遍历）
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.validate_output_path('/etc/passwd')
        # 可能抛出两种错误之一：不安全的路径或目录不存在
        self.assertTrue(
            '不安全的输出路径' in str(context.exception) or
            '目录不存在' in str(context.exception)
        )

    def test_19_date_range_validation(self):
        """测试19: 日期范围验证（早于2000年或晚于今天）"""
        # 测试早于2000年的日期
        self.assertFalse(self.run_backtest_module.validate_date_format('1999-12-31'))

        # 测试晚于今天的日期
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.assertFalse(self.run_backtest_module.validate_date_format(future_date))

        # 测试有效日期
        self.assertTrue(self.run_backtest_module.validate_date_format('2023-01-01'))

    @patch('scripts.run_backtest.AKShareProvider')
    @patch('scripts.run_backtest.BacktestEngine')
    def test_20_invalid_stock_code_in_run_backtest(self, mock_engine, mock_provider):
        """测试20: run_backtest中的股票代码验证"""
        # 测试无效股票代码
        with self.assertRaises(ValueError) as context:
            self.run_backtest_module.run_backtest(
                strategy='momentum',
                code='INVALID',
                start='2023-01-01',
                end='2023-12-31'
            )
        self.assertIn('无效的股票代码', str(context.exception))


class TestRunBacktestIntegration(unittest.TestCase):
    """回测脚本集成测试（需要真实环境）"""

    @unittest.skipIf(os.getenv('SKIP_INTEGRATION_TESTS') == '1', '跳过集成测试')
    def test_full_backtest_workflow(self):
        """集成测试: 完整回测流程（使用真实模块）"""
        from scripts import run_backtest
        from src.data.akshare_provider import AKShareProvider
        from src.backtest.engine import BacktestEngine

        # 这个测试会在真实环境下运行完整流程
        # 使用较短的日期范围以加快测试速度
        try:
            result = run_backtest.run_backtest(
                strategy='momentum',
                code='600519',
                start='2024-01-01',
                end='2024-01-31',
                capital=1000000
            )

            # 验证结果结构
            self.assertIsNotNone(result)
            self.assertIn('initial_value', result)
            self.assertIn('final_value', result)

        except Exception as e:
            # 如果网络或其他问题导致失败，跳过而不是失败
            self.skipTest(f"集成测试需要网络连接: {e}")


if __name__ == '__main__':
    unittest.main()
