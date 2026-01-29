"""
SignalDetector - 信号检测器

功能:
1. 技术信号检测（MA交叉、MACD、RSI、成交量）
2. 价格信号检测（突破、支撑/压力位）
3. 风险信号检测（止损、止盈、异常波动）
4. A股特色检测（涨跌停）
5. 批量扫描
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import numpy as np

from src.data.akshare_provider import AKShareProvider
from src.risk.risk_manager import RiskManager


logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """交易信号数据类"""
    stock_code: str
    stock_name: str
    signal_type: str  # 'BUY', 'SELL', 'WARNING', 'INFO'
    category: str     # 'technical', 'risk', 'price', 'volume'
    description: str
    priority: str     # 'low', 'medium', 'high', 'critical'
    trigger_price: float
    timestamp: datetime
    metadata: Dict[str, Any]


class SignalDetector:
    """信号检测器 - 检测各类交易信号和风险预警"""

    def __init__(self, risk_manager: Optional[RiskManager] = None):
        """
        初始化信号检测器

        Args:
            risk_manager: 风险管理器（可选）
        """
        self.risk_manager = risk_manager
        self.provider = AKShareProvider()

        # 默认参数
        self.ma_short = 5
        self.ma_long = 20
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.volume_multiplier = 2.0

    # ========================================================================
    # 技术信号检测
    # ========================================================================

    def check_ma_crossover(self, stock_code: str) -> Optional[Signal]:
        """
        检测MA均线交叉信号

        Args:
            stock_code: 股票代码

        Returns:
            Signal或None
        """
        try:
            # 获取K线数据
            kline_df = self.provider.get_daily_kline(stock_code)

            if kline_df is None or len(kline_df) < self.ma_long + 5:
                logger.warning(f"Insufficient data for MA crossover: {stock_code}")
                return None

            # 计算均线
            kline_df['ma_short'] = kline_df['close'].rolling(window=self.ma_short).mean()
            kline_df['ma_long'] = kline_df['close'].rolling(window=self.ma_long).mean()

            # 去除NaN
            kline_df = kline_df.dropna()

            if len(kline_df) < 2:
                return None

            # 检查最近的交叉
            # 前一天和今天的MA关系
            prev = kline_df.iloc[-2]
            curr = kline_df.iloc[-1]

            # 金叉: 短期均线上穿长期均线
            if prev['ma_short'] <= prev['ma_long'] and curr['ma_short'] > curr['ma_long']:
                return Signal(
                    stock_code=stock_code,
                    stock_name=stock_code,
                    signal_type='BUY',
                    category='technical',
                    description=f'MA{self.ma_short}金叉MA{self.ma_long}',
                    priority='medium',
                    trigger_price=float(curr['close']),
                    timestamp=datetime.now(),
                    metadata={
                        'ma_short': self.ma_short,
                        'ma_long': self.ma_long,
                        'ma_short_value': float(curr['ma_short']),
                        'ma_long_value': float(curr['ma_long'])
                    }
                )

            # 死叉: 短期均线下穿长期均线
            elif prev['ma_short'] >= prev['ma_long'] and curr['ma_short'] < curr['ma_long']:
                return Signal(
                    stock_code=stock_code,
                    stock_name=stock_code,
                    signal_type='SELL',
                    category='technical',
                    description=f'MA{self.ma_short}死叉MA{self.ma_long}',
                    priority='medium',
                    trigger_price=float(curr['close']),
                    timestamp=datetime.now(),
                    metadata={
                        'ma_short': self.ma_short,
                        'ma_long': self.ma_long,
                        'ma_short_value': float(curr['ma_short']),
                        'ma_long_value': float(curr['ma_long'])
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error checking MA crossover for {stock_code}: {e}")
            return None

    def check_rsi_extremes(self, stock_code: str) -> Optional[Signal]:
        """
        检测RSI超买超卖信号

        Args:
            stock_code: 股票代码

        Returns:
            Signal或None
        """
        try:
            # 获取K线数据
            kline_df = self.provider.get_daily_kline(stock_code)

            if kline_df is None or len(kline_df) < self.rsi_period + 5:
                logger.warning(f"Insufficient data for RSI: {stock_code}")
                return None

            # 计算RSI
            delta = kline_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = float(rsi.iloc[-1])
            current_price = float(kline_df['close'].iloc[-1])

            # 超卖 (RSI < 30)
            if current_rsi < self.rsi_oversold:
                return Signal(
                    stock_code=stock_code,
                    stock_name=stock_code,
                    signal_type='BUY',
                    category='technical',
                    description=f'RSI超卖 ({current_rsi:.1f})',
                    priority='medium',
                    trigger_price=current_price,
                    timestamp=datetime.now(),
                    metadata={
                        'rsi': current_rsi,
                        'rsi_oversold': self.rsi_oversold
                    }
                )

            # 超买 (RSI > 70)
            elif current_rsi > self.rsi_overbought:
                return Signal(
                    stock_code=stock_code,
                    stock_name=stock_code,
                    signal_type='SELL',
                    category='technical',
                    description=f'RSI超买 ({current_rsi:.1f})',
                    priority='medium',
                    trigger_price=current_price,
                    timestamp=datetime.now(),
                    metadata={
                        'rsi': current_rsi,
                        'rsi_overbought': self.rsi_overbought
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error checking RSI for {stock_code}: {e}")
            return None

    def check_volume_breakout(self, stock_code: str) -> Optional[Signal]:
        """
        检测成交量突破信号

        Args:
            stock_code: 股票代码

        Returns:
            Signal或None
        """
        try:
            # 获取K线数据
            kline_df = self.provider.get_daily_kline(stock_code)

            if kline_df is None or len(kline_df) < 20:
                return None

            # 计算平均成交量
            avg_volume = kline_df['volume'].iloc[-20:-1].mean()
            current_volume = kline_df['volume'].iloc[-1]
            current_price = float(kline_df['close'].iloc[-1])

            # 成交量突破（当前成交量 > 平均成交量 * 倍数）
            if current_volume > avg_volume * self.volume_multiplier:
                return Signal(
                    stock_code=stock_code,
                    stock_name=stock_code,
                    signal_type='BUY',
                    category='volume',
                    description=f'放量突破 ({current_volume/avg_volume:.1f}倍)',
                    priority='medium',
                    trigger_price=current_price,
                    timestamp=datetime.now(),
                    metadata={
                        'current_volume': float(current_volume),
                        'avg_volume': float(avg_volume),
                        'multiplier': float(current_volume / avg_volume)
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error checking volume breakout for {stock_code}: {e}")
            return None

    # ========================================================================
    # 风险信号检测
    # ========================================================================

    def check_stop_loss_trigger(
        self,
        stock_code: str,
        position: Dict,
        current_price: float
    ) -> Optional[Signal]:
        """
        检测止损触发

        Args:
            stock_code: 股票代码
            position: 持仓信息
            current_price: 当前价格

        Returns:
            Signal或None
        """
        stop_loss_price = position.get('stop_loss_price')

        if stop_loss_price and current_price <= stop_loss_price:
            return Signal(
                stock_code=stock_code,
                stock_name=position.get('stock_name', stock_code),
                signal_type='SELL',
                category='risk',
                description=f'触发止损 (止损价: {stop_loss_price:.2f})',
                priority='critical',
                trigger_price=current_price,
                timestamp=datetime.now(),
                metadata={
                    'stop_loss_price': stop_loss_price,
                    'entry_price': position.get('entry_price'),
                    'loss_pct': (current_price - position.get('entry_price')) / position.get('entry_price')
                }
            )

        return None

    def check_take_profit_trigger(
        self,
        stock_code: str,
        position: Dict,
        current_price: float
    ) -> Optional[Signal]:
        """
        检测止盈触发

        Args:
            stock_code: 股票代码
            position: 持仓信息
            current_price: 当前价格

        Returns:
            Signal或None
        """
        take_profit_price = position.get('take_profit_price')

        if take_profit_price and current_price >= take_profit_price:
            return Signal(
                stock_code=stock_code,
                stock_name=position.get('stock_name', stock_code),
                signal_type='SELL',
                category='risk',
                description=f'触发止盈 (止盈价: {take_profit_price:.2f})',
                priority='high',
                trigger_price=current_price,
                timestamp=datetime.now(),
                metadata={
                    'take_profit_price': take_profit_price,
                    'entry_price': position.get('entry_price'),
                    'profit_pct': (current_price - position.get('entry_price')) / position.get('entry_price')
                }
            )

        return None

    # ========================================================================
    # A股特色检测
    # ========================================================================

    def check_limit_up_down(self, stock_code: str, quote: Dict) -> Optional[Signal]:
        """
        检测涨跌停

        Args:
            stock_code: 股票代码
            quote: 实时行情

        Returns:
            Signal或None
        """
        change_pct = quote.get('change_pct', 0)
        current_price = quote.get('current_price', 0)

        # 涨停（主板10%，创业板/科创板20%）
        # 简化处理，使用9.5%作为阈值
        if change_pct >= 0.095:
            return Signal(
                stock_code=stock_code,
                stock_name=quote.get('name', stock_code),
                signal_type='WARNING',
                category='price',
                description=f'涨停 ({change_pct*100:.1f}%)',
                priority='high',
                trigger_price=current_price,
                timestamp=datetime.now(),
                metadata={
                    'change_pct': change_pct
                }
            )

        # 跌停
        elif change_pct <= -0.095:
            return Signal(
                stock_code=stock_code,
                stock_name=quote.get('name', stock_code),
                signal_type='WARNING',
                category='price',
                description=f'跌停 ({change_pct*100:.1f}%)',
                priority='critical',
                trigger_price=current_price,
                timestamp=datetime.now(),
                metadata={
                    'change_pct': change_pct
                }
            )

        return None

    # ========================================================================
    # 综合检测
    # ========================================================================

    def detect_all_signals(self, stock_code: str) -> List[Signal]:
        """
        检测所有信号

        Args:
            stock_code: 股票代码

        Returns:
            信号列表
        """
        signals = []

        # 技术信号
        ma_signal = self.check_ma_crossover(stock_code)
        if ma_signal:
            signals.append(ma_signal)

        rsi_signal = self.check_rsi_extremes(stock_code)
        if rsi_signal:
            signals.append(rsi_signal)

        volume_signal = self.check_volume_breakout(stock_code)
        if volume_signal:
            signals.append(volume_signal)

        return signals

    def scan_watchlist(self, stock_list: List[str]) -> Dict[str, List[Signal]]:
        """
        批量扫描股票列表

        Args:
            stock_list: 股票代码列表

        Returns:
            {stock_code: [signals]}
        """
        results = {}

        for stock_code in stock_list:
            try:
                signals = self.detect_all_signals(stock_code)
                if signals:
                    results[stock_code] = signals
            except Exception as e:
                logger.error(f"Error scanning {stock_code}: {e}")
                continue

        return results
