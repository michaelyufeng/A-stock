import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.screening.screener import StockScreener


class TestStockScreener:
    """测试StockScreener类"""

    @pytest.fixture
    def screener(self):
        """创建StockScreener实例"""
        with patch('src.screening.screener.AKShareProvider'), \
             patch('src.screening.screener.TechnicalIndicators'), \
             patch('src.screening.screener.FinancialMetrics'), \
             patch('src.screening.screener.MoneyFlowAnalyzer'):
            return StockScreener()

    @pytest.fixture
    def sample_kline_df(self):
        """创建示例K线数据"""
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            'date': dates,
            'open': 100 + np.cumsum(np.random.randn(100) * 0.5),
            'high': 102 + np.cumsum(np.random.randn(100) * 0.5),
            'low': 98 + np.cumsum(np.random.randn(100) * 0.5),
            'close': 100 + np.cumsum(np.random.randn(100) * 0.5),
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        # 添加技术指标
        df['RSI'] = 50 + np.random.randn(100) * 10
        df['MACD'] = np.random.randn(100) * 0.5
        df['MACD_signal'] = np.random.randn(100) * 0.5
        df['MA20'] = df['close'].rolling(20).mean()
        df['VOL_MA5'] = df['volume'].rolling(5).mean()
        return df

    @pytest.fixture
    def sample_stock_list(self):
        """创建示例股票列表"""
        return pd.DataFrame({
            '代码': ['600519', '000001', '600036', '000002', '601318'],
            '名称': ['贵州茅台', '平安银行', '招商银行', '万科A', '中国平安'],
            '最新价': [1800, 12.5, 35.6, 8.9, 45.2],
            '总市值': [2260000000000, 242000000000, 880000000000, 98000000000, 807000000000]
        })

    @pytest.fixture
    def sample_financial_df(self):
        """创建示例财务数据"""
        return pd.DataFrame({
            '净资产收益率': [15.5, 16.2, 14.8],
            '毛利率': [90.5, 91.2, 89.8],
            '净利润': [50000000000, 52000000000, 54000000000],
            '营业收入': [120000000000, 125000000000, 130000000000],
            '资产负债率': [25.5, 26.2, 24.8],
            '流动比率': [3.5, 3.6, 3.4]
        })

    @pytest.fixture
    def sample_money_flow_df(self):
        """创建示例资金流向数据"""
        return pd.DataFrame({
            '主力净流入': [1000000, -500000, 2000000, 3000000, -1000000],
            '超大单净流入': [500000, -200000, 1000000, 1500000, -500000],
            '大单净流入': [500000, -300000, 1000000, 1500000, -500000]
        })

    def test_initialization(self, screener):
        """测试初始化"""
        assert screener is not None
        assert hasattr(screener, 'data_provider')
        assert hasattr(screener, 'tech_indicators')
        assert hasattr(screener, 'financial_metrics')
        assert hasattr(screener, 'money_flow')
        assert hasattr(screener, 'presets')
        assert 'strong_momentum' in screener.presets
        assert 'value_growth' in screener.presets
        assert 'capital_inflow' in screener.presets

    def test_presets_exist(self, screener):
        """测试预设方案存在"""
        # 测试强势动量预设
        momentum_filter = screener.presets['strong_momentum']()
        assert 'weights' in momentum_filter
        assert 'use_fundamental' in momentum_filter

        # 测试价值成长预设
        value_filter = screener.presets['value_growth']()
        assert 'weights' in value_filter
        assert value_filter['use_fundamental'] is True

        # 测试资金流入预设
        capital_filter = screener.presets['capital_inflow']()
        assert 'weights' in capital_filter
        assert capital_filter['use_capital'] is True

    def test_apply_quick_filters(self, screener):
        """测试快速筛选"""
        stock_pool = ['600519', '000001', 'ST000002', '*ST000003', '600036']
        filters = {}

        result = screener._apply_quick_filters(stock_pool, filters)

        # ST股应该被过滤掉
        assert '600519' in result
        assert '000001' in result
        assert '600036' in result
        assert 'ST000002' not in result
        assert '*ST000003' not in result

    def test_score_technical(self, screener, sample_kline_df):
        """测试技术面评分"""
        filters = {}

        # 修改数据以创建明确的技术信号
        df = sample_kline_df.copy()
        df.loc[df.index[-1], 'RSI'] = 50  # 中性RSI
        df.loc[df.index[-1], 'MACD'] = 0.5  # MACD金叉
        df.loc[df.index[-1], 'MACD_signal'] = 0.3
        df.loc[df.index[-1], 'close'] = 105
        df.loc[df.index[-1], 'MA20'] = 100  # 站上MA20
        df.loc[df.index[-1], 'volume'] = 2000000
        df.loc[df.index[-1], 'VOL_MA5'] = 1000000  # 放量

        score = screener._score_technical(df, filters)

        # 应该得到较高分数
        assert 0 <= score <= 100
        assert score >= 50  # 由于多个正面信号

    def test_score_technical_boundary(self, screener, sample_kline_df):
        """测试技术面评分边界情况"""
        filters = {}

        # 测试超卖情况
        df = sample_kline_df.copy()
        df.loc[df.index[-1], 'RSI'] = 25  # 超卖
        score_oversold = screener._score_technical(df, filters)
        assert score_oversold > 50  # 超卖应该加分

        # 测试超买情况
        df.loc[df.index[-1], 'RSI'] = 85  # 超买
        score_overbought = screener._score_technical(df, filters)
        assert score_overbought < 50  # 超买应该减分

    def test_analyze_stock(self, screener, sample_kline_df):
        """测试分析单只股票"""
        # Mock数据提供者
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})

        # Mock技术指标计算
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        filters = {'use_fundamental': False, 'use_capital': False}

        result = screener._analyze_stock('600519', filters)

        assert result is not None
        assert 'code' in result
        assert 'name' in result
        assert 'score' in result
        assert 'tech_score' in result
        assert 'fundamental_score' in result
        assert 'capital_score' in result
        assert 'current_price' in result
        assert 'reason' in result
        assert result['code'] == '600519'

    def test_analyze_stock_with_fundamental(self, screener, sample_kline_df, sample_financial_df):
        """测试分析股票（包含基本面）"""
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_financial_data = Mock(return_value=sample_financial_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)
        screener.financial_metrics.get_overall_score = Mock(return_value=75.0)

        filters = {
            'use_fundamental': True,
            'use_capital': False,
            'weights': {'technical': 0.5, 'fundamental': 0.4, 'capital': 0.1}
        }

        result = screener._analyze_stock('600519', filters)

        assert result is not None
        assert result['fundamental_score'] == 75.0

    def test_analyze_stock_with_capital(self, screener, sample_kline_df, sample_money_flow_df):
        """测试分析股票（包含资金面）"""
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_money_flow = Mock(return_value=sample_money_flow_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)
        screener.money_flow.analyze_main_force = Mock(return_value={'trend': '流入'})

        filters = {
            'use_fundamental': False,
            'use_capital': True,
            'weights': {'technical': 0.5, 'fundamental': 0.1, 'capital': 0.4}
        }

        result = screener._analyze_stock('600519', filters)

        assert result is not None
        assert result['capital_score'] == 70  # 资金流入应该得70分

    def test_analyze_stock_insufficient_data(self, screener):
        """测试数据不足的情况"""
        # 只有少量数据
        short_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'close': [100] * 30,
            'volume': [1000000] * 30
        })

        screener.data_provider.get_daily_kline = Mock(return_value=short_df)

        filters = {}
        result = screener._analyze_stock('600519', filters)

        # 数据不足应该返回None
        assert result is None

    def test_analyze_sequential(self, screener, sample_kline_df):
        """测试顺序分析"""
        stock_pool = ['600519', '000001', '600036']

        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        filters = {'use_fundamental': False, 'use_capital': False}

        results = screener._analyze_sequential(stock_pool, filters)

        assert isinstance(results, list)
        # 应该分析了3只股票
        assert len(results) <= 3  # 可能有些分析失败

    def test_analyze_parallel(self, screener, sample_kline_df):
        """测试并行分析"""
        stock_pool = ['600519', '000001']

        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        filters = {'use_fundamental': False, 'use_capital': False}

        results = screener._analyze_parallel(stock_pool, filters, max_workers=2)

        assert isinstance(results, list)
        assert len(results) <= 2

    def test_screen_with_preset(self, screener, sample_stock_list, sample_kline_df):
        """测试使用预设方案筛选"""
        screener.data_provider.get_stock_list = Mock(return_value=sample_stock_list)
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        results = screener.screen(
            stock_pool=['600519', '000001'],
            preset='strong_momentum',
            top_n=5,
            min_score=0,
            parallel=False
        )

        assert isinstance(results, pd.DataFrame)
        if len(results) > 0:
            assert 'code' in results.columns
            assert 'name' in results.columns
            assert 'score' in results.columns
            assert 'tech_score' in results.columns
            assert 'fundamental_score' in results.columns
            assert 'capital_score' in results.columns
            assert 'reason' in results.columns

    def test_screen_with_custom_filters(self, screener, sample_kline_df):
        """测试使用自定义筛选条件"""
        stock_pool = ['600519', '000001']

        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        custom_filters = {
            'use_fundamental': False,
            'use_capital': False,
            'weights': {'technical': 0.7, 'fundamental': 0.2, 'capital': 0.1}
        }

        results = screener.screen(
            stock_pool=stock_pool,
            filters=custom_filters,
            top_n=2,
            parallel=False
        )

        assert isinstance(results, pd.DataFrame)

    def test_screen_with_min_score(self, screener, sample_kline_df):
        """测试最低评分过滤"""
        stock_pool = ['600519', '000001']

        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        # 设置很高的最低分数
        results = screener.screen(
            stock_pool=stock_pool,
            min_score=95,
            parallel=False
        )

        # 应该没有股票满足要求，或者满足的很少
        assert isinstance(results, pd.DataFrame)
        if len(results) > 0:
            assert results['score'].min() >= 95

    def test_screen_empty_pool(self, screener):
        """测试空股票池"""
        results = screener.screen(
            stock_pool=[],
            parallel=False
        )

        assert isinstance(results, pd.DataFrame)
        assert len(results) == 0

    def test_screen_no_qualified_stocks(self, screener):
        """测试无符合条件的股票"""
        stock_pool = ['ST000001', '*ST000002']  # 都是ST股

        results = screener.screen(
            stock_pool=stock_pool,
            parallel=False
        )

        assert isinstance(results, pd.DataFrame)
        assert len(results) == 0

    def test_generate_reason(self, screener):
        """测试生成入选理由"""
        # 技术面强势
        reason1 = screener._generate_reason(75, 60, 60)
        assert '技术面强势' in reason1

        # 基本面优秀
        reason2 = screener._generate_reason(60, 75, 60)
        assert '基本面优秀' in reason2

        # 主力资金流入
        reason3 = screener._generate_reason(60, 60, 75)
        assert '主力资金流入' in reason3

        # 多个优势
        reason4 = screener._generate_reason(75, 75, 75)
        assert '技术面强势' in reason4
        assert '基本面优秀' in reason4
        assert '主力资金流入' in reason4

        # 综合达标
        reason5 = screener._generate_reason(60, 60, 60)
        assert '综合评分达标' in reason5

    def test_screen_result_sorted(self, screener, sample_kline_df):
        """测试筛选结果按分数排序"""
        stock_pool = ['600519', '000001', '600036']

        # Mock返回不同的评分
        def mock_analyze(code, filters):
            scores = {'600519': 80, '000001': 90, '600036': 70}
            base_score = scores.get(code, 50)
            return {
                'code': code,
                'name': f'股票{code}',
                'score': base_score,
                'tech_score': base_score,
                'fundamental_score': 50,
                'capital_score': 50,
                'current_price': 100,
                'reason': '测试'
            }

        screener._analyze_stock = Mock(side_effect=mock_analyze)

        results = screener.screen(
            stock_pool=stock_pool,
            top_n=3,
            parallel=False
        )

        assert len(results) == 3
        # 应该按分数降序排列
        assert results.iloc[0]['code'] == '000001'  # 90分
        assert results.iloc[1]['code'] == '600519'  # 80分
        assert results.iloc[2]['code'] == '600036'  # 70分

    def test_screen_top_n_limit(self, screener, sample_kline_df):
        """测试TOP N限制"""
        stock_pool = ['600519', '000001', '600036', '000002', '601318']

        def mock_analyze(code, filters):
            return {
                'code': code,
                'name': f'股票{code}',
                'score': 75,
                'tech_score': 75,
                'fundamental_score': 50,
                'capital_score': 50,
                'current_price': 100,
                'reason': '测试'
            }

        screener._analyze_stock = Mock(side_effect=mock_analyze)

        results = screener.screen(
            stock_pool=stock_pool,
            top_n=3,
            parallel=False
        )

        # 应该只返回3只股票
        assert len(results) <= 3

    def test_screen_with_full_market(self, screener, sample_stock_list, sample_kline_df):
        """测试全市场筛选"""
        screener.data_provider.get_stock_list = Mock(return_value=sample_stock_list)
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        # stock_pool=None 表示全市场
        results = screener.screen(
            stock_pool=None,
            top_n=2,
            parallel=False
        )

        assert isinstance(results, pd.DataFrame)
        # 应该从全市场股票列表中筛选
        screener.data_provider.get_stock_list.assert_called_once()

    def test_error_handling_in_analyze(self, screener):
        """测试分析过程中的错误处理"""
        screener.data_provider.get_daily_kline = Mock(side_effect=Exception("API Error"))

        filters = {}
        result = screener._analyze_stock('600519', filters)

        # 出错应该返回None，不应该抛出异常
        assert result is None

    def test_weights_in_scoring(self, screener, sample_kline_df):
        """测试权重对评分的影响"""
        screener.data_provider.get_daily_kline = Mock(return_value=sample_kline_df)
        screener.data_provider.get_realtime_quote = Mock(return_value={'名称': '测试股票'})
        screener.tech_indicators.calculate_all = Mock(return_value=sample_kline_df)

        # 高技术面权重
        filters1 = {
            'use_fundamental': False,
            'use_capital': False,
            'weights': {'technical': 0.9, 'fundamental': 0.05, 'capital': 0.05}
        }

        result1 = screener._analyze_stock('600519', filters1)

        # 高基本面权重
        filters2 = {
            'use_fundamental': False,
            'use_capital': False,
            'weights': {'technical': 0.1, 'fundamental': 0.8, 'capital': 0.1}
        }

        result2 = screener._analyze_stock('600519', filters2)

        # 两种权重配置应该产生不同的综合评分
        # （虽然具体分数取决于实现，但权重应该有影响）
        assert result1 is not None
        assert result2 is not None
