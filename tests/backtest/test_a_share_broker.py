"""A股Broker测试"""
import pytest
import backtrader as bt
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.backtest.a_share_broker import AShareBroker
from src.core.constants import (
    MAIN_BOARD_LIMIT,
    STAR_MARKET_LIMIT,
    GEM_LIMIT,
    MIN_LOT,
    COMMISSION_RATE,
    STAMP_TAX_RATE
)


class TestBoardIdentification:
    """测试板块识别功能"""

    def test_main_board_sh(self):
        """测试上海主板（600xxx）识别"""
        broker = AShareBroker(stock_code='600000')
        assert broker.limit_ratio == MAIN_BOARD_LIMIT
        assert broker.limit_ratio == 0.10

    def test_main_board_sh_601(self):
        """测试上海主板（601xxx）识别"""
        broker = AShareBroker(stock_code='601398')
        assert broker.limit_ratio == MAIN_BOARD_LIMIT
        assert broker.limit_ratio == 0.10

    def test_main_board_sz(self):
        """测试深圳主板（000xxx）识别"""
        broker = AShareBroker(stock_code='000001')
        assert broker.limit_ratio == MAIN_BOARD_LIMIT
        assert broker.limit_ratio == 0.10

    def test_star_market(self):
        """测试科创板（688xxx）识别"""
        broker = AShareBroker(stock_code='688001')
        assert broker.limit_ratio == STAR_MARKET_LIMIT
        assert broker.limit_ratio == 0.20

    def test_gem_board(self):
        """测试创业板（300xxx）识别"""
        broker = AShareBroker(stock_code='300750')
        assert broker.limit_ratio == GEM_LIMIT
        assert broker.limit_ratio == 0.20

    def test_default_board(self):
        """测试无股票代码时默认主板"""
        broker = AShareBroker()
        assert broker.limit_ratio == MAIN_BOARD_LIMIT
        assert broker.limit_ratio == 0.10


class TestLimitPriceCalculation:
    """测试涨跌停价格计算"""

    def test_main_board_limit_price(self):
        """测试主板涨跌停价格（10%）"""
        broker = AShareBroker(stock_code='600000')
        prev_close = 10.0

        limit_up, limit_down = broker._get_limit_price(prev_close)

        assert limit_up == 11.0  # 10 * 1.1
        assert limit_down == 9.0  # 10 * 0.9

    def test_star_market_limit_price(self):
        """测试科创板涨跌停价格（20%）"""
        broker = AShareBroker(stock_code='688001')
        prev_close = 50.0

        limit_up, limit_down = broker._get_limit_price(prev_close)

        assert limit_up == 60.0  # 50 * 1.2
        assert limit_down == 40.0  # 50 * 0.8

    def test_gem_limit_price(self):
        """测试创业板涨跌停价格（20%）"""
        broker = AShareBroker(stock_code='300750')
        prev_close = 100.0

        limit_up, limit_down = broker._get_limit_price(prev_close)

        assert limit_up == 120.0  # 100 * 1.2
        assert limit_down == 80.0  # 100 * 0.8


class TestBuyRestrictions:
    """测试买入限制"""

    @pytest.fixture
    def broker_setup(self):
        """设置测试Broker"""
        broker = AShareBroker(stock_code='600000')
        broker.setcash(100000)  # 设置初始资金
        return broker

    def test_buy_quantity_rounding_down(self, broker_setup):
        """测试买入数量向下取整到100股整数倍"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        data.close = [-1, 10.0]  # 前一日收盘价10元

        # 尝试买入250股（应调整为200股）
        with patch.object(bt.brokers.BrokerBack, 'buy', return_value=Mock()) as mock_buy:
            broker.buy(owner, data, 250)

            # 验证调用参数
            mock_buy.assert_called_once()
            args, kwargs = mock_buy.call_args
            assert args[2] == 200  # size参数应该是200

    def test_buy_quantity_rounding_zero(self, broker_setup):
        """测试买入数量不足100股时拒绝订单"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        data.close = [-1, 10.0]

        # 尝试买入50股（小于100股，应拒绝）
        result = broker.buy(owner, data, 50)

        assert result is None  # 订单被拒绝

    def test_buy_at_limit_up_rejected(self, broker_setup):
        """测试接近涨停价买入被拒绝"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        prev_close = 10.0
        limit_up = 11.0  # 10% 涨停
        data.close = [-1, prev_close]

        # 尝试以涨停价买入（应被拒绝）
        result = broker.buy(owner, data, 100, price=limit_up)

        assert result is None  # 订单被拒绝

    def test_buy_below_limit_up_allowed(self, broker_setup):
        """测试低于涨停价买入允许"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        prev_close = 10.0
        buy_price = 10.8  # 未涨停
        data.close = [-1, prev_close]

        # 以正常价格买入（应允许）
        with patch.object(bt.brokers.BrokerBack, 'buy', return_value=Mock()) as mock_buy:
            result = broker.buy(owner, data, 100, price=buy_price)

            assert mock_buy.called  # 父类buy被调用
            assert result is not None


