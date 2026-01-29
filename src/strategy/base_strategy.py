"""策略基类模块"""
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger
from src.core.constants import SignalType

logger = get_logger(__name__)


class BaseStrategy(ABC):
    """
    策略基类

    所有具体策略都应该继承此类并实现generate_signals方法。
    提供统一的接口用于信号生成、止损止盈管理和持仓时间管理。

    Attributes:
        strategy_name: 策略名称（对应config/strategies.yaml中的key）
        config: 配置管理器实例
        params: 从配置文件加载的策略参数
    """

    def __init__(self, strategy_name: str):
        """
        初始化策略

        Args:
            strategy_name: 策略名称（对应config/strategies.yaml中的key）

        Raises:
            ValueError: 如果策略名称在配置文件中不存在
        """
        self.strategy_name = strategy_name
        self.config = ConfigManager()
        self.params = self._load_strategy_params()

        logger.info(f"初始化策略: {strategy_name}")

    def _load_strategy_params(self) -> Dict[str, Any]:
        """
        从配置文件加载策略参数

        Returns:
            包含策略参数的字典

        Raises:
            ValueError: 如果策略在配置文件中不存在
        """
        try:
            strategies_config = self.config.get('strategies', {})

            if self.strategy_name not in strategies_config:
                raise ValueError(
                    f"策略 '{self.strategy_name}' 在配置文件中不存在。"
                    f"可用策略: {list(strategies_config.keys())}"
                )

            strategy_config = strategies_config[self.strategy_name]
            params = strategy_config.get('parameters', {})

            logger.debug(f"加载策略 '{self.strategy_name}' 参数: {params}")
            return params

        except Exception as e:
            logger.error(f"加载策略参数失败: {e}")
            raise

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号（子类必须实现）

        Args:
            df: K线数据，包含技术指标

        Returns:
            添加了'signal'列的DataFrame，signal值为'buy'/'sell'/'hold'

        Note:
            - signal列应使用SignalType枚举值
            - 返回的DataFrame应包含原始数据的所有列
            - 子类必须实现此方法
        """
        pass

    def check_stop_loss(self, entry_price: float, current_price: float) -> bool:
        """
        检查是否触及止损

        Args:
            entry_price: 买入价格
            current_price: 当前价格

        Returns:
            True表示触及止损，False表示未触及

        Note:
            - 止损条件: (entry_price - current_price) / entry_price >= stop_loss
            - 价格为0或负数时视为触及止损
        """
        if current_price <= 0:
            logger.warning(f"检测到异常价格: {current_price}，触发止损")
            return True

        stop_loss_threshold = self.get_param('stop_loss', 0.08)
        loss_ratio = (entry_price - current_price) / entry_price

        if loss_ratio >= stop_loss_threshold:
            logger.info(
                f"触发止损: 买入价={entry_price:.2f}, "
                f"当前价={current_price:.2f}, "
                f"亏损={loss_ratio:.2%}, "
                f"止损线={stop_loss_threshold:.2%}"
            )
            return True

        return False

    def check_take_profit(self, entry_price: float, current_price: float) -> bool:
        """
        检查是否触及止盈

        Args:
            entry_price: 买入价格
            current_price: 当前价格

        Returns:
            True表示触及止盈，False表示未触及

        Note:
            - 止盈条件: (current_price - entry_price) / entry_price >= take_profit
        """
        if current_price <= 0:
            return False

        take_profit_threshold = self.get_param('take_profit', 0.15)
        profit_ratio = (current_price - entry_price) / entry_price

        if profit_ratio >= take_profit_threshold:
            logger.info(
                f"触发止盈: 买入价={entry_price:.2f}, "
                f"当前价={current_price:.2f}, "
                f"盈利={profit_ratio:.2%}, "
                f"止盈线={take_profit_threshold:.2%}"
            )
            return True

        return False

    def check_max_holding_days(
        self,
        entry_date: datetime,
        current_date: datetime
    ) -> bool:
        """
        检查是否超过最大持仓天数

        Args:
            entry_date: 买入日期
            current_date: 当前日期

        Returns:
            True表示超过最大持仓天数，False表示未超过

        Note:
            - 持仓天数 = (current_date - entry_date).days
            - 仅当超过最大天数时返回True，等于最大天数返回False
        """
        max_days = self.get_param('max_holding_days', 10)
        holding_days = (current_date - entry_date).days

        if holding_days > max_days:
            logger.info(
                f"超过最大持仓天数: 持仓{holding_days}天, "
                f"最大{max_days}天"
            )
            return True

        return False

    def can_sell_today(self, buy_date: datetime, current_date: datetime) -> bool:
        """
        检查是否可以在当日卖出（T+1规则）

        Args:
            buy_date: 买入日期
            current_date: 当前日期

        Returns:
            True表示可以卖出，False表示不能卖出（当日买入）

        Note:
            - A股实行T+1交易制度
            - 当日买入的股票最快次日才能卖出
        """
        # 比较日期（忽略时间部分）
        can_sell = current_date.date() > buy_date.date()

        if not can_sell:
            logger.debug(
                f"T+1限制: 买入日期={buy_date.date()}, "
                f"当前日期={current_date.date()}, 不能卖出"
            )

        return can_sell

    def get_param(self, key: str, default: Any = None) -> Any:
        """
        获取策略参数

        Args:
            key: 参数名称
            default: 默认值，如果参数不存在则返回此值

        Returns:
            参数值，如果不存在则返回default
        """
        return self.params.get(key, default)

    def __str__(self) -> str:
        """返回策略的字符串表示"""
        return f"<{self.__class__.__name__}(name={self.strategy_name})>"

    def __repr__(self) -> str:
        """返回策略的详细表示"""
        return (
            f"{self.__class__.__name__}("
            f"strategy_name='{self.strategy_name}', "
            f"params={self.params})"
        )
