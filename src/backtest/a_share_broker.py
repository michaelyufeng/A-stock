"""A股市场券商模拟 - 自定义Broker实现A股特色规则"""
import backtrader as bt
from src.core.logger import get_logger
from src.core.constants import (
    MAIN_BOARD_LIMIT,
    STAR_MARKET_LIMIT,
    GEM_LIMIT,
    MIN_LOT,
    COMMISSION_RATE,
    STAMP_TAX_RATE,
    MARKET_PREFIX
)

logger = get_logger(__name__)


class AShareBroker(bt.brokers.BrokerBack):
    """
    A股市场券商模拟

    实现A股特色规则：
    1. 涨跌停限制（主板±10%，创业板/科创板±20%）
    2. T+1交易制度（在策略层面实现）
    3. 最小交易单位（100股整数倍）
    4. 印花税（仅卖出时收取0.1%）

    Attributes:
        stock_code: 股票代码，用于识别板块
        limit_ratio: 涨跌停限制比例
    """

    def __init__(self, stock_code: str = None, **kwargs):
        """
        初始化A股Broker

        Args:
            stock_code: 股票代码，用于识别板块（主板/创业板/科创板）
            **kwargs: 传递给父类的参数
        """
        super().__init__(**kwargs)
        self.stock_code = stock_code
        self.limit_ratio = self._get_limit_ratio()

        logger.info(
            f"A股Broker初始化 - "
            f"股票代码: {stock_code or '未指定'}, "
            f"涨跌停限制: {self.limit_ratio:.0%}"
        )

    def _get_limit_ratio(self) -> float:
        """
        根据股票代码获取涨跌停限制

        Returns:
            涨跌停限制比例（0.10 或 0.20）
        """
        if not self.stock_code:
            logger.debug("未指定股票代码，使用默认主板涨跌停限制")
            return MAIN_BOARD_LIMIT  # 默认主板

        # 科创板 688xxx
        if any(self.stock_code.startswith(p) for p in MARKET_PREFIX['STAR']):
            logger.debug(f"识别为科创板: {self.stock_code}")
            return STAR_MARKET_LIMIT  # 20%

        # 创业板 300xxx
        if any(self.stock_code.startswith(p) for p in MARKET_PREFIX['GEM']):
            logger.debug(f"识别为创业板: {self.stock_code}")
            return GEM_LIMIT  # 20%

        # 默认主板（600xxx, 601xxx, 603xxx, 605xxx, 000xxx, 001xxx）
        logger.debug(f"识别为主板: {self.stock_code}")
        return MAIN_BOARD_LIMIT  # 10%

    def _get_limit_price(self, prev_close: float) -> tuple:
        """
        计算涨跌停价格

        Args:
            prev_close: 前一日收盘价

        Returns:
            (涨停价, 跌停价)
        """
        limit_up = prev_close * (1 + self.limit_ratio)
        limit_down = prev_close * (1 - self.limit_ratio)
        return limit_up, limit_down

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None, parent=None,
            transmit=True, **kwargs):
        """
        买入订单（覆盖父类方法）

        添加A股限制：
        1. 涨停板不能买入（价格接近涨停价时拒绝）
        2. 数量必须是100股整数倍（自动向下取整）

        Args:
            owner: 订单所有者（策略）
            data: 数据源
            size: 买入数量
            price: 限价（可选）
            **其他参数: 传递给父类

        Returns:
            订单对象或None（拒绝订单时）
        """
        # 1. 调整数量为100股整数倍
        if size % MIN_LOT != 0:
            original_size = size
            size = (size // MIN_LOT) * MIN_LOT
            logger.debug(f"买入数量调整: {original_size} → {size} 股")

        if size <= 0:
            logger.warning(f"买入数量不足100股（调整后: {size}），订单拒绝")
            return None

        # 2. 检查涨停限制（仅限价单需要检查）
        if price is not None:
            prev_close = data.close[-1]  # 前一日收盘价
            limit_up, _ = self._get_limit_price(prev_close)

            # 价格接近涨停（留0.99容差避免浮点数误差）
            if price >= limit_up * 0.99:
                logger.warning(
                    f"买入价格 {price:.2f} 接近涨停价 {limit_up:.2f}，订单拒绝"
                )
                return None

        # 3. 调用父类方法执行订单
        return super().buy(
            owner, data, size, price, plimit,
            exectype, valid, tradeid, oco,
            trailamount, trailpercent, parent,
            transmit, **kwargs
        )

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None, parent=None,
             transmit=True, **kwargs):
        """
        卖出订单（覆盖父类方法）

        添加A股限制：
        1. 跌停板不能卖出（价格接近跌停价时拒绝）
        2. 数量必须是100股整数倍（自动向下取整）
        3. 印花税在_getcommission中计算

        Args:
            owner: 订单所有者（策略）
            data: 数据源
            size: 卖出数量
            price: 限价（可选）
            **其他参数: 传递给父类

        Returns:
            订单对象或None（拒绝订单时）
        """
        # 1. 调整数量为100股整数倍
        if size % MIN_LOT != 0:
            original_size = size
            size = (size // MIN_LOT) * MIN_LOT
            logger.debug(f"卖出数量调整: {original_size} → {size} 股")

        if size <= 0:
            logger.warning(f"卖出数量不足100股（调整后: {size}），订单拒绝")
            return None

        # 2. 检查跌停限制（仅限价单需要检查）
        if price is not None:
            prev_close = data.close[-1]  # 前一日收盘价
            _, limit_down = self._get_limit_price(prev_close)

            # 价格接近跌停（留1.01容差避免浮点数误差）
            if price <= limit_down * 1.01:
                logger.warning(
                    f"卖出价格 {price:.2f} 接近跌停价 {limit_down:.2f}，订单拒绝"
                )
                return None

        # 3. 调用父类方法执行订单
        return super().sell(
            owner, data, size, price, plimit,
            exectype, valid, tradeid, oco,
            trailamount, trailpercent, parent,
            transmit, **kwargs
        )

    def _getcommission(self, size, price, pseudoexec):
        """
        计算佣金和印花税（覆盖父类方法）

        A股费用结构：
        - 佣金: 买卖双向收取，0.03%，最低5元
        - 印花税: 仅卖出收取，0.1%
        - 过户费: 忽略（金额很小）

        Args:
            size: 交易数量（正数=买入，负数=卖出）
            price: 交易价格
            pseudoexec: 是否伪执行

        Returns:
            总费用（佣金 + 印花税）
        """
        # 基础佣金（双向）
        commission = abs(size) * price * COMMISSION_RATE
        commission = max(commission, 5.0)  # 最低5元

        # 卖出时加上印花税
        if size < 0:  # 卖出
            stamp_tax = abs(size) * price * STAMP_TAX_RATE
            total_commission = commission + stamp_tax
            logger.debug(
                f"卖出费用: 佣金 {commission:.2f} 元 + "
                f"印花税 {stamp_tax:.2f} 元 = "
                f"总计 {total_commission:.2f} 元"
            )
            return total_commission
        else:  # 买入
            logger.debug(f"买入佣金: {commission:.2f} 元")
            return commission
