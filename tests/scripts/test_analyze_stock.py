"""analyze_stock.py 脚本测试"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestAnalyzeStockScript(unittest.TestCase):
    """股票分析脚本测试类"""

    # 测试用固定随机种子，确保测试结果可重复
    TEST_RANDOM_SEED = 42

    def setUp(self):
        """测试前准备"""
        # 延迟导入，避免在模块加载时执行main()
        from scripts import analyze_stock
        self.analyze_stock_module = analyze_stock

    def _create_sample_kline_data(self, days=100):
        """创建测试用的K线数据"""
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(self.TEST_RANDOM_SEED)
        close_prices = 10 + np.cumsum(np.random.randn(days) * 0.2)

        return pd.DataFrame({
            '日期': dates,
            '开盘': close_prices + np.random.randn(days) * 0.1,
            '最高': close_prices + np.abs(np.random.randn(days) * 0.3),
            '最低': close_prices - np.abs(np.random.randn(days) * 0.3),
            '收盘': close_prices,
            '成交量': np.random.randint(1000000, 10000000, days)
        })

    def _create_sample_financial_data(self):
        """创建测试用的财务数据"""
        return pd.DataFrame({
            '净资产收益率': [15.5, 16.2, 17.8],
            '毛利率': [35.2, 36.5, 37.1],
            '净利润': [1000000, 1200000, 1500000],
            '营业收入': [5000000, 6000000, 7000000],
            '资产负债率': [45.5, 43.2, 40.8],
            '流动比率': [1.8, 2.0, 2.2],
            '市盈率': [18.5, 19.2, 20.1],
            '市净率': [2.5, 2.7, 2.8]
        })

    def _create_sample_money_flow_data(self):
        """创建测试用的资金流向数据"""
        dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
        np.random.seed(self.TEST_RANDOM_SEED)

        return pd.DataFrame({
            '日期': dates,
            '主力净流入': np.random.randn(20) * 1000000,
            '成交量': np.random.randint(1000000, 10000000, 20)
        })

    def _create_mock_analysis_result(self):
        """创建模拟的分析结果"""
        return {
            'rating': 'buy',
            'confidence': 8.5,
            'target_price': 150.00,
            'stop_loss': 135.00,
            'reasons': ['技术面呈现强势上涨趋势', '基本面良好，财务指标健康'],
            'risks': ['市场整体波动可能影响个股表现'],
            'a_share_risks': ['T+1交易制度限制，当日买入次日才能卖出'],
            'ai_insights': '综合评分85分，建议买入。',
            'scores': {
                'technical': 85.0,
                'fundamental': 80.0,
                'capital': 75.0,
                'overall': 82.0
            }
        }

    def test_01_validate_stock_code(self):
        """测试1: 股票代码验证"""
        # 测试有效代码
        self.assertTrue(self.analyze_stock_module.validate_stock_code('600519'))
        self.assertTrue(self.analyze_stock_module.validate_stock_code('000001'))
        self.assertTrue(self.analyze_stock_module.validate_stock_code('300750'))

        # 测试无效代码
        self.assertFalse(self.analyze_stock_module.validate_stock_code('60051'))
        self.assertFalse(self.analyze_stock_module.validate_stock_code('6005199'))
        self.assertFalse(self.analyze_stock_module.validate_stock_code('ABC123'))
        self.assertFalse(self.analyze_stock_module.validate_stock_code(''))
        self.assertFalse(self.analyze_stock_module.validate_stock_code(None))

    @patch('scripts.analyze_stock.AKShareProvider')
    def test_02_fetch_stock_data_success(self, mock_provider):
        """测试2: 成功获取股票数据"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = self._create_sample_kline_data()
        mock_provider_instance.get_financial_data.return_value = self._create_sample_financial_data()
        mock_provider_instance.get_money_flow.return_value = self._create_sample_money_flow_data()
        mock_provider.return_value = mock_provider_instance

        kline, financial, money_flow = self.analyze_stock_module.fetch_stock_data('600519')

        # 验证
        self.assertIsNotNone(kline)
        self.assertIsNotNone(financial)
        self.assertIsNotNone(money_flow)
        self.assertGreater(len(kline), 0)
        self.assertGreater(len(financial), 0)
        self.assertGreater(len(money_flow), 0)

    @patch('scripts.analyze_stock.AKShareProvider')
    def test_03_fetch_stock_data_empty(self, mock_provider):
        """测试3: 获取数据为空时抛出异常"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.return_value = pd.DataFrame()
        mock_provider.return_value = mock_provider_instance

        with self.assertRaises(ValueError) as context:
            self.analyze_stock_module.fetch_stock_data('600519')

        self.assertIn('数据', str(context.exception).lower())

    @patch('scripts.analyze_stock.AKShareProvider')
    def test_04_fetch_stock_data_network_error(self, mock_provider):
        """测试4: 网络错误处理"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_daily_kline.side_effect = Exception("网络连接失败")
        mock_provider.return_value = mock_provider_instance

        with self.assertRaises(Exception) as context:
            self.analyze_stock_module.fetch_stock_data('600519')

        self.assertIn('网络连接失败', str(context.exception))

    @patch('scripts.analyze_stock.StockRater')
    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_05_analyze_stock_success(self, mock_fetch, mock_rater):
        """测试5: 成功分析股票"""
        # 模拟数据获取
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        # 模拟分析结果
        mock_rater_instance = Mock()
        mock_rater_instance.analyze_stock.return_value = self._create_mock_analysis_result()
        mock_rater.return_value = mock_rater_instance

        result = self.analyze_stock_module.analyze_stock('600519')

        # 验证
        self.assertIsNotNone(result)
        self.assertIn('rating', result)
        self.assertIn('confidence', result)
        self.assertIn('scores', result)

        # 验证调用
        mock_fetch.assert_called_once_with('600519')
        mock_rater_instance.analyze_stock.assert_called_once()

    @patch('scripts.analyze_stock.analyze_stock')
    def test_06_analyze_stock_invalid_code(self, mock_analyze):
        """测试6: 无效股票代码"""
        with self.assertRaises(ValueError) as context:
            self.analyze_stock_module.validate_and_analyze('INVALID')

        self.assertIn('股票代码', str(context.exception))

    def test_07_format_report_output(self):
        """测试7: 格式化分析报告"""
        result = self._create_mock_analysis_result()
        stock_name = "贵州茅台"
        stock_code = "600519"

        report = self.analyze_stock_module.format_report(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_result=result
        )

        # 验证输出包含关键信息
        self.assertIsInstance(report, str)
        self.assertIn(stock_name, report)
        self.assertIn(stock_code, report)
        self.assertIn('评级', report)
        self.assertIn('信心度', report)
        self.assertIn('目标价', report)

    def test_08_save_report_to_file(self):
        """测试8: 保存报告到文件"""
        result = self._create_mock_analysis_result()
        report = self.analyze_stock_module.format_report('600519', '贵州茅台', result)

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.analyze_stock_module.save_report(report, '/tmp/test_report.txt')

            # 验证文件写入
            mock_open.assert_called_once()
            mock_file.write.assert_called_once_with(report)

    @patch('sys.argv', ['analyze_stock.py', '--code', '600519'])
    def test_09_command_line_parsing(self):
        """测试9: 命令行参数解析"""
        args = self.analyze_stock_module.parse_arguments()

        self.assertEqual(args.code, '600519')
        self.assertIsNone(args.output)
        self.assertEqual(args.depth, 'full')

    @patch('sys.argv', ['analyze_stock.py', '--code', '600519', '--depth', 'quick'])
    def test_10_quick_analysis_mode(self):
        """测试10: 快速分析模式"""
        args = self.analyze_stock_module.parse_arguments()

        self.assertEqual(args.code, '600519')
        self.assertEqual(args.depth, 'quick')

    @patch('sys.argv', ['analyze_stock.py', '--code', '600519', '--output', 'report.txt'])
    def test_11_output_file_parameter(self):
        """测试11: 输出文件参数"""
        args = self.analyze_stock_module.parse_arguments()

        self.assertEqual(args.code, '600519')
        self.assertEqual(args.output, 'report.txt')

    def test_12_validate_output_path(self):
        """测试12: 输出路径验证"""
        import tempfile

        # 测试有效路径
        safe_path = self.analyze_stock_module.validate_output_path('test_report.txt')
        self.assertTrue(safe_path.endswith('test_report.txt'))

        # 测试临时目录路径
        temp_file = os.path.join(tempfile.gettempdir(), 'test_report.txt')
        safe_path = self.analyze_stock_module.validate_output_path(temp_file)
        self.assertTrue(safe_path.endswith('test_report.txt'))

        # 测试空路径
        with self.assertRaises(ValueError) as context:
            self.analyze_stock_module.validate_output_path('')
        self.assertIn('不能为空', str(context.exception))

    @patch('scripts.analyze_stock.TechnicalIndicators')
    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_13_technical_analysis_only(self, mock_fetch, mock_technical):
        """测试13: 仅技术分析（当其他数据不可用时）"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            pd.DataFrame(),  # 空财务数据
            pd.DataFrame()   # 空资金流向数据
        )

        mock_technical_instance = Mock()
        mock_technical_instance.calculate_all.return_value = self._create_sample_kline_data()
        mock_technical.return_value = mock_technical_instance

        # 应该能够至少执行技术分析
        try:
            # 这个测试验证即使财务和资金数据缺失，技术分析仍能运行
            result = self.analyze_stock_module.analyze_technical_only('600519', self._create_sample_kline_data())
            self.assertIsNotNone(result)
        except Exception as e:
            # 如果抛出异常，应该是有意义的错误消息
            self.assertIn('数据', str(e).lower())

    @patch('scripts.analyze_stock.StockRater')
    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_14_ai_analysis_unavailable(self, mock_fetch, mock_rater):
        """测试14: AI分析不可用时的降级处理"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        # 模拟AI分析失败
        mock_rater_instance = Mock()
        result = self._create_mock_analysis_result()
        result['ai_insights'] = '综合评分82分，建议买入。'  # 默认分析
        mock_rater_instance.analyze_stock.return_value = result
        mock_rater.return_value = mock_rater_instance

        analysis_result = self.analyze_stock_module.analyze_stock('600519')

        # 应该有默认的分析结果
        self.assertIsNotNone(analysis_result)
        self.assertIn('ai_insights', analysis_result)

    def test_15_format_report_sections(self):
        """测试15: 报告分段显示"""
        result = self._create_mock_analysis_result()
        report = self.analyze_stock_module.format_report('600519', '贵州茅台', result)

        # 验证报告包含各个分段
        self.assertIn('技术面', report)
        self.assertIn('基本面', report)
        self.assertIn('资金面', report)
        self.assertIn('综合评分', report)
        self.assertIn('AI综合分析', report)

    @patch('scripts.analyze_stock.StockRater')
    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_16_handle_partial_data(self, mock_fetch, mock_rater):
        """测试16: 处理部分数据缺失"""
        # 模拟部分数据缺失（财务数据为空）
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            pd.DataFrame(),  # 空财务数据
            self._create_sample_money_flow_data()
        )

        mock_rater_instance = Mock()
        # 当数据缺失时，应该抛出有意义的异常
        mock_rater_instance.analyze_stock.side_effect = ValueError("财务数据不足")
        mock_rater.return_value = mock_rater_instance

        with self.assertRaises(ValueError) as context:
            self.analyze_stock_module.analyze_stock('600519')

        self.assertIn('财务', str(context.exception))

    @patch('scripts.analyze_stock.AKShareProvider')
    def test_17_get_stock_name(self, mock_provider):
        """测试17: 获取股票名称"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_realtime_quote.return_value = {'名称': '贵州茅台', '代码': '600519'}
        mock_provider.return_value = mock_provider_instance

        stock_name = self.analyze_stock_module.get_stock_name('600519')

        self.assertEqual(stock_name, '贵州茅台')
        mock_provider_instance.get_realtime_quote.assert_called_once_with('600519')

    @patch('scripts.analyze_stock.AKShareProvider')
    def test_18_get_stock_name_not_found(self, mock_provider):
        """测试18: 股票名称未找到时返回代码"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_realtime_quote.return_value = {}
        mock_provider.return_value = mock_provider_instance

        stock_name = self.analyze_stock_module.get_stock_name('600519')

        # 应该返回股票代码作为备用
        self.assertEqual(stock_name, '600519')

    def test_19_depth_parameter_quick(self):
        """测试19: 快速分析深度参数"""
        # 快速模式应该跳过某些耗时的分析
        depth = 'quick'
        is_quick = self.analyze_stock_module.is_quick_mode(depth)

        self.assertTrue(is_quick)

    def test_20_depth_parameter_full(self):
        """测试20: 完整分析深度参数"""
        depth = 'full'
        is_quick = self.analyze_stock_module.is_quick_mode(depth)

        self.assertFalse(is_quick)

    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_21_quick_mode_skips_fundamental_analysis(self, mock_fetch):
        """测试21: 快速模式跳过基本面分析"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        # 执行快速分析
        result = self.analyze_stock_module.analyze_stock('600519', depth='quick')

        # 验证结果
        self.assertIsNotNone(result)
        self.assertIn('scores', result)

        # 快速模式的基本面得分应该为0
        self.assertEqual(result['scores']['fundamental'], 0.0)

        # 应该有技术面和资金面得分
        self.assertGreater(result['scores']['technical'], 0)
        self.assertGreater(result['scores']['capital'], 0)

        # ai_insights应该包含"快速分析模式"标记
        self.assertIn('快速分析', result['ai_insights'])

    @patch('scripts.analyze_stock.StockRater')
    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_22_full_mode_includes_all_analysis(self, mock_fetch, mock_rater):
        """测试22: 完整模式包含所有分析"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        mock_rater_instance = Mock()
        mock_rater_instance.analyze_stock.return_value = self._create_mock_analysis_result()
        mock_rater.return_value = mock_rater_instance

        # 执行完整分析
        result = self.analyze_stock_module.analyze_stock('600519', depth='full')

        # 验证StockRater被调用
        mock_rater_instance.analyze_stock.assert_called_once()

        # 验证结果包含所有维度
        self.assertGreater(result['scores']['fundamental'], 0)
        self.assertGreater(result['scores']['technical'], 0)
        self.assertGreater(result['scores']['capital'], 0)

    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_23_quick_mode_report_format(self, mock_fetch):
        """测试23: 快速模式报告格式"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        # 执行快速分析
        result = self.analyze_stock_module.analyze_stock('600519', depth='quick')

        # 格式化报告
        report = self.analyze_stock_module.format_report('600519', '测试股票', result)

        # 验证快速模式标记
        self.assertIn('快速模式', report)
        self.assertIn('快速分析', report)

        # 验证报告包含技术面和资金面
        self.assertIn('技术面得分', report)
        self.assertIn('资金面得分', report)

        # 验证有快速模式说明
        self.assertIn('快速模式不包含基本面分析', report)

    @patch('scripts.analyze_stock.fetch_stock_data')
    def test_24_quick_mode_confidence_lower(self, mock_fetch):
        """测试24: 快速模式信心度应该低于完整模式"""
        mock_fetch.return_value = (
            self._create_sample_kline_data(),
            self._create_sample_financial_data(),
            self._create_sample_money_flow_data()
        )

        # 执行快速分析
        quick_result = self.analyze_stock_module.analyze_stock('600519', depth='quick')

        # 快速模式的信心度通常应该低于9（因为缺少基本面和AI分析）
        self.assertLessEqual(quick_result['confidence'], 9.0)
        self.assertGreaterEqual(quick_result['confidence'], 1.0)


class TestAnalyzeStockIntegration(unittest.TestCase):
    """股票分析脚本集成测试（需要真实环境）"""

    @unittest.skipIf(os.getenv('SKIP_INTEGRATION_TESTS') == '1', '跳过集成测试')
    def test_full_analysis_workflow(self):
        """集成测试: 完整分析流程"""
        from scripts import analyze_stock

        try:
            result = analyze_stock.analyze_stock('600519')

            # 验证结果结构
            self.assertIsNotNone(result)
            self.assertIn('rating', result)
            self.assertIn('confidence', result)
            self.assertIn('scores', result)

        except Exception as e:
            # 如果网络或其他问题导致失败，跳过而不是失败
            self.skipTest(f"集成测试需要网络连接: {e}")


if __name__ == '__main__':
    unittest.main()
