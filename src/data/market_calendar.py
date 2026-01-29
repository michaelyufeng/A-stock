"""A股交易日历模块"""
import pandas as pd
import akshare as ak
from datetime import datetime, time, timedelta
from typing import List, Optional
from functools import lru_cache
from src.core.logger import get_logger
from src.core.constants import TRADING_HOURS

logger = get_logger(__name__)


class MarketCalendar:
    """A股交易日历"""

    def __init__(self):
        self._trading_days_cache: Optional[List[datetime]] = None
        self._cache_year: Optional[int] = None

    def _load_trading_days(self, year: int) -> List[datetime]:
        """
        加载指定年份的交易日

        Args:
            year: 年份

        Returns:
            交易日列表
        """
        try:
            # 使用akshare获取交易日历
            df = ak.tool_trade_date_hist_sina()
            # 筛选指定年份
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df_year = df[df['trade_date'].dt.year == year]
            return df_year['trade_date'].tolist()
        except Exception as e:
            logger.warning(f"Failed to load trading days from akshare: {e}")
            # 降级：使用简单规则（仅排除周末，不考虑节假日）
            return self._generate_simple_trading_days(year)

    def _generate_simple_trading_days(self, year: int) -> List[datetime]:
        """
        生成简单的交易日列表（仅排除周末）

        Args:
            year: 年份

        Returns:
            交易日列表
        """
        trading_days = []
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

        current = start_date
        while current <= end_date:
            # 排除周末
            if current.weekday() < 5:  # 0-4是周一到周五
                trading_days.append(current)
            current += timedelta(days=1)

        return trading_days

    def _ensure_cache(self, date: datetime) -> None:
        """确保缓存已加载"""
        year = date.year
        if self._cache_year != year:
            self._trading_days_cache = self._load_trading_days(year)
            self._cache_year = year

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        # 周末肯定不是交易日
        if date.weekday() >= 5:
            return False

        # 检查缓存
        self._ensure_cache(date)

        # 检查是否在交易日列表中
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return any(td.date() == date_only.date() for td in self._trading_days_cache)

    def is_trading_time(self, check_time: time) -> bool:
        """
        判断是否为交易时间

        Args:
            check_time: 时间

        Returns:
            是否为交易时间
        """
        morning_start = time.fromisoformat(TRADING_HOURS['morning_start'])
        morning_end = time.fromisoformat(TRADING_HOURS['morning_end'])
        afternoon_start = time.fromisoformat(TRADING_HOURS['afternoon_start'])
        afternoon_end = time.fromisoformat(TRADING_HOURS['afternoon_end'])

        # 上午时段
        if morning_start <= check_time <= morning_end:
            return True

        # 下午时段
        if afternoon_start <= check_time <= afternoon_end:
            return True

        return False

    def is_call_auction_time(self, check_time: time) -> bool:
        """
        判断是否为集合竞价时间

        Args:
            check_time: 时间

        Returns:
            是否为集合竞价时间
        """
        auction_start = time.fromisoformat(TRADING_HOURS['call_auction_start'])
        auction_end = time.fromisoformat(TRADING_HOURS['call_auction_end'])

        return auction_start <= check_time <= auction_end

    def get_latest_trading_day(self, before_date: Optional[datetime] = None) -> datetime:
        """
        获取最近的交易日

        Args:
            before_date: 参考日期，默认为当前日期

        Returns:
            最近的交易日
        """
        if before_date is None:
            before_date = datetime.now()

        # 向前查找最近的交易日
        current = before_date
        for _ in range(10):  # 最多向前查找10天
            if self.is_trading_day(current):
                return current
            current -= timedelta(days=1)

        # 如果10天内都没有交易日，返回参考日期
        logger.warning(f"No trading day found within 10 days before {before_date}")
        return before_date

    def get_next_trading_day(self, after_date: Optional[datetime] = None) -> datetime:
        """
        获取下一个交易日

        Args:
            after_date: 参考日期，默认为当前日期

        Returns:
            下一个交易日
        """
        if after_date is None:
            after_date = datetime.now()

        # 向后查找下一个交易日
        current = after_date + timedelta(days=1)
        for _ in range(10):  # 最多向后查找10天
            if self.is_trading_day(current):
                return current
            current += timedelta(days=1)

        # 如果10天内都没有交易日，返回参考日期
        logger.warning(f"No trading day found within 10 days after {after_date}")
        return after_date
