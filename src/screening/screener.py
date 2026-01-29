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
from src.screening.filters import apply_filters

logger = get_logger(__name__)

# ==================== 筛选策略常量 ====================

# 低PE价值股策略阈值
LOW_PE_MAX = 15.0  # PE最大值
LOW_PE_ROE_MIN = 10.0  # ROE最小值（%）

# 高股息率策略阈值
HIGH_DIVIDEND_YIELD_MIN = 3.0  # 股息率最小值（%）

# 突破新高策略阈值
BREAKOUT_DAYS_20 = 20  # 20日新高
BREAKOUT_DAYS_60 = 60  # 60日新高
BREAKOUT_VOLUME_RATIO_MIN = 1.2  # 成交量放大倍数

# 超卖反弹策略阈值
OVERSOLD_RSI_THRESHOLD = 30.0  # RSI超卖阈值
REBOUND_RSI_MIN = 30.0  # 反弹RSI最小值

# 机构重仓策略阈值
INSTITUTIONAL_RATIO_MIN = 30.0  # 机构持仓比例最小值（%）


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
            'capital_inflow': self._capital_inflow_filter,
            'low_pe_value': self._low_pe_value_filter,
            'high_dividend': self._high_dividend_filter,
            'breakout': self._breakout_filter,
            'oversold_rebound': self._oversold_rebound_filter,
            'institutional_favorite': self._institutional_favorite_filter
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

            # 获取实时行情（包含PE、PB等基本面数据）
            try:
                quote = self.data_provider.get_realtime_quote(code)

                # 验证quote数据有效性
                if not quote or not isinstance(quote, dict):
                    logger.warning(f"无效的实时行情数据: {code}")
                else:
                    # 将基本面数据添加到K线数据中
                    if 'PE' in quote or '市盈率-动态' in quote:
                        kline_df['PE'] = quote.get('PE', quote.get('市盈率-动态', float('nan')))
                    if 'ROE' in quote or '净资产收益率' in quote:
                        kline_df['ROE'] = quote.get('ROE', quote.get('净资产收益率', float('nan')))
                    if '股息率' in quote:
                        kline_df['股息率'] = quote.get('股息率', float('nan'))
                    if '机构持仓比例' in quote:
                        kline_df['机构持仓比例'] = quote.get('机构持仓比例', float('nan'))
            except Exception as e:
                logger.debug(f"Failed to get quote data for {code}: {e}")

            # 应用预设策略的过滤逻辑
            if 'thresholds' in filters:
                kline_df = apply_filters(kline_df, filters['thresholds'])
                # 如果被过滤掉，返回None
                if len(kline_df) == 0:
                    logger.debug(f"Stock {code} filtered out by preset thresholds")
                    return None

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
                if quote and isinstance(quote, dict):
                    name = quote.get('名称', code)
                else:
                    name = code
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

    # ==================== 新增预设筛选方案 ====================

    def _low_pe_value_filter(self) -> Dict[str, Any]:
        """
        低PE价值股筛选方案

        筛选标准：
        - PE ratio < 15
        - ROE > 10%
        - 目标：寻找被低估的优质公司

        适用场景：
        - 价值投资者
        - 中长期投资
        - 寻找低估值蓝筹股

        Returns:
            筛选条件字典，包含：
            - use_fundamental: 是否使用基本面分析（True）
            - use_capital: 是否使用资金面分析（False）
            - weights: 各维度权重（基本面60%，技术面30%，资金面10%）
            - thresholds: 具体筛选阈值
        """
        return {
            'use_fundamental': True,
            'use_capital': False,
            'weights': {
                'technical': 0.3,
                'fundamental': 0.6,
                'capital': 0.1
            },
            'thresholds': {
                'pe_max': LOW_PE_MAX,
                'roe_min': LOW_PE_ROE_MIN
            }
        }

    def _high_dividend_filter(self) -> Dict[str, Any]:
        """
        高股息率股筛选方案

        筛选标准：
        - 股息率 > 3%
        - 稳定的分红历史
        - 目标：收益型投资标的

        适用场景：
        - 追求稳定现金流
        - 低风险偏好投资者
        - 长期持有策略

        Returns:
            筛选条件字典，包含：
            - use_fundamental: 是否使用基本面分析（True）
            - use_capital: 是否使用资金面分析（False）
            - weights: 各维度权重（基本面70%，技术面20%，资金面10%）
            - thresholds: 具体筛选阈值
        """
        return {
            'use_fundamental': True,
            'use_capital': False,
            'weights': {
                'technical': 0.2,
                'fundamental': 0.7,
                'capital': 0.1
            },
            'thresholds': {
                'dividend_yield_min': HIGH_DIVIDEND_YIELD_MIN
            }
        }

    def _breakout_filter(self) -> Dict[str, Any]:
        """
        突破新高股筛选方案

        筛选标准：
        - 价格突破20日或60日新高
        - 成交量放大确认（> 1.2倍均量）
        - 目标：动量延续机会

        适用场景：
        - 趋势跟踪策略
        - 短中期交易
        - 追涨强势股

        注意事项：
        - 需要设置止损
        - 注意追高风险
        - 关注涨停板限制（A股特色）

        Returns:
            筛选条件字典，包含：
            - use_fundamental: 是否使用基本面分析（False）
            - use_capital: 是否使用资金面分析（True）
            - weights: 各维度权重（技术面60%，资金面30%，基本面10%）
            - thresholds: 具体筛选阈值
        """
        return {
            'use_fundamental': False,
            'use_capital': True,
            'weights': {
                'technical': 0.6,
                'fundamental': 0.1,
                'capital': 0.3
            },
            'thresholds': {
                'breakout_days': BREAKOUT_DAYS_20,  # 默认使用20日新高
                'volume_ratio_min': BREAKOUT_VOLUME_RATIO_MIN
            }
        }

    def _oversold_rebound_filter(self) -> Dict[str, Any]:
        """
        超卖反弹股筛选方案

        筛选标准：
        - RSI < 30（超卖）
        - 随后RSI回升至30以上（反弹信号）
        - 目标：均值回归交易机会

        适用场景：
        - 短期交易
        - 逆向投资策略
        - 超跌反弹机会

        注意事项：
        - 需要快进快出
        - 设置止损位
        - 避免抄底下跌趋势中的股票
        - 结合其他指标确认反转

        Returns:
            筛选条件字典，包含：
            - use_fundamental: 是否使用基本面分析（False）
            - use_capital: 是否使用资金面分析（False）
            - weights: 各维度权重（技术面70%，基本面15%，资金面15%）
            - thresholds: 具体筛选阈值
        """
        return {
            'use_fundamental': False,
            'use_capital': False,
            'weights': {
                'technical': 0.7,
                'fundamental': 0.15,
                'capital': 0.15
            },
            'thresholds': {
                'rsi_oversold': OVERSOLD_RSI_THRESHOLD,
                'rsi_rebound_min': REBOUND_RSI_MIN
            }
        }

    def _institutional_favorite_filter(self) -> Dict[str, Any]:
        """
        机构重仓股筛选方案

        筛选标准：
        - 机构持仓比例 > 30%
        - 机构持仓呈增加趋势
        - 目标：跟随聪明钱

        适用场景：
        - 中长期投资
        - 跟随机构策略
        - 寻找高质量标的

        注意事项：
        - 机构数据可能有延迟
        - 需要结合基本面分析
        - 避免在机构高位减仓时追涨

        Returns:
            筛选条件字典，包含：
            - use_fundamental: 是否使用基本面分析（True）
            - use_capital: 是否使用资金面分析（True）
            - weights: 各维度权重（基本面50%，技术面20%，资金面30%）
            - thresholds: 具体筛选阈值
        """
        return {
            'use_fundamental': True,
            'use_capital': True,
            'weights': {
                'technical': 0.2,
                'fundamental': 0.5,
                'capital': 0.3
            },
            'thresholds': {
                'institutional_ratio_min': INSTITUTIONAL_RATIO_MIN
            }
        }
