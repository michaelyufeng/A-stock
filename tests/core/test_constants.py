import pytest
from src.core.constants import (
    Market, StockStatus, OrderSide, OrderType,
    MAIN_BOARD_LIMIT, STAR_MARKET_LIMIT, GEM_LIMIT,
    TRADING_HOURS, MIN_LOT
)


class TestConstants:
    def test_market_enum(self):
        """测试市场枚举"""
        assert Market.MAIN_BOARD.value == 'main_board'
        assert Market.STAR_MARKET.value == 'star_market'
        assert Market.GEM.value == 'gem'

    def test_stock_status_enum(self):
        """测试股票状态枚举"""
        assert StockStatus.NORMAL.value == 'normal'
        assert StockStatus.ST.value == 'st'
        assert StockStatus.DELISTING.value == 'delisting'

    def test_limit_ratios(self):
        """测试涨跌停限制"""
        assert MAIN_BOARD_LIMIT == 0.10
        assert STAR_MARKET_LIMIT == 0.20
        assert GEM_LIMIT == 0.20

    def test_trading_hours(self):
        """测试交易时间"""
        assert 'morning_start' in TRADING_HOURS
        assert TRADING_HOURS['morning_start'] == '09:30'
        assert TRADING_HOURS['afternoon_end'] == '15:00'

    def test_min_lot(self):
        """测试最小交易单位"""
        assert MIN_LOT == 100
