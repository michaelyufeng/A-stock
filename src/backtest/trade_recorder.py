"""交易记录分析器 - 用于记录详细的交易信息"""
import backtrader as bt
from typing import List, Dict, Any
from src.core.logger import get_logger

logger = get_logger(__name__)


class TradeRecorder(bt.Analyzer):
    """
    交易记录分析器

    记录每笔交易的详细信息，包括：
    - 入场日期、价格、数量
    - 出场日期、价格
    - 盈亏（PnL）
    - 手续费
    - 交易状态

    用于后续的详细指标计算
    """

    def __init__(self):
        """初始化分析器"""
        super(TradeRecorder, self).__init__()
        self.trades = []
        self.open_trades = {}  # 跟踪未平仓的交易

    def notify_trade(self, trade):
        """
        接收交易通知

        Args:
            trade: backtrader交易对象
        """
        if trade.isclosed:
            # 交易已关闭，记录完整信息
            # 注意: backtrader的trade对象在关闭时，很多信息已经不可用
            # 我们主要记录盈亏和手续费用于指标计算

            trade_info = {
                'entry_date': bt.num2date(trade.dtopen).strftime('%Y-%m-%d'),
                'exit_date': bt.num2date(trade.dtclose).strftime('%Y-%m-%d'),
                'entry_price': trade.price,
                'exit_price': 0,  # backtrader不直接提供，需要从价格历史计算
                'size': trade.barlen,  # 持仓bar数量
                'pnl': trade.pnlcomm,  # 包含手续费的净盈亏
                'commission': trade.commission,
                'status': 'closed'
            }

            self.trades.append(trade_info)

            logger.debug(
                f"交易记录: {trade_info['entry_date']} -> {trade_info['exit_date']}, "
                f"PnL: {trade_info['pnl']:.2f}, "
                f"手续费: {trade_info['commission']:.2f}"
            )

    def get_analysis(self) -> Dict[str, Any]:
        """
        获取分析结果

        Returns:
            包含所有交易记录的字典
        """
        return {
            'trades': self.trades,
            'total_trades': len(self.trades)
        }
