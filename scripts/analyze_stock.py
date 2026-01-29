#!/usr/bin/env python
"""
股票分析脚本

使用多维度分析模块对单只股票进行综合分析。

用法:
    python scripts/analyze_stock.py --code 600519                  # 完整分析
    python scripts/analyze_stock.py --code 600519 --depth quick   # 快速分析
    python scripts/analyze_stock.py --code 600519 --output report.txt  # 导出报告
"""

import argparse
import sys
import os
import re
import traceback
from pathlib import Path
from typing import Dict, Any, Tuple, List, Union
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.akshare_provider import AKShareProvider
from src.analysis.technical.indicators import TechnicalIndicators
from src.analysis.fundamental.financial_metrics import FinancialMetrics
from src.analysis.capital.money_flow import MoneyFlowAnalyzer
from src.analysis.ai.stock_rater import StockRater
from src.reporting.html_reporter import HTMLReporter
from src.core.logger import get_logger

logger = get_logger(__name__)

# 常量定义
STOCK_CODE_PATTERN = re.compile(r'^\d{6}$')  # A股代码格式: 6位数字

# 评级阈值常量
BUY_THRESHOLD = 70  # 买入阈值
HOLD_THRESHOLD = 45  # 持有阈值

# 止损比例常量
BUY_STOP_LOSS_RATIO = 0.93  # 买入评级止损比例 -7%
HOLD_STOP_LOSS_RATIO = 0.92  # 持有评级止损比例 -8%
SELL_STOP_LOSS_RATIO = 0.98  # 卖出评级止损比例 -2%

# 目标价格计算常量
BUY_MIN_GAIN_RATIO = 0.05  # 买入最小涨幅 5%
BUY_MAX_GAIN_RATIO = 0.15  # 买入最大涨幅 15%
SELL_MIN_LOSS_RATIO = 0.05  # 卖出最小跌幅 5%
SELL_MAX_LOSS_RATIO = 0.10  # 卖出最大跌幅 10%
HOLD_NEUTRAL_RATIO = 1.02  # 持有中性比例 2%

# 技术分析得分常量
MA_STRONG_SCORE = 100.0  # MA强势信号得分
MA_MODERATE_SCORE = 50.0  # MA中等信号得分
MACD_STRONG_SCORE = 100.0  # MACD强势信号得分
MACD_MODERATE_SCORE = 70.0  # MACD中等信号得分
RSI_OPTIMAL_SCORE = 100.0  # RSI最优区间得分
RSI_MODERATE_SCORE = 50.0  # RSI中等区间得分
RSI_OPTIMAL_LOWER = 40  # RSI最优区间下限
RSI_OPTIMAL_UPPER = 70  # RSI最优区间上限
RSI_MODERATE_LOWER = 30  # RSI中等区间下限
RSI_MODERATE_UPPER = 80  # RSI中等区间上限

# 资金面评分常量
CAPITAL_BASE_SCORE = 50.0  # 资金面基础分
CAPITAL_STRONG_INFLOW_SCORE = 90.0  # 强力流入得分
CAPITAL_MODERATE_INFLOW_SCORE = 75.0  # 中等流入得分
CAPITAL_WEAK_INFLOW_SCORE = 60.0  # 弱流入得分
CAPITAL_STRONG_OUTFLOW_SCORE = 20.0  # 强力流出得分
CAPITAL_MODERATE_OUTFLOW_SCORE = 35.0  # 中等流出得分
CAPITAL_WEAK_OUTFLOW_SCORE = 45.0  # 弱流出得分

# 信心度计算常量
CONFIDENCE_MIN = 1.0  # 最低信心度
CONFIDENCE_MAX_QUICK = 9.0  # 快速模式最高信心度
QUICK_MODE_PENALTY = 0.5  # 快速模式信心度惩罚


def validate_stock_code(code: str) -> bool:
    """
    验证A股股票代码格式

    Args:
        code: 股票代码

    Returns:
        True表示格式正确，False表示格式错误
    """
    if not code or not isinstance(code, str):
        return False
    return STOCK_CODE_PATTERN.match(code) is not None


