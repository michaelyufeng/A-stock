"""回测指标计算模块 - 详细的回测性能指标分析"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from src.core.logger import get_logger

logger = get_logger(__name__)


class BacktestMetrics:
    """
    回测指标计算器

    提供全面的回测性能评估指标，包括：
    1. 收益指标：总收益率、年化收益率、月度收益等
    2. 风险指标：最大回撤、波动率、夏普比率等
    3. 交易指标：胜率、盈亏比、持仓天数等
    4. A股特色指标：费用分析等

    Attributes:
        portfolio_values: 每日资产价值序列（索引为日期）
        trades: 交易记录DataFrame
        initial_capital: 初始资金
        final_capital: 最终资金
    """

    def __init__(
        self,
        portfolio_values: pd.Series,
        trades: Union[List[Dict], pd.DataFrame],
        initial_capital: float
    ):
        """
        初始化指标计算器

        Args:
            portfolio_values: 每日资产价值序列（索引为日期）
            trades: 交易记录列表或DataFrame
            initial_capital: 初始资金
        """
        self.portfolio_values = portfolio_values
        self.trades = pd.DataFrame(trades) if isinstance(trades, list) else trades
        self.initial_capital = initial_capital
        self.final_capital = portfolio_values.iloc[-1] if len(portfolio_values) > 0 else initial_capital

        logger.info(
            f"指标计算器初始化 - "
            f"初始资金: {initial_capital:,.2f}, "
            f"最终资金: {self.final_capital:,.2f}, "
            f"交易次数: {len(self.trades)}"
        )

    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        计算所有指标

        Returns:
            包含所有指标的字典
        """
        logger.info("开始计算所有指标...")

        metrics = {
            # 收益指标
            'total_return': self.calculate_total_return(),
            'annual_return': self.calculate_annual_return(),
            'monthly_returns': self.calculate_monthly_returns(),

            # 风险指标
            'max_drawdown': self.calculate_max_drawdown(),
            'volatility': self.calculate_volatility(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'calmar_ratio': self.calculate_calmar_ratio(),

            # 交易指标
            'total_trades': self.calculate_total_trades(),
            'win_rate': self.calculate_win_rate(),
            'profit_loss_ratio': self.calculate_profit_loss_ratio(),
            'avg_holding_days': self.calculate_avg_holding_days(),
            'max_consecutive_wins': self.calculate_max_consecutive_wins(),
            'max_consecutive_losses': self.calculate_max_consecutive_losses(),

            # A股特色
            'total_fees': self.calculate_total_fees(),
            'fee_percentage': self.calculate_fee_percentage(),
        }

        logger.info("指标计算完成")
        return metrics

    def calculate_total_return(self) -> float:
        """
        计算总收益率

        Returns:
            总收益率（小数形式，如0.15表示15%）
        """
        if self.initial_capital == 0:
            return 0.0
        return (self.final_capital - self.initial_capital) / self.initial_capital

    def calculate_annual_return(self) -> float:
        """
        计算年化收益率

        使用复合年化收益率公式: (1 + total_return) ^ (1/years) - 1

        Returns:
            年化收益率（小数形式）
        """
        if len(self.portfolio_values) < 2:
            return 0.0

        days = (self.portfolio_values.index[-1] - self.portfolio_values.index[0]).days
        if days == 0:
            return 0.0

        years = days / 365.0
        total_return = self.calculate_total_return()

        # 年化公式: (1 + total_return) ^ (1/years) - 1
        return (1 + total_return) ** (1 / years) - 1

    def calculate_monthly_returns(self) -> pd.Series:
        """
        计算月度收益率

        Returns:
            月度收益率序列
        """
        if len(self.portfolio_values) < 2:
            return pd.Series()

        # 重采样为月度（取月末值）
        monthly_values = self.portfolio_values.resample('ME').last()

        # 计算月度收益率
        monthly_returns = monthly_values.pct_change().dropna()

        return monthly_returns

    def calculate_max_drawdown(self) -> Dict[str, Any]:
        """
        计算最大回撤

        Returns:
            字典包含：
            - drawdown_pct: 最大回撤百分比
            - drawdown_amount: 最大回撤金额
            - start_date: 回撤开始日期（峰值日期）
            - end_date: 回撤结束日期（谷值日期）
        """
        if len(self.portfolio_values) < 2:
            return {
                'drawdown_pct': 0,
                'drawdown_amount': 0,
                'start_date': None,
                'end_date': None
            }

        # 计算累计最大值
        cummax = self.portfolio_values.cummax()

        # 计算回撤
        drawdown = (self.portfolio_values - cummax) / cummax

        # 找到最大回撤
        max_dd_idx = drawdown.idxmin()
        max_dd_pct = drawdown.min()
        max_dd_amount = (self.portfolio_values[max_dd_idx] - cummax[max_dd_idx])

        # 找到回撤开始日期（峰值日期）
        start_idx = cummax[:max_dd_idx].idxmax() if max_dd_idx in cummax.index else None

        return {
            'drawdown_pct': abs(max_dd_pct),
            'drawdown_amount': abs(max_dd_amount),
            'start_date': start_idx,
            'end_date': max_dd_idx
        }

    def calculate_volatility(self) -> float:
        """
        计算年化波动率（标准差）

        A股使用252个交易日作为年化因子

        Returns:
            年化波动率
        """
        if len(self.portfolio_values) < 2:
            return 0.0

        # 计算日收益率
        daily_returns = self.portfolio_values.pct_change().dropna()

        # 年化波动率 = 日波动率 * sqrt(252)
        return daily_returns.std() * np.sqrt(252)

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率

        Args:
            risk_free_rate: 无风险利率，默认3%

        Returns:
            夏普比率
        """
        annual_return = self.calculate_annual_return()
        volatility = self.calculate_volatility()

        if volatility == 0:
            return 0.0

        return (annual_return - risk_free_rate) / volatility

    def calculate_sortino_ratio(self, risk_free_rate: float = 0.03) -> float:
        """
        计算索提诺比率（只考虑下行波动）

        与夏普比率不同，索提诺比率只惩罚下行波动，
        更适合评估风险厌恶型投资者的策略

        Args:
            risk_free_rate: 无风险利率，默认3%

        Returns:
            索提诺比率
        """
        if len(self.portfolio_values) < 2:
            return 0.0

        # 计算日收益率
        daily_returns = self.portfolio_values.pct_change().dropna()

        # 只取负收益
        downside_returns = daily_returns[daily_returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        # 下行波动率
        downside_std = downside_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return 0.0

        annual_return = self.calculate_annual_return()

        return (annual_return - risk_free_rate) / downside_std

    def calculate_calmar_ratio(self) -> float:
        """
        计算Calmar比率（年化收益/最大回撤）

        衡量收益相对于最大回撤的比率，
        值越大说明在控制回撤的同时获得更高收益

        Returns:
            Calmar比率
        """
        annual_return = self.calculate_annual_return()
        max_dd = self.calculate_max_drawdown()

        if max_dd['drawdown_pct'] == 0:
            return 0.0

        return annual_return / max_dd['drawdown_pct']

    def calculate_total_trades(self) -> int:
        """
        计算总交易次数

        只计算已完成（closed）的交易

        Returns:
            总交易次数
        """
        if self.trades.empty:
            return 0

        # 只计算完整的买卖对
        closed_trades = self.trades[self.trades.get('status', 'closed') == 'closed']
        return len(closed_trades)

    def calculate_win_rate(self) -> float:
        """
        计算胜率（盈利交易/总交易）

        Returns:
            胜率（0到1之间的小数）
        """
        if self.trades.empty:
            return 0.0

        closed_trades = self.trades[self.trades.get('status', 'closed') == 'closed']
        if len(closed_trades) == 0:
            return 0.0

        winning_trades = len(closed_trades[closed_trades.get('pnl', 0) > 0])

        return winning_trades / len(closed_trades)

    def calculate_profit_loss_ratio(self) -> float:
        """
        计算盈亏比（平均盈利/平均亏损）

        Returns:
            盈亏比，如果没有亏损交易返回inf，如果没有盈利交易返回0
        """
        if self.trades.empty:
            return 0.0

        closed_trades = self.trades[self.trades.get('status', 'closed') == 'closed']
        if len(closed_trades) == 0:
            return 0.0

        winning_trades = closed_trades[closed_trades.get('pnl', 0) > 0]
        losing_trades = closed_trades[closed_trades.get('pnl', 0) < 0]

        if len(losing_trades) == 0:
            return float('inf') if len(winning_trades) > 0 else 0.0

        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = abs(losing_trades['pnl'].mean())

        if avg_loss == 0:
            return 0.0

        return avg_win / avg_loss

    def calculate_avg_holding_days(self) -> float:
        """
        计算平均持仓天数

        Returns:
            平均持仓天数
        """
        if self.trades.empty or 'entry_date' not in self.trades.columns:
            return 0.0

        closed_trades = self.trades[self.trades.get('status', 'closed') == 'closed']
        if len(closed_trades) == 0:
            return 0.0

        # 计算持仓天数
        holding_days = (
            pd.to_datetime(closed_trades['exit_date']) -
            pd.to_datetime(closed_trades['entry_date'])
        ).dt.days

        return holding_days.mean()

    def calculate_max_consecutive_wins(self) -> int:
        """
        计算最大连续盈利次数

        Returns:
            最大连续盈利次数
        """
        return self._calculate_max_consecutive('win')

    def calculate_max_consecutive_losses(self) -> int:
        """
        计算最大连续亏损次数

        Returns:
            最大连续亏损次数
        """
        return self._calculate_max_consecutive('loss')

    def _calculate_max_consecutive(self, type: str) -> int:
        """
        计算最大连续次数

        Args:
            type: 'win' 或 'loss'

        Returns:
            最大连续次数
        """
        if self.trades.empty:
            return 0

        closed_trades = self.trades[self.trades.get('status', 'closed') == 'closed']
        if len(closed_trades) == 0:
            return 0

        # 判断盈亏
        if type == 'win':
            results = (closed_trades.get('pnl', 0) > 0).astype(int)
        else:
            results = (closed_trades.get('pnl', 0) < 0).astype(int)

        # 计算连续次数
        max_consecutive = 0
        current_consecutive = 0

        for result in results:
            if result == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def calculate_total_fees(self) -> float:
        """
        计算总交易费用

        Returns:
            总费用（包括佣金和印花税）
        """
        if self.trades.empty or 'commission' not in self.trades.columns:
            return 0.0

        return self.trades['commission'].sum()

    def calculate_fee_percentage(self) -> float:
        """
        计算费用占总资产的百分比

        Returns:
            费用占比
        """
        total_fees = self.calculate_total_fees()

        if self.initial_capital == 0:
            return 0.0

        return total_fees / self.initial_capital

    def generate_equity_curve_data(self) -> pd.DataFrame:
        """
        生成权益曲线数据

        Returns:
            包含日期、资产价值、收益率、累计收益率的DataFrame
        """
        df = pd.DataFrame({
            'date': self.portfolio_values.index,
            'value': self.portfolio_values.values
        })

        # 添加收益率
        df['return'] = df['value'].pct_change()

        # 添加累计收益率
        df['cumulative_return'] = (df['value'] / self.initial_capital - 1)

        return df

    def generate_drawdown_curve_data(self) -> pd.DataFrame:
        """
        生成回撤曲线数据

        Returns:
            包含日期和回撤的DataFrame
        """
        cummax = self.portfolio_values.cummax()
        drawdown = (self.portfolio_values - cummax) / cummax

        df = pd.DataFrame({
            'date': drawdown.index,
            'drawdown': drawdown.values
        })

        return df

    def format_summary(self) -> str:
        """
        格式化输出摘要

        Returns:
            格式化的摘要字符串
        """
        metrics = self.calculate_all_metrics()

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                      回测结果摘要                              ║
╠══════════════════════════════════════════════════════════════╣
║ 初始资金: ¥{self.initial_capital:,.2f}
║ 最终资金: ¥{self.final_capital:,.2f}
║ 总收益率: {metrics['total_return']:.2%}
║ 年化收益: {metrics['annual_return']:.2%}
╠══════════════════════════════════════════════════════════════╣
║ 最大回撤: {metrics['max_drawdown']['drawdown_pct']:.2%}
║ 波动率: {metrics['volatility']:.2%}
║ 夏普比率: {metrics['sharpe_ratio']:.4f}
║ 索提诺比率: {metrics['sortino_ratio']:.4f}
║ Calmar比率: {metrics['calmar_ratio']:.4f}
╠══════════════════════════════════════════════════════════════╣
║ 总交易次数: {metrics['total_trades']}
║ 胜率: {metrics['win_rate']:.2%}
║ 盈亏比: {metrics['profit_loss_ratio']:.2f}
║ 平均持仓: {metrics['avg_holding_days']:.1f}天
║ 最大连胜: {metrics['max_consecutive_wins']}次
║ 最大连亏: {metrics['max_consecutive_losses']}次
╠══════════════════════════════════════════════════════════════╣
║ 总费用: ¥{metrics['total_fees']:,.2f}
║ 费用占比: {metrics['fee_percentage']:.2%}
╚══════════════════════════════════════════════════════════════╝
        """

        return summary
