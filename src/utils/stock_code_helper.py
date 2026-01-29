"""股票代码辅助工具"""
from src.core.constants import MARKET_PREFIX, Market


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码（添加市场前缀）

    Args:
        code: 股票代码

    Returns:
        标准化后的代码（如 600519 -> 600519.SH）
    """
    code = code.strip()

    # 如果已经有后缀，直接返回
    if '.' in code:
        return code.upper()

    # 根据前缀判断市场
    prefix = code[:3]

    # 上海主板
    if any(code.startswith(p) for p in MARKET_PREFIX['SH_MAIN']):
        return f"{code}.SH"

    # 科创板
    if any(code.startswith(p) for p in MARKET_PREFIX['STAR']):
        return f"{code}.SH"

    # 深圳主板
    if any(code.startswith(p) for p in MARKET_PREFIX['SZ_MAIN']):
        return f"{code}.SZ"

    # 创业板
    if any(code.startswith(p) for p in MARKET_PREFIX['GEM']):
        return f"{code}.SZ"

    # 北交所
    if any(code.startswith(p) for p in MARKET_PREFIX['BJ']):
        return f"{code}.BJ"

    # 默认返回原代码
    return code


def get_market_from_code(code: str) -> Market:
    """
    根据股票代码获取市场类型

    Args:
        code: 股票代码

    Returns:
        市场类型
    """
    code = code.strip()
    prefix = code[:3]

    # 科创板
    if any(code.startswith(p) for p in MARKET_PREFIX['STAR']):
        return Market.STAR_MARKET

    # 创业板
    if any(code.startswith(p) for p in MARKET_PREFIX['GEM']):
        return Market.GEM

    # 默认主板
    return Market.MAIN_BOARD


def strip_market_suffix(code: str) -> str:
    """
    移除市场后缀

    Args:
        code: 股票代码（如 600519.SH）

    Returns:
        纯数字代码（如 600519）
    """
    return code.split('.')[0]