def validate_output_path(path: str) -> str:
    """
    验证输出路径的安全性，防止路径遍历攻击

    Args:
        path: 输出文件路径

    Returns:
        规范化后的安全路径

    Raises:
        ValueError: 如果路径不安全
    """
    if not path:
        raise ValueError("输出路径不能为空")

    # 转换为绝对路径并解析符号链接
    abs_path = Path(path).resolve()

    # 检查是否包含路径遍历
    cwd = Path.cwd().resolve()

    # 定义安全目录
    safe_dirs = [
        cwd,
        Path.home(),
        Path('/tmp').resolve(),
        Path('/var/folders').resolve() if Path('/var/folders').exists() else None,
    ]
    safe_dirs = [d for d in safe_dirs if d is not None]

    # 检查路径是否在安全目录下
    is_safe = False
    try:
        abs_path.relative_to(cwd)
        is_safe = True
    except ValueError:
        for safe_dir in safe_dirs:
            try:
                abs_path.relative_to(safe_dir)
                is_safe = True
                break
            except ValueError:
                continue

    if not is_safe:
        raise ValueError(
            f"不安全的输出路径: {path}\n"
            f"路径必须在当前工作目录、用户主目录或系统临时目录下"
        )

    # 检查文件扩展名
    allowed_extensions = {'.txt', '.md', '.json', '.csv', '.html'}
    if abs_path.suffix.lower() not in allowed_extensions:
        logger.warning(
            f"不常见的文件扩展名: {abs_path.suffix}，"
            f"建议使用: {', '.join(allowed_extensions)}"
        )

    # 确保父目录存在
    parent = abs_path.parent
    if not parent.exists():
        raise ValueError(f"输出目录不存在: {parent}")

    return str(abs_path)


