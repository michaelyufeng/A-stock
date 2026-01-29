"""选股筛选器模块"""
import pandas as pd
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from src.core.logger import get_logger
from src.core.config_manager import ConfigManager
from src.data.akshare_provider import AKShareProvider
from src.analysis.technical.indicators import TechnicalIndicators
from src.analysis.fundamental.financial_metrics import FinancialMetrics
from src.analysis.capital.money_flow import MoneyFlowAnalyzer

logger = get_logger(__name__)


class StockScreener:
    """选股筛选器"""

    def __init__(self):
        """初始化选股筛选器"""
        self.config = ConfigManager()
        self.data_provider = AKShareProvider()
        self.tech_indicators = TechnicalIndicators()
        self.financial_metrics = FinancialMetrics()
        self.money_flow = MoneyFlowAnalyzer()

        # 预设筛选方案
        self.presets = {
            'strong_momentum': self._strong_momentum_filter,
            'value_growth': self._value_growth_filter,
            'capital_inflow': self._capital_inflow_filter
        }

        logger.info("StockScreener initialized")

    def screen(
        self,
        stock_pool: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        preset: Optional[str] = None,
        top_n: int = 20,
        min_score: float = 60.0,
        parallel: bool = True,
        max_workers: int = 5
    ) -> pd.DataFrame:
        """
        执行选股筛选

        Args:
            stock_pool: 股票池（None表示全市场）
            filters: 自定义筛选条件字典
            preset: 预设方案名称
            top_n: 返回TOP N只股票
            min_score: 最低综合评分
            parallel: 是否并行处理
            max_workers: 最大并行数

        Returns:
            筛选结果DataFrame，包含：
            - code: 股票代码
            - name: 股票名称
            - score: 综合评分
            - tech_score: 技术面评分
            - fundamental_score: 基本面评分
            - capital_score: 资金面评分
            - current_price: 当前价格
            - reason: 入选理由
        """
        # 1. 获取股票池
        if stock_pool is None:
            logger.info("Fetching full market stock list...")
            stock_list_df = self.data_provider.get_stock_list()
            stock_pool = stock_list_df['代码'].tolist()
            logger.info(f"Total stocks in market: {len(stock_pool)}")
        elif len(stock_pool) == 0:
            logger.warning("Empty stock pool provided")
            return pd.DataFrame()

        # 2. 应用预设方案或自定义筛选
        if preset and preset in self.presets:
            logger.info(f"Using preset filter: {preset}")
            filters = self.presets[preset]()
        elif filters is None:
            filters = {}

        # 3. 初步筛选（快速过滤）
        logger.info("Applying quick filters...")
        filtered_pool = self._apply_quick_filters(stock_pool, filters)
        logger.info(f"Stocks after quick filters: {len(filtered_pool)}")

        if len(filtered_pool) == 0:
            logger.warning("No stocks passed quick filters")
            return pd.DataFrame()

        # 4. 详细分析和评分
        logger.info("Analyzing and scoring stocks...")
        if parallel:
            results = self._analyze_parallel(filtered_pool, filters, max_workers)
        else:
            results = self._analyze_sequential(filtered_pool, filters)

        # 5. 过滤最低分
        results = [r for r in results if r['score'] >= min_score]

        # 6. 排序并返回TOP N
        results_df = pd.DataFrame(results)
        if len(results_df) == 0:
            logger.warning("No stocks meet the criteria")
            return results_df

        results_df = results_df.sort_values('score', ascending=False).head(top_n)

        logger.info(f"Screening complete. Found {len(results_df)} stocks.")
        return results_df

    def _apply_quick_filters(
        self,
        stock_pool: List[str],
        filters: Dict[str, Any]
    ) -> List[str]:
        """
        快速筛选（基于基础数据，无需技术指标）

        Args:
            stock_pool: 股票池
            filters: 筛选条件

        Returns:
            筛选后的股票列表
        """
        filtered = []

        for code in tqdm(stock_pool, desc="Quick filtering", disable=len(stock_pool) < 10):
            # 过滤ST股
            if 'ST' in code or '*' in code:
                continue

            # 这里可以添加更多快速筛选条件
            # 例如：市值、行业等

            filtered.append(code)

        return filtered

    def _analyze_parallel(
        self,
        stock_pool: List[str],
        filters: Dict[str, Any],
        max_workers: int
    ) -> List[Dict[str, Any]]:
        """
        并行分析股票

        Args:
            stock_pool: 股票池
            filters: 筛选条件
            max_workers: 最大并行数

        Returns:
            分析结果列表
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures = {
                executor.submit(self._analyze_stock, code, filters): code
                for code in stock_pool
            }

            # 收集结果
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Analyzing stocks"
            ):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    code = futures[future]
                    logger.error(f"Error analyzing {code}: {e}")

        return results

    def _analyze_sequential(
        self,
        stock_pool: List[str],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        顺序分析股票

        Args:
            stock_pool: 股票池
            filters: 筛选条件

        Returns:
            分析结果列表
        """
        results = []

        for code in tqdm(stock_pool, desc="Analyzing stocks"):
            try:
                result = self._analyze_stock(code, filters)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {code}: {e}")

        return results

    def _analyze_stock(
        self,
        code: str,
        filters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        分析单只股票

        Args:
            code: 股票代码
            filters: 筛选条件

        Returns:
            分析结果字典，如果分析失败返回None
        """
        try:
            # 获取数据
            kline_df = self.data_provider.get_daily_kline(code, adjust='qfq')
            if len(kline_df) < 60:  # 至少需要60天数据
                logger.debug(f"Insufficient data for {code}: {len(kline_df)} days")
                return None

            # 计算技术指标
            kline_df = self.tech_indicators.calculate_all(kline_df)

            # 技术面评分
            tech_score = self._score_technical(kline_df, filters)

            # 基本面评分（可选，较慢）
            fundamental_score = 50  # 默认中性分
            if filters.get('use_fundamental', False):
                try:
                    financial_df = self.data_provider.get_financial_data(code)
                    if len(financial_df) > 0:
                        fundamental_score = self.financial_metrics.get_overall_score(financial_df)
                except Exception as e:
                    logger.debug(f"Failed to get fundamental data for {code}: {e}")

            # 资金面评分（可选）
            capital_score = 50  # 默认中性分
            if filters.get('use_capital', False):
                try:
                    money_flow_df = self.data_provider.get_money_flow(code)
                    if len(money_flow_df) > 0:
                        analysis = self.money_flow.analyze_main_force(money_flow_df)
                        # 简单转换为分数
                        if analysis.get('trend') == '流入':
                            capital_score = 70
                        elif analysis.get('trend') == '流出':
                            capital_score = 30
                        else:
                            capital_score = 50
                except Exception as e:
                    logger.debug(f"Failed to get capital data for {code}: {e}")

            # 综合评分
            weights = filters.get('weights', {
                'technical': 0.5,
                'fundamental': 0.3,
                'capital': 0.2
            })

            overall_score = (
                tech_score * weights['technical'] +
                fundamental_score * weights['fundamental'] +
                capital_score * weights['capital']
            )

            # 获取股票名称
            try:
                quote = self.data_provider.get_realtime_quote(code)
                name = quote.get('名称', code)
            except Exception as e:
                logger.debug(f"Failed to get quote for {code}: {e}")
                name = code

            return {
                'code': code,
                'name': name,
                'score': overall_score,
                'tech_score': tech_score,
                'fundamental_score': fundamental_score,
                'capital_score': capital_score,
                'current_price': kline_df['close'].iloc[-1],
                'reason': self._generate_reason(tech_score, fundamental_score, capital_score)
            }

        except Exception as e:
            logger.debug(f"Failed to analyze {code}: {e}")
            return None

    def _score_technical(
        self,
        df: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> float:
        """
        技术面评分（0-100分）

        Args:
            df: K线数据（已包含技术指标）
            filters: 筛选条件

        Returns:
            技术面评分
        """
        score = 50  # 基础分

        latest = df.iloc[-1]

        # RSI
        rsi = latest.get('RSI', 50)
        if 40 <= rsi <= 70:
            score += 10
        elif rsi < 30:  # 超卖
            score += 15
        elif rsi > 80:  # 超买
            score -= 10

        # MACD
        macd = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_signal', 0)
        if macd > macd_signal:  # 金叉
            score += 15
        elif macd < macd_signal:  # 死叉
            score -= 10

        # 价格趋势
        ma20 = latest.get('MA20', latest['close'])
        if latest['close'] > ma20:  # 站上MA20
            score += 10

        # 成交量
        vol_ma5 = latest.get('VOL_MA5', latest['volume'])
        if latest['volume'] > vol_ma5 * 1.5:  # 放量
            score += 10

        return max(0, min(100, score))

    def _generate_reason(
        self,
        tech_score: float,
        fundamental_score: float,
        capital_score: float
    ) -> str:
        """
        生成入选理由

        Args:
            tech_score: 技术面评分
            fundamental_score: 基本面评分
            capital_score: 资金面评分

        Returns:
            入选理由文本
        """
        reasons = []

        if tech_score >= 70:
            reasons.append("技术面强势")
        if fundamental_score >= 70:
            reasons.append("基本面优秀")
        if capital_score >= 70:
            reasons.append("主力资金流入")

        return "、".join(reasons) if reasons else "综合评分达标"

    # 预设方案
    def _strong_momentum_filter(self) -> Dict[str, Any]:
        """
        强势动量股筛选方案

        Returns:
            筛选条件字典
        """
        return {
            'use_fundamental': False,
            'use_capital': True,
            'weights': {
                'technical': 0.6,
                'fundamental': 0.2,
                'capital': 0.2
            }
        }

    def _value_growth_filter(self) -> Dict[str, Any]:
        """
        价值成长股筛选方案

        Returns:
            筛选条件字典
        """
        return {
            'use_fundamental': True,
            'use_capital': False,
            'weights': {
                'technical': 0.3,
                'fundamental': 0.6,
                'capital': 0.1
            }
        }

    def _capital_inflow_filter(self) -> Dict[str, Any]:
        """
        资金流入股筛选方案

        Returns:
            筛选条件字典
        """
        return {
            'use_fundamental': False,
            'use_capital': True,
            'weights': {
                'technical': 0.4,
                'fundamental': 0.2,
                'capital': 0.4
            }
        }
