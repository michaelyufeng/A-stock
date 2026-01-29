"""Tests for Stock Rater."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.analysis.ai.stock_rater import StockRater


class TestStockRater:
    """Stock Rater测试类"""

    @pytest.fixture
    def rater(self):
        """创建StockRater实例"""
        with patch('src.analysis.ai.stock_rater.TechnicalIndicators'), \
             patch('src.analysis.ai.stock_rater.FinancialMetrics'), \
             patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer'), \
             patch('src.analysis.ai.stock_rater.DeepSeekClient'):
            return StockRater()

    @pytest.fixture
    def sample_kline_df(self):
        """创建示例K线数据"""
        return pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=10),
            '开盘': np.random.uniform(10, 15, 10),
            '收盘': np.random.uniform(10, 15, 10),
            '最高': np.random.uniform(10, 15, 10),
            '最低': np.random.uniform(10, 15, 10),
            '成交量': np.random.uniform(1000000, 5000000, 10),
        })

    @pytest.fixture
    def sample_financial_df(self):
        """创建示例财务数据"""
        return pd.DataFrame({
            '净资产收益率': [15.5, 16.2, 17.0],
            '毛利率': [35.0, 36.0, 37.0],
            '净利润': [1000000, 1100000, 1200000],
            '营业收入': [5000000, 5500000, 6000000],
            '资产负债率': [45.0, 43.0, 42.0],
            '流动比率': [1.8, 1.9, 2.0],
            '市盈率': [18.0, 17.5, 17.0],
            '市净率': [2.5, 2.4, 2.3],
        })

    @pytest.fixture
    def sample_money_flow_df(self):
        """创建示例资金流向数据"""
        return pd.DataFrame({
            '主力净流入': [1000000, 1500000, 2000000, -500000, 800000],
            '成交量': [5000000, 6000000, 7000000, 4000000, 5500000],
        })

    def test_initialization(self, rater):
        """测试初始化"""
        assert rater is not None
        assert hasattr(rater, 'technical_indicators')
        assert hasattr(rater, 'financial_metrics')
        assert hasattr(rater, 'money_flow_analyzer')
        assert hasattr(rater, 'deepseek_client')

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_analyze_stock_basic(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试基本股票分析"""
        # 设置mock返回值
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0,
            'profitability': {'rating': '良好'},
            'growth': {'rating': '良好'},
            'financial_health': {'rating': '良好'},
            'valuation': {'rating': '良好'}
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000},
            'volume_trend': {'trend': '放量'},
            'recommendation': '建议买入'
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "综合分析：该股票技术面向好，基本面良好，建议买入。"

        # 创建rater
        rater = StockRater()

        # 执行分析
        result = rater.analyze_stock(
            stock_code="000001",
            kline_df=sample_kline_df,
            financial_df=sample_financial_df,
            money_flow_df=sample_money_flow_df
        )

        # 验证返回结果
        assert 'rating' in result
        assert 'confidence' in result
        assert 'target_price' in result
        assert 'stop_loss' in result
        assert 'reasons' in result
        assert 'risks' in result
        assert 'a_share_risks' in result
        assert 'ai_insights' in result
        assert 'scores' in result

        # 验证评级
        assert result['rating'] in ['buy', 'hold', 'sell']
        assert 1 <= result['confidence'] <= 10

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_buy_rating_threshold(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试买入评级阈值"""
        # 设置高分数（应该得到买入评级）
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 90.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 90.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 10000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "强烈建议买入"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        assert result['rating'] == 'buy'
        # Confidence should be reasonable for buy rating (at least 5.0)
        assert result['confidence'] >= 5.0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_sell_rating_threshold(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试卖出评级阈值"""
        # 设置低分数（应该得到卖出评级）
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 30.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 30.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '卖出'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '卖出',
            'main_force': {'trend': '流出', 'strength': '强', 'net_inflow': -10000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "建议卖出"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        assert result['rating'] == 'sell'

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_weighted_score_calculation(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试加权分数计算"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 80.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 80.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证综合分数在合理范围内
        assert 0 <= result['scores']['overall'] <= 100
        assert 'technical' in result['scores']
        assert 'fundamental' in result['scores']
        assert 'capital' in result['scores']

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_target_price_calculation(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试目标价计算"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证目标价和止损价
        assert result['target_price'] > 0
        assert result['stop_loss'] > 0
        # 目标价应该大于止损价
        current_price = sample_kline_df['收盘'].iloc[-1]
        if result['rating'] == 'buy':
            assert result['target_price'] > current_price
            assert result['stop_loss'] < current_price

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_a_share_risk_assessment(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试A股特有风险评估"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证A股风险列表
        assert isinstance(result['a_share_risks'], list)
        assert len(result['a_share_risks']) > 0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_ai_insights_generation(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试AI洞察生成"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        expected_insights = "这是AI生成的综合分析，包含详细的投资建议和风险提示。"
        mock_deepseek_instance.analyze_stock.return_value = expected_insights

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证AI洞察
        assert result['ai_insights'] == expected_insights
        assert len(result['ai_insights']) > 0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_reasons_and_risks(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试原因和风险列表生成"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 85.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 85.0,
            'profitability': {'rating': '优秀'},
            'growth': {'rating': '良好'}
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证原因列表
        assert isinstance(result['reasons'], list)
        assert len(result['reasons']) > 0

        # 验证风险列表
        assert isinstance(result['risks'], list)
        assert len(result['risks']) > 0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_empty_dataframe_handling(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试空DataFrame处理"""
        mock_technical.return_value = Mock()
        mock_financial.return_value = Mock()
        mock_money_flow.return_value = Mock()
        mock_deepseek.return_value = Mock()

        rater = StockRater()

        with pytest.raises(ValueError):
            rater.analyze_stock("000001", pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_confidence_score_range(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试信心度分数范围"""
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证信心度在1-10范围内
        assert 1 <= result['confidence'] <= 10
        assert isinstance(result['confidence'], (int, float))

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_column_name_handling_chinese(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试中文列名处理"""
        # 创建中文列名的数据
        kline_df = pd.DataFrame({
            '日期': pd.date_range('2024-01-01', periods=10),
            '开盘': np.random.uniform(10, 15, 10),
            '收盘': np.random.uniform(10, 15, 10),
            '最高': np.random.uniform(10, 15, 10),
            '最低': np.random.uniform(10, 15, 10),
            '成交量': np.random.uniform(1000000, 5000000, 10),
        })

        financial_df = pd.DataFrame({
            '净资产收益率': [15.5],
            '毛利率': [35.0],
        })

        money_flow_df = pd.DataFrame({
            '主力净流入': [1000000],
            '成交量': [5000000],
        })

        # 设置mock
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = kline_df.copy()

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", kline_df, financial_df, money_flow_df)

        # 验证结果正常返回
        assert result['rating'] in ['buy', 'hold', 'sell']
        assert result['target_price'] > 0
        assert result['stop_loss'] > 0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_column_name_handling_english(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试英文列名处理"""
        # 创建英文列名的数据
        kline_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'open': np.random.uniform(10, 15, 10),
            'close': np.random.uniform(10, 15, 10),
            'high': np.random.uniform(10, 15, 10),
            'low': np.random.uniform(10, 15, 10),
            'volume': np.random.uniform(1000000, 5000000, 10),
        })

        financial_df = pd.DataFrame({
            'roe': [15.5],
            'gross_margin': [35.0],
        })

        money_flow_df = pd.DataFrame({
            'main_net_inflow': [1000000],
            'volume': [5000000],
        })

        # 设置mock
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = kline_df.copy()

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("000001", kline_df, financial_df, money_flow_df)

        # 验证结果正常返回
        assert result['rating'] in ['buy', 'hold', 'sell']
        assert result['target_price'] > 0
        assert result['stop_loss'] > 0

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_insufficient_data_validation(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试数据长度不足验证"""
        # 创建只有1行的K线数据（少于最小要求2行）
        kline_df = pd.DataFrame({
            'close': [10.0],
        })

        financial_df = pd.DataFrame({
            'roe': [15.5],
        })

        money_flow_df = pd.DataFrame({
            'main_net_inflow': [1000000],
        })

        mock_technical.return_value = Mock()
        mock_financial.return_value = Mock()
        mock_money_flow.return_value = Mock()
        mock_deepseek.return_value = Mock()

        rater = StockRater()

        with pytest.raises(ValueError, match="K-line data must have at least 2 rows"):
            rater.analyze_stock("000001", kline_df, financial_df, money_flow_df)

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_missing_required_columns(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试缺少必需列验证"""
        # 创建缺少'close'列的数据
        kline_df = pd.DataFrame({
            'open': [10.0, 11.0],
            'high': [12.0, 13.0],
        })

        financial_df = pd.DataFrame({
            'roe': [15.5],
        })

        money_flow_df = pd.DataFrame({
            'main_net_inflow': [1000000],
        })

        mock_technical.return_value = Mock()
        mock_financial.return_value = Mock()
        mock_money_flow.return_value = Mock()
        mock_deepseek.return_value = Mock()

        rater = StockRater()

        with pytest.raises(ValueError, match="missing required columns"):
            rater.analyze_stock("000001", kline_df, financial_df, money_flow_df)

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_nan_values_handling(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical
    ):
        """测试NaN值处理"""
        # 创建包含NaN的数据
        kline_df = pd.DataFrame({
            'close': [10.0, np.nan, 12.0],
        })

        financial_df = pd.DataFrame({
            'roe': [15.5],
        })

        money_flow_df = pd.DataFrame({
            'main_net_inflow': [1000000],
        })

        mock_technical.return_value = Mock()
        mock_financial.return_value = Mock()
        mock_money_flow.return_value = Mock()
        mock_deepseek.return_value = Mock()

        rater = StockRater()

        with pytest.raises(ValueError, match="contains NaN values"):
            rater.analyze_stock("000001", kline_df, financial_df, money_flow_df)

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_st_stock_detection(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试ST股票风险检测"""
        # 设置mock
        mock_technical_instance = Mock()
        mock_technical.return_value = mock_technical_instance
        mock_technical_instance.calculate_all.return_value = sample_kline_df

        mock_financial_instance = Mock()
        mock_financial.return_value = mock_financial_instance
        mock_financial_instance.get_overall_score.return_value = 75.0
        mock_financial_instance.generate_summary.return_value = {
            'overall_score': 75.0
        }

        mock_money_flow_instance = Mock()
        mock_money_flow.return_value = mock_money_flow_instance
        mock_money_flow_instance.get_money_flow_signal.return_value = '买入'
        mock_money_flow_instance.generate_summary.return_value = {
            'signal': '买入',
            'main_force': {'trend': '流入', 'strength': '强', 'net_inflow': 5000000}
        }

        mock_deepseek_instance = Mock()
        mock_deepseek.return_value = mock_deepseek_instance
        mock_deepseek_instance.analyze_stock.return_value = "分析结果"

        rater = StockRater()
        result = rater.analyze_stock("ST000001", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 验证A股风险中包含ST股票风险提示
        assert any('ST股票退市风险' in risk for risk in result['a_share_risks'])

    @patch('src.analysis.ai.stock_rater.TechnicalIndicators')
    @patch('src.analysis.ai.stock_rater.FinancialMetrics')
    @patch('src.analysis.ai.stock_rater.MoneyFlowAnalyzer')
    @patch('src.analysis.ai.stock_rater.DeepSeekClient')
    def test_invalid_stock_code(
        self,
        mock_deepseek,
        mock_money_flow,
        mock_financial,
        mock_technical,
        sample_kline_df,
        sample_financial_df,
        sample_money_flow_df
    ):
        """测试无效股票代码"""
        mock_technical.return_value = Mock()
        mock_financial.return_value = Mock()
        mock_money_flow.return_value = Mock()
        mock_deepseek.return_value = Mock()

        rater = StockRater()

        # 测试空字符串
        with pytest.raises(ValueError, match="Stock code must be a non-empty string"):
            rater.analyze_stock("", sample_kline_df, sample_financial_df, sample_money_flow_df)

        # 测试None
        with pytest.raises(ValueError, match="Stock code must be a non-empty string"):
            rater.analyze_stock(None, sample_kline_df, sample_financial_df, sample_money_flow_df)