def fetch_stock_data(code: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    获取股票数据

    Args:
        code: 股票代码

    Returns:
        (K线数据, 财务数据, 资金流向数据)元组

    Raises:
        ValueError: 如果数据为空或股票代码无效
        RuntimeError: 如果数据获取失败
    """
    logger.info(f"获取股票数据: {code}")

    try:
        provider = AKShareProvider()

        # 获取K线数据（最近1年）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        kline_df = provider.get_daily_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'  # 前复权
        )

        if kline_df is None or len(kline_df) == 0:
            raise ValueError(
                f"未获取到K线数据: {code}\n"
                f"请检查股票代码是否正确"
            )

        logger.info(f"成功获取 {len(kline_df)} 条K线数据")

        # 获取财务数据
        financial_df = provider.get_financial_data(code)

        if financial_df is None or len(financial_df) == 0:
            raise ValueError(
                f"未获取到财务数据: {code}\n"
                f"该股票可能缺少财务报表数据"
            )

        logger.info(f"成功获取财务数据")

        # 获取资金流向数据
        money_flow_df = provider.get_money_flow(code)

        if money_flow_df is None or len(money_flow_df) == 0:
            raise ValueError(
                f"未获取到资金流向数据: {code}\n"
                f"该股票可能缺少资金流向数据"
            )

        logger.info(f"成功获取资金流向数据")

        return kline_df, financial_df, money_flow_df

    except ValueError:
        # ValueError 已经包含详细错误信息，直接重新抛出
        raise
    except Exception as e:
        # 其他异常转换为 RuntimeError
        logger.error(f"数据获取失败: {e}")
        raise RuntimeError(f"数据获取失败: {e}") from e


def get_stock_name(code: str) -> str:
    """
    获取股票名称

    Args:
        code: 股票代码

    Returns:
        股票名称，如果获取失败则返回代码
    """
    try:
        provider = AKShareProvider()
        quote = provider.get_realtime_quote(code)

        if quote and '名称' in quote:
            return quote['名称']

        return code

    except Exception as e:
        logger.warning(f"获取股票名称失败: {e}")
        return code


def analyze_stock(code: str, depth: str = 'full') -> Dict[str, Union[str, float, List[str], Dict[str, float]]]:
    """
    分析股票

    Args:
        code: 股票代码
        depth: 分析深度 ('quick' 或 'full')
            - 'quick': 仅执行技术面和资金面分析，跳过基本面和AI分析，速度更快
            - 'full': 执行完整的多维度分析（技术面、基本面、资金面、AI）

    Returns:
        分析结果字典，包含以下键:
            - rating: 评级 (str)
            - confidence: 信心度 (float)
            - target_price: 目标价 (float)
            - stop_loss: 止损价 (float)
            - reasons: 评级原因列表 (List[str])
            - risks: 风险提示列表 (List[str])
            - a_share_risks: A股特有风险列表 (List[str])
            - ai_insights: AI分析洞察 (str)
            - scores: 各维度得分字典 (Dict[str, float])

    Raises:
        ValueError: 如果参数无效或数据不足
        RuntimeError: 如果分析失败
    """
    logger.info(f"开始分析股票: {code} (深度: {depth})")

    # 获取数据
    kline_df, financial_df, money_flow_df = fetch_stock_data(code)

    # 根据深度执行不同的分析
    if is_quick_mode(depth):
        logger.info("执行快速分析（技术面 + 资金面）...")
        result = analyze_quick(code, kline_df, money_flow_df)
    else:
        logger.info("执行完整分析（技术面 + 基本面 + 资金面 + AI）...")
        # 创建分析器
        rater = StockRater()
        # 执行综合分析
        result = rater.analyze_stock(
            stock_code=code,
            kline_df=kline_df,
            financial_df=financial_df,
            money_flow_df=money_flow_df
        )

    logger.info(f"分析完成: {code}")
    return result


def analyze_quick(code: str, kline_df: pd.DataFrame, money_flow_df: pd.DataFrame) -> Dict[str, Union[str, float, List[str], Dict[str, float]]]:
    """
    快速分析模式：仅执行技术面和资金面分析

    Args:
        code: 股票代码
        kline_df: K线数据
        money_flow_df: 资金流向数据

    Returns:
        快速分析结果字典，包含以下键:
            - rating: 评级 (str)
            - confidence: 信心度 (float)
            - target_price: 目标价 (float)
            - stop_loss: 止损价 (float)
            - reasons: 评级原因列表 (List[str])
            - risks: 风险提示列表 (List[str])
            - a_share_risks: A股特有风险列表 (List[str])
            - ai_insights: 综合洞察 (str)
            - scores: 各维度得分字典 (Dict[str, float])

    Raises:
        ValueError: 如果数据不足或格式错误
    """
    logger.info(f"执行快速分析: {code}")

    # 1. 技术面分析
    technical = TechnicalIndicators()
    df_with_indicators = technical.calculate_all(kline_df)

    # 计算技术面得分
    technical_score = _calculate_technical_score(df_with_indicators)
    logger.debug(f"Technical score: {technical_score}")

    # 2. 资金面分析
    money_flow = MoneyFlowAnalyzer()
    capital_signal = money_flow.get_money_flow_signal(money_flow_df)
    summary = money_flow.generate_summary(money_flow_df)

    # 计算资金面得分
    capital_score = _calculate_capital_score(summary)
    logger.debug(f"Capital score: {capital_score}, signal: {capital_signal}")

    # 3. 计算简化的综合分数（技术面50%，资金面50%）
    overall_score = (technical_score * 0.5 + capital_score * 0.5)
    logger.info(f"Quick overall score: {overall_score}")

    # 4. 确定评级
    if overall_score >= BUY_THRESHOLD:
        rating = 'buy'
    elif overall_score >= HOLD_THRESHOLD:
        rating = 'hold'
    else:
        rating = 'sell'
    logger.info(f"Rating: {rating}")

    # 5. 计算信心度（快速模式信心度较低）
    confidence = _calculate_quick_confidence(technical_score, capital_score, overall_score)
    logger.info(f"Confidence: {confidence}")

    # 6. 获取当前价格
    current_price = float(kline_df['收盘'].iloc[-1] if '收盘' in kline_df.columns else kline_df['close'].iloc[-1])

    # 7. 计算目标价和止损价
    target_price = _calculate_quick_target_price(current_price, overall_score, rating)
    stop_loss = _calculate_quick_stop_loss(current_price, rating)

    # 8. 生成简化的原因和风险
    reasons = _generate_quick_reasons(rating, technical_score, capital_score, capital_signal)
    risks = _generate_quick_risks(rating)

    # 9. A股特有风险
    a_share_risks = ['T+1交易制度限制，当日买入次日才能卖出']
    if code.startswith('688') or code.startswith('300'):
        a_share_risks.append('科创板/创业板涨跌幅限制为20%，波动较大')

    # 10. 生成简化的分析摘要（不调用AI）
    ai_insights = _generate_quick_insights(rating, overall_score, confidence)

    result = {
        'rating': rating,
        'confidence': confidence,
        'target_price': round(target_price, 2),
        'stop_loss': round(stop_loss, 2),
        'reasons': reasons,
        'risks': risks,
        'a_share_risks': a_share_risks,
        'ai_insights': ai_insights,
        'scores': {
            'technical': round(technical_score, 2),
            'fundamental': 0.0,  # 快速模式不分析基本面
            'capital': round(capital_score, 2),
            'overall': round(overall_score, 2)
        }
    }

    logger.info(f"Quick stock analysis completed for {code}")
    return result


def _calculate_technical_score(df_with_indicators: pd.DataFrame) -> float:
    """
    计算技术面得分（简化版）

    Args:
        df_with_indicators: 包含技术指标的数据框

    Returns:
        技术面分数（0-100）

    Raises:
        ValueError: 如果数据框为空或缺少必要的列
    """
    score = 0.0
    indicators_found = 0

    # 1. MA趋势分析
    if 'MA5' in df_with_indicators.columns and 'MA20' in df_with_indicators.columns:
        indicators_found += 1
        ma5 = df_with_indicators['MA5'].iloc[-1]
        ma20 = df_with_indicators['MA20'].iloc[-1]
        close = df_with_indicators['close'].iloc[-1] if 'close' in df_with_indicators.columns else df_with_indicators['收盘'].iloc[-1]
        if ma5 > ma20 and close > ma5:
            score += MA_STRONG_SCORE
        elif ma5 > ma20 or close > ma20:
            score += MA_MODERATE_SCORE

    # 2. MACD分析
    if 'MACD' in df_with_indicators.columns and 'MACD_signal' in df_with_indicators.columns:
        indicators_found += 1
        macd = df_with_indicators['MACD'].iloc[-1]
        macd_signal = df_with_indicators['MACD_signal'].iloc[-1]
        if macd > macd_signal and macd > 0:
            score += MACD_STRONG_SCORE
        elif macd > macd_signal:
            score += MACD_MODERATE_SCORE

    # 3. RSI分析
    if 'RSI' in df_with_indicators.columns:
        indicators_found += 1
        rsi = df_with_indicators['RSI'].iloc[-1]
        if RSI_OPTIMAL_LOWER <= rsi <= RSI_OPTIMAL_UPPER:
            score += RSI_OPTIMAL_SCORE
        elif RSI_MODERATE_LOWER <= rsi < RSI_OPTIMAL_LOWER or RSI_OPTIMAL_UPPER < rsi <= RSI_MODERATE_UPPER:
            score += RSI_MODERATE_SCORE

    # 如果没有指标，基于价格趋势
    if indicators_found == 0:
        close_col = 'close' if 'close' in df_with_indicators.columns else '收盘'
        if len(df_with_indicators) >= 5:
            recent_close = df_with_indicators[close_col].iloc[-5:]
            trend = recent_close.iloc[-1] / recent_close.iloc[0] - 1
            if trend > 0.05:
                return 75.0
            elif trend > 0:
                return 60.0
            elif trend > -0.05:
                return 45.0
            else:
                return 30.0
        return 50.0

    return min(score / indicators_found if indicators_found > 0 else 50.0, 100.0)


def _calculate_capital_score(summary: Dict[str, Any]) -> float:
    """
    计算资金面得分

    Args:
        summary: 资金流向摘要，包含main_force字段，其中包含trend和strength

    Returns:
        资金面分数（0-100）

    Raises:
        KeyError: 如果summary缺少必要的字段
    """
    main_force = summary['main_force']
    trend = main_force['trend']
    strength = main_force['strength']

    score = CAPITAL_BASE_SCORE  # 基础分

    # 根据趋势调整
    if trend == '流入':
        if strength == '强':
            score = CAPITAL_STRONG_INFLOW_SCORE
        elif strength == '中':
            score = CAPITAL_MODERATE_INFLOW_SCORE
        else:
            score = CAPITAL_WEAK_INFLOW_SCORE
    elif trend == '流出':
        if strength == '强':
            score = CAPITAL_STRONG_OUTFLOW_SCORE
        elif strength == '中':
            score = CAPITAL_MODERATE_OUTFLOW_SCORE
        else:
            score = CAPITAL_WEAK_OUTFLOW_SCORE

    return score


def _calculate_quick_confidence(technical_score: float, capital_score: float, overall_score: float) -> float:
    """
    计算快速模式的信心度（相比完整模式较低）

    Args:
        technical_score: 技术面分数（0-100）
        capital_score: 资金面分数（0-100）
        overall_score: 综合分数（0-100）

    Returns:
        信心度（1.0-9.0），保留一位小数

    Notes:
        快速模式由于缺少基本面和AI分析，信心度整体降低0.5分
        信心度受两个因素影响：
        1. 综合分数的绝对值
        2. 各维度分数的一致性（标准差）
    """
    # 计算一致性
    scores = [technical_score, capital_score]
    std_dev = np.std(scores)
    consistency_factor = max(0, 1 - std_dev / 60)

    # 基础信心度
    if overall_score >= BUY_THRESHOLD:
        base_confidence = 6.0 + (overall_score - BUY_THRESHOLD) / 15
    elif overall_score >= 50:
        base_confidence = 4.5 + (overall_score - 50) / 10
    elif overall_score >= 30:
        base_confidence = 3.0 + (overall_score - 30) / 10
    else:
        base_confidence = 1.5 + overall_score / 20

    # 调整信心度（快速模式整体降低）
    confidence = base_confidence * (0.6 + 0.4 * consistency_factor) - QUICK_MODE_PENALTY

    return max(CONFIDENCE_MIN, min(CONFIDENCE_MAX_QUICK, round(confidence, 1)))


def _calculate_quick_target_price(current_price: float, overall_score: float, rating: str) -> float:
    """
    计算快速模式的目标价

    Args:
        current_price: 当前价格
        overall_score: 综合分数（0-100）
        rating: 评级 ('buy', 'sell', 'hold')

    Returns:
        目标价格

    Notes:
        - 买入评级：目标涨幅5%-20%，随分数线性增长
        - 卖出评级：目标跌幅5%-15%，随分数线性增长
        - 持有评级：目标中性偏上，2%涨幅
    """
    if rating == 'buy':
        gain_ratio = BUY_MIN_GAIN_RATIO + (overall_score - BUY_THRESHOLD) / 100 * BUY_MAX_GAIN_RATIO
        return current_price * (1 + gain_ratio)
    elif rating == 'sell':
        loss_ratio = SELL_MIN_LOSS_RATIO + (HOLD_THRESHOLD - overall_score) / 100 * SELL_MAX_LOSS_RATIO
        return current_price * (1 - loss_ratio)
    else:  # hold
        return current_price * HOLD_NEUTRAL_RATIO


def _calculate_quick_stop_loss(current_price: float, rating: str) -> float:
    """
    计算快速模式的止损价

    Args:
        current_price: 当前价格
        rating: 评级 ('buy', 'sell', 'hold')

    Returns:
        止损价格

    Notes:
        止损策略：
        - 买入评级：-7% 止损，给予一定波动空间
        - 卖出评级：-2% 止损，严格控制风险
        - 持有评级：-8% 止损，允许更大波动观察
    """
    if rating == 'buy':
        return current_price * BUY_STOP_LOSS_RATIO
    elif rating == 'sell':
        return current_price * SELL_STOP_LOSS_RATIO
    else:  # hold
        return current_price * HOLD_STOP_LOSS_RATIO


def _generate_quick_reasons(rating: str, technical_score: float, capital_score: float, capital_signal: str) -> List[str]:
    """
    生成快速分析的评级原因

    Args:
        rating: 评级 ('buy', 'sell', 'hold')
        technical_score: 技术面分数（0-100）
        capital_score: 资金面分数（0-100）
        capital_signal: 资金信号 ('买入', '卖出', '观望')

    Returns:
        评级原因列表，至少包含一条原因

    Notes:
        根据评级和各维度得分生成具体的评级依据
    """
    reasons = []

    if rating == 'buy':
        if technical_score >= BUY_THRESHOLD:
            reasons.append('技术面呈现强势上涨趋势')
        if capital_score >= BUY_THRESHOLD:
            reasons.append('主力资金持续流入，市场情绪积极')
        if capital_signal == '买入':
            reasons.append('资金流向信号显示买入机会')
    elif rating == 'sell':
        if technical_score < HOLD_THRESHOLD:
            reasons.append('技术面走弱，下跌趋势明显')
        if capital_score < HOLD_THRESHOLD:
            reasons.append('主力资金流出，市场情绪悲观')
        if capital_signal == '卖出':
            reasons.append('资金流向信号显示卖出风险')
    else:  # hold
        reasons.append('技术面和资金面综合显示震荡整理，建议观望')

    if not reasons:
        reasons.append('综合分析建议当前操作')

    return reasons


def _generate_quick_risks(rating: str) -> List[str]:
    """
    生成快速分析的风险提示

    Args:
        rating: 评级 ('buy', 'sell', 'hold')

    Returns:
        风险提示列表，至少包含一条风险

    Notes:
        快速分析缺少基本面和AI深度分析，需要特别提示
    """
    risks = []

    if rating == 'buy':
        risks.append('快速分析未包含基本面和AI深度分析，建议谨慎决策')
        risks.append('市场整体波动可能影响个股表现')
    elif rating == 'sell':
        risks.append('快速分析未包含基本面评估，建议进行完整分析后决策')
        risks.append('继续持有可能面临进一步下跌风险')
    else:  # hold
        risks.append('快速分析结果不确定性较高，建议观望或进行完整分析')
        risks.append('横盘整理期间可能出现方向选择')

    risks.append('政策和宏观环境变化风险')

    return risks


def _generate_quick_insights(rating: str, overall_score: float, confidence: float) -> str:
    """
    生成快速分析的综合洞察

    Args:
        rating: 评级 ('buy', 'sell', 'hold')
        overall_score: 综合分数（0-100）
        confidence: 信心度（1-10）

    Returns:
        综合分析文本，包含模式说明、评分、评级建议和后续建议

    Notes:
        快速模式生成的洞察不包含AI分析，仅基于规则引擎
    """
    mode_note = "【快速分析模式】仅基于技术面和资金面分析。"

    if rating == 'buy':
        return (
            f"{mode_note}\n"
            f"综合评分{overall_score:.1f}分，建议买入。"
            f"技术面和资金面综合表现良好，信心度{confidence}/10。"
            f"建议关注买入时机，分批建仓以降低风险。"
            f"如需更准确的评估，建议使用完整分析模式。"
        )
    elif rating == 'sell':
        return (
            f"{mode_note}\n"
            f"综合评分{overall_score:.1f}分，建议卖出。"
            f"技术面和资金面显示下行风险，信心度{confidence}/10。"
            f"建议及时止损，避免损失进一步扩大。"
            f"如需更准确的评估，建议使用完整分析模式。"
        )
    else:
        return (
            f"{mode_note}\n"
            f"综合评分{overall_score:.1f}分，建议持有观望。"
            f"当前处于震荡整理阶段，信心度{confidence}/10。"
            f"建议等待明确方向信号后再做决策。"
            f"如需更准确的评估，建议使用完整分析模式。"
        )


def analyze_technical_only(code: str, kline_df: pd.DataFrame) -> Dict[str, Any]:
    """
    仅执行技术分析（当其他数据不可用时）

    Args:
        code: 股票代码
        kline_df: K线数据

    Returns:
        技术分析结果字典，包含以下键:
            - code: 股票代码 (str)
            - analysis_type: 分析类型 (str)
            - indicators: 技术指标字典 (Dict)

    Notes:
        这是一个降级分析方法，仅在无法获取完整数据时使用
    """
    logger.info(f"执行技术分析: {code}")

    technical = TechnicalIndicators()
    df_with_indicators = technical.calculate_all(kline_df)

    # 简单的技术面评分
    result = {
        'code': code,
        'analysis_type': 'technical_only',
        'indicators': df_with_indicators.tail(1).to_dict('records')[0] if len(df_with_indicators) > 0 else {}
    }

    return result


def validate_and_analyze(code: str, depth: str = 'full') -> Dict[str, Union[str, float, List[str], Dict[str, float]]]:
    """
    验证并分析股票

    Args:
        code: 股票代码（6位数字）
        depth: 分析深度 ('quick' 或 'full')

    Returns:
        分析结果字典

    Raises:
        ValueError: 如果股票代码格式无效
        RuntimeError: 如果分析过程失败
    """
    if not validate_stock_code(code):
        raise ValueError(
            f"无效的股票代码: {code}\n"
            f"A股代码必须是6位数字（如: 600519）"
        )

    return analyze_stock(code, depth)


def format_report(stock_code: str, stock_name: str, analysis_result: Dict[str, Any]) -> str:
    """
    格式化分析报告

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        analysis_result: 分析结果字典

    Returns:
        格式化的多行报告文本，包含评分、评级、原因、风险等信息

    Notes:
        报告格式会根据是否为快速分析模式自动调整
    """
    lines = []
    scores = analysis_result['scores']
    is_quick = (scores.get('fundamental', 0) == 0)  # 判断是否为快速分析

    lines.append("=" * 80)
    if is_quick:
        lines.append("                    股票分析报告（快速模式）")
    else:
        lines.append("                        股票分析报告")
    lines.append("=" * 80)
    lines.append(f"股票代码: {stock_code}")
    lines.append(f"股票名称: {stock_name}")
    lines.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if is_quick:
        lines.append(f"分析模式: 快速分析（技术面 + 资金面）")
    else:
        lines.append(f"分析模式: 完整分析（技术面 + 基本面 + 资金面 + AI）")
    lines.append("=" * 80)
    lines.append("")

    # 综合评分
    lines.append("-" * 80)
    lines.append("  综合评分")
    lines.append("-" * 80)
    lines.append(f"评级: {analysis_result['rating'].upper()}")
    lines.append(f"信心度: {analysis_result['confidence']:.1f}/10.0")
    lines.append(f"目标价: {analysis_result['target_price']:.2f}")
    lines.append(f"止损价: {analysis_result['stop_loss']:.2f}")
    lines.append("")

    # 各维度得分
    lines.append("-" * 80)
    lines.append("  各维度评分")
    lines.append("-" * 80)
    lines.append(f"技术面得分: {scores['technical']:.2f}")
    if not is_quick:
        lines.append(f"基本面得分: {scores['fundamental']:.2f}")
    lines.append(f"资金面得分: {scores['capital']:.2f}")
    lines.append(f"综合得分: {scores['overall']:.2f}")
    if is_quick:
        lines.append("")
        lines.append("注: 快速模式不包含基本面分析")
    lines.append("")

    # 评级原因
    lines.append("-" * 80)
    lines.append("  评级原因")
    lines.append("-" * 80)
    for i, reason in enumerate(analysis_result['reasons'], 1):
        lines.append(f"{i}. {reason}")
    lines.append("")

    # 风险提示
    lines.append("-" * 80)
    lines.append("  风险提示")
    lines.append("-" * 80)
    for i, risk in enumerate(analysis_result['risks'], 1):
        lines.append(f"{i}. {risk}")
    lines.append("")

    # A股特有风险
    lines.append("-" * 80)
    lines.append("  A股特有风险")
    lines.append("-" * 80)
    for i, risk in enumerate(analysis_result['a_share_risks'], 1):
        lines.append(f"{i}. {risk}")
    lines.append("")

    # AI综合分析 / 综合分析
    lines.append("-" * 80)
    if is_quick:
        lines.append("  综合分析")
    else:
        lines.append("  AI综合分析")
    lines.append("-" * 80)
    lines.append(analysis_result['ai_insights'])
    lines.append("")

    lines.append("=" * 80)
    lines.append("免责声明: 本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。")
    lines.append("=" * 80)

    return "\n".join(lines)


def save_report(report: str, output_path: str) -> None:
    """
    保存Markdown报告到文件

    Args:
        report: 报告内容
        output_path: 输出文件路径

    Raises:
        ValueError: 如果输出路径不安全或父目录不存在
        IOError: 如果文件写入失败

    Notes:
        输出路径会经过安全性验证，防止路径遍历攻击
    """
    safe_path = validate_output_path(output_path)

    try:
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Markdown报告已保存至: {safe_path}")
        print(f"\nMarkdown报告已保存至: {safe_path}")

    except IOError as e:
        logger.error(f"保存报告失败: {e}")
        raise
    except Exception as e:
        logger.error(f"保存报告时发生未知错误: {e}")
        raise IOError(f"保存报告失败: {e}") from e


def save_html_report(
    stock_code: str,
    stock_name: str,
    analysis_result: Dict[str, Any],
    output_path: str
) -> None:
    """
    保存HTML报告到文件

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        analysis_result: 分析结果字典
        output_path: 输出文件路径

    Raises:
        ValueError: 如果输出路径不安全
        IOError: 如果文件写入失败

    Notes:
        使用HTMLReporter生成并保存报告
    """
    try:
        html_reporter = HTMLReporter()
        html_reporter.generate_report(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_result=analysis_result,
            save_to_file=True,
            output_path=output_path
        )

        logger.info(f"HTML报告已保存至: {output_path}")
        print(f"\nHTML报告已保存至: {output_path}")

    except ValueError as e:
        logger.error(f"输出路径验证失败: {e}")
        raise
    except Exception as e:
        logger.error(f"保存HTML报告失败: {e}")
        raise IOError(f"保存HTML报告失败: {e}") from e


def is_quick_mode(depth: str) -> bool:
    """
    判断是否为快速模式

    Args:
        depth: 分析深度字符串（'quick' 或 'full'，大小写不敏感）

    Returns:
        True表示快速模式，False表示完整模式

    Notes:
        快速模式仅执行技术面和资金面分析，跳过基本面和AI分析
    """
    return depth.lower() == 'quick'


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象，包含以下属性:
            - code: 股票代码 (str)
            - depth: 分析深度 (str)
            - output: 输出文件路径 (str | None)
            - verbose: 是否显示详细输出 (bool)

    Notes:
        使用 --help 参数可查看详细使用说明
    """
    parser = argparse.ArgumentParser(
        description='A股单只股票分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整分析
  python scripts/analyze_stock.py --code 600519

  # 快速分析
  python scripts/analyze_stock.py --code 600519 --depth quick

  # 导出Markdown报告
  python scripts/analyze_stock.py --code 600519 --output report.md

  # 导出HTML报告
  python scripts/analyze_stock.py --code 600519 --html-output report.html

  # 同时导出Markdown和HTML报告
  python scripts/analyze_stock.py --code 600519 --output report.md --html-output report.html

  # 完整分析并导出HTML报告
  python scripts/analyze_stock.py --code 600519 --depth full --html-output 600519_analysis.html
        """
    )

    parser.add_argument(
        '--code',
        required=True,
        help='股票代码（如: 600519）'
    )

    parser.add_argument(
        '--depth',
        choices=['quick', 'full'],
        default='full',
        help='分析深度（默认: full）\n'
             '  quick: 仅技术面+资金面，速度快，适合快速浏览\n'
             '  full: 完整分析（技术+基本+资金+AI），结果更准确'
    )

    parser.add_argument(
        '--output',
        help='导出Markdown报告到文件'
    )

    parser.add_argument(
        '--html-output',
        help='导出HTML报告到文件'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    return parser.parse_args()


def main() -> None:
    """
    主函数，程序入口点

    Notes:
        1. 解析命令行参数
        2. 获取股票基本信息
        3. 执行分析（快速或完整模式）
        4. 格式化并显示报告
        5. 可选：导出报告到文件

    Raises:
        SystemExit: 如果参数错误或分析失败，返回退出码1
    """
    # 解析参数
    args = parse_arguments()

    # 打印欢迎信息
    print("=" * 80)
    print("                   A股单只股票分析系统")
    print("=" * 80)
    print(f"股票代码: {args.code}")
    print(f"分析深度: {args.depth}")
    if args.output:
        print(f"Markdown输出: {args.output}")
    if args.html_output:
        print(f"HTML输出: {args.html_output}")
    print("=" * 80)
    print()

    try:
        # 获取股票名称
        print("获取股票信息...")
        stock_name = get_stock_name(args.code)
        print(f"股票名称: {stock_name}")
        print()

        # 执行分析
        print("开始分析，请稍候...")
        print()

        result = validate_and_analyze(args.code, args.depth)

        # 格式化并显示报告
        report = format_report(args.code, stock_name, result)
        print(report)

        # 导出Markdown报告
        if args.output:
            save_report(report, args.output)

        # 导出HTML报告
        if args.html_output:
            save_html_report(args.code, stock_name, result, args.html_output)

        print("\n分析完成")

    except ValueError as e:
        print(f"\n参数错误: {e}")
        logger.error(f"参数错误: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\n分析失败: {e}")
        logger.error(f"分析失败: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
