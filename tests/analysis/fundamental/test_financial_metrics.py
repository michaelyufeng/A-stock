"""财务指标分析测试"""
import pytest
import pandas as pd
from src.analysis.fundamental.financial_metrics import FinancialMetrics


class TestFinancialMetrics:
    @pytest.fixture
    def sample_financial_data(self):
        """创建示例财务数据"""
        return pd.DataFrame({
            '净资产收益率': [15.5, 16.2, 14.8],
            '市盈率': [25.3, 23.5, 26.1],
            '市净率': [3.2, 3.0, 3.5],
            '毛利率': [35.2, 36.1, 34.5],
            '资产负债率': [45.2, 43.8, 46.5],
            '流动比率': [1.8, 1.9, 1.7],
            '营业收入': [1000000, 1200000, 1100000],
            '净利润': [150000, 180000, 165000]
        })

    @pytest.fixture
    def metrics(self):
        """创建FinancialMetrics实例"""
        return FinancialMetrics()

    def test_analyze_profitability(self, metrics, sample_financial_data):
        """测试盈利能力分析"""
        result = metrics.analyze_profitability(sample_financial_data)

        # 验证返回字典
        assert isinstance(result, dict)

        # 验证包含必要的键
        assert 'roe_avg' in result
        assert 'roe_latest' in result
        assert 'gross_margin_avg' in result
        assert 'net_margin_latest' in result
        assert 'rating' in result

        # 验证数值范围
        assert 14 <= result['roe_avg'] <= 17
        assert result['roe_latest'] == 14.8
        assert 34 <= result['gross_margin_avg'] <= 37

        # 验证评级
        assert result['rating'] in ['优秀', '良好', '一般', '差']

    def test_analyze_growth(self, metrics, sample_financial_data):
        """测试成长性分析"""
        result = metrics.analyze_growth(sample_financial_data)

        # 验证返回字典
        assert isinstance(result, dict)

        # 验证包含必要的键
        assert 'revenue_growth' in result
        assert 'profit_growth' in result
        assert 'avg_growth' in result
        assert 'rating' in result

        # 验证增长率计算
        # 营业收入从1000000到1100000，增长10%
        assert abs(result['revenue_growth'] - 10.0) < 0.1

        # 净利润从150000到165000，增长10%
        assert abs(result['profit_growth'] - 10.0) < 0.1

        # 验证评级
        assert result['rating'] in ['优秀', '良好', '一般', '差']

    def test_analyze_financial_health(self, metrics, sample_financial_data):
        """测试财务健康度分析"""
        result = metrics.analyze_financial_health(sample_financial_data)

        # 验证返回字典
        assert isinstance(result, dict)

        # 验证包含必要的键
        assert 'debt_ratio_avg' in result
        assert 'debt_ratio_latest' in result
        assert 'current_ratio_avg' in result
        assert 'current_ratio_latest' in result
        assert 'rating' in result

        # 验证数值
        assert 43 <= result['debt_ratio_avg'] <= 47
        assert result['debt_ratio_latest'] == 46.5
        assert 1.7 <= result['current_ratio_avg'] <= 2.0
        assert result['current_ratio_latest'] == 1.7

        # 验证评级
        assert result['rating'] in ['优秀', '良好', '一般', '差']

    def test_analyze_valuation(self, metrics, sample_financial_data):
        """测试估值分析"""
        result = metrics.analyze_valuation(sample_financial_data)

        # 验证返回字典
        assert isinstance(result, dict)

        # 验证包含必要的键
        assert 'pe_avg' in result
        assert 'pe_latest' in result
        assert 'pb_avg' in result
        assert 'pb_latest' in result
        assert 'rating' in result

        # 验证数值
        assert 23 <= result['pe_avg'] <= 27
        assert result['pe_latest'] == 26.1
        assert 3.0 <= result['pb_avg'] <= 3.5
        assert result['pb_latest'] == 3.5

        # 验证评级
        assert result['rating'] in ['优秀', '良好', '一般', '差']

    def test_get_overall_score(self, metrics, sample_financial_data):
        """测试综合评分"""
        score = metrics.get_overall_score(sample_financial_data)

        # 验证评分范围
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

        # 验证合理性（好的财务数据应该有中等以上评分）
        assert score >= 50

    def test_generate_summary(self, metrics, sample_financial_data):
        """测试生成分析摘要"""
        summary = metrics.generate_summary(sample_financial_data)

        # 验证返回字典
        assert isinstance(summary, dict)

        # 验证包含所有分析维度
        assert 'profitability' in summary
        assert 'growth' in summary
        assert 'financial_health' in summary
        assert 'valuation' in summary
        assert 'overall_score' in summary

        # 验证每个维度都包含rating
        assert 'rating' in summary['profitability']
        assert 'rating' in summary['growth']
        assert 'rating' in summary['financial_health']
        assert 'rating' in summary['valuation']

        # 验证综合评分
        assert 0 <= summary['overall_score'] <= 100

    def test_empty_dataframe(self, metrics):
        """测试空数据框"""
        empty_df = pd.DataFrame()

        # 应该抛出异常或返回空结果
        with pytest.raises(Exception):
            metrics.analyze_profitability(empty_df)

    def test_missing_columns(self, metrics):
        """测试缺少列的情况"""
        incomplete_df = pd.DataFrame({
            '净资产收益率': [15.5, 16.2, 14.8]
        })

        # 应该抛出异常或处理缺失
        with pytest.raises(Exception):
            metrics.analyze_profitability(incomplete_df)

    def test_single_row_data(self, metrics):
        """测试单行数据（无法计算增长率）"""
        single_row_df = pd.DataFrame({
            '净资产收益率': [15.5],
            '市盈率': [25.3],
            '市净率': [3.2],
            '毛利率': [35.2],
            '资产负债率': [45.2],
            '流动比率': [1.8],
            '营业收入': [1000000],
            '净利润': [150000]
        })

        # 盈利能力分析应该可以正常工作
        profitability = metrics.analyze_profitability(single_row_df)
        assert isinstance(profitability, dict)

        # 成长性分析应该处理这种情况（无增长数据）
        growth = metrics.analyze_growth(single_row_df)
        assert isinstance(growth, dict)
        assert growth['revenue_growth'] == 0 or 'revenue_growth' not in growth
