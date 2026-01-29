"""
Test suite for RiskManager class.

Tests cover:
1. Initialization
2. Position limits (single stock, sector, total)
3. Trade restrictions (ST stocks, delisting risk, frequency)
4. Stop loss/take profit calculations
5. Position management
6. Portfolio risk assessment
7. A-share specific features
"""

import pytest
from datetime import datetime, timedelta
from src.risk.risk_manager import RiskManager
import pandas as pd


# ============================================================================
# 1. Initialization Tests (2 tests)
# ============================================================================

def test_init_loads_config():
    """Test RiskManager initializes with correct configuration."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    assert risk_mgr.total_capital == 1_000_000
    assert risk_mgr.config is not None
    assert 'position' in risk_mgr.config
    assert 'stop_loss' in risk_mgr.config


def test_init_empty_positions():
    """Test RiskManager starts with empty positions."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    assert len(risk_mgr.positions) == 0
    assert risk_mgr.get_all_positions() == {}


# ============================================================================
# 2. Position Limit Tests (8 tests)
# ============================================================================

def test_check_single_stock_limit_allowed():
    """Test position check passes when under single stock limit."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Try to buy 15% position (under 20% limit)
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=150_000
    )

    assert result['allowed'] is True
    assert result['max_position_value'] == 200_000  # 20% of 1M


def test_check_single_stock_limit_exceeded():
    """Test position check fails when exceeding single stock limit."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Try to buy 25% position (over 20% limit)
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=250_000
    )

    assert result['allowed'] is False
    assert '单一持仓' in result['reason']
    assert result['max_position_value'] == 200_000


def test_check_sector_limit_allowed():
    """Test sector exposure check passes when under limit."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Add existing 15% position in 白酒
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())

    # Try to add 10% more (total 25%, under 30% sector limit)
    result = risk_mgr.check_position_limit(
        stock_code='000858',
        stock_name='五粮液',
        sector='白酒',
        position_value=100_000
    )

    assert result['allowed'] is True


def test_check_sector_limit_exceeded():
    """Test sector exposure check fails when exceeding limit."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Add existing 20% position in 白酒
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 134, 1500, datetime.now())

    # Try to add 15% more (total 35%, over 30% sector limit)
    result = risk_mgr.check_position_limit(
        stock_code='000858',
        stock_name='五粮液',
        sector='白酒',
        position_value=150_000
    )

    assert result['allowed'] is False
    assert '行业' in result['reason']


def test_check_total_position_limit():
    """Test total position limit is enforced."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Add positions totaling 90%
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 600, 1500, datetime.now())
    risk_mgr.add_position('600036', '招商银行', '银行', 2000, 35, datetime.now())
    risk_mgr.add_position('000858', '五粮液', '白酒', 200, 1500, datetime.now())

    # Try to add 10% more (total 100%, over 95% limit)
    result = risk_mgr.check_position_limit(
        stock_code='601318',
        stock_name='中国平安',
        sector='保险',
        position_value=100_000
    )

    assert result['allowed'] is False
    assert '总仓位' in result['reason']


def test_check_min_position_value():
    """Test minimum position value requirement."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Try to buy 5,000 yuan position (under 10,000 minimum)
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=5_000
    )

    assert result['allowed'] is False
    assert '最小建仓' in result['reason']


def test_position_warning_threshold():
    """Test position warning when approaching limits."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Try 18% position (over 15% warning threshold, under 20% limit)
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=180_000
    )

    assert result['allowed'] is True
    assert len(result['warnings']) > 0
    assert any('接近' in w for w in result['warnings'])


def test_multiple_positions_cumulative():
    """Test position limits consider existing holdings."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Add 12% position
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 80, 1500, datetime.now())

    # Try to add 10% more to same stock (22% total, over limit)
    result = risk_mgr.check_position_limit(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        position_value=100_000
    )

    assert result['allowed'] is False


# ============================================================================
# 3. Trade Restriction Tests (6 tests)
# ============================================================================

def test_block_st_stock():
    """Test ST stocks are blocked from trading."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    st_stocks = ['ST海航', '*ST凯迪', 'SST前锋', 'S*ST昌鱼']

    for stock_name in st_stocks:
        result = risk_mgr.check_trade_restrictions('600000', stock_name)
        assert result['allowed'] is False
        assert 'ST' in result['reason']


def test_allow_normal_stock():
    """Test normal stocks pass trade restrictions."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    result = risk_mgr.check_trade_restrictions('600519', '贵州茅台')

    assert result['allowed'] is True
    assert result['reason'] == ''


