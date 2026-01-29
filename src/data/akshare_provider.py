"""AKShare数据提供者"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.core.logger import get_logger
from src.core.config_manager import ConfigManager
from src.data.cache_manager import CacheManager
from src.utils.stock_code_helper import strip_market_suffix

logger = get_logger(__name__)


class AKShareProvider:
    """AKShare数据提供者"""

    def __init__(self):
        self.config = ConfigManager()
        self.cache = CacheManager()
        self.sources = self.config.get('data.sources', {})

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股股票列表

        Returns:
            股票列表DataFrame
        """
        cache_key = 'stock_list'

        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info("Fetching stock list from akshare...")
            df = ak.stock_zh_a_spot_em()

            # 缓存1小时
            self.cache.set(cache_key, df, ttl=3600)

            logger.info(f"Fetched {len(df)} stocks")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch stock list: {e}")
            raise

    def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取实时行情

        Args:
            code: 股票代码

        Returns:
            行情字典
        """
        code = strip_market_suffix(code)
        cache_key = f'realtime_quote:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('realtime')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching realtime quote for {code}...")
            df = ak.stock_zh_a_spot_em()

            # 查找指定股票
            stock_data = df[df['代码'] == code]
            if stock_data.empty:
                logger.warning(f"Stock {code} not found")
                return {}

            # 转换为字典
            quote = stock_data.iloc[0].to_dict()

            # 缓存
            self.cache.set(cache_key, quote, ttl=ttl)

            return quote
        except Exception as e:
            logger.error(f"Failed to fetch realtime quote for {code}: {e}")
            raise

    def get_realtime_quotes(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取实时行情（优化版本，减少API调用）

        Args:
            codes: 股票代码列表

        Returns:
            行情字典 {code: quote_data}
        """
        if not codes:
            return {}

        # 标准化代码
        codes = [strip_market_suffix(code) for code in codes]

        try:
            logger.info(f"Fetching realtime quotes for {len(codes)} stocks...")
            # 一次性获取全市场数据
            df = ak.stock_zh_a_spot_em()

            # 筛选指定股票
            result = {}
            for code in codes:
                stock_data = df[df['代码'] == code]
                if not stock_data.empty:
                    quote = stock_data.iloc[0].to_dict()
                    result[code] = quote
                else:
                    logger.warning(f"Stock {code} not found in realtime data")

            logger.info(f"Successfully fetched {len(result)} quotes")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch realtime quotes: {e}")
            return {}

    def get_daily_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ('qfq'-前复权, 'hfq'-后复权, ''-不复权)

        Returns:
            日线数据DataFrame
        """
        code = strip_market_suffix(code)

        # 默认日期
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - pd.Timedelta(days=365)).strftime('%Y%m%d')

        cache_key = f'daily_kline:{code}:{start_date}:{end_date}:{adjust}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('daily')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching daily kline for {code} ({start_date} to {end_date})...")
            df = ak.stock_zh_a_hist(
                symbol=code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched {len(df)} daily records for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch daily kline for {code}: {e}")
            raise

    def get_financial_data(self, code: str) -> pd.DataFrame:
        """
        获取财务指标数据

        Args:
            code: 股票代码

        Returns:
            财务指标DataFrame
        """
        code = strip_market_suffix(code)
        cache_key = f'financial:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('financial')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching financial data for {code}...")
            df = ak.stock_financial_analysis_indicator(symbol=code)

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched financial data for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch financial data for {code}: {e}")
            raise

    def get_money_flow(self, code: str) -> pd.DataFrame:
        """
        获取资金流向数据

        Args:
            code: 股票代码

        Returns:
            资金流向DataFrame
        """
        code = strip_market_suffix(code)
        cache_key = f'money_flow:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('realtime')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching money flow for {code}...")
            df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith('6') else "sz")

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched money flow data for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch money flow for {code}: {e}")
            raise
