"""
RealTimeWatcher - 实时行情监控器

功能:
1. 监控股票列表的实时行情
2. 批量获取和单个获取行情数据
3. 行情缓存和自动刷新
4. 异常处理和数据验证
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from src.data.akshare_provider import AKShareProvider


logger = logging.getLogger(__name__)


class RealTimeWatcher:
    """实时行情监控器"""

    def __init__(self, stock_list: List[Dict[str, str]], update_interval: int = 60):
        """
        初始化实时监控器

        Args:
            stock_list: 股票列表，格式: [{'code': '600519', 'name': '贵州茅台'}, ...]
            update_interval: 更新间隔（秒），默认60秒
        """
        self.update_interval = update_interval
        self.watchlist: Dict[str, str] = {}  # {code: name}
        self.quotes: Dict[str, Dict] = {}  # {code: quote_data}
        self.provider = AKShareProvider()

        # 初始化监控列表
        for stock in stock_list:
            self.watchlist[stock['code']] = stock['name']

    # ========================================================================
    # 监控列表管理
    # ========================================================================

    def add_stock(self, stock_code: str, stock_name: str):
        """
        添加股票到监控列表

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
        """
        self.watchlist[stock_code] = stock_name
        logger.info(f"Added {stock_code} {stock_name} to watchlist")

    def remove_stock(self, stock_code: str) -> bool:
        """
        从监控列表移除股票

        Args:
            stock_code: 股票代码

        Returns:
            是否成功移除
        """
        if stock_code not in self.watchlist:
            logger.warning(f"Stock {stock_code} not in watchlist")
            return False

        del self.watchlist[stock_code]

        # 同时删除行情缓存
        if stock_code in self.quotes:
            del self.quotes[stock_code]

        logger.info(f"Removed {stock_code} from watchlist")
        return True

    def get_watchlist(self) -> Dict[str, str]:
        """
        获取当前监控列表

        Returns:
            监控列表字典 {code: name}
        """
        return self.watchlist.copy()

    # ========================================================================
    # 行情获取
    # ========================================================================

    def get_latest_quote(
        self,
        stock_code: str,
        max_age_seconds: int = None
    ) -> Optional[Dict]:
        """
        获取单只股票的最新行情

        Args:
            stock_code: 股票代码
            max_age_seconds: 缓存最大年龄（秒），超过则刷新

        Returns:
            行情数据字典或None
        """
        # 检查是否在监控列表
        if stock_code not in self.watchlist:
            logger.warning(f"Stock {stock_code} not in watchlist")
            return None

        # 检查缓存
        if stock_code in self.quotes:
            quote = self.quotes[stock_code]

            # 检查缓存是否过期
            if max_age_seconds is not None:
                age = (datetime.now() - quote['update_time']).total_seconds()
                if age <= max_age_seconds:
                    return quote.copy()

                # 缓存过期，刷新
                logger.debug(f"Cache expired for {stock_code}, refreshing")
            else:
                return quote.copy()

        # 获取新数据
        try:
            quote_data = self.provider.get_realtime_quote(stock_code)

            if quote_data is None:
                logger.warning(f"No data returned for {stock_code}")
                return None

            # 添加更新时间戳
            quote_data['update_time'] = datetime.now()

            # 确保有名称
            if 'name' not in quote_data:
                quote_data['name'] = self.watchlist[stock_code]

            # 缓存
            self.quotes[stock_code] = quote_data

            return quote_data.copy()

        except Exception as e:
            logger.error(f"Error fetching quote for {stock_code}: {e}")
            return None

    def get_all_quotes(self) -> Dict[str, Dict]:
        """
        获取所有监控股票的行情

        Returns:
            行情数据字典 {code: quote_data}
        """
        if not self.watchlist:
            return {}

        # 从缓存返回
        return self.quotes.copy()

    def update_quotes(self, force: bool = False):
        """
        更新所有股票行情

        Args:
            force: 是否强制刷新（忽略缓存）
        """
        if not self.watchlist:
            logger.debug("Watchlist is empty, skipping update")
            return

        try:
            # 批量获取行情
            stock_codes = list(self.watchlist.keys())
            quotes_data = self.provider.get_realtime_quotes(stock_codes)

            if quotes_data is None:
                logger.warning("No quotes data returned from provider")
                return

            # 更新缓存
            current_time = datetime.now()
            for code, quote in quotes_data.items():
                # 添加更新时间戳
                quote['update_time'] = current_time

                # 确保有名称
                if 'name' not in quote:
                    quote['name'] = self.watchlist.get(code, '')

                # 缓存
                self.quotes[code] = quote

            logger.info(f"Updated quotes for {len(quotes_data)} stocks")

        except Exception as e:
            logger.error(f"Error updating quotes: {e}")

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def get_quote_age(self, stock_code: str) -> Optional[float]:
        """
        获取行情数据的年龄（秒）

        Args:
            stock_code: 股票代码

        Returns:
            年龄（秒）或None
        """
        if stock_code not in self.quotes:
            return None

        quote = self.quotes[stock_code]
        age = (datetime.now() - quote['update_time']).total_seconds()
        return age

    def clear_cache(self):
        """清空行情缓存"""
        self.quotes.clear()
        logger.info("Quote cache cleared")

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self.quotes)
