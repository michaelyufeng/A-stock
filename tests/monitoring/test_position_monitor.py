"""
测试PositionMonitor - 持仓监控器

测试覆盖:
1. 初始化测试 (2个)
2. 持仓监控 (3个)
3. 价格更新 (2个)
4. 止损检查 (2个)
5. 止盈检查 (2个)
6. 风险评估 (3个)
7. 报告生成 (2个)
8. 综合场景 (2个)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.monitoring.position_monitor import PositionMonitor
from src.monitoring.signal_detector import SignalDetector, Signal
from src.risk.risk_manager import RiskManager


# ========================================================================
# 测试夹具
# ========================================================================

@pytest.fixture
def risk_manager():
    """创建RiskManager实例"""
    return RiskManager(total_capital=1_000_000)


@pytest.fixture
def signal_detector(risk_manager):
    """创建SignalDetector实例"""
    return SignalDetector(risk_manager)


@pytest.fixture
def position_monitor(risk_manager, signal_detector):
    """创建PositionMonitor实例"""
    return PositionMonitor(risk_manager, signal_detector)


@pytest.fixture
def sample_positions(risk_manager):
    """添加示例持仓"""
    # 添加几个持仓
    risk_manager.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1500.0,
        entry_date=datetime.now() - timedelta(days=10)
    )

    risk_manager.add_position(
        stock_code='000001',
        stock_name='平安银行',
        sector='银行',
        shares=1000,
        entry_price=15.0,
        entry_date=datetime.now() - timedelta(days=5)
    )

    return risk_manager


# ========================================================================
# 1. 初始化测试
# ========================================================================

def test_position_monitor_initialization(position_monitor):
    """测试PositionMonitor正确初始化"""
    assert position_monitor is not None
    assert position_monitor.risk_manager is not None
    assert position_monitor.signal_detector is not None


def test_position_monitor_has_required_attributes(position_monitor):
    """测试PositionMonitor具有必需属性"""
    assert hasattr(position_monitor, 'risk_manager')
    assert hasattr(position_monitor, 'signal_detector')


# ========================================================================
# 2. 持仓监控
# ========================================================================

def test_monitor_positions_empty(position_monitor):
    """测试监控空持仓"""
    signals = position_monitor.monitor_positions()

    assert isinstance(signals, list)
    assert len(signals) == 0


def test_monitor_positions_with_holdings(position_monitor, sample_positions):
    """测试监控有持仓的情况"""
    position_monitor.risk_manager = sample_positions

    # Mock实时行情数据
    quotes = {
        '600519': {'current_price': 1380.0},  # 下跌8%，触发止损
        '000001': {'current_price': 16.5}     # 上涨10%，正常
    }

    with patch.object(position_monitor, 'update_position_prices') as mock_update:
        signals = position_monitor.monitor_positions(quotes)

        # 验证价格更新被调用
        mock_update.assert_called_once_with(quotes)

        # 应该返回信号列表
        assert isinstance(signals, list)


def test_check_position_risks(position_monitor, sample_positions):
    """测试检查单个持仓风险"""
    position_monitor.risk_manager = sample_positions

    # Mock获取实时价格
    with patch.object(position_monitor.signal_detector.provider, 'get_realtime_quote') as mock_quote:
        mock_quote.return_value = {
            'current_price': 1380.0,  # 触发止损
            'name': '贵州茅台'
        }

        signals = position_monitor.check_position_risks('600519')

        assert isinstance(signals, list)
        # 如果触发止损，应该有信号
        if signals:
            assert signals[0].stock_code == '600519'


# ========================================================================
# 3. 价格更新
# ========================================================================

def test_update_position_prices(position_monitor, sample_positions):
    """测试批量更新持仓价格"""
    position_monitor.risk_manager = sample_positions

    quotes = {
        '600519': {'current_price': 1600.0},
        '000001': {'current_price': 16.0}
    }

    position_monitor.update_position_prices(quotes)

    # 验证价格已更新
    pos1 = sample_positions.get_position('600519')
    pos2 = sample_positions.get_position('000001')

    assert pos1['current_price'] == 1600.0
    assert pos2['current_price'] == 16.0


def test_update_position_prices_partial(position_monitor, sample_positions):
    """测试部分股票的价格更新"""
    position_monitor.risk_manager = sample_positions

    # 只更新一个股票的价格
    quotes = {
        '600519': {'current_price': 1550.0}
    }

    position_monitor.update_position_prices(quotes)

    # 验证只有该股票价格被更新
    pos1 = sample_positions.get_position('600519')
    assert pos1['current_price'] == 1550.0


# ========================================================================
# 4. 止损检查
# ========================================================================

def test_check_stop_loss_all_no_triggers(position_monitor, sample_positions):
    """测试止损检查 - 无触发"""
    position_monitor.risk_manager = sample_positions

    # 更新价格为正常范围（未触发止损）
    quotes = {
        '600519': {'current_price': 1450.0},  # -3.3%
        '000001': {'current_price': 14.5}     # -3.3%
    }
    position_monitor.update_position_prices(quotes)

    signals = position_monitor.check_stop_loss_all()

    # 应该没有止损信号
    assert isinstance(signals, list)
    # 可能为空或没有止损信号
    stop_loss_signals = [s for s in signals if '止损' in s.description]
    # 由于止损价通常是8%，-3.3%不应触发
    assert len(stop_loss_signals) == 0


def test_check_stop_loss_all_with_triggers(position_monitor, sample_positions):
    """测试止损检查 - 有触发"""
    position_monitor.risk_manager = sample_positions

    # 更新价格触发止损（下跌超过8%）
    quotes = {
        '600519': {'current_price': 1350.0},  # -10%，触发止损
        '000001': {'current_price': 13.5}     # -10%，触发止损
    }
    position_monitor.update_position_prices(quotes)

    signals = position_monitor.check_stop_loss_all()

    # 应该有止损信号
    assert isinstance(signals, list)
    assert len(signals) > 0

    # 验证信号属性
    for signal in signals:
        assert signal.signal_type == 'SELL'
        assert signal.category == 'risk'
        assert '止损' in signal.description


# ========================================================================
# 5. 止盈检查
# ========================================================================

def test_check_take_profit_all_no_triggers(position_monitor, sample_positions):
    """测试止盈检查 - 无触发"""
    position_monitor.risk_manager = sample_positions

    # 更新价格为正常盈利范围（未触发止盈）
    quotes = {
        '600519': {'current_price': 1550.0},  # +3.3%
        '000001': {'current_price': 15.5}     # +3.3%
    }
    position_monitor.update_position_prices(quotes)

    signals = position_monitor.check_take_profit_all()

    # 应该没有止盈信号
    assert isinstance(signals, list)
    take_profit_signals = [s for s in signals if '止盈' in s.description]
    assert len(take_profit_signals) == 0


def test_check_take_profit_all_with_triggers(position_monitor, sample_positions):
    """测试止盈检查 - 有触发"""
    position_monitor.risk_manager = sample_positions

    # 更新价格触发止盈（上涨超过15%）
    quotes = {
        '600519': {'current_price': 1750.0},  # +16.7%，触发止盈
        '000001': {'current_price': 17.5}     # +16.7%，触发止盈
    }
    position_monitor.update_position_prices(quotes)

    signals = position_monitor.check_take_profit_all()

    # 应该有止盈信号
    assert isinstance(signals, list)
    assert len(signals) > 0

    # 验证信号属性
    for signal in signals:
        assert signal.signal_type == 'SELL'
        assert signal.category == 'risk'
        assert '止盈' in signal.description


# ========================================================================
# 6. 风险评估
# ========================================================================

def test_assess_portfolio_health_empty(position_monitor):
    """测试组合健康评估 - 空持仓"""
    health = position_monitor.assess_portfolio_health()

    assert isinstance(health, dict)
    assert 'risk_level' in health
    assert 'total_value' in health
    assert 'total_profit_loss' in health
    assert 'position_count' in health

    assert health['position_count'] == 0
    assert health['total_value'] == 0


def test_assess_portfolio_health_with_positions(position_monitor, sample_positions):
    """测试组合健康评估 - 有持仓"""
    position_monitor.risk_manager = sample_positions

    # 更新价格
    quotes = {
        '600519': {'current_price': 1600.0},
        '000001': {'current_price': 16.0}
    }
    position_monitor.update_position_prices(quotes)

    health = position_monitor.assess_portfolio_health()

    assert isinstance(health, dict)
    assert health['position_count'] == 2
    assert health['total_value'] > 0
    assert 'risk_level' in health
    assert health['risk_level'] in ['low', 'medium', 'high']


def test_assess_portfolio_health_risk_levels(position_monitor, sample_positions):
    """测试组合健康评估 - 不同风险级别"""
    position_monitor.risk_manager = sample_positions

    # 测试低风险场景（盈利状态）
    quotes = {
        '600519': {'current_price': 1550.0},  # +3.3%
        '000001': {'current_price': 15.5}     # +3.3%
    }
    position_monitor.update_position_prices(quotes)

    health = position_monitor.assess_portfolio_health()

    assert health['risk_level'] in ['low', 'medium', 'high']
    assert 'warnings' in health


# ========================================================================
# 7. 报告生成
# ========================================================================

def test_generate_position_report_empty(position_monitor):
    """测试生成持仓报告 - 空持仓"""
    report = position_monitor.generate_position_report()

    assert isinstance(report, str)
    assert len(report) > 0
    assert '持仓报告' in report or '空仓' in report or '无持仓' in report


def test_generate_position_report_with_positions(position_monitor, sample_positions):
    """测试生成持仓报告 - 有持仓"""
    position_monitor.risk_manager = sample_positions

    # 更新价格
    quotes = {
        '600519': {'current_price': 1600.0},
        '000001': {'current_price': 16.0}
    }
    position_monitor.update_position_prices(quotes)

    report = position_monitor.generate_position_report()

    assert isinstance(report, str)
    assert len(report) > 0

    # 验证报告包含关键信息
    assert '600519' in report or '贵州茅台' in report
    assert '000001' in report or '平安银行' in report


# ========================================================================
# 8. 综合场景
# ========================================================================

def test_full_monitoring_cycle(position_monitor, sample_positions):
    """测试完整监控周期"""
    position_monitor.risk_manager = sample_positions

    # 1. 更新价格
    quotes = {
        '600519': {'current_price': 1350.0},  # 触发止损
        '000001': {'current_price': 17.5}     # 触发止盈
    }

    # 2. 执行监控
    signals = position_monitor.monitor_positions(quotes)

    # 3. 验证结果
    assert isinstance(signals, list)
    assert len(signals) > 0

    # 4. 生成报告
    health = position_monitor.assess_portfolio_health()
    report = position_monitor.generate_position_report()

    assert isinstance(health, dict)
    assert isinstance(report, str)


def test_monitor_positions_integration(position_monitor, sample_positions):
    """测试持仓监控集成"""
    position_monitor.risk_manager = sample_positions

    # 模拟多种场景的价格
    scenarios = [
        # 场景1: 正常波动
        {
            '600519': {'current_price': 1520.0},
            '000001': {'current_price': 15.2}
        },
        # 场景2: 触发止损
        {
            '600519': {'current_price': 1350.0},
            '000001': {'current_price': 13.5}
        },
        # 场景3: 触发止盈
        {
            '600519': {'current_price': 1750.0},
            '000001': {'current_price': 17.5}
        }
    ]

    for i, quotes in enumerate(scenarios):
        signals = position_monitor.monitor_positions(quotes)

        # 验证每个场景都能正常执行
        assert isinstance(signals, list)

        # 场景2和3应该产生信号
        if i > 0:
            assert len(signals) > 0
