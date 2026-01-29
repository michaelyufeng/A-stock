"""AI综合评级系统"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.analysis.technical.indicators import TechnicalIndicators
from src.analysis.fundamental.financial_metrics import FinancialMetrics
from src.analysis.capital.money_flow import MoneyFlowAnalyzer
from src.analysis.ai.deepseek_client import DeepSeekClient
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger(__name__)


class StockRater:
    """AI综合评级系统，整合技术面、基本面、资金面分析"""

    def __init__(self):
        """初始化股票评级器"""
        logger.info("Initializing StockRater...")

        # 初始化各个分析器
        self.technical_indicators = TechnicalIndicators()
        self.financial_metrics = FinancialMetrics()
        self.money_flow_analyzer = MoneyFlowAnalyzer()
        self.deepseek_client = DeepSeekClient()

        # 从配置读取权重
        config = ConfigManager()
        self.weights = {
            'technical': config.get('ai.rating_weights.technical', 0.30),
            'fundamental': config.get('ai.rating_weights.fundamental', 0.30),
            'capital': config.get('ai.rating_weights.capital', 0.25),
            'sentiment': config.get('ai.rating_weights.sentiment', 0.15)
        }

        logger.info(f"StockRater initialized with weights: {self.weights}")

    def analyze_stock(
        self,
        stock_code: str,
        kline_df: pd.DataFrame,
        financial_df: pd.DataFrame,
        money_flow_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        综合股票分析，生成AI评级

        Args:
            stock_code: 股票代码
            kline_df: K线数据
            financial_df: 财务数据
            money_flow_df: 资金流向数据

        Returns:
            综合评级结果字典

        Raises:
            ValueError: 当输入数据为空时
        """
        logger.info(f"Analyzing stock {stock_code}...")

        # 验证输入数据
        if kline_df.empty or financial_df.empty or money_flow_df.empty:
            raise ValueError("Input DataFrames cannot be empty")

        # 1. 技术面分析
        technical_score = self._analyze_technical(kline_df)
        logger.debug(f"Technical score: {technical_score}")

        # 2. 基本面分析
        fundamental_score = self._analyze_fundamental(financial_df)
        logger.debug(f"Fundamental score: {fundamental_score}")

        # 3. 资金面分析
        capital_score, capital_signal = self._analyze_capital(money_flow_df)
        logger.debug(f"Capital score: {capital_score}, signal: {capital_signal}")

        # 4. 情绪面分析（基于资金流向和AI分析）
        sentiment_score = self._analyze_sentiment(capital_signal, capital_score)
        logger.debug(f"Sentiment score: {sentiment_score}")

        # 5. 计算加权综合分数
        overall_score = self._calculate_weighted_score(
            technical_score,
            fundamental_score,
            capital_score,
            sentiment_score
        )
        logger.info(f"Overall score: {overall_score}")

        # 6. 确定评级
        rating = self._determine_rating(overall_score)
        logger.info(f"Rating: {rating}")

        # 7. 计算信心度
        confidence = self._calculate_confidence(
            technical_score,
            fundamental_score,
            capital_score,
            sentiment_score,
            overall_score
        )
        logger.info(f"Confidence: {confidence}")

        # 8. 获取当前价格
        current_price = float(kline_df['收盘'].iloc[-1])

        # 9. 计算目标价和止损价
        target_price = self._calculate_target_price(current_price, overall_score, rating)
        stop_loss = self._calculate_stop_loss(current_price, overall_score, rating)

        # 10. 生成原因和风险
        reasons = self._generate_reasons(
            rating,
            technical_score,
            fundamental_score,
            capital_score,
            capital_signal
        )
        risks = self._generate_risks(rating, overall_score)

        # 11. 评估A股特有风险
        a_share_risks = self._assess_a_share_risks(stock_code, kline_df, rating)

        # 12. 使用AI生成综合洞察
        ai_insights = self._generate_ai_insights(
            stock_code,
            {
                'technical_score': technical_score,
                'fundamental_score': fundamental_score,
                'capital_score': capital_score,
                'sentiment_score': sentiment_score,
                'overall_score': overall_score,
                'rating': rating,
                'confidence': confidence,
                'capital_signal': capital_signal,
                'current_price': current_price
            }
        )

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
                'fundamental': round(fundamental_score, 2),
                'capital': round(capital_score, 2),
                'overall': round(overall_score, 2)
            }
        }

        logger.info(f"Stock analysis completed for {stock_code}")
        return result

    def _analyze_technical(self, kline_df: pd.DataFrame) -> float:
        """
        分析技术面

        Args:
            kline_df: K线数据

        Returns:
            技术面分数（0-100）
        """
        # 计算所有技术指标
        df_with_indicators = self.technical_indicators.calculate_all(kline_df)

        score = 0.0
        indicators_found = 0
        total_indicators = 7  # 7个主要指标

        # 1. MA趋势分析
        if 'MA5' in df_with_indicators.columns and 'MA20' in df_with_indicators.columns:
            indicators_found += 1
            ma5 = df_with_indicators['MA5'].iloc[-1]
            ma20 = df_with_indicators['MA20'].iloc[-1]
            close = df_with_indicators['close'].iloc[-1]
            if ma5 > ma20 and close > ma5:
                score += 100.0
            elif ma5 > ma20 or close > ma20:
                score += 50.0

        # 2. MACD分析
        if 'MACD' in df_with_indicators.columns and 'MACD_signal' in df_with_indicators.columns:
            indicators_found += 1
            macd = df_with_indicators['MACD'].iloc[-1]
            macd_signal = df_with_indicators['MACD_signal'].iloc[-1]
            if macd > macd_signal and macd > 0:
                score += 100.0
            elif macd > macd_signal:
                score += 70.0

        # 3. RSI分析
        if 'RSI' in df_with_indicators.columns:
            indicators_found += 1
            rsi = df_with_indicators['RSI'].iloc[-1]
            if 40 <= rsi <= 70:  # 健康区间
                score += 100.0
            elif 30 <= rsi < 40 or 70 < rsi <= 80:
                score += 50.0

        # 4. KDJ分析
        if 'K' in df_with_indicators.columns and 'D' in df_with_indicators.columns:
            indicators_found += 1
            k = df_with_indicators['K'].iloc[-1]
            d = df_with_indicators['D'].iloc[-1]
            if k > d and k < 80:
                score += 100.0
            elif k > d:
                score += 50.0

        # 5. 布林带分析
        if 'BOLL_UPPER' in df_with_indicators.columns and 'BOLL_LOWER' in df_with_indicators.columns:
            indicators_found += 1
            close = df_with_indicators['close'].iloc[-1]
            boll_upper = df_with_indicators['BOLL_UPPER'].iloc[-1]
            boll_lower = df_with_indicators['BOLL_LOWER'].iloc[-1]
            boll_middle = df_with_indicators['BOLL_MIDDLE'].iloc[-1]
            if boll_lower < close < boll_middle:
                score += 100.0
            elif close < boll_upper:
                score += 50.0

        # 6. 成交量分析
        if 'VOL_MA5' in df_with_indicators.columns:
            indicators_found += 1
            volume = df_with_indicators['volume'].iloc[-1]
            vol_ma5 = df_with_indicators['VOL_MA5'].iloc[-1]
            if volume > vol_ma5 * 1.2:  # 放量
                score += 80.0
            elif volume > vol_ma5:
                score += 50.0

        # 7. ATR波动率分析
        if 'ATR' in df_with_indicators.columns:
            indicators_found += 1
            atr = df_with_indicators['ATR'].iloc[-1]
            close = df_with_indicators['close'].iloc[-1]
            atr_ratio = atr / close if close > 0 else 0
            if atr_ratio < 0.03:  # 低波动
                score += 70.0
            elif atr_ratio < 0.05:
                score += 50.0

        # 如果没有找到任何指标，给出一个基于价格趋势的简单分数
        if indicators_found == 0:
            logger.warning("No technical indicators found, using simple price trend analysis")
            if len(df_with_indicators) >= 5:
                recent_close = df_with_indicators['收盘'].iloc[-5:] if '收盘' in df_with_indicators.columns else df_with_indicators['close'].iloc[-5:]
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

        # 计算平均分数
        final_score = score / indicators_found if indicators_found > 0 else 50.0
        return min(final_score, 100.0)

    def _analyze_fundamental(self, financial_df: pd.DataFrame) -> float:
        """
        分析基本面

        Args:
            financial_df: 财务数据

        Returns:
            基本面分数（0-100）
        """
        return self.financial_metrics.get_overall_score(financial_df)

    def _analyze_capital(self, money_flow_df: pd.DataFrame) -> tuple:
        """
        分析资金面

        Args:
            money_flow_df: 资金流向数据

        Returns:
            (资金面分数, 资金信号)
        """
        signal = self.money_flow_analyzer.get_money_flow_signal(money_flow_df)
        summary = self.money_flow_analyzer.generate_summary(money_flow_df)

        # 根据信号和主力强度计算分数
        main_force = summary['main_force']
        trend = main_force['trend']
        strength = main_force['strength']

        score = 50.0  # 基础分

        # 根据趋势调整
        if trend == '流入':
            if strength == '强':
                score = 90.0
            elif strength == '中':
                score = 75.0
            else:
                score = 60.0
        elif trend == '流出':
            if strength == '强':
                score = 20.0
            elif strength == '中':
                score = 35.0
            else:
                score = 45.0

        return score, signal

    def _analyze_sentiment(self, capital_signal: str, capital_score: float) -> float:
        """
        分析情绪面

        Args:
            capital_signal: 资金信号
            capital_score: 资金分数

        Returns:
            情绪面分数（0-100）
        """
        # 情绪主要基于资金流向
        if capital_signal == '买入':
            return min(capital_score * 1.1, 100.0)
        elif capital_signal == '卖出':
            return max(capital_score * 0.9, 0.0)
        else:
            return capital_score

    def _calculate_weighted_score(
        self,
        technical_score: float,
        fundamental_score: float,
        capital_score: float,
        sentiment_score: float
    ) -> float:
        """
        计算加权综合分数

        Args:
            technical_score: 技术面分数
            fundamental_score: 基本面分数
            capital_score: 资金面分数
            sentiment_score: 情绪面分数

        Returns:
            加权综合分数（0-100）
        """
        overall = (
            technical_score * self.weights['technical'] +
            fundamental_score * self.weights['fundamental'] +
            capital_score * self.weights['capital'] +
            sentiment_score * self.weights['sentiment']
        )
        return round(overall, 2)

    def _determine_rating(self, overall_score: float) -> str:
        """
        根据综合分数确定评级

        Args:
            overall_score: 综合分数

        Returns:
            评级：'buy', 'hold', 'sell'
        """
        if overall_score >= 70:
            return 'buy'
        elif overall_score >= 45:
            return 'hold'
        else:
            return 'sell'

    def _calculate_confidence(
        self,
        technical_score: float,
        fundamental_score: float,
        capital_score: float,
        sentiment_score: float,
        overall_score: float
    ) -> float:
        """
        计算信心度

        Args:
            technical_score: 技术面分数
            fundamental_score: 基本面分数
            capital_score: 资金面分数
            sentiment_score: 情绪面分数
            overall_score: 综合分数

        Returns:
            信心度（1-10）
        """
        # 计算各维度的一致性
        scores = [technical_score, fundamental_score, capital_score, sentiment_score]
        std_dev = np.std(scores)

        # 标准差越小，一致性越高，信心度越高
        consistency_factor = max(0, 1 - std_dev / 60)  # 放宽一致性要求

        # 综合分数越极端（接近0或100），信心度越高
        extremity_factor = abs(overall_score - 50) / 50

        # 基础信心度（根据综合分数线性映射到1-10）
        if overall_score >= 70:
            # 70-100 映射到 7.5-10
            base_confidence = 7.5 + (overall_score - 70) / 12
        elif overall_score >= 50:
            # 50-70 映射到 5-7
            base_confidence = 5.0 + (overall_score - 50) / 10
        elif overall_score >= 30:
            # 30-50 映射到 3-5
            base_confidence = 3.0 + (overall_score - 30) / 10
        else:
            # 0-30 映射到 1-3
            base_confidence = 1.0 + overall_score / 15

        # 调整信心度（一致性和极端性都会增加信心度）
        # 对于高分，更多依赖综合分数，减少一致性影响
        if overall_score >= 70:
            confidence = base_confidence * (0.7 + 0.3 * consistency_factor) * (0.8 + 0.2 * extremity_factor)
        else:
            confidence = base_confidence * (0.6 + 0.4 * consistency_factor) * (0.7 + 0.3 * extremity_factor)

        # 对于高分和低分，给予额外加成
        if overall_score >= 80:
            confidence = min(confidence * 1.15, 10.0)
        elif overall_score <= 30:
            confidence = min(confidence * 1.1, 10.0)

        # 限制在1-10范围内
        return max(1.0, min(10.0, round(confidence, 1)))

    def _calculate_target_price(self, current_price: float, overall_score: float, rating: str) -> float:
        """
        计算目标价

        Args:
            current_price: 当前价格
            overall_score: 综合分数
            rating: 评级

        Returns:
            目标价
        """
        if rating == 'buy':
            # 根据分数计算涨幅（5%-25%）
            gain_ratio = 0.05 + (overall_score - 70) / 100 * 0.20
            return current_price * (1 + gain_ratio)
        elif rating == 'sell':
            # 根据分数计算跌幅（5%-20%）
            loss_ratio = 0.05 + (45 - overall_score) / 100 * 0.15
            return current_price * (1 - loss_ratio)
        else:  # hold
            # 持有时目标价接近当前价，略有上涨
            return current_price * 1.03

    def _calculate_stop_loss(self, current_price: float, overall_score: float, rating: str) -> float:
        """
        计算止损价

        Args:
            current_price: 当前价格
            overall_score: 综合分数
            rating: 评级

        Returns:
            止损价
        """
        if rating == 'buy':
            # 买入止损为-5%到-10%
            stop_loss_ratio = 0.05 + (100 - overall_score) / 100 * 0.05
            return current_price * (1 - stop_loss_ratio)
        elif rating == 'sell':
            # 卖出时止损即为当前价（建议立即卖出）
            return current_price * 0.98
        else:  # hold
            # 持有止损为-7%
            return current_price * 0.93

    def _generate_reasons(
        self,
        rating: str,
        technical_score: float,
        fundamental_score: float,
        capital_score: float,
        capital_signal: str
    ) -> List[str]:
        """
        生成评级原因

        Args:
            rating: 评级
            technical_score: 技术面分数
            fundamental_score: 基本面分数
            capital_score: 资金面分数
            capital_signal: 资金信号

        Returns:
            原因列表
        """
        reasons = []

        if rating == 'buy':
            if technical_score >= 70:
                reasons.append('技术面呈现强势上涨趋势')
            if fundamental_score >= 70:
                reasons.append('基本面良好，财务指标健康')
            if capital_score >= 70:
                reasons.append('主力资金持续流入，市场情绪积极')
            if capital_signal == '买入':
                reasons.append('资金流向信号显示买入机会')
        elif rating == 'sell':
            if technical_score < 45:
                reasons.append('技术面走弱，下跌趋势明显')
            if fundamental_score < 45:
                reasons.append('基本面欠佳，财务风险较高')
            if capital_score < 45:
                reasons.append('主力资金流出，市场情绪悲观')
            if capital_signal == '卖出':
                reasons.append('资金流向信号显示卖出风险')
        else:  # hold
            reasons.append('综合指标显示震荡整理，建议观望')
            if 50 <= technical_score < 70:
                reasons.append('技术面处于平衡状态')
            if 50 <= fundamental_score < 70:
                reasons.append('基本面稳定，但缺乏亮点')

        if not reasons:
            reasons.append('综合分析建议当前操作')

        return reasons

    def _generate_risks(self, rating: str, overall_score: float) -> List[str]:
        """
        生成风险提示

        Args:
            rating: 评级
            overall_score: 综合分数

        Returns:
            风险列表
        """
        risks = []

        if rating == 'buy':
            risks.append('市场整体波动可能影响个股表现')
            if overall_score < 80:
                risks.append('部分指标存在分歧，需密切关注')
        elif rating == 'sell':
            risks.append('继续持有可能面临进一步下跌风险')
            risks.append('建议及时止损，避免损失扩大')
        else:  # hold
            risks.append('横盘整理期间可能出现方向选择')
            risks.append('需关注市场和个股基本面变化')

        # 通用风险
        risks.append('政策和宏观环境变化风险')

        return risks

    def _assess_a_share_risks(self, stock_code: str, kline_df: pd.DataFrame, rating: str) -> List[str]:
        """
        评估A股特有风险

        Args:
            stock_code: 股票代码
            kline_df: K线数据
            rating: 评级

        Returns:
            A股特有风险列表
        """
        risks = []

        # 1. T+1流动性风险
        risks.append('T+1交易制度限制，当日买入次日才能卖出')

        # 2. 涨跌停风险
        current_price = float(kline_df['收盘'].iloc[-1])
        prev_price = float(kline_df['收盘'].iloc[-2]) if len(kline_df) >= 2 else current_price
        change_pct = abs((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0

        if change_pct > 8:
            risks.append('涨跌幅较大，需警惕涨跌停板限制')

        # 3. ST股票风险
        if stock_code.startswith('ST') or 'ST' in stock_code:
            risks.append('ST股票退市风险较高，投资需谨慎')

        # 4. 科创板/创业板风险
        if stock_code.startswith('688') or stock_code.startswith('300'):
            risks.append('科创板/创业板涨跌幅限制为20%，波动较大')

        # 5. 买入卖出时机风险
        if rating == 'buy':
            risks.append('建议分批建仓，降低单次买入风险')
        elif rating == 'sell':
            risks.append('T+1限制下，需提前规划卖出时机')

        return risks

    def _generate_ai_insights(self, stock_code: str, analysis_data: Dict[str, Any]) -> str:
        """
        使用AI生成综合洞察

        Args:
            stock_code: 股票代码
            analysis_data: 分析数据

        Returns:
            AI生成的综合分析文本
        """
        try:
            logger.info(f"Generating AI insights for {stock_code}...")

            # 构建分析数据
            ai_data = {
                'technical': {
                    'score': analysis_data['technical_score'],
                    'rating': self._score_to_rating(analysis_data['technical_score'])
                },
                'fundamental': {
                    'score': analysis_data['fundamental_score'],
                    'rating': self._score_to_rating(analysis_data['fundamental_score'])
                },
                'capital': {
                    'score': analysis_data['capital_score'],
                    'signal': analysis_data['capital_signal']
                },
                'overall': {
                    'score': analysis_data['overall_score'],
                    'rating': analysis_data['rating'],
                    'confidence': analysis_data['confidence']
                }
            }

            insights = self.deepseek_client.analyze_stock(stock_code, ai_data)
            return insights

        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            # 返回默认分析
            return self._generate_default_insights(analysis_data)

    def _generate_default_insights(self, analysis_data: Dict[str, Any]) -> str:
        """
        生成默认分析洞察（AI不可用时）

        Args:
            analysis_data: 分析数据

        Returns:
            默认分析文本
        """
        rating = analysis_data['rating']
        overall_score = analysis_data['overall_score']
        confidence = analysis_data['confidence']

        if rating == 'buy':
            return (
                f"综合评分{overall_score}分，建议买入。"
                f"技术面、基本面和资金面综合表现良好，信心度{confidence}/10。"
                f"建议关注买入时机，分批建仓以降低风险。"
            )
        elif rating == 'sell':
            return (
                f"综合评分{overall_score}分，建议卖出。"
                f"多项指标显示下行风险，信心度{confidence}/10。"
                f"建议及时止损，避免损失进一步扩大。"
            )
        else:
            return (
                f"综合评分{overall_score}分，建议持有观望。"
                f"当前处于震荡整理阶段，信心度{confidence}/10。"
                f"建议等待明确方向信号后再做决策。"
            )

    def _score_to_rating(self, score: float) -> str:
        """
        将分数转换为评级文本

        Args:
            score: 分数（0-100）

        Returns:
            评级文本
        """
        if score >= 75:
            return '优秀'
        elif score >= 60:
            return '良好'
        elif score >= 40:
            return '一般'
        else:
            return '差'
