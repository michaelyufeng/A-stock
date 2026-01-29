"""技术指标计算模块"""
import pandas as pd
from typing import List, Dict, Any
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from src.core.logger import get_logger
from src.core.constants import DEFAULT_INDICATORS

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self):
        self.config = DEFAULT_INDICATORS

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名

        Args:
            df: 原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        df = df.copy()

        # 列名映射
        column_map = {
            '收盘': 'close',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '日期': 'date',
        }

        df.rename(columns=column_map, inplace=True)
        return df

    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算移动平均线

        Args:
            df: 股票数据
            periods: MA周期列表

        Returns:
            添加MA指标的DataFrame
        """
        if periods is None:
            periods = self.config['MA']

        df = self._standardize_columns(df)

        for period in periods:
            indicator = SMAIndicator(close=df['close'], window=period)
            df[f'MA{period}'] = indicator.sma_indicator()
            logger.debug(f"Calculated MA{period}")

        return df

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = None,
        slow: int = None,
        signal: int = None
    ) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: 股票数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            添加MACD指标的DataFrame
        """
        macd_config = self.config['MACD']
        if fast is None:
            fast = macd_config['fast']
        if slow is None:
            slow = macd_config['slow']
        if signal is None:
            signal = macd_config['signal']

        df = self._standardize_columns(df)

        indicator = MACD(close=df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
        df['MACD'] = indicator.macd()
        df['MACD_signal'] = indicator.macd_signal()
        df['MACD_hist'] = indicator.macd_diff()

        logger.debug(f"Calculated MACD ({fast}/{slow}/{signal})")
        return df

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI指标

        Args:
            df: 股票数据
            period: RSI周期

        Returns:
            添加RSI指标的DataFrame
        """
        df = self._standardize_columns(df)
        indicator = RSIIndicator(close=df['close'], window=period)
        df['RSI'] = indicator.rsi()

        logger.debug(f"Calculated RSI ({period})")
        return df

    def calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标

        Args:
            df: 股票数据

        Returns:
            添加KDJ指标的DataFrame
        """
        df = self._standardize_columns(df)

        kdj_config = self.config['KDJ']
        n = kdj_config['n']
        k = kdj_config['k']
        d = kdj_config['d']

        indicator = StochasticOscillator(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=n,
            smooth_window=k
        )
        df['K'] = indicator.stoch()
        df['D'] = indicator.stoch_signal()
        df['J'] = 3 * df['K'] - 2 * df['D']

        logger.debug(f"Calculated KDJ (n={n})")
        return df

    def calculate_boll(self, df: pd.DataFrame, n: int = 20, std: int = 2) -> pd.DataFrame:
        """
        计算布林带指标

        Args:
            df: 股票数据
            n: 周期
            std: 标准差倍数

        Returns:
            添加布林带指标的DataFrame
        """
        df = self._standardize_columns(df)

        indicator = BollingerBands(close=df['close'], window=n, window_dev=std)
        df['BOLL_UPPER'] = indicator.bollinger_hband()
        df['BOLL_MIDDLE'] = indicator.bollinger_mavg()
        df['BOLL_LOWER'] = indicator.bollinger_lband()

        logger.debug(f"Calculated BOLL (n={n}, std={std})")
        return df

    def calculate_volume_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算成交量均线

        Args:
            df: 股票数据
            periods: 均线周期列表

        Returns:
            添加成交量均线的DataFrame
        """
        if periods is None:
            periods = self.config['VOL_MA']

        df = self._standardize_columns(df)

        for period in periods:
            indicator = SMAIndicator(close=df['volume'], window=period)
            df[f'VOL_MA{period}'] = indicator.sma_indicator()

        logger.debug(f"Calculated VOL_MA {periods}")
        return df

    def calculate_atr(self, df: pd.DataFrame, period: int = None) -> pd.DataFrame:
        """
        计算ATR指标

        Args:
            df: 股票数据
            period: ATR周期

        Returns:
            添加ATR指标的DataFrame
        """
        if period is None:
            period = self.config['ATR']

        df = self._standardize_columns(df)
        indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period)
        df['ATR'] = indicator.average_true_range()

        logger.debug(f"Calculated ATR ({period})")
        return df

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 股票数据

        Returns:
            添加所有指标的DataFrame
        """
        logger.info("Calculating all technical indicators...")

        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_kdj(df)
        df = self.calculate_boll(df)
        df = self.calculate_volume_ma(df)
        df = self.calculate_atr(df)

        logger.info("All technical indicators calculated")
        return df
