import pytest
from datetime import datetime, time
from src.data.market_calendar import MarketCalendar


class TestMarketCalendar:
    def test_is_trading_day_workday(self):
        """测试工作日判断"""
        calendar = MarketCalendar()
        # 2024年1月2日是交易日（周二）
        result = calendar.is_trading_day(datetime(2024, 1, 2))
        assert result is True

    def test_is_trading_day_weekend(self):
        """测试周末判断"""
        calendar = MarketCalendar()
        # 2024年1月6日是周六
        result = calendar.is_trading_day(datetime(2024, 1, 6))
        assert result is False

    def test_is_trading_time_during_market(self):
        """测试交易时段判断"""
        calendar = MarketCalendar()
        # 上午10点是交易时间
        result = calendar.is_trading_time(time(10, 0))
        assert result is True

    def test_is_trading_time_lunch(self):
        """测试午休时段判断"""
        calendar = MarketCalendar()
        # 中午12点是午休时间
        result = calendar.is_trading_time(time(12, 0))
        assert result is False

    def test_is_trading_time_after_close(self):
        """测试闭市后判断"""
        calendar = MarketCalendar()
        # 下午4点已闭市
        result = calendar.is_trading_time(time(16, 0))
        assert result is False

    def test_get_latest_trading_day(self):
        """测试获取最近交易日"""
        calendar = MarketCalendar()
        result = calendar.get_latest_trading_day()
        assert isinstance(result, datetime)

    def test_is_call_auction_time(self):
        """测试集合竞价时间判断"""
        calendar = MarketCalendar()
        # 9:20是集合竞价时间
        result = calendar.is_call_auction_time(time(9, 20))
        assert result is True
