"""回测引擎模块 - 基于backtrader的A股回测系统"""
import backtrader as bt
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List, Type
from src.core.logger import get_logger
from src.core.constants import (
    DEFAULT_CAPITAL,
    COMMISSION_RATE,
    STAMP_TAX_RATE,
    SignalType
)
from src.strategy.base_strategy import BaseStrategy

logger = get_logger(__name__)


class BacktestEngine:
    """
    回测引擎 - 封装backtrader框架，提供简单易用的回测接口

    功能：
    1. 支持单股票回测
    2. A股特色规则（T+1、涨跌停、交易费用）
    3. 策略集成（BaseStrategy及其子类）
    4. 结果输出（收益、夏普比率、最大回撤等）

    Attributes:
        initial_cash: 初始资金
        commission: 佣金率
        stamp_tax: 印花税率
        cerebro: backtrader引擎实例
    """

    def __init__(
        self,
        initial_cash: float = DEFAULT_CAPITAL,
        commission: float = COMMISSION_RATE,
        stamp_tax: float = STAMP_TAX_RATE
    ):
        """
        初始化回测引擎

        Args:
            initial_cash: 初始资金，默认100万
            commission: 佣金率，默认0.0003
            stamp_tax: 印花税率（仅卖出），默认0.001
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.stamp_tax = stamp_tax
        self.cerebro = None

        logger.info(
            f"回测引擎初始化完成 - "
            f"初始资金: {initial_cash:,.0f}, "
            f"佣金率: {commission:.4%}, "
            f"印花税率: {stamp_tax:.4%}"
        )

    def run_backtest(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行回测

        Args:
            strategy_class: 策略类（继承自BaseStrategy）
            data: K线数据DataFrame（需包含OHLCV）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）

        Returns:
            回测结果字典：
            {
                'initial_value': 初始资金,
                'final_value': 最终资金,
                'total_return': 总收益率,
                'sharpe_ratio': 夏普比率,
                'max_drawdown': 最大回撤,
                'total_trades': 总交易次数,
                'win_rate': 胜率
            }
        """
        logger.info("=" * 60)
        logger.info("开始回测")
        logger.info(f"策略: {strategy_class.__name__}")
        logger.info(f"数据量: {len(data)} 条")
        if start_date:
            logger.info(f"开始日期: {start_date}")
        if end_date:
            logger.info(f"结束日期: {end_date}")
        logger.info("=" * 60)

        # 1. 创建Cerebro引擎
        self.cerebro = bt.Cerebro()

        # 2. 设置初始资金
        self.cerebro.broker.setcash(self.initial_cash)

        # 3. 设置佣金（A股特色）
        # 注意：backtrader的佣金是双向的，我们设置总佣金率
        # 印花税只在卖出时收取，这里先设置基础佣金
        total_commission = self.commission
        self.cerebro.broker.setcommission(
            commission=total_commission,
            stocklike=True,
            percabs=True  # 百分比佣金
        )

        # 4. 准备并添加数据
        bt_data = self._prepare_data(data, start_date, end_date)
        self.cerebro.adddata(bt_data)

        # 5. 预先生成所有交易信号（关键：策略转换方案1）
        signals_df = self._generate_all_signals(strategy_class, data, start_date, end_date)

        # 6. 添加策略（将BaseStrategy转换为backtrader策略）
        bt_strategy = self._convert_strategy(strategy_class, signals_df)
        self.cerebro.addstrategy(bt_strategy)

        # 7. 添加分析器
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 8. 记录初始资金
        initial_value = self.cerebro.broker.getvalue()
        logger.info(f"初始资金: {initial_value:,.2f}")

        # 9. 运行回测
        logger.info("开始执行回测...")
        results = self.cerebro.run()

        # 10. 获取最终资金
        final_value = self.cerebro.broker.getvalue()
        logger.info(f"最终资金: {final_value:,.2f}")
        logger.info(f"收益率: {(final_value - initial_value) / initial_value:.2%}")

        # 11. 提取结果
        backtest_results = self._extract_results(results[0], initial_value, final_value)

        logger.info("=" * 60)
        logger.info("回测完成")
        logger.info("=" * 60)

        return backtest_results

    def _prepare_data(
        self,
        df: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> bt.feeds.PandasData:
        """
        准备backtrader数据源

        Args:
            df: 原始K线数据
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            backtrader数据源对象
        """
        # 标准化列名
        df = df.copy()
        df = self._standardize_columns(df)

        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("数据必须包含'date'列或DatetimeIndex")

        # 过滤日期范围
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        if len(df) == 0:
            raise ValueError("过滤后数据为空，请检查日期范围")

        logger.info(f"数据准备完成 - 数据量: {len(df)}, 日期范围: {df.index[0]} 至 {df.index[-1]}")

        # 创建backtrader数据源
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为日期
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1  # A股没有持仓量
        )

        return data

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名（中文→英文）

        Args:
            df: 原始DataFrame

        Returns:
            列名标准化后的DataFrame
        """
        column_map = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        }
        return df.rename(columns=column_map)

    def _generate_all_signals(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        预先生成所有交易信号（方案1的核心）

        这是解决BaseStrategy(pandas)和backtrader(逐bar)转换的关键：
        1. 实例化BaseStrategy
        2. 调用generate_signals()生成所有信号
        3. 返回带信号的DataFrame供backtrader查询

        Args:
            strategy_class: 策略类
            data: K线数据
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含信号列的DataFrame
        """
        logger.info("预先生成交易信号...")

        # 标准化数据
        df = data.copy()
        df = self._standardize_columns(df)

        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # 过滤日期
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        # 实例化策略并生成信号
        strategy = strategy_class()
        signals_df = strategy.generate_signals(df)

        # 统计信号
        buy_count = (signals_df['signal'] == SignalType.BUY.value).sum()
        sell_count = (signals_df['signal'] == SignalType.SELL.value).sum()
        hold_count = (signals_df['signal'] == SignalType.HOLD.value).sum()

        logger.info(
            f"信号生成完成 - "
            f"买入: {buy_count}, 卖出: {sell_count}, 持有: {hold_count}"
        )

        return signals_df

    def _convert_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        signals_df: pd.DataFrame
    ) -> Type[bt.Strategy]:
        """
        将BaseStrategy转换为backtrader策略

        核心转换逻辑：
        1. 预先生成所有信号（已在_generate_all_signals中完成）
        2. 在backtrader的next()中查询对应日期的信号
        3. 根据信号执行买卖操作
        4. 应用T+1规则、止损止盈等

        Args:
            strategy_class: BaseStrategy子类
            signals_df: 预先生成的信号DataFrame

        Returns:
            backtrader策略类
        """
        # 保存外部变量的引用
        signals = signals_df
        base_strategy_class = strategy_class

        class BTStrategy(bt.Strategy):
            """Backtrader策略包装器"""

            def __init__(self):
                """初始化策略"""
                # 实例化原始策略（用于访问参数和方法）
                self.base_strategy = base_strategy_class()

                # 交易状态
                self.order = None
                self.buy_date = None
                self.entry_price = None

                logger.info(f"Backtrader策略包装器初始化: {base_strategy_class.__name__}")

            def next(self):
                """
                每个bar执行一次

                逻辑：
                1. 获取当前日期的信号
                2. 未持仓时，检查买入信号
                3. 持仓时，检查卖出信号（T+1、止损止盈）
                """
                # 如果有未完成订单，等待
                if self.order:
                    return

                # 获取当前日期和价格
                current_date = self.data.datetime.date(0)
                current_price = self.data.close[0]

                # 查询当前日期的信号
                try:
                    # 将当前日期转换为pandas Timestamp进行查询
                    current_timestamp = pd.Timestamp(current_date)

                    if current_timestamp in signals.index:
                        signal = signals.loc[current_timestamp, 'signal']
                    else:
                        signal = SignalType.HOLD.value

                except Exception as e:
                    logger.debug(f"查询信号失败 {current_date}: {e}")
                    signal = SignalType.HOLD.value

                # 未持仓 - 检查买入信号
                if not self.position:
                    if signal == SignalType.BUY.value:
                        # 计算可买数量（使用95%资金，留5%作为手续费缓冲）
                        available_cash = self.broker.getcash() * 0.95
                        size = int(available_cash / current_price / 100) * 100  # A股按手交易

                        if size >= 100:  # 至少1手
                            self.order = self.buy(size=size)
                            self.buy_date = current_date
                            self.entry_price = current_price
                            logger.info(
                                f"买入信号 - {current_date} "
                                f"价格: {current_price:.2f} "
                                f"数量: {size}"
                            )

                # 持仓中 - 检查卖出条件
                else:
                    should_sell = False
                    sell_reason = ""

                    # 1. 检查T+1规则
                    if not self.base_strategy.can_sell_today(
                        pd.Timestamp(self.buy_date),
                        pd.Timestamp(current_date)
                    ):
                        return  # T+1限制，不能卖出

                    # 2. 检查信号卖出
                    if signal == SignalType.SELL.value:
                        should_sell = True
                        sell_reason = "信号卖出"

                    # 3. 检查止损
                    elif self.base_strategy.check_stop_loss(self.entry_price, current_price):
                        should_sell = True
                        sell_reason = "止损"

                    # 4. 检查止盈
                    elif self.base_strategy.check_take_profit(self.entry_price, current_price):
                        should_sell = True
                        sell_reason = "止盈"

                    # 5. 检查最大持仓天数
                    elif self.base_strategy.check_max_holding_days(
                        pd.Timestamp(self.buy_date),
                        pd.Timestamp(current_date)
                    ):
                        should_sell = True
                        sell_reason = "超过最大持仓天数"

                    # 执行卖出
                    if should_sell:
                        self.order = self.sell(size=self.position.size)
                        profit_pct = (current_price - self.entry_price) / self.entry_price
                        logger.info(
                            f"卖出 ({sell_reason}) - {current_date} "
                            f"买入价: {self.entry_price:.2f} "
                            f"卖出价: {current_price:.2f} "
                            f"收益率: {profit_pct:.2%}"
                        )

            def notify_order(self, order):
                """订单状态通知"""
                if order.status in [order.Completed]:
                    if order.isbuy():
                        logger.debug(
                            f"订单执行: 买入 {order.executed.size} 股 "
                            f"@ {order.executed.price:.2f}"
                        )
                    elif order.issell():
                        logger.debug(
                            f"订单执行: 卖出 {order.executed.size} 股 "
                            f"@ {order.executed.price:.2f}"
                        )

                    # 重置订单
                    self.order = None

                elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                    logger.warning(f"订单未执行: {order.status}")
                    self.order = None

        return BTStrategy

    def _extract_results(
        self,
        strategy,
        initial_value: float,
        final_value: float
    ) -> Dict[str, Any]:
        """
        提取回测结果

        Args:
            strategy: backtrader策略实例
            initial_value: 初始资金
            final_value: 最终资金

        Returns:
            回测结果字典
        """
        # 获取分析器结果
        sharpe_analysis = strategy.analyzers.sharpe.get_analysis()
        drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
        returns_analysis = strategy.analyzers.returns.get_analysis()
        trades_analysis = strategy.analyzers.trades.get_analysis()

        # 计算收益率
        total_return = (final_value - initial_value) / initial_value

        # 提取夏普比率
        sharpe_ratio = sharpe_analysis.get('sharperatio', 0)
        if sharpe_ratio is None:
            sharpe_ratio = 0

        # 提取最大回撤
        max_drawdown = 0.0
        if hasattr(drawdown_analysis, 'max') and hasattr(drawdown_analysis.max, 'drawdown'):
            max_drawdown = drawdown_analysis.max.drawdown / 100 if drawdown_analysis.max.drawdown else 0.0

        # 提取交易统计
        total_trades = 0
        win_rate = 0

        try:
            if hasattr(trades_analysis, 'total'):
                total = getattr(trades_analysis, 'total', None)
                if total and hasattr(total, 'closed'):
                    total_trades = total.closed

                    if total_trades > 0 and hasattr(trades_analysis, 'won'):
                        won = getattr(trades_analysis, 'won', None)
                        if won and hasattr(won, 'total'):
                            won_trades = won.total
                            win_rate = won_trades / total_trades
        except (KeyError, AttributeError):
            # 如果没有交易,分析器可能没有这些字段
            pass

        results = {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate
        }

        # 打印结果摘要
        logger.info("=" * 60)
        logger.info("回测结果摘要")
        logger.info("-" * 60)
        logger.info(f"初始资金: {initial_value:,.2f}")
        logger.info(f"最终资金: {final_value:,.2f}")
        logger.info(f"总收益率: {total_return:.2%}")
        logger.info(f"夏普比率: {sharpe_ratio:.4f}")
        logger.info(f"最大回撤: {max_drawdown:.2%}")
        logger.info(f"总交易次数: {total_trades}")
        logger.info(f"胜率: {win_rate:.2%}")
        logger.info("=" * 60)

        return results

    def plot_results(self, output_path: Optional[str] = None):
        """
        绘制回测结果图表

        Args:
            output_path: 输出路径（可选）

        Note:
            需要先运行run_backtest()
        """
        if self.cerebro is None:
            logger.warning("请先运行回测")
            return

        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端

            # 绘制图表
            figs = self.cerebro.plot(style='candlestick', iplot=False)

            # 保存图表
            if output_path and figs:
                figs[0][0].savefig(output_path)
                logger.info(f"回测图表已保存至: {output_path}")

        except Exception as e:
            logger.error(f"绘制图表失败: {e}")
