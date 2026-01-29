"""
测试AlertManager - 提醒管理器

测试覆盖:
1. 初始化测试 (2个)
2. 添加/移除提醒规则 (4个)
3. 检查触发条件 (6个)
4. 通知发送 (5个)
5. 提醒历史管理 (4个)
6. 批量检查 (2个)
7. 配置管理 (2个)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import Signal


# ========================================================================
# 测试夹具
# ========================================================================

@pytest.fixture
def alert_manager():
    """创建AlertManager实例"""
    return AlertManager()


@pytest.fixture
def sample_signal():
    """创建示例Signal"""
    return Signal(
        stock_code='600519',
        stock_name='贵州茅台',
        signal_type='BUY',
        category='technical',
        description='MA5金叉MA20',
        priority='medium',
        trigger_price=1680.50,
        timestamp=datetime.now(),
        metadata={'ma_short': 5, 'ma_long': 20}
    )


@pytest.fixture
def sample_rule():
    """创建示例AlertRule"""
    return AlertRule(
        rule_id='rule_001',
        name='MA金叉提醒',
        stock_codes=['600519'],
        signal_types=['BUY'],
        categories=['technical'],
        min_priority='medium',
        channels=[AlertChannel.CONSOLE],
        enabled=True,
        cooldown_minutes=60
    )


# ========================================================================
# 1. 初始化测试
# ========================================================================

def test_alert_manager_initialization(alert_manager):
    """测试AlertManager正确初始化"""
    assert alert_manager is not None
    assert isinstance(alert_manager.rules, dict)
    assert isinstance(alert_manager.alert_history, list)
    assert len(alert_manager.rules) == 0
    assert len(alert_manager.alert_history) == 0


def test_alert_manager_loads_config(alert_manager):
    """测试AlertManager加载配置"""
    # 应该有默认的冷却期配置
    assert hasattr(alert_manager, 'default_cooldown_minutes')
    assert alert_manager.default_cooldown_minutes >= 0


# ========================================================================
# 2. 添加/移除提醒规则
# ========================================================================

def test_add_rule_success(alert_manager, sample_rule):
    """测试成功添加提醒规则"""
    result = alert_manager.add_rule(sample_rule)

    assert result['success'] is True
    assert sample_rule.rule_id in alert_manager.rules
    assert alert_manager.rules[sample_rule.rule_id] == sample_rule


def test_add_duplicate_rule(alert_manager, sample_rule):
    """测试添加重复规则ID"""
    alert_manager.add_rule(sample_rule)
    result = alert_manager.add_rule(sample_rule)

    assert result['success'] is False
    assert 'already exists' in result['message'].lower()


def test_remove_rule_success(alert_manager, sample_rule):
    """测试成功移除提醒规则"""
    alert_manager.add_rule(sample_rule)
    result = alert_manager.remove_rule(sample_rule.rule_id)

    assert result['success'] is True
    assert sample_rule.rule_id not in alert_manager.rules


def test_remove_nonexistent_rule(alert_manager):
    """测试移除不存在的规则"""
    result = alert_manager.remove_rule('nonexistent_rule')

    assert result['success'] is False
    assert 'not found' in result['message'].lower()


# ========================================================================
# 3. 检查触发条件
# ========================================================================

def test_check_signal_matches_rule(alert_manager, sample_rule, sample_signal):
    """测试信号匹配规则"""
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is True


def test_check_signal_wrong_stock_code(alert_manager, sample_rule, sample_signal):
    """测试股票代码不匹配"""
    sample_rule.stock_codes = ['000001']
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is False


def test_check_signal_wrong_type(alert_manager, sample_rule, sample_signal):
    """测试信号类型不匹配"""
    sample_rule.signal_types = ['SELL']
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is False


def test_check_signal_wrong_category(alert_manager, sample_rule, sample_signal):
    """测试信号类别不匹配"""
    sample_rule.categories = ['risk']
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is False


def test_check_signal_priority_too_low(alert_manager, sample_rule, sample_signal):
    """测试信号优先级不够"""
    sample_rule.min_priority = 'high'
    sample_signal.priority = 'low'
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is False


def test_check_signal_disabled_rule(alert_manager, sample_rule, sample_signal):
    """测试禁用的规则不触发"""
    sample_rule.enabled = False
    alert_manager.add_rule(sample_rule)

    matched = alert_manager.check_signal_matches(sample_signal, sample_rule)

    assert matched is False


# ========================================================================
# 4. 通知发送
# ========================================================================

@patch('builtins.print')
def test_send_console_notification(mock_print, alert_manager, sample_signal):
    """测试控制台通知"""
    alert_manager.send_notification(sample_signal, AlertChannel.CONSOLE)

    mock_print.assert_called()
    # Check all calls for stock code or name
    all_calls = str(mock_print.call_args_list)
    assert '600519' in all_calls or '贵州茅台' in all_calls


@patch('logging.Logger.info')
def test_send_log_notification(mock_log, alert_manager, sample_signal):
    """测试日志通知"""
    alert_manager.send_notification(sample_signal, AlertChannel.LOG)

    mock_log.assert_called()


def test_send_unsupported_channel(alert_manager, sample_signal):
    """测试不支持的通知渠道"""
    # EMAIL和WECHAT还未实现，应该优雅处理
    result = alert_manager.send_notification(sample_signal, AlertChannel.EMAIL)

    assert result is not None
    # 不应该抛出异常


def test_process_signal_sends_notification(alert_manager, sample_rule, sample_signal):
    """测试处理信号发送通知"""
    alert_manager.add_rule(sample_rule)

    with patch.object(alert_manager, 'send_notification') as mock_send:
        alert_manager.process_signal(sample_signal)
        mock_send.assert_called_once()


def test_cooldown_prevents_duplicate_alerts(alert_manager, sample_rule, sample_signal):
    """测试冷却期防止重复提醒"""
    sample_rule.cooldown_minutes = 60
    alert_manager.add_rule(sample_rule)

    # 第一次应该发送
    with patch.object(alert_manager, 'send_notification') as mock_send:
        alert_manager.process_signal(sample_signal)
        assert mock_send.call_count == 1

    # 冷却期内第二次不应该发送
    with patch.object(alert_manager, 'send_notification') as mock_send:
        alert_manager.process_signal(sample_signal)
        assert mock_send.call_count == 0


# ========================================================================
# 5. 提醒历史管理
# ========================================================================

def test_record_alert_history(alert_manager, sample_rule, sample_signal):
    """测试记录提醒历史"""
    alert_manager.add_rule(sample_rule)
    alert_manager.process_signal(sample_signal)

    assert len(alert_manager.alert_history) > 0

    last_alert = alert_manager.alert_history[-1]
    assert last_alert['stock_code'] == sample_signal.stock_code
    assert last_alert['rule_id'] == sample_rule.rule_id


def test_get_alert_history_by_stock(alert_manager, sample_rule, sample_signal):
    """测试按股票查询提醒历史"""
    alert_manager.add_rule(sample_rule)
    alert_manager.process_signal(sample_signal)

    history = alert_manager.get_alert_history(stock_code='600519')

    assert len(history) > 0
    assert all(h['stock_code'] == '600519' for h in history)


def test_get_alert_history_by_timerange(alert_manager, sample_rule, sample_signal):
    """测试按时间范围查询提醒历史"""
    alert_manager.add_rule(sample_rule)
    alert_manager.process_signal(sample_signal)

    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now() + timedelta(hours=1)

    history = alert_manager.get_alert_history(start_time=start_time, end_time=end_time)

    assert len(history) > 0


def test_clear_old_history(alert_manager, sample_rule, sample_signal):
    """测试清理旧历史记录"""
    alert_manager.add_rule(sample_rule)
    alert_manager.process_signal(sample_signal)

    # 手动修改历史记录时间为7天前
    if alert_manager.alert_history:
        alert_manager.alert_history[0]['timestamp'] = datetime.now() - timedelta(days=8)

    alert_manager.clear_old_history(days=7)

    # 8天前的记录应该被清理
    assert all(
        h['timestamp'] > datetime.now() - timedelta(days=7)
        for h in alert_manager.alert_history
    )


# ========================================================================
# 6. 批量检查
# ========================================================================

def test_process_multiple_signals(alert_manager, sample_rule):
    """测试批量处理多个信号"""
    alert_manager.add_rule(sample_rule)

    signals = [
        Signal('600519', '贵州茅台', 'BUY', 'technical', 'MA金叉', 'medium', 1680.0, datetime.now(), {}),
        Signal('600519', '贵州茅台', 'SELL', 'technical', 'MA死叉', 'medium', 1650.0, datetime.now(), {}),
    ]

    results = alert_manager.process_signals(signals)

    assert len(results) == 2
    assert results[0]['triggered'] is True  # BUY匹配
    assert results[1]['triggered'] is False  # SELL不匹配（规则只允许BUY）


def test_process_signals_with_multiple_rules(alert_manager):
    """测试多个规则同时匹配"""
    rule1 = AlertRule('rule1', '规则1', ['600519'], ['BUY'], ['technical'], 'low', [AlertChannel.CONSOLE], True, 60)
    rule2 = AlertRule('rule2', '规则2', ['600519'], ['BUY'], ['technical'], 'low', [AlertChannel.LOG], True, 60)

    alert_manager.add_rule(rule1)
    alert_manager.add_rule(rule2)

    signal = Signal('600519', '贵州茅台', 'BUY', 'technical', 'MA金叉', 'medium', 1680.0, datetime.now(), {})

    with patch.object(alert_manager, 'send_notification') as mock_send:
        alert_manager.process_signal(signal)
        # 两个规则都匹配，应该发送2次通知
        assert mock_send.call_count == 2


# ========================================================================
# 7. 配置管理
# ========================================================================

def test_update_rule_configuration(alert_manager, sample_rule):
    """测试更新规则配置"""
    alert_manager.add_rule(sample_rule)

    result = alert_manager.update_rule(
        sample_rule.rule_id,
        enabled=False,
        min_priority='high'
    )

    assert result['success'] is True
    updated_rule = alert_manager.rules[sample_rule.rule_id]
    assert updated_rule.enabled is False
    assert updated_rule.min_priority == 'high'


def test_get_all_rules(alert_manager, sample_rule):
    """测试获取所有规则"""
    alert_manager.add_rule(sample_rule)

    rules = alert_manager.get_all_rules()

    assert len(rules) == 1
    assert rules[0].rule_id == sample_rule.rule_id
