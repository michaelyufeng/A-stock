"""测试BaseStrategy基类"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.strategy.base_strategy import BaseStrategy
from src.core.constants import SignalType


class ConcreteStrategy(BaseStrategy):
    """具体策略实现（用于测试）"""

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """简单的信号生成实现"""
        df = df.copy()
        df['signal'] = SignalType.HOLD.value
        return df


class TestBaseStrategy:
    """测试BaseStrategy类"""

    @pytest.fixture
    def strategy(self):
        """创建测试策略实例"""
        return ConcreteStrategy('momentum')

    def test_init(self, strategy):
        """测试策略初始化"""
        assert strategy.strategy_name == 'momentum'
        assert strategy.config is not None
        assert strategy.params is not None

    def test_load_strategy_params(self, strategy):
        """测试策略参数加载"""
        params = strategy.params

        # 验证从strategies.yaml加载的参数
        assert 'stop_loss' in params
        assert 'take_profit' in params
        assert 'max_holding_days' in params

        # 验证参数值
        assert params['stop_loss'] == 0.08
        assert params['take_profit'] == 0.15
        assert params['max_holding_days'] == 10

    def test_get_param(self, strategy):
        """测试参数获取"""
        # 获取存在的参数
        assert strategy.get_param('stop_loss') == 0.08
        assert strategy.get_param('take_profit') == 0.15

        # 获取不存在的参数，返回默认值
        assert strategy.get_param('non_existent', 0.05) == 0.05
        assert strategy.get_param('non_existent') is None

    def test_check_stop_loss_triggered(self, strategy):
        """测试止损触发（价格下跌8%）"""
        entry_price = 100.0
        current_price = 91.9  # 下跌8.1%

        assert strategy.check_stop_loss(entry_price, current_price) is True

    def test_check_stop_loss_not_triggered(self, strategy):
        """测试止损未触发（价格下跌7%）"""
        entry_price = 100.0
        current_price = 93.0  # 下跌7%

        assert strategy.check_stop_loss(entry_price, current_price) is False

    def test_check_stop_loss_price_up(self, strategy):
        """测试价格上涨时不触发止损"""
        entry_price = 100.0
        current_price = 105.0  # 上涨5%

        assert strategy.check_stop_loss(entry_price, current_price) is False

    def test_check_take_profit_triggered(self, strategy):
        """测试止盈触发（价格上涨15%）"""
        entry_price = 100.0
        current_price = 115.1  # 上涨15.1%

        assert strategy.check_take_profit(entry_price, current_price) is True

    def test_check_take_profit_not_triggered(self, strategy):
        """测试止盈未触发（价格上涨14%）"""
        entry_price = 100.0
        current_price = 114.0  # 上涨14%

        assert strategy.check_take_profit(entry_price, current_price) is False

    def test_check_take_profit_price_down(self, strategy):
        """测试价格下跌时不触发止盈"""
        entry_price = 100.0
        current_price = 95.0  # 下跌5%

        assert strategy.check_take_profit(entry_price, current_price) is False

    def test_check_max_holding_days_exceeded(self, strategy):
        """测试超过最大持仓天数"""
        entry_date = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 12)  # 持仓11天

        assert strategy.check_max_holding_days(entry_date, current_date) is True

    def test_check_max_holding_days_not_exceeded(self, strategy):
        """测试未超过最大持仓天数"""
        entry_date = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 10)  # 持仓9天

        assert strategy.check_max_holding_days(entry_date, current_date) is False

    def test_check_max_holding_days_exact(self, strategy):
        """测试刚好到达最大持仓天数"""
        entry_date = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 11)  # 持仓10天

        # 等于最大天数不算超过
        assert strategy.check_max_holding_days(entry_date, current_date) is False

    def test_can_sell_today_t1_rule(self, strategy):
        """测试T+1规则（当日买入不能卖出）"""
        buy_date = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 1)

        assert strategy.can_sell_today(buy_date, current_date) is False

    def test_can_sell_today_next_day(self, strategy):
        """测试次日可以卖出"""
        buy_date = datetime(2024, 1, 1)
        current_date = datetime(2024, 1, 2)

        assert strategy.can_sell_today(buy_date, current_date) is True

    def test_generate_signals_abstract(self):
        """测试generate_signals是抽象方法"""
        # BaseStrategy不能直接实例化（因为是抽象类）
        with pytest.raises(TypeError):
            BaseStrategy('test')

    def test_generate_signals_concrete(self, strategy):
        """测试具体策略的信号生成"""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })

        result = strategy.generate_signals(df)

        # 验证返回DataFrame包含signal列
        assert 'signal' in result.columns
        assert len(result) == len(df)

    def test_edge_case_zero_price(self, strategy):
        """测试边界情况：价格为0"""
        entry_price = 100.0
        current_price = 0.0

        # 价格为0应该触发止损
        assert strategy.check_stop_loss(entry_price, current_price) is True

    def test_edge_case_negative_price(self, strategy):
        """测试边界情况：负价格"""
        entry_price = 100.0
        current_price = -10.0

        # 负价格应该触发止损
        assert strategy.check_stop_loss(entry_price, current_price) is True

    def test_edge_case_same_price(self, strategy):
        """测试边界情况：价格相同"""
        entry_price = 100.0
        current_price = 100.0

        # 价格相同不触发止损或止盈
        assert strategy.check_stop_loss(entry_price, current_price) is False
        assert strategy.check_take_profit(entry_price, current_price) is False

    def test_strategy_with_custom_params(self):
        """测试自定义参数的策略"""
        # 使用value_investing策略测试
        strategy = ConcreteStrategy('value_investing')

        # 验证不同策略有不同的参数
        assert strategy.get_param('stop_loss') == 0.15
        assert strategy.get_param('take_profit') == 0.50
        assert strategy.get_param('max_holding_days') == 365

    def test_invalid_strategy_name(self):
        """测试无效的策略名称"""
        with pytest.raises(ValueError):
            ConcreteStrategy('non_existent_strategy')