def test_block_delisting_risk():
    """Test stocks with delisting risk are blocked."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    result = risk_mgr.check_trade_restrictions('600000', '*ST退市股')

    assert result['allowed'] is False


def test_daily_trade_frequency_limit():
    """Test daily trade frequency limit is enforced."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Make 5 trades today (max limit)
    today = datetime.now()
    for i in range(5):
        code = f'60000{i}'
        risk_mgr.add_position(code, f'股票{i}', '电子', 100, 10, today)
        risk_mgr.remove_position(code, 11, today)

    # Try 6th trade
    result = risk_mgr.check_trade_restrictions('600006', '第六只股票')

    assert result['allowed'] is False
    assert '每日交易次数' in result['reason']


def test_cooling_period_enforced():
    """Test cooling period prevents re-trading too soon."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Buy and sell a stock
    past_date = datetime.now() - timedelta(days=3)
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, past_date)
    risk_mgr.remove_position('600519', 1600, past_date)

    # Try to trade again within 5-day cooling period
    result = risk_mgr.check_trade_restrictions('600519', '贵州茅台')

    assert result['allowed'] is False
    assert '冷却期' in result['reason']


def test_cooling_period_expired():
    """Test cooling period allows trading after expiry."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Buy and sell a stock 6 days ago
    past_date = datetime.now() - timedelta(days=6)
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, past_date)
    risk_mgr.remove_position('600519', 1600, past_date)

    # Should be allowed after 5-day cooling period
    result = risk_mgr.check_trade_restrictions('600519', '贵州茅台')

    assert result['allowed'] is True


# ============================================================================
# 4. Stop Loss / Take Profit Tests (6 tests)
# ============================================================================

def test_calculate_fixed_stop_loss():
    """Test fixed ratio stop loss calculation."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_price = 100.0
    stop_loss = risk_mgr.calculate_stop_loss(entry_price, method='fixed')

    # Default 8% stop loss
    assert stop_loss == pytest.approx(92.0, rel=0.01)


def test_calculate_trailing_stop_loss():
    """Test trailing stop loss calculation."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_price = 100.0
    stop_loss = risk_mgr.calculate_stop_loss(entry_price, method='trailing')

    # Default 5% trailing stop
    assert stop_loss == pytest.approx(95.0, rel=0.01)


def test_calculate_atr_stop_loss():
    """Test ATR-based stop loss calculation."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_price = 100.0
    atr = 3.0  # Average True Range
    stop_loss = risk_mgr.calculate_stop_loss(
        entry_price,
        method='atr',
        atr=atr
    )

    # Default 2.0 ATR multiplier: 100 - (2 * 3) = 94
    assert stop_loss == pytest.approx(94.0, rel=0.01)


def test_calculate_fixed_take_profit():
    """Test fixed ratio take profit calculation."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_price = 100.0
    take_profit = risk_mgr.calculate_take_profit(entry_price, method='fixed')

    # Default 15% take profit
    assert take_profit == pytest.approx(115.0, rel=0.01)


def test_calculate_dynamic_take_profit():
    """Test dynamic take profit calculation."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_price = 100.0
    take_profit = risk_mgr.calculate_take_profit(entry_price, method='dynamic')

    # Dynamic should return higher than fixed
    assert take_profit > 115.0


def test_stop_loss_atr_requires_atr_value():
    """Test ATR stop loss requires ATR parameter."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    with pytest.raises(ValueError, match='ATR'):
        risk_mgr.calculate_stop_loss(100.0, method='atr', atr=None)


# ============================================================================
# 5. Position Management Tests (5 tests)
# ============================================================================

def test_add_position():
    """Test adding a new position."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_date = datetime.now()
    risk_mgr.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1500.0,
        entry_date=entry_date
    )

    position = risk_mgr.get_position('600519')
    assert position is not None
    assert position['stock_name'] == '贵州茅台'
    assert position['shares'] == 100
    assert position['entry_price'] == 1500.0
    assert position['current_value'] == 150_000.0
    assert 'stop_loss_price' in position
    assert 'take_profit_price' in position


def test_remove_position_calculates_pnl():
    """Test removing position calculates profit/loss."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    entry_date = datetime.now() - timedelta(days=10)
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, entry_date)

    exit_date = datetime.now()
    pnl = risk_mgr.remove_position('600519', exit_price=1650, exit_date=exit_date)

    # Profit: (1650 - 1500) * 100 = 15,000
    assert pnl == pytest.approx(15_000, rel=0.01)
    assert risk_mgr.get_position('600519') is None


def test_update_position_current_price():
    """Test updating position with current price."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())

    # Update to new price
    risk_mgr.update_position('600519', current_price=1600)

    position = risk_mgr.get_position('600519')
    assert position['current_price'] == 1600
    assert position['current_value'] == 160_000
    assert position['unrealized_pnl'] == pytest.approx(10_000, rel=0.01)


def test_get_position_nonexistent():
    """Test getting non-existent position returns None."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    position = risk_mgr.get_position('999999')

    assert position is None


