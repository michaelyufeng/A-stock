"""股票筛选过滤器模块

提供各种预设策略的具体过滤逻辑，用于从股票池中筛选出符合特定条件的股票。
"""
import pandas as pd
import numpy as np
from typing import Optional
from src.core.logger import get_logger

logger = get_logger(__name__)


def filter_by_pe_roe(
    df: pd.DataFrame,
    pe_max: float,
    roe_min: float
) -> pd.DataFrame:
    """
    根据PE和ROE过滤股票（低PE价值股策略）

    Args:
        df: 股票数据DataFrame，必须包含'PE'和'ROE'列
        pe_max: PE比率最大值（例如15.0表示PE<15）
        roe_min: ROE最小值，单位为%（例如10.0表示ROE>10%）

    Returns:
        过滤后的DataFrame，只包含满足PE和ROE条件的股票。
        如果缺少必需的列，返回空DataFrame并记录警告日志。
    """
    if df.empty:
        return df

    # 检查必需的列
    required_cols = ['PE', 'ROE']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"DataFrame缺少必需的列: {missing_cols}，跳过过滤")
        return pd.DataFrame()

    # 过滤掉NaN值
    filtered = df.dropna(subset=['PE', 'ROE'])

    # 应用PE过滤
    filtered = filtered[filtered['PE'] < pe_max]

    # 应用ROE过滤
    filtered = filtered[filtered['ROE'] > roe_min]

    logger.debug(f"PE/ROE过滤: {len(df)} -> {len(filtered)} 只股票 (PE<{pe_max}, ROE>{roe_min}%)")

    return filtered


def filter_by_dividend_yield(
    df: pd.DataFrame,
    yield_min: float
) -> pd.DataFrame:
    """
    根据股息率过滤股票（高股息率策略）

    Args:
        df: 股票数据DataFrame，必须包含'股息率'列
        yield_min: 股息率最小值，单位为%（例如3.0表示股息率>=3%）

    Returns:
        过滤后的DataFrame，只包含满足股息率条件的股票。
        如果缺少必需的列，返回空DataFrame并记录警告日志。
    """
    if df.empty:
        return df

    # 检查必需的列
    if '股息率' not in df.columns:
        logger.warning("DataFrame缺少必需的列: 股息率，跳过过滤")
        return pd.DataFrame()

    # 过滤掉NaN值
    filtered = df.dropna(subset=['股息率'])

    # 应用股息率过滤
    filtered = filtered[filtered['股息率'] >= yield_min]

    logger.debug(f"股息率过滤: {len(df)} -> {len(filtered)} 只股票 (股息率>={yield_min}%)")

    return filtered


