"""股票报告生成器测试"""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.reporting.stock_report import StockReportGenerator


@pytest.fixture
def mock_buy_analysis_result():
    """模拟买入评级的分析结果"""
    return {
        'rating': 'buy',
        'confidence': 8.5,
        'target_price': 15.80,
        'stop_loss': 13.50,
        'reasons': [
            '技术面呈现强势上涨趋势',
            '基本面良好，财务指标健康',
            '主力资金持续流入，市场情绪积极'
        ],
        'risks': [
            '市场整体波动可能影响个股表现',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            '建议分批建仓，降低单次买入风险'
        ],
        'ai_insights': '综合评分75分，建议买入。技术面、基本面和资金面综合表现良好，信心度8.5/10。建议关注买入时机，分批建仓以降低风险。',
        'scores': {
            'technical': 78.5,
            'fundamental': 72.3,
            'capital': 80.0,
            'overall': 75.2
        }
    }


@pytest.fixture
def mock_hold_analysis_result():
    """模拟持有评级的分析结果"""
    return {
        'rating': 'hold',
        'confidence': 6.0,
        'target_price': 14.42,
        'stop_loss': 13.02,
        'reasons': [
            '综合指标显示震荡整理，建议观望',
            '技术面处于平衡状态'
        ],
        'risks': [
            '横盘整理期间可能出现方向选择',
            '需关注市场和个股基本面变化',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出'
        ],
        'ai_insights': '综合评分58分，建议持有观望。当前处于震荡整理阶段，信心度6.0/10。建议等待明确方向信号后再做决策。',
        'scores': {
            'technical': 55.0,
            'fundamental': 60.0,
            'capital': 58.0,
            'overall': 58.0
        }
    }


@pytest.fixture
def mock_sell_analysis_result():
    """模拟卖出评级的分析结果"""
    return {
        'rating': 'sell',
        'confidence': 7.8,
        'target_price': 12.60,
        'stop_loss': 13.72,
        'reasons': [
            '技术面走弱，下跌趋势明显',
            '主力资金流出，市场情绪悲观',
            '资金流向信号显示卖出风险'
        ],
        'risks': [
            '继续持有可能面临进一步下跌风险',
            '建议及时止损，避免损失扩大',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            'T+1限制下，需提前规划卖出时机'
        ],
        'ai_insights': '综合评分35分，建议卖出。多项指标显示下行风险，信心度7.8/10。建议及时止损，避免损失进一步扩大。',
        'scores': {
            'technical': 30.0,
            'fundamental': 38.0,
            'capital': 35.0,
            'overall': 35.0
        }
    }


