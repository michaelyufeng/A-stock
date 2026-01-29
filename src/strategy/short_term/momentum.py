"""动量策略模块"""
import pandas as pd
import numpy as np
from src.strategy.base_strategy import BaseStrategy
from src.analysis.technical.indicators import TechnicalIndicators
from src.core.constants import SignalType
from src.core.logger import get_logger

logger = get_logger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    动量策略 - 基于技术指标的短线交易策略

    策略逻辑：
    - 买入条件：满足3个或以上条件
      1. RSI从超卖区回升
      2. MACD金叉
      3. 成交量放大
      4. 价格突破MA20

    - 卖出条件：任意满足
      1. RSI超买
      2. MACD死叉
      3. 止损止盈（继承自BaseStrategy）
      4. 超过最大持仓天数

    Attributes:
        indicators: 技术指标计算器
    """

    def __init__(self):
        """初始化动量策略"""
        super().__init__('momentum')
        self.indicators = TechnicalIndicators()
        logger.info("动量策略初始化完成")

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号

        Args:
            df: K线数据DataFrame，需包含以下列：
                - date: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量

        Returns:
            添加了'signal'列的DataFrame，signal值为'buy'/'sell'/'hold'

        Raises:
            ValueError: 如果输入数据为空或缺少必要列
        """
        # 验证输入数据
        if df is None or len(df) == 0:
            raise ValueError("输入数据不能为空")

        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        # 检查中文列名
        chinese_columns = ['开盘', '最高', '最低', '收盘', '成交量']
        has_chinese = any(col in df.columns for col in chinese_columns)

        if missing_columns and not has_chinese:
            raise ValueError(
                f"输入数据缺少必要列: {missing_columns}。"
                f"需要的列: {required_columns}"
            )

        logger.info(f"开始生成动量策略信号，数据量: {len(df)}")

        # 复制数据框，避免修改原始数据
        df = df.copy()

        # 1. 计算所有技术指标
        try:
            df = self.indicators.calculate_all(df)
            logger.debug("技术指标计算完成")
        except Exception as e:
            logger.error(f"技术指标计算失败: {e}")
            raise

        # 2. 初始化信号列为HOLD
        df['signal'] = SignalType.HOLD.value

        # 3. 检查买入条件
        try:
            buy_conditions = self._check_buy_conditions(df)
            df.loc[buy_conditions, 'signal'] = SignalType.BUY.value
            buy_count = buy_conditions.sum()
            logger.info(f"生成 {buy_count} 个买入信号")
        except Exception as e:
            logger.error(f"检查买入条件失败: {e}")
            raise

        # 4. 检查卖出条件（卖出信号优先级高于买入信号）
        try:
            sell_conditions = self._check_sell_conditions(df)
            df.loc[sell_conditions, 'signal'] = SignalType.SELL.value
            sell_count = sell_conditions.sum()
            logger.info(f"生成 {sell_count} 个卖出信号")
        except Exception as e:
            logger.error(f"检查卖出条件失败: {e}")
            raise

        hold_count = (df['signal'] == SignalType.HOLD.value).sum()
        logger.info(f"信号生成完成 - 买入: {buy_count}, 卖出: {sell_count}, 持有: {hold_count}")

        return df

    def _check_buy_conditions(self, df: pd.DataFrame) -> pd.Series:
        """
        检查买入条件（需满足3个以上）

        Args:
            df: 包含技术指标的DataFrame

        Returns:
            布尔Series，True表示满足买入条件

        买入条件：
        1. RSI从超卖区回升: RSI前一天 < oversold AND RSI当天 > recovery_threshold
        2. MACD金叉: MACD前一天 < Signal前一天 AND MACD当天 > Signal当天
        3. 成交量放大: 当日成交量 > VOL_MA5 * surge_ratio
        4. 价格突破MA20: 收盘价 > MA20
        """
        # 获取参数
        rsi_oversold = self.get_param('rsi_oversold', 30)
        rsi_overbought = self.get_param('rsi_overbought', 70)
        volume_surge_ratio = self.get_param('volume_surge_ratio', 2.0)

        # RSI回升阈值（从超卖区回升到这个值以上）
        rsi_recovery_threshold = 40

        # 条件1: RSI从超卖区回升
        rsi_condition = (
            (df['RSI'].shift(1) < rsi_oversold) &
            (df['RSI'] > rsi_recovery_threshold)
        ).fillna(False)

        # 条件2: MACD金叉
        macd_golden_cross = (
            (df['MACD'].shift(1) < df['MACD_signal'].shift(1)) &
            (df['MACD'] > df['MACD_signal'])
        ).fillna(False)

        # 条件3: 成交量放大
        volume_surge = (
            df['volume'] > df['VOL_MA5'] * volume_surge_ratio
        ).fillna(False)

        # 条件4: 价格突破MA20
        price_breakout = (
            df['close'] > df['MA20']
        ).fillna(False)

        # 计算满足的条件数量
        conditions_met = (
            rsi_condition.astype(int) +
            macd_golden_cross.astype(int) +
            volume_surge.astype(int) +
            price_breakout.astype(int)
        )

        # 满足3个或以上条件时触发买入
        buy_signal = conditions_met >= 3

        # 记录调试信息
        if buy_signal.any():
            logger.debug(
                f"买入条件满足情况 - "
                f"RSI回升: {rsi_condition.sum()}, "
                f"MACD金叉: {macd_golden_cross.sum()}, "
                f"成交量放大: {volume_surge.sum()}, "
                f"突破MA20: {price_breakout.sum()}"
            )

        return buy_signal

    def _check_sell_conditions(self, df: pd.DataFrame) -> pd.Series:
        """
        检查卖出条件（任意满足即触发）

        Args:
            df: 包含技术指标的DataFrame

        Returns:
            布尔Series，True表示满足卖出条件

        卖出条件（任意满足）：
        1. RSI超买: RSI > overbought
        2. MACD死叉: MACD前一天 > Signal前一天 AND MACD当天 < Signal当天
        """
        # 获取参数
        rsi_overbought = self.get_param('rsi_overbought', 70)

        # 条件1: RSI超买
        rsi_condition = (
            df['RSI'] > rsi_overbought
        ).fillna(False)

        # 条件2: MACD死叉
        macd_death_cross = (
            (df['MACD'].shift(1) > df['MACD_signal'].shift(1)) &
            (df['MACD'] < df['MACD_signal'])
        ).fillna(False)

        # 任意条件满足即触发卖出
        sell_signal = rsi_condition | macd_death_cross

        # 记录调试信息
        if sell_signal.any():
            logger.debug(
                f"卖出条件满足情况 - "
                f"RSI超买: {rsi_condition.sum()}, "
                f"MACD死叉: {macd_death_cross.sum()}"
            )

        return sell_signal

    def __str__(self) -> str:
        """返回策略的字符串表示"""
        return f"<MomentumStrategy(name={self.strategy_name})>"

    def __repr__(self) -> str:
        """返回策略的详细表示"""
        return (
            f"MomentumStrategy("
            f"strategy_name='{self.strategy_name}', "
            f"rsi_period={self.get_param('rsi_period')}, "
            f"rsi_oversold={self.get_param('rsi_oversold')}, "
            f"rsi_overbought={self.get_param('rsi_overbought')}, "
            f"volume_surge_ratio={self.get_param('volume_surge_ratio')}"
            f")"
        )