def test_get_all_positions_multiple():
    """Test getting all positions returns complete dict."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())
    risk_mgr.add_position('600036', '招商银行', '银行', 1000, 35, datetime.now())

    positions = risk_mgr.get_all_positions()

    assert len(positions) == 2
    assert '600519' in positions
    assert '600036' in positions


# ============================================================================
# 6. Portfolio Risk Assessment Tests (5 tests)
# ============================================================================

def test_assess_empty_portfolio():
    """Test risk assessment of empty portfolio."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    risk = risk_mgr.assess_portfolio_risk()

    assert risk['risk_level'] == 'low'
    assert risk['total_position_pct'] == 0.0
    assert risk['position_count'] == 0
    assert len(risk['warnings']) == 0


def test_assess_low_risk_portfolio():
    """Test low risk portfolio assessment."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Single 10% position
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 67, 1500, datetime.now())

    risk = risk_mgr.assess_portfolio_risk()

    assert risk['risk_level'] == 'low'
    assert risk['total_position_pct'] < 0.15


def test_assess_medium_risk_high_total_position():
    """Test medium risk from high total position."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Add positions totaling 85%
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 333, 1500, datetime.now())
    risk_mgr.add_position('600036', '招商银行', '银行', 5000, 35, datetime.now())
    risk_mgr.add_position('000858', '五粮液', '白酒', 200, 1500, datetime.now())

    risk = risk_mgr.assess_portfolio_risk()

    assert risk['risk_level'] in ['medium', 'high']
    assert risk['total_position_pct'] > 0.70


def test_assess_high_risk_concentration():
    """Test high risk from sector and individual concentration."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # High concentration: 2 stocks in same sector, each near 20%
    risk_mgr.add_position('600519', '贵州茅台', '白酒', 133, 1500, datetime.now())
    risk_mgr.add_position('000858', '五粮液', '白酒', 133, 1500, datetime.now())

    risk = risk_mgr.assess_portfolio_risk()

    assert risk['risk_level'] == 'high'
    assert len(risk['warnings']) > 0
    assert '白酒' in risk['sector_exposure']
    assert risk['sector_exposure']['白酒'] > 0.35


def test_assess_includes_sector_breakdown():
    """Test risk assessment includes sector exposure breakdown."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    risk_mgr.add_position('600519', '贵州茅台', '白酒', 100, 1500, datetime.now())
    risk_mgr.add_position('600036', '招商银行', '银行', 1000, 35, datetime.now())

    risk = risk_mgr.assess_portfolio_risk()

    assert '白酒' in risk['sector_exposure']
    assert '银行' in risk['sector_exposure']
    assert risk['sector_exposure']['白酒'] == pytest.approx(0.15, rel=0.01)
    assert risk['sector_exposure']['银行'] == pytest.approx(0.035, rel=0.01)


# ============================================================================
# 7. A-Share Specific Tests (3 tests)
# ============================================================================

def test_check_continuous_limit_up():
    """Test detection of continuous limit up."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Create DataFrame with 3 consecutive limit ups (10%)
    dates = pd.date_range(end=datetime.now(), periods=5)
    kline_df = pd.DataFrame({
        'open': [100, 110, 121, 133.1, 146.4],
        'close': [110, 121, 133.1, 146.4, 146.4],
        'high': [110, 121, 133.1, 146.4, 146.4],
        'low': [100, 110, 121, 133.1, 146.4],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)

    assert result['continuous_limit_up'] >= 3
    assert result['warning'] is True


def test_check_continuous_limit_down():
    """Test detection of continuous limit down."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Create DataFrame with 3 consecutive limit downs (-10%)
    dates = pd.date_range(end=datetime.now(), periods=5)
    kline_df = pd.DataFrame({
        'open': [100, 90, 81, 72.9, 65.6],
        'close': [90, 81, 72.9, 65.6, 65.6],
        'high': [100, 90, 81, 72.9, 65.6],
        'low': [90, 81, 72.9, 65.6, 65.6],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)

    assert result['continuous_limit_down'] >= 3
    assert result['warning'] is True


def test_check_no_continuous_limit():
    """Test normal trading days show no continuous limits."""
    risk_mgr = RiskManager(total_capital=1_000_000)

    # Normal price fluctuations
    dates = pd.date_range(end=datetime.now(), periods=5)
    kline_df = pd.DataFrame({
        'open': [100, 102, 101, 103, 104],
        'close': [102, 101, 103, 104, 105],
        'high': [103, 103, 104, 105, 106],
        'low': [99, 100, 100, 102, 103],
    }, index=dates)

    result = risk_mgr.check_continuous_limit('600519', kline_df)

    assert result['continuous_limit_up'] == 0
    assert result['continuous_limit_down'] == 0
    assert result['warning'] is False
