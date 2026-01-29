import pytest
import pandas as pd
import numpy as np
from src.analysis.technical.indicators import TechnicalIndicators


class TestTechnicalIndicators:
    @pytest.fixture
    def sample_df(self):
        """创建示例DataFrame"""
        dates = pd.date_range('2023-01-01', periods=100)
        np.random.seed(42)
        df = pd.DataFrame({
            '日期': dates,
            '收盘': np.cumsum(np.random.randn(100)) + 100,
            '最高': np.cumsum(np.random.randn(100)) + 105,
            '最低': np.cumsum(np.random.randn(100)) + 95,
            '成交量': np.random.randint(1000000, 10000000, 100)
        })
        return df

    def test_calculate_ma(self, sample_df):
        """测试计算移动平均线"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_ma(sample_df, periods=[5, 10, 20])

        assert 'MA5' in result.columns
        assert 'MA10' in result.columns
        assert 'MA20' in result.columns
        assert not result['MA5'].isna().all()

    def test_calculate_macd(self, sample_df):
        """测试计算MACD"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_macd(sample_df)

        assert 'MACD' in result.columns
        assert 'MACD_signal' in result.columns
        assert 'MACD_hist' in result.columns

    def test_calculate_rsi(self, sample_df):
        """测试计算RSI"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_rsi(sample_df, period=14)

        assert 'RSI' in result.columns
        assert result['RSI'].max() <= 100
        assert result['RSI'].min() >= 0

    def test_calculate_kdj(self, sample_df):
        """测试计算KDJ"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_kdj(sample_df)

        assert 'K' in result.columns
        assert 'D' in result.columns
        assert 'J' in result.columns

    def test_calculate_boll(self, sample_df):
        """测试计算布林带"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_boll(sample_df)

        assert 'BOLL_UPPER' in result.columns
        assert 'BOLL_MIDDLE' in result.columns
        assert 'BOLL_LOWER' in result.columns

    def test_calculate_all(self, sample_df):
        """测试计算所有指标"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(sample_df)

        # 验证主要指标都已添加
        assert 'MA5' in result.columns
        assert 'MACD' in result.columns
        assert 'RSI' in result.columns
        assert 'K' in result.columns
        assert 'BOLL_UPPER' in result.columns
