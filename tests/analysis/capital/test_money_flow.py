"""Tests for money flow analyzer."""
import pytest
import pandas as pd
import numpy as np
from src.analysis.capital.money_flow import MoneyFlowAnalyzer


class TestMoneyFlowAnalyzer:
    @pytest.fixture
    def sample_money_flow_data(self):
        """创建示例资金流向数据"""
        dates = pd.date_range('2023-01-01', periods=20)
        np.random.seed(42)  # For reproducibility
        return pd.DataFrame({
            '日期': dates,
            '主力净流入': np.random.randn(20) * 1000000,
            '超大单净流入': np.random.randn(20) * 500000,
            '大单净流入': np.random.randn(20) * 500000,
            '中单净流入': np.random.randn(20) * 300000,
            '小单净流入': np.random.randn(20) * 200000,
            '成交量': np.random.randint(1000000, 10000000, 20)
        })

    @pytest.fixture
    def analyzer(self):
        """创建MoneyFlowAnalyzer实例"""
        return MoneyFlowAnalyzer()

    def test_analyze_main_force(self, analyzer, sample_money_flow_data):
        """测试主力资金分析"""
        result = analyzer.analyze_main_force(sample_money_flow_data)

        # 验证返回结果包含必要字段
        assert 'total_inflow' in result
        assert 'total_outflow' in result
        assert 'net_inflow' in result
        assert 'inflow_days' in result
        assert 'outflow_days' in result
        assert 'trend' in result
        assert 'strength' in result

        # 验证趋势值
        assert result['trend'] in ['流入', '流出', '平衡']

        # 验证力度值
        assert result['strength'] in ['强', '中', '弱']

        # 验证数值类型
        assert isinstance(result['total_inflow'], (int, float))
        assert isinstance(result['total_outflow'], (int, float))
        assert isinstance(result['net_inflow'], (int, float))
        assert isinstance(result['inflow_days'], int)
        assert isinstance(result['outflow_days'], int)

    def test_analyze_volume_trend(self, analyzer, sample_money_flow_data):
        """测试成交量趋势分析"""
        result = analyzer.analyze_volume_trend(sample_money_flow_data)

        # 验证返回结果包含必要字段
        assert 'avg_volume' in result
        assert 'current_volume' in result
        assert 'volume_ratio' in result
        assert 'trend' in result
        assert 'price_volume_match' in result

        # 验证趋势值
        assert result['trend'] in ['放量', '缩量', '平稳']

        # 验证量价配合值
        assert result['price_volume_match'] in ['良好', '一般', '背离']

        # 验证数值类型
        assert isinstance(result['avg_volume'], (int, float))
        assert isinstance(result['current_volume'], (int, float))
        assert isinstance(result['volume_ratio'], float)

    def test_analyze_money_flow_trend(self, analyzer, sample_money_flow_data):
        """测试资金流向趋势"""
        result = analyzer.analyze_money_flow_trend(sample_money_flow_data, window=5)

        # 验证返回结果包含必要字段
        assert 'window_days' in result
        assert 'continuous_inflow_days' in result
        assert 'continuous_outflow_days' in result
        assert 'net_inflow_sum' in result
        assert 'trend' in result

        # 验证趋势值
        assert result['trend'] in ['持续流入', '持续流出', '震荡']

        # 验证数值类型
        assert isinstance(result['window_days'], int)
        assert result['window_days'] == 5
        assert isinstance(result['continuous_inflow_days'], int)
        assert isinstance(result['continuous_outflow_days'], int)
        assert isinstance(result['net_inflow_sum'], (int, float))

    def test_get_money_flow_signal(self, analyzer, sample_money_flow_data):
        """测试资金流向信号"""
        signal = analyzer.get_money_flow_signal(sample_money_flow_data)

        # 验证信号值
        assert signal in ['买入', '卖出', '持有']

    def test_generate_summary(self, analyzer, sample_money_flow_data):
        """测试生成分析摘要"""
        summary = analyzer.generate_summary(sample_money_flow_data)

        # 验证返回结果包含必要字段
        assert 'main_force' in summary
        assert 'volume_trend' in summary
        assert 'money_flow_trend' in summary
        assert 'signal' in summary
        assert 'recommendation' in summary

        # 验证各部分分析结果
        assert isinstance(summary['main_force'], dict)
        assert isinstance(summary['volume_trend'], dict)
        assert isinstance(summary['money_flow_trend'], dict)
        assert isinstance(summary['signal'], str)
        assert isinstance(summary['recommendation'], str)

        # 验证信号值
        assert summary['signal'] in ['买入', '卖出', '持有']

    def test_empty_dataframe(self, analyzer):
        """测试空数据框"""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="数据框不能为空"):
            analyzer.analyze_main_force(empty_df)

    def test_missing_columns(self, analyzer):
        """测试缺失必要列"""
        df = pd.DataFrame({
            '日期': pd.date_range('2023-01-01', periods=5)
        })

        with pytest.raises(ValueError, match="缺少必要的列"):
            analyzer.analyze_main_force(df)

    def test_analyze_money_flow_trend_custom_window(self, analyzer, sample_money_flow_data):
        """测试自定义窗口期的资金流向趋势"""
        result = analyzer.analyze_money_flow_trend(sample_money_flow_data, window=3)

        assert result['window_days'] == 3
        assert isinstance(result['continuous_inflow_days'], int)
        assert isinstance(result['continuous_outflow_days'], int)