def filter_by_breakout(
    df: pd.DataFrame,
    breakout_days: int = 20,
    volume_ratio_min: float = 1.2
) -> pd.DataFrame:
    """
    根据突破新高和成交量过滤股票（突破新高策略）

    筛选逻辑:
    1. 当前价格突破N日新高（通常是20日或60日）
    2. 成交量相对于平均成交量放大（例如>1.2倍）

    Args:
        df: 股票数据DataFrame，必须包含'close', 'high', 'volume'列
        breakout_days: 突破周期（20或60日）
        volume_ratio_min: 成交量放大倍数最小值

    Returns:
        过滤后的DataFrame，只包含满足突破条件的股票

    注意:
        - 此函数假设df已经按时间排序，最新数据在最后
        - 需要足够的历史数据来计算N日最高价
    """
    if df.empty:
        return df

    # 检查必需的列
    required_cols = ['close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"DataFrame缺少必需的列: {missing_cols}")
        return pd.DataFrame()

    # 如果数据不足，无法计算突破
    if len(df) < breakout_days:
        logger.debug(f"数据不足以计算{breakout_days}日突破 (需要{breakout_days}条，实际{len(df)}条)")
        return pd.DataFrame()

    # 创建副本以避免修改输入DataFrame
    df = df.copy()

    # 计算N日最高价（如果不存在）
    # 注意：要计算前N日的最高价，不包括当前日
    high_col = f'{breakout_days}日最高价'
    if high_col not in df.columns:
        # 使用shift(1)来计算前N日的最高价（不包括当前日）
        df[high_col] = df['close'].shift(1).rolling(window=breakout_days).max()

    # 计算平均成交量（如果不存在）
    if '平均成交量' not in df.columns:
        # 同样使用shift(1)来计算前N日的平均成交量
        df['平均成交量'] = df['volume'].shift(1).rolling(window=breakout_days).mean()

    # 获取最新的数据点
    latest = df.iloc[-1]

    # 检查是否有NaN（数据不足）
    if pd.isna(latest[high_col]) or pd.isna(latest['平均成交量']):
        logger.debug(f"数据不足以计算{breakout_days}日突破指标")
        return pd.DataFrame()

    # 条件1: 突破新高（当前价格 > 前N日最高价）
    is_breakout = latest['close'] > latest[high_col]

    # 条件2: 成交量放大
    is_volume_surge = latest['volume'] >= latest['平均成交量'] * volume_ratio_min

    # 只有同时满足两个条件才返回
    if is_breakout and is_volume_surge:
        logger.debug(f"突破新高确认: 价格={latest['close']:.2f}, {breakout_days}日最高={latest[high_col]:.2f}, "
                    f"成交量倍数={latest['volume']/latest['平均成交量']:.2f}x")
        return df
    else:
        logger.debug(f"未满足突破条件: 突破={is_breakout}, 放量={is_volume_surge}")
        return pd.DataFrame()


def filter_by_oversold_rebound(
    df: pd.DataFrame,
    rsi_oversold: float = 30.0,
    rsi_rebound_min: float = 30.0,
    lookback_periods: int = 50
) -> pd.DataFrame:
    """
    根据超卖反弹信号过滤股票（超卖反弹策略）

    筛选逻辑:
    1. 在lookback_periods期间内，RSI曾经低于超卖阈值（例如<30）
    2. 当前RSI已经回升到反弹阈值以上（例如>30）

    Args:
        df: 股票数据DataFrame，必须包含'RSI'列
        rsi_oversold: RSI超卖阈值
        rsi_rebound_min: RSI反弹最小值
        lookback_periods: 回看周期数

    Returns:
        过滤后的DataFrame，只包含满足超卖反弹条件的股票

    注意:
        - 此函数假设df已经按时间排序，最新数据在最后
    """
    if df.empty:
        return df

    # 检查必需的列
    if 'RSI' not in df.columns:
        logger.warning("DataFrame缺少必需的列: RSI")
        return pd.DataFrame()

    # 数据不足
    if len(df) < 2:
        logger.debug("数据不足以检测超卖反弹")
        return pd.DataFrame()

    # 获取回看期间的数据
    lookback_df = df.tail(min(lookback_periods, len(df)))

    # 获取当前RSI
    current_rsi = df.iloc[-1]['RSI']

    # 条件1: 当前RSI已经回升
    is_rebounded = current_rsi >= rsi_rebound_min

    # 条件2: 在回看期间内曾经超卖
    was_oversold = (lookback_df['RSI'] < rsi_oversold).any()

    # 同时满足两个条件才返回
    if is_rebounded and was_oversold:
        # 找到最近一次超卖的位置
        oversold_mask = lookback_df['RSI'] < rsi_oversold
        if oversold_mask.any():
            last_oversold_idx = lookback_df[oversold_mask].index[-1]
            logger.debug(f"超卖反弹确认: 当前RSI={current_rsi:.2f}, "
                        f"曾在索引{last_oversold_idx}超卖")
        return df
    else:
        logger.debug(f"未满足超卖反弹条件: 已反弹={is_rebounded}, 曾超卖={was_oversold}")
        return pd.DataFrame()


def filter_by_institutional_holding(
    df: pd.DataFrame,
    ratio_min: float
) -> pd.DataFrame:
    """
    根据机构持仓比例过滤股票（机构重仓策略）

    Args:
        df: 股票数据DataFrame，必须包含'机构持仓比例'列
        ratio_min: 机构持仓比例最小值，单位为%（例如30.0表示>=30%）

    Returns:
        过滤后的DataFrame，只包含满足机构持仓条件的股票。
        如果缺少必需的列，返回空DataFrame并记录警告日志。
    """
    if df.empty:
        return df

    # 检查必需的列
    if '机构持仓比例' not in df.columns:
        logger.warning("DataFrame缺少必需的列: 机构持仓比例，跳过过滤")
        return pd.DataFrame()

    # 过滤掉NaN值
    filtered = df.dropna(subset=['机构持仓比例'])

    # 应用机构持仓比例过滤
    filtered = filtered[filtered['机构持仓比例'] >= ratio_min]

    logger.debug(f"机构持仓过滤: {len(df)} -> {len(filtered)} 只股票 (机构持仓>={ratio_min}%)")

    return filtered


# 为了方便使用，提供一个统一的过滤函数
def apply_filters(
    df: pd.DataFrame,
    filter_config: dict
) -> pd.DataFrame:
    """
    根据配置字典应用多个过滤器

    Args:
        df: 股票数据DataFrame
        filter_config: 过滤配置字典，包含各种阈值

    Returns:
        过滤后的DataFrame

    示例:
        filter_config = {
            'pe_max': 15.0,
            'roe_min': 10.0,
            'dividend_yield_min': 3.0
        }
    """
    result = df

    # PE和ROE过滤
    if 'pe_max' in filter_config and 'roe_min' in filter_config:
        result = filter_by_pe_roe(
            result,
            pe_max=filter_config['pe_max'],
            roe_min=filter_config['roe_min']
        )

    # 股息率过滤
    if 'dividend_yield_min' in filter_config:
        result = filter_by_dividend_yield(
            result,
            yield_min=filter_config['dividend_yield_min']
        )

    # 突破过滤
    if 'breakout_days' in filter_config:
        result = filter_by_breakout(
            result,
            breakout_days=filter_config.get('breakout_days', 20),
            volume_ratio_min=filter_config.get('volume_ratio_min', 1.2)
        )

    # 超卖反弹过滤
    if 'rsi_oversold' in filter_config:
        result = filter_by_oversold_rebound(
            result,
            rsi_oversold=filter_config.get('rsi_oversold', 30.0),
            rsi_rebound_min=filter_config.get('rsi_rebound_min', 30.0),
            lookback_periods=filter_config.get('lookback_periods', 50)
        )

    # 机构持仓过滤
    if 'institutional_ratio_min' in filter_config:
        result = filter_by_institutional_holding(
            result,
            ratio_min=filter_config['institutional_ratio_min']
        )

    return result