@pytest.fixture
def sample_kline_df():
    """模拟K线数据"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'close': [14.0, 14.2, 14.5, 14.3, 14.0],
        'open': [13.8, 14.1, 14.2, 14.4, 14.2],
        'high': [14.3, 14.4, 14.6, 14.5, 14.3],
        'low': [13.7, 13.9, 14.1, 14.2, 13.9],
        'volume': [1000000, 1200000, 1500000, 1100000, 900000],
        'MA5': [13.9, 14.0, 14.1, 14.2, 14.2],
        'MA20': [13.5, 13.6, 13.7, 13.8, 13.9],
        'MACD': [0.05, 0.08, 0.10, 0.07, 0.05],
        'MACD_signal': [0.03, 0.05, 0.07, 0.06, 0.04],
        'RSI': [55.0, 58.0, 62.0, 60.0, 58.0],
        'K': [60.0, 65.0, 70.0, 68.0, 65.0],
        'D': [55.0, 58.0, 62.0, 65.0, 66.0],
        'BOLL_UPPER': [15.0, 15.1, 15.2, 15.1, 15.0],
        'BOLL_MIDDLE': [14.0, 14.1, 14.2, 14.1, 14.0],
        'BOLL_LOWER': [13.0, 13.1, 13.2, 13.1, 13.0],
        'VOL_MA5': [1000000, 1050000, 1100000, 1150000, 1140000],
        'ATR': [0.30, 0.32, 0.35, 0.33, 0.31]
    })


class TestStockReportGenerator:
    """测试StockReportGenerator类"""

    def test_init(self):
        """测试初始化"""
        generator = StockReportGenerator()
        assert generator is not None

    def test_generate_report_buy_rating(self, mock_buy_analysis_result, sample_kline_df):
        """测试生成买入评级报告"""
        generator = StockReportGenerator()

        report = generator.generate_report(
            stock_code='000001',
            stock_name='平安银行',
            analysis_result=mock_buy_analysis_result,
            kline_df=sample_kline_df
        )

        # 验证报告内容
        assert isinstance(report, str)
        assert len(report) > 0

        # 验证标题
        assert '# 股票分析报告' in report
        assert '000001' in report
        assert '平安银行' in report

        # 验证投资决策部分
        assert '## 📊 投资决策' in report
        assert '买入' in report
        assert '15.80' in report  # target_price
        assert '13.50' in report  # stop_loss
        assert '8.5/10' in report  # confidence

        # 验证核心理由
        assert '## 💡 核心理由' in report
        assert '技术面呈现强势上涨趋势' in report

        # 验证风险提示
        assert '## ⚠️ 风险提示' in report
        assert '### 通用风险' in report
        assert '### A股特色风险' in report
        assert 'T+1交易制度' in report

        # 验证详细分析
        assert '## 📈 详细分析' in report
        assert '### 技术面分析' in report
        assert '### 基本面分析' in report
        assert '### 资金面分析' in report

        # 验证AI分析
        assert '## 🤖 AI综合分析' in report
        assert mock_buy_analysis_result['ai_insights'] in report

        # 验证综合评分
        assert '## 📊 综合评分' in report
        assert '78.5' in report  # technical score
        assert '75.2' in report  # overall score

        # 验证免责声明
        assert '免责声明' in report
        assert '股市有风险' in report

    def test_generate_report_hold_rating(self, mock_hold_analysis_result):
        """测试生成持有评级报告"""
        generator = StockReportGenerator()

        report = generator.generate_report(
            stock_code='600000',
            stock_name='浦发银行',
            analysis_result=mock_hold_analysis_result
        )

        assert isinstance(report, str)
        assert '持有' in report
        assert '600000' in report
        assert '浦发银行' in report
        assert '6.0/10' in report

    def test_generate_report_sell_rating(self, mock_sell_analysis_result):
        """测试生成卖出评级报告"""
        generator = StockReportGenerator()

        report = generator.generate_report(
            stock_code='601398',
            stock_name='工商银行',
            analysis_result=mock_sell_analysis_result
        )

        assert isinstance(report, str)
        assert '卖出' in report
        assert '601398' in report
        assert '工商银行' in report
        assert '7.8/10' in report

    def test_generate_report_without_kline_df(self, mock_buy_analysis_result):
        """测试不提供K线数据时生成报告"""
        generator = StockReportGenerator()

        report = generator.generate_report(
            stock_code='000002',
            stock_name='万科A',
            analysis_result=mock_buy_analysis_result,
            kline_df=None
        )

        assert isinstance(report, str)
        assert '000002' in report
        assert '万科A' in report
        # 应该仍然包含其他部分
        assert '## 📊 投资决策' in report
        assert '## 💡 核心理由' in report

    def test_save_to_file(self, mock_buy_analysis_result, tmp_path):
        """测试保存报告到文件"""
        generator = StockReportGenerator()

        output_path = tmp_path / "report.md"

        report = generator.generate_report(
            stock_code='000001',
            stock_name='平安银行',
            analysis_result=mock_buy_analysis_result,
            save_to_file=True,
            output_path=str(output_path)
        )

        # 验证文件被创建
        assert output_path.exists()

        # 验证文件内容
        content = output_path.read_text(encoding='utf-8')
        assert content == report
        assert '平安银行' in content

    def test_save_to_file_default_path(self, mock_buy_analysis_result, tmp_path):
        """测试使用默认路径保存报告"""
        generator = StockReportGenerator()

        with patch('src.reporting.stock_report.Path') as mock_path:
            # Mock the Path.cwd() to return tmp_path
            mock_path.cwd.return_value = tmp_path
            mock_file = tmp_path / 'stock_report_000001.md'
            mock_path.return_value = mock_file

            report = generator.generate_report(
                stock_code='000001',
                stock_name='平安银行',
                analysis_result=mock_buy_analysis_result,
                save_to_file=True
            )

            # 验证返回的是报告内容
            assert isinstance(report, str)
            assert '平安银行' in report

    def test_format_decision_section(self, mock_buy_analysis_result):
        """测试投资决策部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_decision_section(
            stock_code='000001',
            stock_name='平安银行',
            analysis_result=mock_buy_analysis_result
        )

        assert '## 📊 投资决策' in section
        assert '**评级**' in section
        assert '买入' in section
        assert '**目标价**' in section
        assert '15.80' in section
        assert '**止损价**' in section
        assert '13.50' in section
        assert '**信心度**' in section
        assert '8.5/10' in section

    def test_format_reasons_section(self, mock_buy_analysis_result):
        """测试核心理由部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_reasons_section(mock_buy_analysis_result)

        assert '## 💡 核心理由' in section
        assert '1. 技术面呈现强势上涨趋势' in section
        assert '2. 基本面良好，财务指标健康' in section
        assert '3. 主力资金持续流入，市场情绪积极' in section

    def test_format_risks_section(self, mock_buy_analysis_result):
        """测试风险提示部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_risks_section(mock_buy_analysis_result)

        assert '## ⚠️ 风险提示' in section
        assert '### 通用风险' in section
        assert '### A股特色风险' in section
        assert 'T+1交易制度' in section

    def test_format_technical_section_with_kline(self, mock_buy_analysis_result, sample_kline_df):
        """测试技术面分析部分格式化（含K线数据）"""
        generator = StockReportGenerator()

        section = generator._format_technical_section(
            mock_buy_analysis_result,
            sample_kline_df
        )

        assert '### 技术面分析' in section
        assert '| 指标 | 数值 | 评价 |' in section
        assert '**技术面评分**: 78.5/100' in section

    def test_format_technical_section_without_kline(self, mock_buy_analysis_result):
        """测试技术面分析部分格式化（无K线数据）"""
        generator = StockReportGenerator()

        section = generator._format_technical_section(
            mock_buy_analysis_result,
            None
        )

        assert '### 技术面分析' in section
        assert '**技术面评分**: 78.5/100' in section

    def test_format_fundamental_section(self, mock_buy_analysis_result):
        """测试基本面分析部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_fundamental_section(mock_buy_analysis_result)

        assert '### 基本面分析' in section
        assert '**基本面评分**: 72.3/100' in section

    def test_format_capital_section(self, mock_buy_analysis_result):
        """测试资金面分析部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_capital_section(mock_buy_analysis_result)

        assert '### 资金面分析' in section
        assert '**资金面评分**: 80.0/100' in section

    def test_format_ai_section(self, mock_buy_analysis_result):
        """测试AI分析部分格式化"""
        generator = StockReportGenerator()

        section = generator._format_ai_section(mock_buy_analysis_result)

        assert '## 🤖 AI综合分析' in section
        assert mock_buy_analysis_result['ai_insights'] in section

    def test_format_scores_table(self, mock_buy_analysis_result):
        """测试综合评分表格格式化"""
        generator = StockReportGenerator()

        section = generator._format_scores_table(mock_buy_analysis_result)

        assert '## 📊 综合评分' in section
        assert '| 维度 | 评分 | 权重 |' in section
        assert '| 技术面 | 78.5 | 30% |' in section
        assert '| 基本面 | 72.3 | 30% |' in section
        assert '| 资金面 | 80.0 | 25% |' in section
        assert '| **总分** | **75.2** | **100%** |' in section

    def test_rating_translation(self):
        """测试评级翻译"""
        generator = StockReportGenerator()

        assert generator._translate_rating('buy') == '买入'
        assert generator._translate_rating('hold') == '持有'
        assert generator._translate_rating('sell') == '卖出'
        assert generator._translate_rating('unknown') == 'unknown'

    def test_format_timestamp(self):
        """测试时间戳格式化"""
        generator = StockReportGenerator()

        timestamp = generator._format_timestamp()

        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # 验证格式类似：2024-01-29 10:30:00
        assert '-' in timestamp
        assert ':' in timestamp

    def test_markdown_table_formatting(self, sample_kline_df):
        """测试Markdown表格格式正确性"""
        generator = StockReportGenerator()

        # 测试技术指标表格
        table = generator._create_technical_table(sample_kline_df)

        # 验证表格包含正确的列
        assert '|' in table
        assert 'MA5' in table or 'RSI' in table or 'MACD' in table

        # 验证表头分隔符
        assert '|---' in table or '| ---' in table

    def test_empty_reasons_handling(self):
        """测试空理由列表的处理"""
        generator = StockReportGenerator()

        result = {
            'rating': 'buy',
            'reasons': [],
            'risks': [],
            'a_share_risks': [],
            'ai_insights': 'Test insights',
            'scores': {
                'technical': 70.0,
                'fundamental': 70.0,
                'capital': 70.0,
                'overall': 70.0
            },
            'confidence': 7.0,
            'target_price': 15.0,
            'stop_loss': 13.0
        }

        report = generator.generate_report(
            stock_code='000001',
            stock_name='测试股票',
            analysis_result=result
        )

        # 即使没有理由，报告也应该能生成
        assert isinstance(report, str)
        assert '000001' in report

    def test_special_characters_handling(self):
        """测试特殊字符处理"""
        generator = StockReportGenerator()

        result = {
            'rating': 'buy',
            'reasons': ['原因1 < > & "test"'],
            'risks': ['风险1 | test'],
            'a_share_risks': ['A股风险'],
            'ai_insights': 'AI分析 <test>',
            'scores': {
                'technical': 70.0,
                'fundamental': 70.0,
                'capital': 70.0,
                'overall': 70.0
            },
            'confidence': 7.0,
            'target_price': 15.0,
            'stop_loss': 13.0
        }

        report = generator.generate_report(
            stock_code='000001',
            stock_name='测试<股票>',
            analysis_result=result
        )

        # 特殊字符应该被保留或正确转义
        assert isinstance(report, str)
        assert len(report) > 0

    def test_score_rating_interpretation(self):
        """测试分数评级解释"""
        generator = StockReportGenerator()

        # 测试不同分数段的评级
        assert generator._interpret_score(85) == '优秀'
        assert generator._interpret_score(70) == '良好'
        assert generator._interpret_score(50) == '一般'
        assert generator._interpret_score(30) == '较差'

    def test_report_structure_completeness(self, mock_buy_analysis_result, sample_kline_df):
        """测试报告结构完整性"""
        generator = StockReportGenerator()

        report = generator.generate_report(
            stock_code='000001',
            stock_name='平安银行',
            analysis_result=mock_buy_analysis_result,
            kline_df=sample_kline_df
        )

        # 验证所有必要的部分都存在
        required_sections = [
            '# 股票分析报告',
            '生成时间:',
            '## 📊 投资决策',
            '## 💡 核心理由',
            '## ⚠️ 风险提示',
            '## 📈 详细分析',
            '### 技术面分析',
            '### 基本面分析',
            '### 资金面分析',
            '## 🤖 AI综合分析',
            '## 📊 综合评分',
            '免责声明'
        ]

        for section in required_sections:
            assert section in report, f"Missing section: {section}"
