"""
自定义筛选示例 - Custom Screening Example

展示如何创建自定义筛选条件：
1. 自定义技术指标过滤器
2. 自定义基本面过滤器
3. 组合多个过滤器
4. 自定义排序规则

作者: A-stock量化交易系统
日期: 2026-01-29
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screening.screener import StockScreener
from src.data.akshare_provider import AKShareProvider
from src.analysis.technical.indicators import TechnicalIndicators
from src.analysis.fundamental.financial_metrics import FinancialMetrics
from src.analysis.capital.money_flow import MoneyFlowAnalyzer
from src.core.logger import get_logger

logger = get_logger(__name__)


class CustomScreener:
    """自定义筛选器"""

    def __init__(self):
        self.data_provider = AKShareProvider()
        self.tech_indicators = TechnicalIndicators()
        self.financial_metrics = FinancialMetrics()
        self.money_flow = MoneyFlowAnalyzer()

    def print_separator(self, title):
        """打印分隔线"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    # ========================================================================
    # 自定义技术指标过滤器
    # ========================================================================

    def technical_breakout_filter(self, stock_code):
        """
        技术突破过滤器

        条件：
        1. 价格突破20日均线
        2. MACD金叉
        3. RSI在40-70之间（不超买不超卖）
        4. 成交量放大

        Returns:
            (是否通过, 评分, 理由)
        """
        try:
            # 获取数据
            data = self.data_provider.get_stock_data(stock_code, adjust='qfq')
            if data is None or len(data) < 60:
                return False, 0, "数据不足"

            # 计算技术指标
            close = data['close']
            volume = data['volume']

            # 计算均线
            ma20 = close.rolling(20).mean()
            ma5_vol = volume.rolling(5).mean()

            # 获取最新值
            current_price = close.iloc[-1]
            current_ma20 = ma20.iloc[-1]
            current_volume = volume.iloc[-1]
            avg_volume = ma5_vol.iloc[-1]

            # 计算MACD
            df_with_macd = self.tech_indicators.calculate_macd(data)
            macd = df_with_macd['macd'].iloc[-1]
            signal = df_with_macd['macd_signal'].iloc[-1]

            # 计算RSI
            df_with_rsi = self.tech_indicators.calculate_rsi(data)
            rsi = df_with_rsi['rsi'].iloc[-1]

            # 评分
            score = 50  # 基础分
            reasons = []

            # 1. 价格突破MA20
            if current_price > current_ma20:
                score += 20
                pct = (current_price - current_ma20) / current_ma20 * 100
                reasons.append(f"突破MA20 (+{pct:.1f}%)")

            # 2. MACD金叉
            if macd > signal and macd > 0:
                score += 20
                reasons.append("MACD金叉")

            # 3. RSI在合理区间
            if 40 <= rsi <= 70:
                score += 15
                reasons.append(f"RSI健康({rsi:.1f})")
            elif rsi < 30:
                score += 10
                reasons.append(f"RSI超卖({rsi:.1f})")

            # 4. 成交量放大
            if current_volume > avg_volume * 1.5:
                score += 15
                ratio = current_volume / avg_volume
                reasons.append(f"成交量放大({ratio:.1f}x)")

            # 判断是否通过
            passed = score >= 75
            reason = ", ".join(reasons) if reasons else "无明显特征"

            return passed, score, reason

        except Exception as e:
            logger.error(f"技术突破过滤器失败 {stock_code}: {e}")
            return False, 0, str(e)

    def trend_following_filter(self, stock_code):
        """
        趋势跟踪过滤器

        条件：
        1. 短期均线(MA5)在长期均线(MA20)之上
        2. 均线呈多头排列
        3. 价格在上升通道中
        4. 连续上涨天数 >= 3

        Returns:
            (是否通过, 评分, 理由)
        """
        try:
            data = self.data_provider.get_stock_data(stock_code, adjust='qfq')
            if data is None or len(data) < 60:
                return False, 0, "数据不足"

            close = data['close']

            # 计算均线
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean()
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()

            # 最新值
            current_ma5 = ma5.iloc[-1]
            current_ma10 = ma10.iloc[-1]
            current_ma20 = ma20.iloc[-1]
            current_ma60 = ma60.iloc[-1]
            current_price = close.iloc[-1]

            # 计算连续上涨天数
            up_days = 0
            for i in range(len(close) - 1, 0, -1):
                if close.iloc[i] > close.iloc[i - 1]:
                    up_days += 1
                else:
                    break

            # 评分
            score = 50
            reasons = []

            # 1. MA5 > MA20
            if current_ma5 > current_ma20:
                score += 20
                reasons.append("短期强于长期")

            # 2. 多头排列 (MA5 > MA10 > MA20 > MA60)
            if current_ma5 > current_ma10 > current_ma20 > current_ma60:
                score += 25
                reasons.append("多头排列")

            # 3. 价格在MA20之上
            if current_price > current_ma20:
                score += 15
                reasons.append("价格在MA20之上")

            # 4. 连续上涨
            if up_days >= 3:
                score += 10
                reasons.append(f"连续上涨{up_days}天")

            passed = score >= 80
            reason = ", ".join(reasons) if reasons else "趋势不明显"

            return passed, score, reason

        except Exception as e:
            logger.error(f"趋势跟踪过滤器失败 {stock_code}: {e}")
            return False, 0, str(e)

    # ========================================================================
    # 自定义基本面过滤器
    # ========================================================================

    def high_quality_company_filter(self, stock_code):
        """
        优质公司过滤器

        条件：
        1. ROE > 15%
        2. 毛利率 > 30%
        3. 营收增长率 > 10%
        4. 净利润增长率 > 10%
        5. 负债率 < 60%

        Returns:
            (是否通过, 评分, 理由)
        """
        try:
            # 获取财务数据
            financial_data = self.data_provider.get_financial_data(stock_code)
            if not financial_data:
                return False, 0, "财务数据缺失"

            # 计算财务指标
            indicators = self.financial_metrics.calculate_all_indicators(financial_data)

            # 提取关键指标
            roe = indicators.get('roe', 0)
            gross_margin = indicators.get('gross_margin', 0)
            revenue_growth = indicators.get('revenue_growth_rate', 0)
            profit_growth = indicators.get('net_profit_growth_rate', 0)
            debt_ratio = indicators.get('debt_to_asset_ratio', 100)

            # 评分
            score = 50
            reasons = []

            # 1. ROE
            if roe > 20:
                score += 25
                reasons.append(f"ROE优秀({roe:.1f}%)")
            elif roe > 15:
                score += 15
                reasons.append(f"ROE良好({roe:.1f}%)")

            # 2. 毛利率
            if gross_margin > 40:
                score += 20
                reasons.append(f"高毛利({gross_margin:.1f}%)")
            elif gross_margin > 30:
                score += 10
                reasons.append(f"毛利率健康({gross_margin:.1f}%)")

            # 3. 营收增长
            if revenue_growth > 20:
                score += 15
                reasons.append(f"营收高增长({revenue_growth:.1f}%)")
            elif revenue_growth > 10:
                score += 8
                reasons.append(f"营收增长({revenue_growth:.1f}%)")

            # 4. 利润增长
            if profit_growth > 20:
                score += 15
                reasons.append(f"利润高增长({profit_growth:.1f}%)")
            elif profit_growth > 10:
                score += 8
                reasons.append(f"利润增长({profit_growth:.1f}%)")

            # 5. 负债率
            if debt_ratio < 40:
                score += 10
                reasons.append(f"低负债({debt_ratio:.1f}%)")
            elif debt_ratio < 60:
                score += 5
                reasons.append(f"负债健康({debt_ratio:.1f}%)")

            passed = score >= 75
            reason = ", ".join(reasons) if reasons else "基本面一般"

            return passed, score, reason

        except Exception as e:
            logger.error(f"优质公司过滤器失败 {stock_code}: {e}")
            return False, 0, str(e)

    def undervalued_filter(self, stock_code):
        """
        低估值过滤器

        条件：
        1. PE < 行业平均
        2. PB < 3
        3. 股息率 > 2%
        4. PEG < 1（如果有增长）

        Returns:
            (是否通过, 评分, 理由)
        """
        try:
            # 获取估值数据
            # 注意：这里简化处理，实际应该获取行业数据进行对比
            financial_data = self.data_provider.get_financial_data(stock_code)
            if not financial_data:
                return False, 0, "数据缺失"

            # 这里使用简化的估值判断
            # 实际使用时应该调用AKShare的估值接口

            score = 50
            reasons = []

            # 简化示例：假设符合低估值
            score += 30
            reasons.append("估值合理")

            passed = score >= 60
            reason = ", ".join(reasons) if reasons else "估值数据不足"

            return passed, score, reason

        except Exception as e:
            logger.error(f"低估值过滤器失败 {stock_code}: {e}")
            return False, 0, str(e)

    # ========================================================================
    # 组合过滤器
    # ========================================================================

    def combined_filter(self, stock_code, filters, weights=None):
        """
        组合多个过滤器

        Args:
            stock_code: 股票代码
            filters: 过滤器列表 [(filter_func, filter_name), ...]
            weights: 权重字典 {filter_name: weight}

        Returns:
            (是否通过, 综合评分, 详细信息)
        """
        if weights is None:
            # 默认等权重
            weights = {name: 1.0 / len(filters) for _, name in filters}

        results = {}
        total_score = 0
        all_reasons = []

        # 执行每个过滤器
        for filter_func, filter_name in filters:
            passed, score, reason = filter_func(stock_code)
            results[filter_name] = {
                'passed': passed,
                'score': score,
                'reason': reason
            }

            # 计算加权分数
            weight = weights.get(filter_name, 0)
            total_score += score * weight

            if reason:
                all_reasons.append(f"{filter_name}: {reason}")

        # 判断是否通过（所有过滤器都要通过）
        all_passed = all(r['passed'] for r in results.values())

        return all_passed, total_score, results, all_reasons

    # ========================================================================
    # 示例筛选场景
    # ========================================================================

    def example1_momentum_breakout(self):
        """示例1: 动量突破选股"""
        self.print_separator("示例1: 动量突破选股")

        print("\n【策略说明】")
        print("  寻找技术面突破的强势股")
        print("  适合短期交易")

        # 测试股票池
        stock_pool = [
            '600519',  # 贵州茅台
            '000858',  # 五粮液
            '600036',  # 招商银行
            '601318',  # 中国平安
        ]

        print(f"\n【筛选结果】")
        results = []

        for code in stock_pool:
            passed, score, reason = self.technical_breakout_filter(code)

            if passed:
                # 获取股票名称
                try:
                    stock_list = self.data_provider.get_stock_list()
                    name = stock_list[stock_list['代码'] == code]['名称'].values[0]
                except:
                    name = code

                results.append({
                    'code': code,
                    'name': name,
                    'score': score,
                    'reason': reason
                })

                print(f"\n  ✓ {name}({code})")
                print(f"    评分: {score:.1f}")
                print(f"    理由: {reason}")

        if not results:
            print("  未找到符合条件的股票")

        return results

    def example2_quality_growth(self):
        """示例2: 优质成长股选股"""
        self.print_separator("示例2: 优质成长股选股")

        print("\n【策略说明】")
        print("  寻找基本面优秀的成长股")
        print("  适合中长期投资")

        stock_pool = [
            '600519',  # 贵州茅台
            '000858',  # 五粮液
            '600036',  # 招商银行
        ]

        print(f"\n【筛选结果】")
        results = []

        for code in stock_pool:
            passed, score, reason = self.high_quality_company_filter(code)

            if passed:
                try:
                    stock_list = self.data_provider.get_stock_list()
                    name = stock_list[stock_list['代码'] == code]['名称'].values[0]
                except:
                    name = code

                results.append({
                    'code': code,
                    'name': name,
                    'score': score,
                    'reason': reason
                })

                print(f"\n  ✓ {name}({code})")
                print(f"    评分: {score:.1f}")
                print(f"    理由: {reason}")

        if not results:
            print("  未找到符合条件的股票")

        return results

    def example3_combined_strategy(self):
        """示例3: 组合策略选股"""
        self.print_separator("示例3: 组合策略选股")

        print("\n【策略说明】")
        print("  结合技术面和基本面")
        print("  寻找优质+强势的股票")

        stock_pool = ['600519', '000858', '600036']

        # 定义过滤器组合
        filters = [
            (self.technical_breakout_filter, 'technical'),
            (self.high_quality_company_filter, 'fundamental')
        ]

        # 定义权重
        weights = {
            'technical': 0.4,
            'fundamental': 0.6
        }

        print(f"\n【筛选结果】")
        results = []

        for code in stock_pool:
            all_passed, total_score, details, reasons = self.combined_filter(
                code, filters, weights
            )

            # 即使不是全部通过，评分高的也保留
            if total_score >= 70:
                try:
                    stock_list = self.data_provider.get_stock_list()
                    name = stock_list[stock_list['代码'] == code]['名称'].values[0]
                except:
                    name = code

                results.append({
                    'code': code,
                    'name': name,
                    'score': total_score,
                    'all_passed': all_passed,
                    'details': details
                })

                print(f"\n  {'✓' if all_passed else '○'} {name}({code})")
                print(f"    综合评分: {total_score:.1f}")
                print(f"    技术评分: {details['technical']['score']:.1f}")
                print(f"    基本面评分: {details['fundamental']['score']:.1f}")

        if not results:
            print("  未找到符合条件的股票")

        return results

    def example4_custom_sorting(self):
        """示例4: 自定义排序规则"""
        self.print_separator("示例4: 自定义排序规则")

        print("\n【策略说明】")
        print("  使用自定义规则对股票排序")
        print("  优先技术强+基本面好的股票")

        stock_pool = ['600519', '000858', '600036', '601318']

        print(f"\n【评估股票】")
        stocks_data = []

        for code in stock_pool:
            # 获取技术和基本面评分
            tech_passed, tech_score, tech_reason = self.technical_breakout_filter(code)
            fund_passed, fund_score, fund_reason = self.high_quality_company_filter(code)

            try:
                stock_list = self.data_provider.get_stock_list()
                name = stock_list[stock_list['代码'] == code]['名称'].values[0]
            except:
                name = code

            stocks_data.append({
                'code': code,
                'name': name,
                'tech_score': tech_score,
                'fund_score': fund_score,
                'tech_reason': tech_reason,
                'fund_reason': fund_reason
            })

        # 转换为DataFrame便于排序
        df = pd.DataFrame(stocks_data)

        # 自定义排序规则
        # 规则1: 优先技术面强的
        df['sort_key1'] = df['tech_score'] * 0.6 + df['fund_score'] * 0.4

        # 规则2: 优先基本面好的
        df['sort_key2'] = df['tech_score'] * 0.3 + df['fund_score'] * 0.7

        # 规则3: 均衡排序
        df['sort_key3'] = df['tech_score'] * 0.5 + df['fund_score'] * 0.5

        print("\n【排序结果1】优先技术面 (技术60% + 基本面40%)")
        df_sorted1 = df.sort_values('sort_key1', ascending=False)
        for idx, row in df_sorted1.iterrows():
            print(f"  {row['name']}({row['code']})")
            print(f"    综合分: {row['sort_key1']:.1f}")
            print(f"    技术: {row['tech_score']:.1f}, 基本面: {row['fund_score']:.1f}")

        print("\n【排序结果2】优先基本面 (技术30% + 基本面70%)")
        df_sorted2 = df.sort_values('sort_key2', ascending=False)
        for idx, row in df_sorted2.iterrows():
            print(f"  {row['name']}({row['code']})")
            print(f"    综合分: {row['sort_key2']:.1f}")
            print(f"    技术: {row['tech_score']:.1f}, 基本面: {row['fund_score']:.1f}")

        return df


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" A股量化交易系统 - 自定义筛选示例")
    print(" Custom Screening Example")
    print("=" * 70)

    screener = CustomScreener()

    print("\n本示例展示如何创建自定义筛选条件:")
    print("  1. 技术指标过滤器（突破、趋势）")
    print("  2. 基本面过滤器（质量、估值）")
    print("  3. 组合多个过滤器")
    print("  4. 自定义排序规则")

    try:
        # 示例1: 动量突破
        screener.example1_momentum_breakout()

        # 示例2: 优质成长
        screener.example2_quality_growth()

        # 示例3: 组合策略
        screener.example3_combined_strategy()

        # 示例4: 自定义排序
        screener.example4_custom_sorting()

        print("\n" + "=" * 70)
        print(" 示例完成")
        print("=" * 70)

        print("\n【使用建议】")
        print("  1. 根据自己的交易风格定制过滤器")
        print("  2. 组合多个过滤器提高筛选质量")
        print("  3. 使用自定义排序找到最佳标的")
        print("  4. 定期回测验证筛选效果")

        print("\n【扩展方向】")
        print("  1. 添加更多技术指标（KDJ、布林带等）")
        print("  2. 添加行业、市值等过滤条件")
        print("  3. 实现机器学习评分模型")
        print("  4. 添加实时监控和自动筛选")

    except Exception as e:
        logger.error(f"示例运行失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
        print("注意: 示例需要网络连接以获取数据")


if __name__ == '__main__':
    main()
