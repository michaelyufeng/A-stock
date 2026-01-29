"""
HTML Reporter Tests
Tests for the HTMLReporter class that generates HTML stock analysis reports.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.reporting.html_reporter import HTMLReporter


class TestHTMLReporter:
    """Test cases for HTMLReporter class"""

    @pytest.fixture
    def sample_analysis_result(self):
        """Provides sample analysis result for testing"""
        return {
            'rating': 'buy',
            'confidence': 8.5,
            'target_price': 120.50,
            'stop_loss': 95.00,
            'reasons': [
                '技术面呈现强势上涨趋势',
                '主力资金持续流入，市场情绪积极',
                '基本面良好，盈利能力强'
            ],
            'risks': [
                '市场整体波动可能影响个股表现',
                '技术指标显示超买区域，短期可能回调'
            ],
            'a_share_risks': [
                'T+1交易制度限制，当日买入次日才能卖出',
                '科创板/创业板涨跌幅限制为20%，波动较大'
            ],
            'ai_insights': '综合分析显示该股票具有较好的投资价值。技术面强势，资金面活跃，建议关注买入时机。',
            'scores': {
                'technical': 85.50,
                'fundamental': 78.30,
                'capital': 82.00,
                'overall': 81.95
            }
        }

    @pytest.fixture
    def html_reporter(self):
        """Provides an instance of HTMLReporter"""
        return HTMLReporter()

    def test_html_reporter_initialization(self, html_reporter):
        """Test HTMLReporter can be initialized"""
        assert html_reporter is not None
        assert hasattr(html_reporter, 'generate_report')

    def test_generate_report_returns_string(self, html_reporter, sample_analysis_result):
        """Test that generate_report returns a string"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert isinstance(html, str)
        assert len(html) > 0

    def test_html_has_doctype(self, html_reporter, sample_analysis_result):
        """Test that generated HTML has proper DOCTYPE"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '<!DOCTYPE html>' in html or '<!doctype html>' in html

    def test_html_has_viewport_meta(self, html_reporter, sample_analysis_result):
        """Test that HTML includes viewport meta tag for responsive design"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert 'viewport' in html
        assert 'width=device-width' in html

    def test_html_includes_stock_code(self, html_reporter, sample_analysis_result):
        """Test that HTML includes stock code"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '600519' in html

    def test_html_includes_stock_name(self, html_reporter, sample_analysis_result):
        """Test that HTML includes stock name"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '贵州茅台' in html

    def test_html_includes_rating(self, html_reporter, sample_analysis_result):
        """Test that HTML includes rating"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        # Should include translated rating
        assert '买入' in html or 'buy' in html.lower()

    def test_html_includes_scores(self, html_reporter, sample_analysis_result):
        """Test that HTML includes all scores"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '85.50' in html or '85.5' in html  # technical score
        assert '78.30' in html or '78.3' in html  # fundamental score
        assert '82.00' in html or '82' in html or '82.0' in html  # capital score

    def test_html_includes_target_price(self, html_reporter, sample_analysis_result):
        """Test that HTML includes target price"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '120.50' in html or '120.5' in html

    def test_html_includes_stop_loss(self, html_reporter, sample_analysis_result):
        """Test that HTML includes stop loss"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '95.00' in html or '95' in html or '95.0' in html

    def test_html_includes_reasons(self, html_reporter, sample_analysis_result):
        """Test that HTML includes rating reasons"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        for reason in sample_analysis_result['reasons']:
            assert reason in html

    def test_html_includes_risks(self, html_reporter, sample_analysis_result):
        """Test that HTML includes risk warnings"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        for risk in sample_analysis_result['risks']:
            assert risk in html

    def test_html_includes_a_share_risks(self, html_reporter, sample_analysis_result):
        """Test that HTML includes A-share specific risks"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        for risk in sample_analysis_result['a_share_risks']:
            assert risk in html

    def test_html_includes_ai_insights(self, html_reporter, sample_analysis_result):
        """Test that HTML includes AI insights"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert sample_analysis_result['ai_insights'] in html

    def test_html_includes_disclaimer(self, html_reporter, sample_analysis_result):
        """Test that HTML includes disclaimer"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '免责声明' in html or '风险' in html

    def test_html_includes_chartjs(self, html_reporter, sample_analysis_result):
        """Test that HTML includes Chart.js for radar chart"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert 'chart.js' in html.lower() or 'chartjs' in html.lower()

    def test_html_autoescaping(self, html_reporter):
        """Test that HTML properly escapes user input to prevent XSS"""
        malicious_result = {
            'rating': 'buy',
            'confidence': 8.5,
            'target_price': 120.50,
            'stop_loss': 95.00,
            'reasons': ['<script>alert("XSS")</script>'],
            'risks': ['<img src=x onerror=alert(1)>'],
            'a_share_risks': [],
            'ai_insights': '<script>malicious()</script>',
            'scores': {
                'technical': 85.50,
                'fundamental': 78.30,
                'capital': 82.00,
                'overall': 81.95
            }
        }
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='<script>alert(1)</script>',
            analysis_result=malicious_result
        )
        # Should be escaped
        assert '<script>alert("XSS")</script>' not in html
        assert '<script>alert(1)</script>' not in html
        assert '<script>malicious()</script>' not in html
        # Escaped versions should be present
        assert '&lt;script&gt;' in html or html.count('<script') == 0

    def test_save_to_file(self, html_reporter, sample_analysis_result, tmp_path):
        """Test saving HTML report to file"""
        output_file = tmp_path / "test_report.html"

        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            save_to_file=True,
            output_path=str(output_file)
        )

        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        assert len(content) > 0
        assert '600519' in content

    def test_save_to_file_creates_parent_dirs(self, html_reporter, sample_analysis_result, tmp_path):
        """Test that saving creates parent directories if needed"""
        output_file = tmp_path / "subdir" / "test_report.html"

        html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result,
            save_to_file=True,
            output_path=str(output_file)
        )

        assert output_file.exists()

    def test_validate_output_path_security(self, html_reporter, sample_analysis_result):
        """Test that output path validation prevents path traversal"""
        with pytest.raises(ValueError):
            # Try to write outside safe directories
            html_reporter.generate_report(
                stock_code='600519',
                stock_name='贵州茅台',
                analysis_result=sample_analysis_result,
                save_to_file=True,
                output_path='/etc/passwd'
            )

    def test_rating_translation(self, html_reporter):
        """Test that ratings are properly translated to Chinese"""
        test_cases = [
            ('buy', '买入'),
            ('sell', '卖出'),
            ('hold', '持有')
        ]

        for rating_en, rating_zh in test_cases:
            result = {
                'rating': rating_en,
                'confidence': 7.0,
                'target_price': 100.0,
                'stop_loss': 90.0,
                'reasons': ['test'],
                'risks': ['test'],
                'a_share_risks': [],
                'ai_insights': 'test',
                'scores': {
                    'technical': 70.0,
                    'fundamental': 70.0,
                    'capital': 70.0,
                    'overall': 70.0
                }
            }
            html = html_reporter.generate_report(
                stock_code='600519',
                stock_name='测试股票',
                analysis_result=result
            )
            assert rating_zh in html

    def test_quick_mode_detection(self, html_reporter):
        """Test that quick mode is properly detected and displayed"""
        quick_result = {
            'rating': 'buy',
            'confidence': 7.5,
            'target_price': 100.0,
            'stop_loss': 90.0,
            'reasons': ['Quick analysis'],
            'risks': ['Quick risk'],
            'a_share_risks': [],
            'ai_insights': 'Quick insights',
            'scores': {
                'technical': 75.0,
                'fundamental': 0.0,  # Zero indicates quick mode
                'capital': 80.0,
                'overall': 77.5
            }
        }
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='测试股票',
            analysis_result=quick_result
        )
        assert '快速' in html or 'quick' in html.lower()

    def test_html_has_proper_encoding(self, html_reporter, sample_analysis_result):
        """Test that HTML has UTF-8 encoding specified"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert 'charset=utf-8' in html.lower() or 'charset="utf-8"' in html.lower()

    def test_confidence_display(self, html_reporter, sample_analysis_result):
        """Test that confidence is properly displayed"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        assert '8.5' in html  # confidence value
        assert '/10' in html or '/ 10' in html  # confidence scale

    def test_date_included_in_report(self, html_reporter, sample_analysis_result):
        """Test that analysis date is included in report"""
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='贵州茅台',
            analysis_result=sample_analysis_result
        )
        # Should contain a date in some format
        current_year = str(datetime.now().year)
        assert current_year in html

    def test_empty_reasons_handling(self, html_reporter):
        """Test handling of empty reasons list"""
        result = {
            'rating': 'hold',
            'confidence': 5.0,
            'target_price': 100.0,
            'stop_loss': 90.0,
            'reasons': [],  # Empty
            'risks': ['some risk'],
            'a_share_risks': [],
            'ai_insights': 'test',
            'scores': {
                'technical': 50.0,
                'fundamental': 50.0,
                'capital': 50.0,
                'overall': 50.0
            }
        }
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='测试股票',
            analysis_result=result
        )
        assert isinstance(html, str)
        assert len(html) > 0

    def test_empty_risks_handling(self, html_reporter):
        """Test handling of empty risks lists"""
        result = {
            'rating': 'hold',
            'confidence': 5.0,
            'target_price': 100.0,
            'stop_loss': 90.0,
            'reasons': ['some reason'],
            'risks': [],  # Empty
            'a_share_risks': [],  # Empty
            'ai_insights': 'test',
            'scores': {
                'technical': 50.0,
                'fundamental': 50.0,
                'capital': 50.0,
                'overall': 50.0
            }
        }
        html = html_reporter.generate_report(
            stock_code='600519',
            stock_name='测试股票',
            analysis_result=result
        )
        assert isinstance(html, str)
        assert len(html) > 0
