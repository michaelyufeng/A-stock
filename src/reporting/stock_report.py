"""股票分析报告生成器"""
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from src.core.logger import get_logger

logger = get_logger(__name__)


class StockReportGenerator:
    """股票分析报告生成器，生成Markdown格式的综合分析报告"""

    # 权重配置（与StockRater保持一致）
    WEIGHTS = {
        'technical': 30,
        'fundamental': 30,
        'capital': 25,
        'sentiment': 15
    }

    def __init__(self):
        """初始化报告生成器"""
        logger.info("Initializing StockReportGenerator...")

    def generate_report(
        self,
        stock_code: str,
        stock_name: str,
        analysis_result: Dict[str, Any],
        kline_df: Optional[pd.DataFrame] = None,
        save_to_file: bool = False,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成综合Markdown报告

        Args:
            stock_code: 股票代码（如 "000001"）
            stock_name: 股票名称（如 "平安银行"）
            analysis_result: StockRater.analyze_stock()的结果
            kline_df: 可选的K线数据，用于额外上下文
            save_to_file: 是否保存到文件
            output_path: 保存文件的路径

        Returns:
            Markdown格式的报告字符串
        """
        logger.info(f"Generating report for {stock_code} {stock_name}...")

        # 构建报告各部分
        sections = []

        # 1. 标题和时间戳
        sections.append(self._format_header(stock_code, stock_name))

        # 2. 投资决策
        sections.append(self._format_decision_section(stock_code, stock_name, analysis_result))

        # 3. 核心理由
        sections.append(self._format_reasons_section(analysis_result))

        # 4. 风险提示
        sections.append(self._format_risks_section(analysis_result))

        # 5. 详细分析
        sections.append(self._format_detailed_analysis_header())
        sections.append(self._format_technical_section(analysis_result, kline_df))
        sections.append(self._format_fundamental_section(analysis_result))
        sections.append(self._format_capital_section(analysis_result))

        # 6. AI综合分析
        sections.append(self._format_ai_section(analysis_result))

        # 7. 综合评分
        sections.append(self._format_scores_table(analysis_result))

        # 8. 免责声明
        sections.append(self._format_disclaimer())

        # 合并所有部分
        report = '\n\n'.join(sections)

        # 保存到文件
        if save_to_file:
            self._save_to_file(report, stock_code, output_path)

        logger.info(f"Report generated successfully for {stock_code}")
        return report

    def _format_header(self, stock_code: str, stock_name: str) -> str:
        """
        格式化报告标题

        Args:
            stock_code: 股票代码
            stock_name: 股票名称

        Returns:
            标题部分的Markdown文本
        """
        timestamp = self._format_timestamp()
        return f"# 股票分析报告 - {stock_code} {stock_name}\n\n生成时间: {timestamp}"

    def _format_decision_section(
        self,
        stock_code: str,
        stock_name: str,
        analysis_result: Dict[str, Any]
    ) -> str:
        """
        格式化投资决策部分

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            analysis_result: 分析结果

        Returns:
            投资决策部分的Markdown文本
        """
        rating = self._translate_rating(analysis_result['rating'])
        confidence = analysis_result['confidence']
        target_price = analysis_result['target_price']
        stop_loss = analysis_result['stop_loss']

        return f"""## 📊 投资决策

- **股票代码**: {stock_code}
- **股票名称**: {stock_name}
- **评级**: {rating}
- **目标价**: {target_price:.2f}元
- **止损价**: {stop_loss:.2f}元
- **信心度**: {confidence}/10"""

    def _format_reasons_section(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化核心理由部分

        Args:
            analysis_result: 分析结果

        Returns:
            核心理由部分的Markdown文本
        """
        reasons = analysis_result.get('reasons', [])

        if not reasons:
            return "## 💡 核心理由\n\n暂无详细理由。"

        reasons_list = '\n'.join([f"{i+1}. {reason}" for i, reason in enumerate(reasons)])

        return f"## 💡 核心理由\n\n{reasons_list}"

    def _format_risks_section(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化风险提示部分

        Args:
            analysis_result: 分析结果

        Returns:
            风险提示部分的Markdown文本
        """
        general_risks = analysis_result.get('risks', [])
        a_share_risks = analysis_result.get('a_share_risks', [])

        sections = ["## ⚠️ 风险提示"]

        # 通用风险
        if general_risks:
            sections.append("### 通用风险")
            risks_list = '\n'.join([f"- {risk}" for risk in general_risks])
            sections.append(risks_list)

        # A股特色风险
        if a_share_risks:
            sections.append("### A股特色风险")
            a_risks_list = '\n'.join([f"- {risk}" for risk in a_share_risks])
            sections.append(a_risks_list)

        return '\n\n'.join(sections)

    def _format_detailed_analysis_header(self) -> str:
        """
        格式化详细分析标题

        Returns:
            详细分析标题的Markdown文本
        """
        return "## 📈 详细分析"

    def _format_technical_section(
        self,
        analysis_result: Dict[str, Any],
        kline_df: Optional[pd.DataFrame]
    ) -> str:
        """
        格式化技术面分析部分

        Args:
            analysis_result: 分析结果
            kline_df: K线数据

        Returns:
            技术面分析部分的Markdown文本
        """
        technical_score = analysis_result['scores']['technical']
        score_rating = self._interpret_score(technical_score)

        sections = ["### 技术面分析"]

        # 如果有K线数据，生成详细的技术指标表格
        if kline_df is not None and not kline_df.empty:
            table = self._create_technical_table(kline_df)
            sections.append(table)

        # 添加评分
        sections.append(f"**技术面评分**: {technical_score}/100 ({score_rating})")

        return '\n\n'.join(sections)

    def _format_fundamental_section(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化基本面分析部分

        Args:
            analysis_result: 分析结果

        Returns:
            基本面分析部分的Markdown文本
        """
        fundamental_score = analysis_result['scores']['fundamental']
        score_rating = self._interpret_score(fundamental_score)

        return f"""### 基本面分析

基本面指标综合评估结果显示，该股票财务状况{score_rating}。

**基本面评分**: {fundamental_score}/100 ({score_rating})"""

    def _format_capital_section(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化资金面分析部分

        Args:
            analysis_result: 分析结果

        Returns:
            资金面分析部分的Markdown文本
        """
        capital_score = analysis_result['scores']['capital']
        score_rating = self._interpret_score(capital_score)

        return f"""### 资金面分析

资金流向和市场情绪分析显示，当前资金状况{score_rating}。

**资金面评分**: {capital_score}/100 ({score_rating})"""

    def _format_ai_section(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化AI分析部分

        Args:
            analysis_result: 分析结果

        Returns:
            AI分析部分的Markdown文本
        """
        ai_insights = analysis_result.get('ai_insights', '暂无AI分析。')

        return f"## 🤖 AI综合分析\n\n{ai_insights}"

    def _format_scores_table(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化综合评分表格

        Args:
            analysis_result: 分析结果

        Returns:
            综合评分表格的Markdown文本
        """
        scores = analysis_result['scores']

        table = """## 📊 综合评分

| 维度 | 评分 | 权重 |
|------|------|------|
| 技术面 | {} | 30% |
| 基本面 | {} | 30% |
| 资金面 | {} | 25% |
| 情绪面 | - | 15% |
| **总分** | **{}** | **100%** |""".format(
            scores['technical'],
            scores['fundamental'],
            scores['capital'],
            scores['overall']
        )

        return table

    def _format_disclaimer(self) -> str:
        """
        格式化免责声明

        Returns:
            免责声明的Markdown文本
        """
        return """---

*免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。*"""

    def _create_technical_table(self, kline_df: pd.DataFrame) -> str:
        """
        创建技术指标表格

        Args:
            kline_df: K线数据

        Returns:
            技术指标表格的Markdown文本
        """
        if kline_df.empty or len(kline_df) == 0:
            return "技术指标数据不足。"

        # 获取最新一行数据
        latest = kline_df.iloc[-1]

        table_rows = []
        table_rows.append("| 指标 | 数值 | 评价 |")
        table_rows.append("|------|------|------|")

        # MA5/MA20
        if 'MA5' in kline_df.columns and 'MA20' in kline_df.columns:
            ma5 = latest['MA5']
            ma20 = latest['MA20']
            close = latest.get('close', 0)
            if ma5 > ma20 and close > ma5:
                evaluation = "金叉向上"
            elif ma5 < ma20:
                evaluation = "死叉向下"
            else:
                evaluation = "震荡"
            table_rows.append(f"| MA5/MA20 | {ma5:.2f}/{ma20:.2f} | {evaluation} |")

        # MACD
        if 'MACD' in kline_df.columns and 'MACD_signal' in kline_df.columns:
            macd = latest['MACD']
            signal = latest['MACD_signal']
            if macd > signal and macd > 0:
                evaluation = "多头强势"
            elif macd > signal:
                evaluation = "多头"
            else:
                evaluation = "空头"
            table_rows.append(f"| MACD | {macd:.4f} | {evaluation} |")

        # RSI
        if 'RSI' in kline_df.columns:
            rsi = latest['RSI']
            if rsi >= 70:
                evaluation = "超买"
            elif rsi <= 30:
                evaluation = "超卖"
            else:
                evaluation = "中性"
            table_rows.append(f"| RSI | {rsi:.2f} | {evaluation} |")

        # KDJ
        if 'K' in kline_df.columns and 'D' in kline_df.columns:
            k = latest['K']
            d = latest['D']
            if k > d and k < 80:
                evaluation = "金叉"
            elif k > 80:
                evaluation = "超买"
            else:
                evaluation = "死叉"
            table_rows.append(f"| KDJ | K:{k:.2f} D:{d:.2f} | {evaluation} |")

        # 布林带
        if 'BOLL_UPPER' in kline_df.columns and 'BOLL_LOWER' in kline_df.columns:
            upper = latest['BOLL_UPPER']
            lower = latest['BOLL_LOWER']
            middle = latest.get('BOLL_MIDDLE', (upper + lower) / 2)
            close = latest.get('close', 0)
            if close > upper:
                evaluation = "超买区"
            elif close < lower:
                evaluation = "超卖区"
            elif close > middle:
                evaluation = "上轨区"
            else:
                evaluation = "下轨区"
            table_rows.append(f"| 布林带 | 上:{upper:.2f} 中:{middle:.2f} 下:{lower:.2f} | {evaluation} |")

        # 成交量
        if 'volume' in kline_df.columns and 'VOL_MA5' in kline_df.columns:
            volume = latest['volume']
            vol_ma5 = latest['VOL_MA5']
            if volume > vol_ma5 * 1.5:
                evaluation = "大幅放量"
            elif volume > vol_ma5:
                evaluation = "放量"
            else:
                evaluation = "缩量"
            table_rows.append(f"| 成交量 | {volume/10000:.2f}万 | {evaluation} |")

        # ATR
        if 'ATR' in kline_df.columns:
            atr = latest['ATR']
            close = latest.get('close', 1)
            atr_ratio = (atr / close * 100) if close > 0 else 0
            if atr_ratio < 3:
                evaluation = "低波动"
            elif atr_ratio < 5:
                evaluation = "中波动"
            else:
                evaluation = "高波动"
            table_rows.append(f"| ATR | {atr:.2f} ({atr_ratio:.2f}%) | {evaluation} |")

        return '\n'.join(table_rows)

    def _translate_rating(self, rating: str) -> str:
        """
        翻译评级为中文

        Args:
            rating: 英文评级

        Returns:
            中文评级
        """
        rating_map = {
            'buy': '买入',
            'hold': '持有',
            'sell': '卖出'
        }
        return rating_map.get(rating, rating)

    def _interpret_score(self, score: float) -> str:
        """
        解释分数等级

        Args:
            score: 分数（0-100）

        Returns:
            分数等级描述
        """
        if score >= 80:
            return '优秀'
        elif score >= 65:
            return '良好'
        elif score >= 45:
            return '一般'
        else:
            return '较差'

    def _format_timestamp(self) -> str:
        """
        格式化当前时间戳

        Returns:
            格式化的时间字符串
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _save_to_file(self, report: str, stock_code: str, output_path: Optional[str] = None) -> None:
        """
        保存报告到文件

        Args:
            report: 报告内容
            stock_code: 股票代码
            output_path: 输出路径
        """
        if output_path is None:
            # 使用默认路径
            output_path = Path.cwd() / f'stock_report_{stock_code}.md'
        else:
            output_path = Path(output_path)

        # 确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        output_path.write_text(report, encoding='utf-8')
        logger.info(f"Report saved to {output_path}")
