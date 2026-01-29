import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.data.akshare_provider import AKShareProvider


class TestAKShareProvider:
    def test_get_stock_list(self):
        """测试获取股票列表"""
        provider = AKShareProvider()
        df = provider.get_stock_list()
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert '代码' in df.columns or 'symbol' in df.columns

    def test_get_realtime_quote(self):
        """测试获取实时行情"""
        provider = AKShareProvider()
        quote = provider.get_realtime_quote('600519')
        assert quote is not None
        assert isinstance(quote, dict)
        assert 'price' in quote or '最新价' in quote

    def test_get_daily_kline(self):
        """测试获取日线数据"""
        provider = AKShareProvider()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        df = provider.get_daily_kline(
            '600519',
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_cache_usage(self):
        """测试缓存功能"""
        provider = AKShareProvider()

        # 第一次调用
        quote1 = provider.get_realtime_quote('600519')

        # 第二次调用应该使用缓存
        quote2 = provider.get_realtime_quote('600519')

        assert quote1 == quote2
