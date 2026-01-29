"""
PositionMonitor - 持仓监控器

功能:
1. 整合RiskManager和SignalDetector监控持仓
2. 实时更新持仓价格和盈亏
3. 检测止损止盈触发
4. 评估组合风险健康度
5. 生成持仓监控报告
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.risk.risk_manager import RiskManager
from src.monitoring.signal_detector import SignalDetector, Signal


logger = logging.getLogger(__name__)


class PositionMonitor:
    """持仓监控器 - 监控持仓状态和风险"""

    def __init__(
        self,
        risk_manager: RiskManager,
        signal_detector: SignalDetector
    ):
        """
        初始化持仓监控器

        Args:
            risk_manager: 风险管理器实例
            signal_detector: 信号检测器实例
        """
        self.risk_manager = risk_manager
        self.signal_detector = signal_detector

        logger.info("PositionMonitor initialized")

    # ========================================================================
    # 持仓监控
    # ========================================================================

    def monitor_positions(self, quotes: Optional[Dict[str, Dict]] = None) -> List[Signal]:
        """
        监控所有持仓，检测风险信号

        Args:
            quotes: 实时行情数据 {stock_code: {'current_price': float}}

        Returns:
            检测到的信号列表
        """
        signals = []

        # 获取所有持仓
        positions = self.risk_manager.get_all_positions()

        if not positions:
            logger.debug("No positions to monitor")
            return signals

        # 如果提供了行情数据，先更新价格
        if quotes:
            self.update_position_prices(quotes)

        # 检查每个持仓的风险
        for stock_code in positions.keys():
            position_signals = self.check_position_risks(stock_code)
            signals.extend(position_signals)

        logger.info(f"Monitored {len(positions)} positions, detected {len(signals)} signals")

        return signals

    def check_position_risks(self, stock_code: str) -> List[Signal]:
        """
        检查单个持仓的风险

        Args:
            stock_code: 股票代码

        Returns:
            该持仓的风险信号列表
        """
        signals = []

        # 获取持仓信息
        position = self.risk_manager.get_position(stock_code)

        if not position:
            logger.warning(f"Position not found: {stock_code}")
            return signals

        # 获取当前价格
        current_price = position.get('current_price')

        if not current_price:
            # 如果没有当前价格，尝试获取实时行情
            try:
                quote = self.signal_detector.provider.get_realtime_quote(stock_code)
                if quote and 'current_price' in quote:
                    current_price = quote['current_price']
                    # 更新持仓价格
                    self.risk_manager.update_position(stock_code, current_price)
            except Exception as e:
                logger.error(f"Failed to get quote for {stock_code}: {e}")
                return signals

        if not current_price:
            logger.warning(f"No current price available for {stock_code}")
            return signals

        # 检查止损触发
        stop_loss_signal = self.signal_detector.check_stop_loss_trigger(
            stock_code=stock_code,
            position=position,
            current_price=current_price
        )

        if stop_loss_signal:
            signals.append(stop_loss_signal)

        # 检查止盈触发
        take_profit_signal = self.signal_detector.check_take_profit_trigger(
            stock_code=stock_code,
            position=position,
            current_price=current_price
        )

        if take_profit_signal:
            signals.append(take_profit_signal)

        return signals

    def update_position_prices(self, quotes: Dict[str, Dict]):
        """
        批量更新持仓价格

        Args:
            quotes: 行情数据 {stock_code: {'current_price': float}}
        """
        updated_count = 0

        for stock_code, quote in quotes.items():
            if 'current_price' in quote:
                try:
                    current_price = float(quote['current_price'])
                    self.risk_manager.update_position(stock_code, current_price)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update price for {stock_code}: {e}")

        logger.debug(f"Updated prices for {updated_count} positions")

    # ========================================================================
    # 止损止盈检查
    # ========================================================================

    def check_stop_loss_all(self) -> List[Signal]:
        """
        检查所有持仓的止损触发

        Returns:
            止损信号列表
        """
        signals = []

        positions = self.risk_manager.get_all_positions()

        for stock_code, position in positions.items():
            current_price = position.get('current_price')

            if not current_price:
                logger.warning(f"No current price for {stock_code}, skipping stop loss check")
                continue

            signal = self.signal_detector.check_stop_loss_trigger(
                stock_code=stock_code,
                position=position,
                current_price=current_price
            )

            if signal:
                signals.append(signal)

        logger.info(f"Checked stop loss for {len(positions)} positions, {len(signals)} triggered")

        return signals

    def check_take_profit_all(self) -> List[Signal]:
        """
        检查所有持仓的止盈触发

        Returns:
            止盈信号列表
        """
        signals = []

        positions = self.risk_manager.get_all_positions()

        for stock_code, position in positions.items():
            current_price = position.get('current_price')

            if not current_price:
                logger.warning(f"No current price for {stock_code}, skipping take profit check")
                continue

            signal = self.signal_detector.check_take_profit_trigger(
                stock_code=stock_code,
                position=position,
                current_price=current_price
            )

            if signal:
                signals.append(signal)

        logger.info(f"Checked take profit for {len(positions)} positions, {len(signals)} triggered")

        return signals

    # ========================================================================
    # 风险评估
    # ========================================================================

    def assess_portfolio_health(self) -> Dict:
        """
        评估组合整体健康状况

        Returns:
            健康评估结果
        """
        positions = self.risk_manager.get_all_positions()

        if not positions:
            return {
                'risk_level': 'low',
                'total_value': 0,
                'total_profit_loss': 0,
                'total_profit_loss_pct': 0,
                'position_count': 0,
                'positions_at_risk': 0,
                'warnings': []
            }

        # 计算总市值和盈亏
        total_value = 0
        total_cost = 0
        positions_at_risk = 0
        warnings = []

        for stock_code, position in positions.items():
            current_price = position.get('current_price', position.get('entry_price'))
            shares = position.get('shares', 0)
            entry_price = position.get('entry_price', 0)

            position_value = current_price * shares
            position_cost = entry_price * shares

            total_value += position_value
            total_cost += position_cost

            # 检查止损风险
            stop_loss_price = position.get('stop_loss_price')
            if stop_loss_price and current_price <= stop_loss_price * 1.02:  # 接近止损价（2%内）
                positions_at_risk += 1
                warnings.append(f"{position.get('stock_name', stock_code)} 接近止损位")

        # 计算总盈亏
        total_profit_loss = total_value - total_cost
        total_profit_loss_pct = (total_profit_loss / total_cost) if total_cost > 0 else 0

        # 使用RiskManager的风险评估
        portfolio_risk = self.risk_manager.assess_portfolio_risk()

        # 综合判断风险级别
        risk_level = portfolio_risk.get('risk_level', 'medium')

        # 如果有持仓接近止损，提升风险级别
        if positions_at_risk > 0:
            if risk_level == 'low':
                risk_level = 'medium'
            elif risk_level == 'medium':
                risk_level = 'high'

        # 如果总体亏损超过5%，提升风险级别
        if total_profit_loss_pct < -0.05:
            if risk_level == 'low':
                risk_level = 'medium'
            elif risk_level == 'medium':
                risk_level = 'high'

        return {
            'risk_level': risk_level,
            'total_value': total_value,
            'total_cost': total_cost,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_pct': total_profit_loss_pct,
            'position_count': len(positions),
            'positions_at_risk': positions_at_risk,
            'warnings': warnings,
            'portfolio_risk': portfolio_risk
        }

    def generate_position_report(self) -> str:
        """
        生成持仓监控报告

        Returns:
            格式化的报告文本
        """
        positions = self.risk_manager.get_all_positions()

        if not positions:
            return self._generate_empty_report()

        # 评估组合健康度
        health = self.assess_portfolio_health()

        # 构建报告
        lines = []
        lines.append("=" * 60)
        lines.append("  持仓监控报告")
        lines.append("=" * 60)
        lines.append("")

        # 组合概览
        lines.append("【组合概览】")
        lines.append(f"持仓数量: {health['position_count']} 只")
        lines.append(f"总市值: ¥{health['total_value']:,.2f}")
        lines.append(f"总成本: ¥{health['total_cost']:,.2f}")
        lines.append(f"浮动盈亏: ¥{health['total_profit_loss']:,.2f} ({health['total_profit_loss_pct']:.2%})")
        lines.append(f"风险级别: {health['risk_level'].upper()}")

        if health['positions_at_risk'] > 0:
            lines.append(f"⚠️  风险持仓: {health['positions_at_risk']} 只")

        lines.append("")

        # 持仓明细
        lines.append("【持仓明细】")
        lines.append("")

        for stock_code, position in positions.items():
            lines.append(f"股票: {position.get('stock_name', stock_code)} ({stock_code})")

            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', entry_price)
            shares = position.get('shares', 0)

            position_value = current_price * shares
            position_cost = entry_price * shares
            profit_loss = position_value - position_cost
            profit_loss_pct = (profit_loss / position_cost) if position_cost > 0 else 0

            lines.append(f"  成本价: ¥{entry_price:.2f} | 现价: ¥{current_price:.2f}")
            lines.append(f"  持仓: {shares} 股 | 市值: ¥{position_value:,.2f}")
            lines.append(f"  盈亏: ¥{profit_loss:,.2f} ({profit_loss_pct:+.2%})")

            # 止损止盈信息
            if 'stop_loss_price' in position:
                stop_loss_price = position['stop_loss_price']
                stop_loss_dist = (current_price - stop_loss_price) / current_price
                lines.append(f"  止损价: ¥{stop_loss_price:.2f} (距离: {stop_loss_dist:.2%})")

            if 'take_profit_price' in position:
                take_profit_price = position['take_profit_price']
                take_profit_dist = (take_profit_price - current_price) / current_price
                lines.append(f"  止盈价: ¥{take_profit_price:.2f} (距离: {take_profit_dist:.2%})")

            # 持仓天数
            if 'entry_date' in position:
                holding_days = (datetime.now() - position['entry_date']).days
                lines.append(f"  持仓天数: {holding_days} 天")

            lines.append("")

        # 风险提示
        if health['warnings']:
            lines.append("【风险提示】")
            for warning in health['warnings']:
                lines.append(f"⚠️  {warning}")
            lines.append("")

        # 报告时间
        lines.append(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_empty_report(self) -> str:
        """生成空持仓报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("  持仓监控报告")
        lines.append("=" * 60)
        lines.append("")
        lines.append("【组合概览】")
        lines.append("持仓数量: 0 只")
        lines.append("总市值: ¥0.00")
        lines.append("状态: 空仓")
        lines.append("")
        lines.append(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        return "\n".join(lines)
