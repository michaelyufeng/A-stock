"""
Integration tests for HTML output in analyze_stock.py script
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.analyze_stock import save_html_report, parse_arguments


class TestAnalyzeStockHTMLIntegration:
    """Integration tests for HTML output feature"""

    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result for testing"""
        return {
            'rating': 'buy',
            'confidence': 8.5,
            'target_price': 120.50,
            'stop_loss': 95.00,
            'reasons': [
                '技术面呈现强势上涨趋势',
                '主力资金持续流入，市场情绪积极'
            ],
            'risks': ['市场整体波动可能影响个股表现'],
            'a_share_risks': ['T+1交易制度限制'],
            'ai_insights': '综合分析显示该股票具有较好的投资价值',
            'scores': {
                'technical': 85.50,
                'fundamental': 78.30,
                'capital': 82.00,
                'overall': 81.95
            }
        }

    def test_save_html_report_creates_file(self, sample_analysis_result, tmp_path):
        """Test that save_html_report creates HTML file"""
        output_file = tmp_path / "test_report.html"

        save_html_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            output_path=str(output_file)
        )

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert '600519' in content
        assert '贵州茅台' in content
        assert '<!DOCTYPE html>' in content or '<!doctype html>' in content

    def test_save_html_report_contains_analysis_data(self, sample_analysis_result, tmp_path):
        """Test that saved HTML contains analysis data"""
        output_file = tmp_path / "test_report.html"

        save_html_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            output_path=str(output_file)
        )

        content = output_file.read_text(encoding='utf-8')
        assert '买入' in content or 'buy' in content.lower()
        assert '8.5' in content
        assert '技术面呈现强势上涨趋势' in content

    def test_save_html_report_validates_path(self, sample_analysis_result):
        """Test that save_html_report validates output path"""
        with pytest.raises((ValueError, IOError)):
            save_html_report(
                stock_code='600519',
                stock_name='贵州茅台',
                analysis_result=sample_analysis_result,
                output_path='/etc/passwd'
            )

    def test_parse_arguments_includes_html_output(self):
        """Test that argument parser includes --html-output option"""
        test_args = ['--code', '600519', '--html-output', 'report.html']

        with patch('sys.argv', ['analyze_stock.py'] + test_args):
            args = parse_arguments()
            assert hasattr(args, 'html_output')
            assert args.html_output == 'report.html'

    def test_parse_arguments_html_output_optional(self):
        """Test that --html-output is optional"""
        test_args = ['--code', '600519']

        with patch('sys.argv', ['analyze_stock.py'] + test_args):
            args = parse_arguments()
            assert hasattr(args, 'html_output')
            assert args.html_output is None

    def test_parse_arguments_supports_both_outputs(self):
        """Test that both --output and --html-output can be used together"""
        test_args = [
            '--code', '600519',
            '--output', 'report.md',
            '--html-output', 'report.html'
        ]

        with patch('sys.argv', ['analyze_stock.py'] + test_args):
            args = parse_arguments()
            assert args.output == 'report.md'
            assert args.html_output == 'report.html'

    def test_html_output_with_quick_mode(self, sample_analysis_result, tmp_path):
        """Test HTML output works with quick mode analysis"""
        # Modify result to simulate quick mode
        quick_result = sample_analysis_result.copy()
        quick_result['scores']['fundamental'] = 0.0

        output_file = tmp_path / "quick_report.html"

        save_html_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=quick_result,
            output_path=str(output_file)
        )

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert '快速' in content or 'quick' in content.lower()

    def test_html_output_with_full_mode(self, sample_analysis_result, tmp_path):
        """Test HTML output works with full mode analysis"""
        output_file = tmp_path / "full_report.html"

        save_html_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            output_path=str(output_file)
        )

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        # Should contain all four dimension scores
        assert '78.30' in content or '78.3' in content  # fundamental score

    def test_html_file_is_valid_utf8(self, sample_analysis_result, tmp_path):
        """Test that generated HTML file is valid UTF-8"""
        output_file = tmp_path / "test_report.html"

        save_html_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            output_path=str(output_file)
        )

        # Should be able to read as UTF-8 without errors
        content = output_file.read_text(encoding='utf-8')
        assert len(content) > 0

    def test_html_output_error_handling(self, sample_analysis_result):
        """Test error handling in save_html_report"""
        # Test with invalid path
        with pytest.raises((ValueError, IOError)):
            save_html_report(
                stock_code='600519',
                stock_name='贵州茅台',
                analysis_result=sample_analysis_result,
                output_path='/nonexistent/directory/report.html'
            )
