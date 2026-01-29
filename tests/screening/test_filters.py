"""测试筛选过滤器模块"""
import pytest
import pandas as pd
import numpy as np
from src.screening.filters import (
    filter_by_pe_roe,
    filter_by_dividend_yield,
    filter_by_breakout,
    filter_by_oversold_rebound,
    filter_by_institutional_holding
)


class TestFilters:
    """测试筛选过滤器函数"""

    @pytest.fixture
    def sample_stock_data(self):
        """创建示例股票数据"""
        return pd.DataFrame({
            '代码': ['000001', '000002', '000003', '000004', '000005'],
            '名称': ['平安银行', '万科A', '中国平安', '贵州茅台', '招商银行'],
            'PE': [8.5, 18.0, 12.0, 25.0, 10.5],
            'ROE': [12.0, 8.0, 15.0, 20.0, 14.0],
            '股息率': [4.5, 2.0, 3.5, 1.5, 3.8],
            'close': [12.5, 8.9, 45.2, 1800.0, 35.6],
            'RSI': [45.0, 65.0, 35.0, 55.0, 50.0]
        })

    @pytest.fixture
    def sample_with_history(self):
        """创建包含历史数据的股票数据"""
        dates = pd.date_range('2024-01-01', periods=100)
        return pd.DataFrame({
            '代码': ['600519'] * 100,
            '名称': ['贵州茅台'] * 100,
            'date': dates,
            'close': list(range(1700, 1800)),
            'high': list(range(1705, 1805)),
            'volume': [1000000] * 50 + [1500000] * 50,  # 后50天放量
            'RSI': [25] * 30 + [35] * 70,  # 前30天超卖，后70天反弹
            'MA20': list(range(1680, 1780)),
            '20日最高价': [1750] * 80 + [1790] * 20,  # 最后20天突破
            '60日最高价': [1750] * 80 + [1790] * 20,
            '机构持仓比例': [35.0] * 100,
            '平均成交量': [1000000] * 100
        })

    def test_filter_by_pe_roe_basic(self, sample_stock_data):
        """测试基本的PE和ROE过滤"""
        # 过滤条件: PE < 15, ROE > 10%
        result = filter_by_pe_roe(sample_stock_data, pe_max=15.0, roe_min=10.0)

        # 应该包含: 000001 (PE=8.5, ROE=12), 000003 (PE=12, ROE=15), 000005 (PE=10.5, ROE=14)
        # 应该排除: 000002 (PE=18), 000004 (PE=25)
        assert len(result) == 3
        assert '000001' in result['代码'].values
        assert '000003' in result['代码'].values
        assert '000005' in result['代码'].values
        assert '000002' not in result['代码'].values
        assert '000004' not in result['代码'].values

    def test_filter_by_pe_roe_strict(self, sample_stock_data):
        """测试严格的PE和ROE过滤"""
        # 更严格的条件: PE < 10, ROE > 11%
        result = filter_by_pe_roe(sample_stock_data, pe_max=10.0, roe_min=11.0)

        # 只有000001满足条件 (PE=8.5, ROE=12 > 11)
        assert len(result) == 1
        assert '000001' in result['代码'].values

    def test_filter_by_pe_roe_empty(self, sample_stock_data):
        """测试过于严格导致无结果"""
        # 非常严格的条件
        result = filter_by_pe_roe(sample_stock_data, pe_max=5.0, roe_min=25.0)

        # 应该没有股票满足
        assert len(result) == 0

    def test_filter_by_dividend_yield_basic(self, sample_stock_data):
        """测试基本的股息率过滤"""
        # 过滤条件: 股息率 >= 3%
        result = filter_by_dividend_yield(sample_stock_data, yield_min=3.0)

        # 应该包含: 000001 (4.5%), 000003 (3.5%), 000005 (3.8%)
        # 应该排除: 000002 (2.0%), 000004 (1.5%)
        assert len(result) == 3
        assert '000001' in result['代码'].values
        assert '000003' in result['代码'].values
        assert '000005' in result['代码'].values
        assert '000002' not in result['代码'].values
        assert '000004' not in result['代码'].values

    def test_filter_by_dividend_yield_high_threshold(self, sample_stock_data):
        """测试高股息率阈值"""
        # 只要股息率 >= 4%
        result = filter_by_dividend_yield(sample_stock_data, yield_min=4.0)

        # 只有000001满足 (4.5%)
        assert len(result) == 1
        assert '000001' in result['代码'].values

    def test_filter_by_breakout_20day(self, sample_with_history):
        """测试20日新高突破"""
        # 过滤条件: 突破20日新高，成交量 > 1.2倍均量
        result = filter_by_breakout(
            sample_with_history,
            breakout_days=20,
            volume_ratio_min=1.2
        )

        # 最后20天价格突破了之前的高点，且成交量放大
        assert len(result) > 0

        # 检查最新数据点
        latest = result.iloc[-1]
        assert latest['close'] >= latest['20日最高价'] * 0.95  # 接近或突破新高
        assert latest['volume'] >= latest['平均成交量'] * 1.2

    def test_filter_by_breakout_no_volume(self, sample_with_history):
        """测试突破但无放量确认"""
        # 修改数据：价格突破但成交量不放大
        df = sample_with_history.copy()
        df['volume'] = 1000000  # 恒定成交量，无放大
        df['平均成交量'] = 1000000

        result = filter_by_breakout(
            df,
            breakout_days=20,
            volume_ratio_min=1.5  # 要求1.5倍放量
        )

        # 无放量确认，应该被过滤
        assert len(result) == 0

    def test_filter_by_oversold_rebound_basic(self, sample_with_history):
        """测试基本的超卖反弹过滤"""
        # 修改数据：确保在lookback期间内有超卖和反弹
        # 最近60天: 前40天RSI=25(超卖), 后20天RSI=35(反弹)
        df = sample_with_history.copy()
        df['RSI'] = [50] * 40 + [25] * 40 + [35] * 20  # 前40天正常，中40天超卖，后20天反弹

        # 过滤条件: 曾经RSI < 30，现在RSI >= 30
        result = filter_by_oversold_rebound(
            df,
            rsi_oversold=30.0,
            rsi_rebound_min=30.0,
            lookback_periods=50  # 查看最近50天（包含超卖和反弹）
        )

        # 最近50天内包含超卖期（中间40天）和反弹期（后20天）
        # 应该检测到超卖反弹信号
        assert len(result) > 0

        # 当前RSI应该高于超卖阈值
        latest_rsi = result.iloc[-1]['RSI']
        assert latest_rsi >= 30.0

    def test_filter_by_oversold_rebound_no_oversold(self):
        """测试无超卖历史"""
        # 创建从未超卖的数据
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            '代码': ['600519'] * 100,
            'date': dates,
            'close': [1800] * 100,
            'RSI': [50] * 100  # RSI一直保持在50，从未超卖
        })

        result = filter_by_oversold_rebound(
            df,
            rsi_oversold=30.0,
            rsi_rebound_min=30.0,
            lookback_periods=50
        )

        # 从未超卖，不应该返回结果
        assert len(result) == 0

    def test_filter_by_oversold_rebound_still_oversold(self):
        """测试仍处于超卖状态"""
        # 创建持续超卖的数据
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            '代码': ['600519'] * 100,
            'date': dates,
            'close': [1800] * 100,
            'RSI': [25] * 100  # RSI一直保持在25，持续超卖
        })

        result = filter_by_oversold_rebound(
            df,
            rsi_oversold=30.0,
            rsi_rebound_min=30.0,
            lookback_periods=50
        )

        # 仍在超卖，未反弹，不应该返回结果
        assert len(result) == 0

    def test_filter_by_institutional_holding_basic(self, sample_stock_data):
        """测试基本的机构持仓过滤"""
        # 添加机构持仓比例列
        df = sample_stock_data.copy()
        df['机构持仓比例'] = [35.0, 25.0, 40.0, 28.0, 32.0]

        # 过滤条件: 机构持仓 >= 30%
        result = filter_by_institutional_holding(df, ratio_min=30.0)

        # 应该包含: 000001 (35%), 000003 (40%), 000005 (32%)
        # 应该排除: 000002 (25%), 000004 (28%)
        assert len(result) == 3
        assert '000001' in result['代码'].values
        assert '000003' in result['代码'].values
        assert '000005' in result['代码'].values
        assert '000002' not in result['代码'].values
        assert '000004' not in result['代码'].values

    def test_filter_by_institutional_holding_high_threshold(self, sample_stock_data):
        """测试高机构持仓阈值"""
        df = sample_stock_data.copy()
        df['机构持仓比例'] = [35.0, 25.0, 45.0, 28.0, 32.0]

        # 只要机构持仓 >= 40%
        result = filter_by_institutional_holding(df, ratio_min=40.0)

        # 只有000003满足 (45%)
        assert len(result) == 1
        assert '000003' in result['代码'].values

    def test_filter_by_institutional_holding_missing_column(self, sample_stock_data):
        """测试缺少机构持仓数据列"""
        # 不添加机构持仓比例列，应返回空DataFrame并记录警告
        result = filter_by_institutional_holding(sample_stock_data, ratio_min=30.0)
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_filter_chain_multiple_conditions(self, sample_stock_data):
        """测试链式过滤多个条件"""
        # 同时满足低PE和高股息
        df = sample_stock_data.copy()

        # 第一步: 低PE和高ROE
        result = filter_by_pe_roe(df, pe_max=15.0, roe_min=10.0)
        # 结果: 000001, 000003, 000005

        # 第二步: 高股息率
        result = filter_by_dividend_yield(result, yield_min=3.5)
        # 结果: 000001 (4.5%), 000003 (3.5%), 000005 (3.8%)

        assert len(result) == 3
        assert all(code in result['代码'].values for code in ['000001', '000003', '000005'])

    def test_filter_preserves_dataframe_structure(self, sample_stock_data):
        """测试过滤后保留DataFrame结构"""
        result = filter_by_pe_roe(sample_stock_data, pe_max=15.0, roe_min=10.0)

        # 应该保留所有原始列
        assert all(col in result.columns for col in sample_stock_data.columns)

        # 应该保持DataFrame类型
        assert isinstance(result, pd.DataFrame)

    def test_filter_handles_nan_values(self):
        """测试处理NaN值"""
        df = pd.DataFrame({
            '代码': ['000001', '000002', '000003'],
            'PE': [10.0, np.nan, 12.0],
            'ROE': [15.0, 12.0, np.nan]
        })

        # 过滤应该排除包含NaN的行
        result = filter_by_pe_roe(df, pe_max=15.0, roe_min=10.0)

        # 只有000001满足且无NaN
        assert len(result) == 1
        assert '000001' in result['代码'].values
