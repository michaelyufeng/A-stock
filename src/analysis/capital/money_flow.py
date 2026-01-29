"""Money flow analyzer module."""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MoneyFlowAnalyzer:
    """资金流向分析器"""

    def __init__(self):
        """初始化资金流向分析器"""
        logger.info("MoneyFlowAnalyzer initialized")

    def analyze_main_force(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析主力资金动向

        Args:
            df: 资金流向数据框，需包含'主力净流入'等列

        Returns:
            主力资金分析结果，包含流入/流出趋势、力度等
        """
        logger.info("Analyzing main force capital flow")

        # 验证数据
        if df.empty:
            logger.error("DataFrame is empty")
            raise ValueError("数据框不能为空")

        required_columns = ['主力净流入']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns. Required: {required_columns}")
            raise ValueError(f"缺少必要的列: {required_columns}")

        # 计算主力资金流入流出
        main_force_flow = df['主力净流入']
        total_inflow = main_force_flow[main_force_flow > 0].sum()
        total_outflow = abs(main_force_flow[main_force_flow < 0].sum())
        net_inflow = main_force_flow.sum()

        # 统计流入流出天数
        inflow_days = (main_force_flow > 0).sum()
        outflow_days = (main_force_flow < 0).sum()

        # 判断趋势
        if net_inflow > 0:
            trend = '流入'
        elif net_inflow < 0:
            trend = '流出'
        else:
            trend = '平衡'

        # 判断力度（基于净流入与总流入的比例）
        if total_inflow > 0:
            strength_ratio = abs(net_inflow) / total_inflow
            if strength_ratio > 0.5:
                strength = '强'
            elif strength_ratio > 0.2:
                strength = '中'
            else:
                strength = '弱'
        else:
            strength = '弱'

        result = {
            'total_inflow': float(total_inflow),
            'total_outflow': float(total_outflow),
            'net_inflow': float(net_inflow),
            'inflow_days': int(inflow_days),
            'outflow_days': int(outflow_days),
            'trend': trend,
            'strength': strength
        }

        logger.info(f"Main force analysis result: trend={trend}, strength={strength}, net_inflow={net_inflow:.2f}")
        return result

    def analyze_volume_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析成交量趋势

        Args:
            df: 资金流向数据框，需包含'成交量'列

        Returns:
            成交量趋势分析结果，包含放量/缩量、量价配合等
        """
        logger.info("Analyzing volume trend")

        # 验证数据
        if df.empty:
            logger.error("DataFrame is empty")
            raise ValueError("数据框不能为空")

        required_columns = ['成交量', '主力净流入']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns. Required: {required_columns}")
            raise ValueError(f"缺少必要的列: {required_columns}")

        # 计算成交量指标
        volume = df['成交量']
        avg_volume = volume.mean()
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # 判断成交量趋势
        if volume_ratio > 1.2:
            trend = '放量'
        elif volume_ratio < 0.8:
            trend = '缩量'
        else:
            trend = '平稳'

        # 判断量价配合（成交量与主力资金流向的关系）
        main_force_flow = df['主力净流入'].iloc[-5:]  # 最近5天
        volume_recent = volume.iloc[-5:]

        # 计算最近5天的平均成交量比率和主力资金净流入
        avg_volume_recent = volume_recent.mean()
        net_inflow_recent = main_force_flow.sum()

        # 量价配合判断：放量 + 资金流入 = 良好；缩量 + 资金流出 = 良好；其他 = 背离
        if (avg_volume_recent > avg_volume and net_inflow_recent > 0) or \
           (avg_volume_recent < avg_volume and net_inflow_recent < 0):
            price_volume_match = '良好'
        elif abs(avg_volume_recent - avg_volume) / avg_volume < 0.2:
            price_volume_match = '一般'
        else:
            price_volume_match = '背离'

        result = {
            'avg_volume': float(avg_volume),
            'current_volume': float(current_volume),
            'volume_ratio': float(volume_ratio),
            'trend': trend,
            'price_volume_match': price_volume_match
        }

        logger.info(f"Volume trend analysis result: trend={trend}, volume_ratio={volume_ratio:.2f}, match={price_volume_match}")
        return result

    def analyze_money_flow_trend(self, df: pd.DataFrame, window: int = 5) -> Dict[str, Any]:
        """
        分析资金流向趋势

        Args:
            df: 资金流向数据框
            window: 分析窗口期（天数）

        Returns:
            资金流向趋势分析结果
        """
        logger.info(f"Analyzing money flow trend with window={window} days")

        # 验证数据
        if df.empty:
            logger.error("DataFrame is empty")
            raise ValueError("数据框不能为空")

        required_columns = ['主力净流入']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns. Required: {required_columns}")
            raise ValueError(f"缺少必要的列: {required_columns}")

        # 获取最近window天的数据
        recent_data = df.tail(window)
        main_force_flow = recent_data['主力净流入']

        # 计算连续流入/流出天数
        continuous_inflow_days = 0
        continuous_outflow_days = 0

        for value in reversed(main_force_flow.values):
            if value > 0:
                continuous_inflow_days += 1
                if continuous_outflow_days > 0:
                    break
            elif value < 0:
                continuous_outflow_days += 1
                if continuous_inflow_days > 0:
                    break
            else:
                break

        # 计算窗口期内净流入总和
        net_inflow_sum = main_force_flow.sum()

        # 判断趋势
        if continuous_inflow_days >= 3:
            trend = '持续流入'
        elif continuous_outflow_days >= 3:
            trend = '持续流出'
        else:
            trend = '震荡'

        result = {
            'window_days': window,
            'continuous_inflow_days': int(continuous_inflow_days),
            'continuous_outflow_days': int(continuous_outflow_days),
            'net_inflow_sum': float(net_inflow_sum),
            'trend': trend
        }

        logger.info(f"Money flow trend analysis result: trend={trend}, continuous_inflow={continuous_inflow_days}, continuous_outflow={continuous_outflow_days}")
        return result

    def get_money_flow_signal(self, df: pd.DataFrame) -> str:
        """
        获取资金流向信号

        Args:
            df: 资金流向数据框

        Returns:
            信号：'买入'、'卖出'或'持有'
        """
        logger.info("Generating money flow signal")

        # 分析主力资金、成交量和资金流向趋势
        main_force = self.analyze_main_force(df)
        volume_trend = self.analyze_volume_trend(df)
        money_flow_trend = self.analyze_money_flow_trend(df)

        # 信号生成逻辑
        # 买入信号：主力持续流入 + 成交量放大 + 趋势向上
        buy_conditions = [
            main_force['trend'] == '流入',
            main_force['strength'] in ['强', '中'],
            volume_trend['trend'] == '放量',
            money_flow_trend['trend'] == '持续流入',
            money_flow_trend['continuous_inflow_days'] >= 3
        ]

        # 卖出信号：主力持续流出 + 成交量放大 + 趋势向下
        sell_conditions = [
            main_force['trend'] == '流出',
            main_force['strength'] in ['强', '中'],
            volume_trend['trend'] == '放量',
            money_flow_trend['trend'] == '持续流出',
            money_flow_trend['continuous_outflow_days'] >= 3
        ]

        # 判断信号
        buy_score = sum(buy_conditions)
        sell_score = sum(sell_conditions)

        if buy_score >= 3:
            signal = '买入'
        elif sell_score >= 3:
            signal = '卖出'
        else:
            signal = '持有'

        logger.info(f"Money flow signal generated: {signal} (buy_score={buy_score}, sell_score={sell_score})")
        return signal

    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成分析摘要

        Args:
            df: 资金流向数据框

        Returns:
            完整的分析摘要
        """
        logger.info("Generating money flow analysis summary")

        # 执行各项分析
        main_force = self.analyze_main_force(df)
        volume_trend = self.analyze_volume_trend(df)
        money_flow_trend = self.analyze_money_flow_trend(df)
        signal = self.get_money_flow_signal(df)

        # 生成建议
        if signal == '买入':
            recommendation = (
                f"主力资金呈现{main_force['trend']}态势，力度{main_force['strength']}，"
                f"成交量{volume_trend['trend']}，资金流向{money_flow_trend['trend']}。"
                f"建议关注买入机会。"
            )
        elif signal == '卖出':
            recommendation = (
                f"主力资金呈现{main_force['trend']}态势，力度{main_force['strength']}，"
                f"成交量{volume_trend['trend']}，资金流向{money_flow_trend['trend']}。"
                f"建议谨慎持仓或减仓。"
            )
        else:
            recommendation = (
                f"主力资金呈现{main_force['trend']}态势，力度{main_force['strength']}，"
                f"成交量{volume_trend['trend']}，资金流向{money_flow_trend['trend']}。"
                f"建议保持观望。"
            )

        summary = {
            'main_force': main_force,
            'volume_trend': volume_trend,
            'money_flow_trend': money_flow_trend,
            'signal': signal,
            'recommendation': recommendation
        }

        logger.info(f"Summary generated successfully. Signal: {signal}")
        return summary
