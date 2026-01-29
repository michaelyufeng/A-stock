#!/usr/bin/env python
"""
tests/scripts/test_run_screening.py - 批量筛选脚本测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
from io import StringIO
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestScreeningConstants(unittest.TestCase):
    """测试常量定义"""

    def test_constants_defined(self):
        """测试常量是否定义"""
        # 这个测试会在我们实现脚本后通过
        # 导入时会自动检查常量是否存在
        from scripts import run_screening

        # 验证预设条件
        self.assertIn('strong_momentum', run_screening.PRESET_FILTERS)
        self.assertIn('value_growth', run_screening.PRESET_FILTERS)
        self.assertIn('capital_inflow', run_screening.PRESET_FILTERS)

        # 验证默认值常量
        self.assertEqual(run_screening.DEFAULT_TOP_N, 20)
        self.assertGreaterEqual(run_screening.MIN_SCORE, 0)
        self.assertLessEqual(run_screening.MIN_SCORE, 100)


class TestValidateTopN(unittest.TestCase):
    """测试TOP N参数验证"""

    def test_validate_top_n_valid(self):
        """测试有效的TOP N参数"""
        from scripts.run_screening import validate_top_n

        # 有效值应该通过
        self.assertIsNone(validate_top_n(1))
        self.assertIsNone(validate_top_n(20))
        self.assertIsNone(validate_top_n(100))

    def test_validate_top_n_too_small(self):
        """测试过小的TOP N参数"""
        from scripts.run_screening import validate_top_n

        with self.assertRaises(ValueError) as ctx:
            validate_top_n(0)
        self.assertIn('至少为1', str(ctx.exception))

    def test_validate_top_n_too_large(self):
        """测试过大的TOP N参数"""
        from scripts.run_screening import validate_top_n

        with self.assertRaises(ValueError) as ctx:
            validate_top_n(1001)
        self.assertIn('不能超过1000', str(ctx.exception))


class TestValidatePreset(unittest.TestCase):
    """测试预设条件验证"""

    def test_validate_preset_valid(self):
        """测试有效的预设条件"""
        from scripts.run_screening import validate_preset

        # 有效预设应该返回True
        self.assertTrue(validate_preset('strong_momentum'))
        self.assertTrue(validate_preset('value_growth'))
        self.assertTrue(validate_preset('capital_inflow'))

    def test_validate_preset_invalid(self):
        """测试无效的预设条件"""
        from scripts.run_screening import validate_preset

        # 无效预设应该返回False
        self.assertFalse(validate_preset('invalid_preset'))
        self.assertFalse(validate_preset(''))
        self.assertFalse(validate_preset(None))


class TestValidateMaxWorkers(unittest.TestCase):
    """测试并行工作线程数验证"""

    def test_validate_max_workers_valid(self):
        """测试有效的max_workers参数"""
        from scripts.run_screening import validate_max_workers

        # 有效值应该通过
        self.assertIsNone(validate_max_workers(1))
        self.assertIsNone(validate_max_workers(5))
        self.assertIsNone(validate_max_workers(10))
        self.assertIsNone(validate_max_workers(20))

    def test_validate_max_workers_too_small(self):
        """测试过小的max_workers参数"""
        from scripts.run_screening import validate_max_workers

        with self.assertRaises(ValueError) as ctx:
            validate_max_workers(0)
        self.assertIn('至少为1', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            validate_max_workers(-1)
        self.assertIn('至少为1', str(ctx.exception))

    def test_validate_max_workers_too_large(self):
        """测试过大的max_workers参数"""
        from scripts.run_screening import validate_max_workers

        with self.assertRaises(ValueError) as ctx:
            validate_max_workers(21)
        self.assertIn('不能超过20', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            validate_max_workers(100)
        self.assertIn('不能超过20', str(ctx.exception))


class TestValidateStockPool(unittest.TestCase):
    """测试股票池参数验证"""

    def test_validate_stock_pool_none(self):
        """测试None股票池（允许）"""
        from scripts.run_screening import validate_stock_pool

        # None应该通过（表示全市场）
        self.assertIsNone(validate_stock_pool(None))

    def test_validate_stock_pool_valid(self):
        """测试有效的股票池"""
        from scripts.run_screening import validate_stock_pool

        # 有效的股票代码应该通过
        self.assertIsNone(validate_stock_pool(['600519', '000858', '000001']))
        self.assertIsNone(validate_stock_pool(['600519.SH', '000858.SZ']))

    def test_validate_stock_pool_empty_list(self):
        """测试空列表"""
        from scripts.run_screening import validate_stock_pool

        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool([])
        self.assertIn('不能为空列表', str(ctx.exception))

    def test_validate_stock_pool_not_list(self):
        """测试非列表类型"""
        from scripts.run_screening import validate_stock_pool

        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool("600519")
        self.assertIn('必须是列表类型', str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool({'600519'})
        self.assertIn('必须是列表类型', str(ctx.exception))

    def test_validate_stock_pool_invalid_code_format(self):
        """测试无效的股票代码格式"""
        from scripts.run_screening import validate_stock_pool

        # 代码太短
        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool(['60051'])
        self.assertIn('无效的股票代码', str(ctx.exception))

        # 代码太长
        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool(['6005199'])
        self.assertIn('无效的股票代码', str(ctx.exception))

        # 包含字母（除了后缀）
        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool(['60051A'])
        self.assertIn('无效的股票代码', str(ctx.exception))

        # 无效的市场后缀
        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool(['600519.BJ'])
        self.assertIn('无效的股票代码', str(ctx.exception))

    def test_validate_stock_pool_mixed_valid_invalid(self):
        """测试混合有效和无效的股票代码"""
        from scripts.run_screening import validate_stock_pool

        with self.assertRaises(ValueError) as ctx:
            validate_stock_pool(['600519', 'INVALID', '000858'])
        self.assertIn('无效的股票代码', str(ctx.exception))
        self.assertIn('INVALID', str(ctx.exception))


class TestRunScreening(unittest.TestCase):
    """测试筛选执行"""

    @patch('scripts.run_screening.StockScreener')
    def test_run_screening_basic(self, mock_screener_class):
        """测试基本筛选执行"""
        from scripts.run_screening import run_screening

        # 模拟筛选结果
        mock_result = pd.DataFrame({
            'code': ['600519', '000858'],
            'name': ['贵州茅台', '五粮液'],
            'score': [85.5, 82.3],
            'tech_score': [80, 78],
            'fundamental_score': [90, 85],
            'capital_score': [86, 84],
            'current_price': [1800.5, 150.2],
            'reason': ['技术面强势', '基本面优秀']
        })

        # 配置mock
        mock_screener = Mock()
        mock_screener.screen.return_value = mock_result
        mock_screener_class.return_value = mock_screener

        # 执行筛选
        result = run_screening(preset='strong_momentum', top_n=20)

        # 验证调用
        mock_screener.screen.assert_called_once()
        call_args = mock_screener.screen.call_args
        self.assertEqual(call_args[1]['preset'], 'strong_momentum')
        self.assertEqual(call_args[1]['top_n'], 20)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    @patch('scripts.run_screening.StockScreener')
    def test_run_screening_empty_result(self, mock_screener_class):
        """测试筛选结果为空"""
        from scripts.run_screening import run_screening

        # 模拟空结果
        mock_screener = Mock()
        mock_screener.screen.return_value = pd.DataFrame()
        mock_screener_class.return_value = mock_screener

        # 执行筛选
        result = run_screening(preset='strong_momentum', top_n=20)

        # 验证结果
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    @patch('scripts.run_screening.StockScreener')
    def test_run_screening_with_min_score(self, mock_screener_class):
        """测试带最低分数的筛选"""
        from scripts.run_screening import run_screening

        mock_screener = Mock()
        mock_screener.screen.return_value = pd.DataFrame()
        mock_screener_class.return_value = mock_screener

        # 执行筛选
        run_screening(preset='strong_momentum', top_n=20, min_score=70.0)

        # 验证参数传递
        call_args = mock_screener.screen.call_args
        self.assertEqual(call_args[1]['min_score'], 70.0)


class TestFormatScreeningResults(unittest.TestCase):
    """测试结果格式化"""

    def test_format_results_table(self):
        """测试表格格式化"""
        from scripts.run_screening import format_results_table

        # 创建测试数据
        df = pd.DataFrame({
            'code': ['600519', '000858'],
            'name': ['贵州茅台', '五粮液'],
            'score': [85.5, 82.3],
            'tech_score': [80.0, 78.0],
            'fundamental_score': [90.0, 85.0],
            'capital_score': [86.0, 84.0],
            'current_price': [1800.5, 150.2],
            'reason': ['技术面强势', '基本面优秀']
        })

        # 格式化
        result = format_results_table(df)

        # 验证结果包含必要信息
        self.assertIsInstance(result, str)
        self.assertIn('600519', result)
        self.assertIn('贵州茅台', result)
        self.assertIn('85.5', result)

    def test_format_results_empty(self):
        """测试空结果格式化"""
        from scripts.run_screening import format_results_table

        df = pd.DataFrame()
        result = format_results_table(df)

        # 验证空结果消息
        self.assertIsInstance(result, str)
        self.assertIn('未找到', result)

    def test_format_results_missing_columns(self):
        """测试缺少必需列的格式化"""
        from scripts.run_screening import format_results_table

        # 缺少'code'列
        df = pd.DataFrame({
            'name': ['贵州茅台'],
            'score': [85.5],
            'current_price': [1800.5]
        })

        with self.assertRaises(ValueError) as ctx:
            format_results_table(df)
        self.assertIn('缺少必需的列', str(ctx.exception))
        self.assertIn('code', str(ctx.exception))


class TestExportResults(unittest.TestCase):
    """测试结果导出"""

    def test_export_csv(self):
        """测试CSV导出"""
        from scripts.run_screening import export_results

        # 创建测试数据
        df = pd.DataFrame({
            'code': ['600519'],
            'name': ['贵州茅台'],
            'score': [85.5]
        })

        # 创建临时文件路径
        temp_path = Path('/tmp/test_screening.csv')

        try:
            # 导出
            export_results(df, str(temp_path))

            # 验证文件存在
            self.assertTrue(temp_path.exists())

            # 验证内容
            df_loaded = pd.read_csv(temp_path)
            self.assertEqual(len(df_loaded), 1)
            self.assertEqual(str(df_loaded['code'].iloc[0]), '600519')

        finally:
            # 清理
            if temp_path.exists():
                temp_path.unlink()

    def test_export_excel(self):
        """测试Excel导出"""
        from scripts.run_screening import export_results

        # 创建测试数据
        df = pd.DataFrame({
            'code': ['600519'],
            'name': ['贵州茅台'],
            'score': [85.5]
        })

        # 创建临时文件路径
        temp_path = Path('/tmp/test_screening.xlsx')

        try:
            # 导出
            export_results(df, str(temp_path))

            # 验证文件存在
            self.assertTrue(temp_path.exists())

            # 验证内容
            df_loaded = pd.read_excel(temp_path)
            self.assertEqual(len(df_loaded), 1)
            self.assertEqual(str(df_loaded['code'].iloc[0]), '600519')

        finally:
            # 清理
            if temp_path.exists():
                temp_path.unlink()

    def test_export_invalid_extension(self):
        """测试不支持的文件格式"""
        from scripts.run_screening import export_results

        df = pd.DataFrame({'code': ['600519']})

        with self.assertRaises(ValueError) as ctx:
            export_results(df, '/tmp/test.txt')
        self.assertIn('不支持的文件格式', str(ctx.exception))


class TestParseArguments(unittest.TestCase):
    """测试参数解析"""

    @patch('sys.argv', ['run_screening.py', '--preset', 'strong_momentum'])
    def test_parse_arguments_basic(self):
        """测试基本参数解析"""
        from scripts.run_screening import parse_arguments

        args = parse_arguments()

        self.assertEqual(args.preset, 'strong_momentum')
        self.assertEqual(args.top, 20)  # 默认值
        self.assertIsNone(args.output)

    @patch('sys.argv', ['run_screening.py', '--preset', 'value_growth', '--top', '50'])
    def test_parse_arguments_with_top(self):
        """测试带TOP参数的解析"""
        from scripts.run_screening import parse_arguments

        args = parse_arguments()

        self.assertEqual(args.preset, 'value_growth')
        self.assertEqual(args.top, 50)

    @patch('sys.argv', ['run_screening.py', '--preset', 'capital_inflow', '--output', 'results.csv'])
    def test_parse_arguments_with_output(self):
        """测试带输出参数的解析"""
        from scripts.run_screening import parse_arguments

        args = parse_arguments()

        self.assertEqual(args.preset, 'capital_inflow')
        self.assertEqual(args.output, 'results.csv')


class TestMainFunction(unittest.TestCase):
    """测试主函数"""

    @patch('sys.argv', ['run_screening.py', '--preset', 'strong_momentum'])
    @patch('scripts.run_screening.run_screening')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_run_screening):
        """测试主函数成功执行"""
        from scripts.run_screening import main

        # 模拟筛选结果（包含必需的列）
        mock_result = pd.DataFrame({
            'code': ['600519'],
            'name': ['贵州茅台'],
            'score': [85.5],
            'tech_score': [80.0],
            'fundamental_score': [90.0],
            'capital_score': [86.0],
            'current_price': [1800.5],
            'reason': ['技术面强势']
        })
        mock_run_screening.return_value = mock_result

        # 执行主函数
        main()

        # 验证筛选被调用
        mock_run_screening.assert_called_once()

    @patch('sys.argv', ['run_screening.py', '--preset', 'strong_momentum', '--top', '0'])
    @patch('builtins.print')
    def test_main_invalid_top_n(self, mock_print):
        """测试主函数处理无效TOP N参数"""
        from scripts.run_screening import main

        # 执行主函数应该捕获异常
        with self.assertRaises(SystemExit):
            main()


class TestOutputPathValidation(unittest.TestCase):
    """测试输出路径验证"""

    def test_validate_output_path_csv(self):
        """测试CSV路径验证"""
        from scripts.run_screening import validate_output_path

        # 使用临时目录
        path = '/tmp/test.csv'
        validated = validate_output_path(path)

        self.assertIsInstance(validated, str)
        self.assertTrue(validated.endswith('.csv'))

    def test_validate_output_path_excel(self):
        """测试Excel路径验证"""
        from scripts.run_screening import validate_output_path

        path = '/tmp/test.xlsx'
        validated = validate_output_path(path)

        self.assertIsInstance(validated, str)
        self.assertTrue(validated.endswith('.xlsx'))

    def test_validate_output_path_invalid_directory(self):
        """测试不存在的目录"""
        from scripts.run_screening import validate_output_path

        with self.assertRaises(ValueError) as ctx:
            validate_output_path('/nonexistent/directory/test.csv')
        # 由于路径不在安全目录下，会抛出"不安全的输出路径"错误
        self.assertIn('不安全', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
