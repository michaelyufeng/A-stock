"""
Risk Manager - 风险管理器

功能:
1. 仓位管理（单一股票、行业、总仓位限制）
2. 止损止盈计算
3. 交易限制检查（ST股、退市风险股、交易频率）
4. 持仓管理（添加、移除、更新）
5. 组合风险评估
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path
import pandas as pd

from src.core.constants import ST_PATTERNS


class RiskManager:
    """风险管理器 - 仓位控制和风险评估"""

    def __init__(self, total_capital: float):
        """
        初始化风险管理器

        Args:
            total_capital: 总资金
        """
        self.total_capital = total_capital
        self.positions: Dict[str, Dict] = {}  # 当前持仓
        self.trade_history: List[Dict] = []  # 交易历史
        self.closed_positions: Dict[str, List[Dict]] = {}  # 已平仓记录

        # 加载配置
        self._load_config()

    def _load_config(self):
        """加载风控配置"""
        config_path = Path(__file__).parent.parent.parent / "config" / "risk_rules.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    # ========================================================================
    # 仓位检查模块
    # ========================================================================

    def check_position_limit(
        self,
        stock_code: str,
        stock_name: str,
        sector: str,
        position_value: float
    ) -> Dict[str, Any]:
        """
        检查仓位限制

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            sector: 所属行业
            position_value: 拟建仓金额

        Returns:
            {
                'allowed': bool,
                'reason': str,
                'max_position_value': float,
                'warnings': List[str]
            }
        """
        warnings = []

        # 1. 检查最小建仓金额
        min_value = self.config['position']['min_position_value']
        if position_value < min_value:
            return {
                'allowed': False,
                'reason': f'最小建仓金额为{min_value}元',
                'max_position_value': 0,
                'warnings': []
            }

        # 2. 计算单一持仓限制
        max_single_pct = self.config['position']['max_single_position']
        max_single_value = self.total_capital * max_single_pct

        # 如果已有该股票持仓，累加计算
        existing_position = self.positions.get(stock_code)
        total_stock_value = position_value
        if existing_position:
            total_stock_value += existing_position['current_value']

        if total_stock_value > max_single_value:
            return {
                'allowed': False,
                'reason': f'单一持仓超过限制{max_single_pct*100}%',
                'max_position_value': max_single_value,
                'warnings': []
            }

        # 检查单一持仓预警阈值
        warning_pct = self.config['alerts']['position_concentration']['warning']
        if total_stock_value / self.total_capital > warning_pct:
            warnings.append(f'单一持仓接近警戒线({warning_pct*100}%)')

        # 3. 检查行业集中度
        max_sector_pct = self.config['position']['max_sector_exposure']
        sector_value = position_value

        # 累加同行业现有持仓
        for pos in self.positions.values():
            if pos['sector'] == sector:
                sector_value += pos['current_value']

        if sector_value / self.total_capital > max_sector_pct:
            return {
                'allowed': False,
                'reason': f'行业集中度超过限制{max_sector_pct*100}%',
                'max_position_value': max_single_value,
                'warnings': warnings
            }

        # 4. 检查总仓位限制
        max_total_pct = self.config['position']['max_total_position']
        total_position_value = position_value + sum(
            pos['current_value'] for pos in self.positions.values()
        )

        if total_position_value / self.total_capital > max_total_pct:
            return {
                'allowed': False,
                'reason': f'总仓位超过限制{max_total_pct*100}%',
                'max_position_value': max_single_value,
                'warnings': warnings
            }

        return {
            'allowed': True,
            'reason': '',
            'max_position_value': max_single_value,
            'warnings': warnings
        }

    # ========================================================================
    # 交易限制模块
    # ========================================================================

    def check_trade_restrictions(
        self,
        stock_code: str,
        stock_name: str
    ) -> Dict[str, Any]:
        """
        检查交易限制

        Args:
            stock_code: 股票代码
            stock_name: 股票名称

        Returns:
            {
                'allowed': bool,
                'reason': str
            }
        """
        # 1. 检查ST股
        if self._is_st_stock(stock_name):
            return {
                'allowed': False,
                'reason': 'ST股禁止交易'
            }

        # 2. 检查交易频率
        if not self._check_trading_frequency():
            return {
                'allowed': False,
                'reason': '每日交易次数超过限制'
            }

        # 3. 检查冷却期
        if not self._check_cooling_period(stock_code):
            return {
                'allowed': False,
                'reason': f'冷却期内，需等待{self.config["trading_limits"]["cooling_period"]}天'
            }

        return {
            'allowed': True,
            'reason': ''
        }

    def _is_st_stock(self, stock_name: str) -> bool:
        """判断是否为ST股"""
        for pattern in ST_PATTERNS:
            if pattern in stock_name:
                return True
        return False

    def _check_trading_frequency(self) -> bool:
        """检查交易频率限制"""
        max_daily = self.config['trading_limits']['max_trades_per_day']
        today = datetime.now().date()

        # 计算今日交易次数
        today_trades = sum(
            1 for trade in self.trade_history
            if trade['date'].date() == today
        )

        return today_trades < max_daily

    def _check_cooling_period(self, stock_code: str) -> bool:
        """检查冷却期"""
        cooling_days = self.config['trading_limits']['cooling_period']

        # 检查是否有该股票的已平仓记录
        if stock_code not in self.closed_positions:
            return True

        # 获取最近一次平仓时间
        last_close = self.closed_positions[stock_code][-1]
        last_close_date = last_close['exit_date']

        days_passed = (datetime.now() - last_close_date).days

        return days_passed >= cooling_days

    # ========================================================================
    # 止损止盈计算模块
    # ========================================================================

    def calculate_stop_loss(
        self,
        entry_price: float,
        method: str = 'fixed',
        atr: Optional[float] = None
    ) -> float:
        """
        计算止损价

        Args:
            entry_price: 入场价格
            method: 止损方式 (fixed/trailing/atr)
            atr: ATR值（method='atr'时必需）

        Returns:
            止损价格
        """
        if method == 'fixed':
            ratio = self.config['stop_loss']['fixed_ratio']
            return entry_price * (1 - ratio)

        elif method == 'trailing':
            ratio = self.config['stop_loss']['trailing_ratio']
            return entry_price * (1 - ratio)

        elif method == 'atr':
            if atr is None:
                raise ValueError('ATR方法需要提供atr参数')
            multiplier = self.config['stop_loss']['atr_multiplier']
            return entry_price - (atr * multiplier)

        else:
            raise ValueError(f'未知的止损方法: {method}')

    def calculate_take_profit(
        self,
        entry_price: float,
        method: str = 'fixed'
    ) -> float:
        """
        计算止盈价

        Args:
            entry_price: 入场价格
            method: 止盈方式 (fixed/dynamic)

        Returns:
            止盈价格
        """
        if method == 'fixed':
            ratio = self.config['take_profit']['fixed_ratio']
            return entry_price * (1 + ratio)

        elif method == 'dynamic':
            # 动态止盈使用更高的目标
            ratio = self.config['take_profit']['fixed_ratio'] * 1.5
            return entry_price * (1 + ratio)

        else:
            raise ValueError(f'未知的止盈方法: {method}')

    # ========================================================================
    # 持仓管理模块
    # ========================================================================

    def add_position(
        self,
        stock_code: str,
        stock_name: str,
        sector: str,
        shares: int,
        entry_price: float,
        entry_date: datetime
    ):
        """
        添加持仓

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            sector: 所属行业
            shares: 股数
            entry_price: 入场价格
            entry_date: 入场日期
        """
        position_value = shares * entry_price

        # 计算止损止盈
        stop_loss_price = self.calculate_stop_loss(entry_price)
        take_profit_price = self.calculate_take_profit(entry_price)

        self.positions[stock_code] = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'sector': sector,
            'shares': shares,
            'entry_price': entry_price,
            'entry_date': entry_date,
            'current_price': entry_price,
            'current_value': position_value,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'unrealized_pnl': 0.0
        }

        # 记录交易历史
        self.trade_history.append({
            'date': entry_date,
            'type': 'buy',
            'stock_code': stock_code,
            'shares': shares,
            'price': entry_price
        })

    def remove_position(
        self,
        stock_code: str,
        exit_price: float,
        exit_date: datetime
    ) -> float:
        """
        移除持仓并计算盈亏

        Args:
            stock_code: 股票代码
            exit_price: 卖出价格
            exit_date: 卖出日期

        Returns:
            盈亏金额
        """
        position = self.positions.pop(stock_code)

        # 计算盈亏
        pnl = (exit_price - position['entry_price']) * position['shares']

        # 保存已平仓记录
        if stock_code not in self.closed_positions:
            self.closed_positions[stock_code] = []

        self.closed_positions[stock_code].append({
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'shares': position['shares'],
            'pnl': pnl
        })

        # 记录交易历史
        self.trade_history.append({
            'date': exit_date,
            'type': 'sell',
            'stock_code': stock_code,
            'shares': position['shares'],
            'price': exit_price
        })

        return pnl

    def update_position(
        self,
        stock_code: str,
        current_price: float
    ):
        """
        更新持仓市值

        Args:
            stock_code: 股票代码
            current_price: 当前价格
        """
        position = self.positions.get(stock_code)
        if position is None:
            return

        position['current_price'] = current_price
        position['current_value'] = current_price * position['shares']
        position['unrealized_pnl'] = (
            (current_price - position['entry_price']) * position['shares']
        )

    def get_position(self, stock_code: str) -> Optional[Dict]:
        """
        获取单个持仓详情

        Args:
            stock_code: 股票代码

        Returns:
            持仓信息或None
        """
        return self.positions.get(stock_code)

    def get_all_positions(self) -> Dict[str, Dict]:
        """获取所有持仓"""
        return self.positions.copy()

    # ========================================================================
    # 风险评估模块
    # ========================================================================

    def assess_portfolio_risk(self) -> Dict[str, Any]:
        """
        评估组合风险

        Returns:
            {
                'risk_level': 'low'|'medium'|'high',
                'warnings': List[str],
                'total_position_pct': float,
                'sector_exposure': Dict[str, float],
                'position_count': int
            }
        """
        if not self.positions:
            return {
                'risk_level': 'low',
                'warnings': [],
                'total_position_pct': 0.0,
                'sector_exposure': {},
                'position_count': 0
            }

        warnings = []

        # 1. 计算总仓位
        total_value = sum(pos['current_value'] for pos in self.positions.values())
        total_pct = total_value / self.total_capital

        # 2. 计算行业分布
        sector_exposure = {}
        for pos in self.positions.values():
            sector = pos['sector']
            value = pos['current_value']
            pct = value / self.total_capital

            sector_exposure[sector] = sector_exposure.get(sector, 0) + pct

        # 3. 检查个股集中度
        max_single_pct = self.config['position']['max_single_position']
        critical_pct = self.config['alerts']['position_concentration']['critical']

        for pos in self.positions.values():
            pos_pct = pos['current_value'] / self.total_capital
            if pos_pct >= critical_pct:
                warnings.append(f'{pos["stock_name"]}持仓过于集中({pos_pct*100:.1f}%)')

        # 4. 检查行业集中度
        max_sector_pct = self.config['position']['max_sector_exposure']
        for sector, pct in sector_exposure.items():
            if pct >= max_sector_pct * 0.9:  # 90%阈值
                warnings.append(f'{sector}行业集中度过高({pct*100:.1f}%)')

        # 5. 检查总仓位
        if total_pct > 0.85:
            warnings.append(f'总仓位过高({total_pct*100:.1f}%)')

        # 6. 确定风险等级
        risk_level = 'low'

        if total_pct > 0.70 or len(warnings) > 0:
            risk_level = 'medium'

        if (
            max(sector_exposure.values(), default=0) > max_sector_pct * 0.8
            or any(
                pos['current_value'] / self.total_capital > critical_pct
                for pos in self.positions.values()
            )
        ):
            risk_level = 'high'

        return {
            'risk_level': risk_level,
            'warnings': warnings,
            'total_position_pct': total_pct,
            'sector_exposure': sector_exposure,
            'position_count': len(self.positions)
        }

    # ========================================================================
    # A股特色检查
    # ========================================================================

    def check_continuous_limit(
        self,
        stock_code: str,
        kline_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        检查连续涨跌停

        Args:
            stock_code: 股票代码
            kline_df: K线数据 (必须包含 open, close, high, low列)

        Returns:
            {
                'continuous_limit_up': int,
                'continuous_limit_down': int,
                'warning': bool
            }
        """
        if len(kline_df) < 2:
            return {
                'continuous_limit_up': 0,
                'continuous_limit_down': 0,
                'warning': False
            }

        # 计算每日涨跌幅
        kline_df = kline_df.copy()
        kline_df['pct_change'] = (
            (kline_df['close'] - kline_df['close'].shift(1))
            / kline_df['close'].shift(1)
        )

        # 判断涨跌停（主板10%，创业板/科创板20%）
        # 这里简化处理，统一使用10%作为阈值
        limit_threshold = 0.098  # 略小于10%，考虑浮点误差

        # 统计连续涨停
        continuous_up = 0
        max_continuous_up = 0

        for pct in kline_df['pct_change'].dropna():
            if pct >= limit_threshold:
                continuous_up += 1
                max_continuous_up = max(max_continuous_up, continuous_up)
            else:
                continuous_up = 0

        # 统计连续跌停
        continuous_down = 0
        max_continuous_down = 0

        for pct in kline_df['pct_change'].dropna():
            if pct <= -limit_threshold:
                continuous_down += 1
                max_continuous_down = max(max_continuous_down, continuous_down)
            else:
                continuous_down = 0

        # 检查是否超过配置的阈值
        max_allowed = self.config['trade_restrictions']['max_continuous_limit']
        warning = (max_continuous_up >= max_allowed or max_continuous_down >= max_allowed)

        return {
            'continuous_limit_up': max_continuous_up,
            'continuous_limit_down': max_continuous_down,
            'warning': warning
        }