class TestSellRestrictions:
    """测试卖出限制"""

    @pytest.fixture
    def broker_setup(self):
        """设置测试Broker"""
        broker = AShareBroker(stock_code='600000')
        broker.setcash(100000)
        return broker

    def test_sell_quantity_rounding_down(self, broker_setup):
        """测试卖出数量向下取整到100股整数倍"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        data.close = [-1, 10.0]

        # 尝试卖出350股（应调整为300股）
        with patch.object(bt.brokers.BrokerBack, 'sell', return_value=Mock()) as mock_sell:
            broker.sell(owner, data, 350)

            # 验证调用参数
            mock_sell.assert_called_once()
            args, kwargs = mock_sell.call_args
            assert args[2] == 300  # size参数应该是300

    def test_sell_quantity_rounding_zero(self, broker_setup):
        """测试卖出数量不足100股时拒绝订单"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        data.close = [-1, 10.0]

        # 尝试卖出99股（小于100股，应拒绝）
        result = broker.sell(owner, data, 99)

        assert result is None  # 订单被拒绝

    def test_sell_at_limit_down_rejected(self, broker_setup):
        """测试接近跌停价卖出被拒绝"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        prev_close = 10.0
        limit_down = 9.0  # 10% 跌停
        data.close = [-1, prev_close]

        # 尝试以跌停价卖出（应被拒绝）
        result = broker.sell(owner, data, 100, price=limit_down)

        assert result is None  # 订单被拒绝

    def test_sell_above_limit_down_allowed(self, broker_setup):
        """测试高于跌停价卖出允许"""
        broker = broker_setup

        # Mock数据
        owner = Mock()
        data = Mock()
        prev_close = 10.0
        sell_price = 9.2  # 未跌停
        data.close = [-1, prev_close]

        # 以正常价格卖出（应允许）
        with patch.object(bt.brokers.BrokerBack, 'sell', return_value=Mock()) as mock_sell:
            result = broker.sell(owner, data, 100, price=sell_price)

            assert mock_sell.called  # 父类sell被调用
            assert result is not None


class TestCommissionCalculation:
    """测试佣金和印花税计算"""

    @pytest.fixture
    def broker_setup(self):
        """设置测试Broker"""
        broker = AShareBroker(stock_code='600000')
        return broker

    def test_buy_commission(self, broker_setup):
        """测试买入佣金计算"""
        broker = broker_setup

        size = 1000  # 买入1000股
        price = 10.0
        pseudoexec = False

        commission = broker._getcommission(size, price, pseudoexec)

        # 佣金 = 1000 * 10 * 0.0003 = 3元
        # 但最低5元
        expected_commission = 5.0
        assert commission == expected_commission

    def test_buy_commission_above_minimum(self, broker_setup):
        """测试买入佣金（高于最低5元）"""
        broker = broker_setup

        size = 10000  # 买入10000股
        price = 10.0
        pseudoexec = False

        commission = broker._getcommission(size, price, pseudoexec)

        # 佣金 = 10000 * 10 * 0.0003 = 30元
        expected_commission = 30.0
        assert abs(commission - expected_commission) < 0.01  # 允许浮点数误差

    def test_sell_commission_with_stamp_tax(self, broker_setup):
        """测试卖出佣金+印花税"""
        broker = broker_setup

        size = -1000  # 卖出1000股（负数）
        price = 10.0
        pseudoexec = False

        commission = broker._getcommission(size, price, pseudoexec)

        # 佣金 = 1000 * 10 * 0.0003 = 3元 → 最低5元
        # 印花税 = 1000 * 10 * 0.001 = 10元
        # 总计 = 5 + 10 = 15元
        expected_commission = 15.0
        assert commission == expected_commission

    def test_sell_commission_large_amount(self, broker_setup):
        """测试卖出大额佣金+印花税"""
        broker = broker_setup

        size = -10000  # 卖出10000股
        price = 50.0
        pseudoexec = False

        commission = broker._getcommission(size, price, pseudoexec)

        # 佣金 = 10000 * 50 * 0.0003 = 150元
        # 印花税 = 10000 * 50 * 0.001 = 500元
        # 总计 = 150 + 500 = 650元
        expected_commission = 650.0
        assert commission == expected_commission


class TestIntegration:
    """集成测试"""

    def test_broker_initialization(self):
        """测试Broker初始化"""
        broker = AShareBroker(stock_code='600000')

        assert broker.stock_code == '600000'
        assert broker.limit_ratio == MAIN_BOARD_LIMIT
        assert isinstance(broker, bt.brokers.BrokerBack)

    def test_broker_with_cerebro(self):
        """测试Broker与Cerebro集成"""
        cerebro = bt.Cerebro()
        broker = AShareBroker(stock_code='688001')
        cerebro.broker = broker

        assert cerebro.broker == broker
        assert cerebro.broker.limit_ratio == STAR_MARKET_LIMIT

    def test_different_boards_different_limits(self):
        """测试不同板块的涨跌停限制不同"""
        main_broker = AShareBroker(stock_code='600000')
        star_broker = AShareBroker(stock_code='688001')
        gem_broker = AShareBroker(stock_code='300750')

        prev_close = 10.0

        main_up, main_down = main_broker._get_limit_price(prev_close)
        star_up, star_down = star_broker._get_limit_price(prev_close)
        gem_up, gem_down = gem_broker._get_limit_price(prev_close)

        # 主板±10%
        assert main_up == 11.0
        assert main_down == 9.0

        # 科创板±20%
        assert star_up == 12.0
        assert star_down == 8.0

        # 创业板±20%
        assert gem_up == 12.0
        assert gem_down == 8.0
