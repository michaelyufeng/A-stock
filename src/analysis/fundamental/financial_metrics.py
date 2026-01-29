"""财务指标分析模块"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from src.core.logger import get_logger

logger = get_logger(__name__)


class FinancialMetrics:
    """财务指标分析类"""

    def __init__(self):
        """初始化财务指标分析器"""
        logger.debug("Initializing FinancialMetrics")

    def analyze_profitability(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析盈利能力

        Args:
            df: 财务数据DataFrame，需包含净资产收益率、毛利率等列

        Returns:
            盈利能力分析结果字典
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        required_columns = ['净资产收益率', '毛利率', '净利润', '营业收入']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        logger.info("Analyzing profitability...")

        # 计算ROE指标
        roe_values = df['净资产收益率'].dropna()
        roe_avg = float(roe_values.mean()) if len(roe_values) > 0 else 0
        roe_latest = float(roe_values.iloc[-1]) if len(roe_values) > 0 else 0

        # 计算毛利率
        gross_margin_values = df['毛利率'].dropna()
        gross_margin_avg = float(gross_margin_values.mean()) if len(gross_margin_values) > 0 else 0
        gross_margin_latest = float(gross_margin_values.iloc[-1]) if len(gross_margin_values) > 0 else 0

        # 计算净利率
        net_profit = df['净利润'].dropna()
        revenue = df['营业收入'].dropna()
        if len(net_profit) > 0 and len(revenue) > 0 and revenue.iloc[-1] != 0:
            net_margin_latest = float((net_profit.iloc[-1] / revenue.iloc[-1]) * 100)
        else:
            net_margin_latest = 0

        # 评级
        rating = self._rate_profitability(roe_latest, gross_margin_latest, net_margin_latest)

        result = {
            'roe_avg': round(roe_avg, 2),
            'roe_latest': round(roe_latest, 2),
            'gross_margin_avg': round(gross_margin_avg, 2),
            'gross_margin_latest': round(gross_margin_latest, 2),
            'net_margin_latest': round(net_margin_latest, 2),
            'rating': rating
        }

        logger.info(f"Profitability analysis result: {result}")
        return result

    def analyze_growth(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析成长性

        Args:
            df: 财务数据DataFrame，需包含营业收入、净利润等列

        Returns:
            成长性分析结果字典
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        required_columns = ['营业收入', '净利润']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        logger.info("Analyzing growth...")

        # 计算营收增长率
        revenue = df['营业收入'].dropna()
        if len(revenue) >= 2:
            revenue_growth = float(((revenue.iloc[-1] - revenue.iloc[0]) / revenue.iloc[0]) * 100)
        else:
            revenue_growth = 0

        # 计算利润增长率
        profit = df['净利润'].dropna()
        if len(profit) >= 2:
            profit_growth = float(((profit.iloc[-1] - profit.iloc[0]) / profit.iloc[0]) * 100)
        else:
            profit_growth = 0

        # 平均增长率
        avg_growth = (revenue_growth + profit_growth) / 2

        # 评级
        rating = self._rate_growth(avg_growth)

        result = {
            'revenue_growth': round(revenue_growth, 2),
            'profit_growth': round(profit_growth, 2),
            'avg_growth': round(avg_growth, 2),
            'rating': rating
        }

        logger.info(f"Growth analysis result: {result}")
        return result

    def analyze_financial_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析财务健康度

        Args:
            df: 财务数据DataFrame，需包含资产负债率、流动比率等列

        Returns:
            财务健康度分析结果字典
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        required_columns = ['资产负债率', '流动比率']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        logger.info("Analyzing financial health...")

        # 计算负债率
        debt_ratio = df['资产负债率'].dropna()
        debt_ratio_avg = float(debt_ratio.mean()) if len(debt_ratio) > 0 else 0
        debt_ratio_latest = float(debt_ratio.iloc[-1]) if len(debt_ratio) > 0 else 0

        # 计算流动比率
        current_ratio = df['流动比率'].dropna()
        current_ratio_avg = float(current_ratio.mean()) if len(current_ratio) > 0 else 0
        current_ratio_latest = float(current_ratio.iloc[-1]) if len(current_ratio) > 0 else 0

        # 评级
        rating = self._rate_financial_health(debt_ratio_latest, current_ratio_latest)

        result = {
            'debt_ratio_avg': round(debt_ratio_avg, 2),
            'debt_ratio_latest': round(debt_ratio_latest, 2),
            'current_ratio_avg': round(current_ratio_avg, 2),
            'current_ratio_latest': round(current_ratio_latest, 2),
            'rating': rating
        }

        logger.info(f"Financial health analysis result: {result}")
        return result

    def analyze_valuation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析估值水平

        Args:
            df: 财务数据DataFrame，需包含市盈率、市净率等列

        Returns:
            估值分析结果字典
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        required_columns = ['市盈率', '市净率']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        logger.info("Analyzing valuation...")

        # 计算PE
        pe = df['市盈率'].dropna()
        pe_avg = float(pe.mean()) if len(pe) > 0 else 0
        pe_latest = float(pe.iloc[-1]) if len(pe) > 0 else 0

        # 计算PB
        pb = df['市净率'].dropna()
        pb_avg = float(pb.mean()) if len(pb) > 0 else 0
        pb_latest = float(pb.iloc[-1]) if len(pb) > 0 else 0

        # 评级
        rating = self._rate_valuation(pe_latest, pb_latest)

        result = {
            'pe_avg': round(pe_avg, 2),
            'pe_latest': round(pe_latest, 2),
            'pb_avg': round(pb_avg, 2),
            'pb_latest': round(pb_latest, 2),
            'rating': rating
        }

        logger.info(f"Valuation analysis result: {result}")
        return result

    def get_overall_score(self, df: pd.DataFrame) -> float:
        """
        计算综合评分

        Args:
            df: 财务数据DataFrame

        Returns:
            综合评分（0-100分）
        """
        logger.info("Calculating overall score...")

        try:
            # 获取各维度分析结果
            profitability = self.analyze_profitability(df)
            growth = self.analyze_growth(df)
            health = self.analyze_financial_health(df)
            valuation = self.analyze_valuation(df)

            # 计算各维度得分（0-100）
            profitability_score = self._rating_to_score(profitability['rating'])
            growth_score = self._rating_to_score(growth['rating'])
            health_score = self._rating_to_score(health['rating'])
            valuation_score = self._rating_to_score(valuation['rating'])

            # 加权平均（盈利能力30%，成长性30%，财务健康25%，估值15%）
            overall = (
                profitability_score * 0.30 +
                growth_score * 0.30 +
                health_score * 0.25 +
                valuation_score * 0.15
            )

            score = round(overall, 2)
            logger.info(f"Overall score: {score}")
            return score

        except Exception as e:
            logger.error(f"Failed to calculate overall score: {e}")
            raise

    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成分析摘要

        Args:
            df: 财务数据DataFrame

        Returns:
            完整的分析摘要字典
        """
        logger.info("Generating analysis summary...")

        try:
            summary = {
                'profitability': self.analyze_profitability(df),
                'growth': self.analyze_growth(df),
                'financial_health': self.analyze_financial_health(df),
                'valuation': self.analyze_valuation(df),
                'overall_score': self.get_overall_score(df)
            }

            logger.info("Analysis summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise

    def _rate_profitability(self, roe: float, gross_margin: float, net_margin: float) -> str:
        """
        评估盈利能力等级

        Args:
            roe: 净资产收益率
            gross_margin: 毛利率
            net_margin: 净利率

        Returns:
            评级字符串
        """
        score = 0

        # ROE评分（满分40）
        if roe >= 20:
            score += 40
        elif roe >= 15:
            score += 30
        elif roe >= 10:
            score += 20
        else:
            score += 10

        # 毛利率评分（满分30）
        if gross_margin >= 40:
            score += 30
        elif gross_margin >= 30:
            score += 20
        elif gross_margin >= 20:
            score += 10
        else:
            score += 5

        # 净利率评分（满分30）
        if net_margin >= 20:
            score += 30
        elif net_margin >= 10:
            score += 20
        elif net_margin >= 5:
            score += 10
        else:
            score += 5

        return self._score_to_rating(score)

    def _rate_growth(self, avg_growth: float) -> str:
        """
        评估成长性等级

        Args:
            avg_growth: 平均增长率

        Returns:
            评级字符串
        """
        if avg_growth >= 30:
            return '优秀'
        elif avg_growth >= 15:
            return '良好'
        elif avg_growth >= 5:
            return '一般'
        else:
            return '差'

    def _rate_financial_health(self, debt_ratio: float, current_ratio: float) -> str:
        """
        评估财务健康度等级

        Args:
            debt_ratio: 资产负债率
            current_ratio: 流动比率

        Returns:
            评级字符串
        """
        score = 0

        # 负债率评分（满分50，越低越好）
        if debt_ratio <= 30:
            score += 50
        elif debt_ratio <= 50:
            score += 35
        elif debt_ratio <= 70:
            score += 20
        else:
            score += 10

        # 流动比率评分（满分50）
        if current_ratio >= 2.0:
            score += 50
        elif current_ratio >= 1.5:
            score += 35
        elif current_ratio >= 1.0:
            score += 20
        else:
            score += 10

        return self._score_to_rating(score)

    def _rate_valuation(self, pe: float, pb: float) -> str:
        """
        评估估值等级

        Args:
            pe: 市盈率
            pb: 市净率

        Returns:
            评级字符串
        """
        score = 0

        # PE评分（满分50，适中为好）
        if 10 <= pe <= 20:
            score += 50
        elif 5 <= pe < 10 or 20 < pe <= 30:
            score += 35
        elif 30 < pe <= 50:
            score += 20
        else:
            score += 10

        # PB评分（满分50，适中为好）
        if 1 <= pb <= 3:
            score += 50
        elif 3 < pb <= 5:
            score += 35
        elif 5 < pb <= 8:
            score += 20
        else:
            score += 10

        return self._score_to_rating(score)

    def _score_to_rating(self, score: float) -> str:
        """
        将分数转换为评级

        Args:
            score: 分数（0-100）

        Returns:
            评级字符串
        """
        if score >= 75:
            return '优秀'
        elif score >= 60:
            return '良好'
        elif score >= 40:
            return '一般'
        else:
            return '差'

    def _rating_to_score(self, rating: str) -> float:
        """
        将评级转换为分数

        Args:
            rating: 评级字符串

        Returns:
            分数（0-100）
        """
        rating_map = {
            '优秀': 90,
            '良好': 75,
            '一般': 55,
            '差': 30
        }
        return rating_map.get(rating, 50)
