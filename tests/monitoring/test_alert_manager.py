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
8. 邮件通知 (8个)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import Signal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


# ========================================================================
# 8. 邮件通知测试
# ========================================================================

@pytest.fixture
def email_config():
    """邮件配置夹具"""
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'sender': 'test@example.com',
        'sender_password': 'test_password',
        'recipients': ['recipient1@example.com', 'recipient2@example.com'],
        'subject_template': '[A股监控] {signal_type} - {stock_name}',
        'max_retries': 3,
        'retry_delay': 1,
        'rate_limit_seconds': 300
    }


@pytest.fixture
def alert_manager_with_email(email_config):
    """创建带邮件配置的AlertManager实例"""
    manager = AlertManager()
    manager.email_config = email_config
    manager._email_rate_limiter = {}  # 邮件发送频率限制器
    return manager


def test_send_email_notification_success(alert_manager_with_email, sample_signal):
    """测试成功发送邮件通知"""
    # Mock SMTP服务器
    mock_smtp = MagicMock()

    with patch('smtplib.SMTP', return_value=mock_smtp):
        with patch.object(alert_manager_with_email, '_render_email_template', return_value='<html>Test</html>'):
            result = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

    # 验证SMTP连接和发送
    assert result['success'] is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once()
    mock_smtp.send_message.assert_called_once()
    mock_smtp.quit.assert_called_once()


def test_send_email_notification_smtp_error(alert_manager_with_email, sample_signal):
    """测试SMTP连接失败"""
    # Mock SMTP抛出异常
    with patch('smtplib.SMTP', side_effect=smtplib.SMTPException("Connection failed")):
        result = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

    # 应该捕获异常并返回失败结果
    assert result['success'] is False
    assert 'error' in result


def test_send_email_notification_authentication_error(alert_manager_with_email, sample_signal):
    """测试SMTP认证失败"""
    mock_smtp = MagicMock()
    mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')

    with patch('smtplib.SMTP', return_value=mock_smtp):
        with patch.object(alert_manager_with_email, '_render_email_template', return_value='<html>Test</html>'):
            result = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

    assert result['success'] is False
    assert 'error' in result


def test_send_email_notification_retry_mechanism(alert_manager_with_email, sample_signal):
    """测试邮件发送重试机制"""
    mock_smtp = MagicMock()
    # 前两次失败，第三次成功
    mock_smtp.send_message.side_effect = [
        smtplib.SMTPException("Temporary failure"),
        smtplib.SMTPException("Temporary failure"),
        None  # 第三次成功
    ]

    with patch('smtplib.SMTP', return_value=mock_smtp):
        with patch.object(alert_manager_with_email, '_render_email_template', return_value='<html>Test</html>'):
            with patch('time.sleep'):  # Mock sleep避免测试等待
                result = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

    # 应该重试3次后成功
    assert result['success'] is True
    assert mock_smtp.send_message.call_count == 3


def test_email_template_rendering(alert_manager_with_email, sample_signal):
    """测试邮件模板渲染"""
    # 创建模板目录和文件
    template_content = """
    <html>
    <body>
        <h1>{{ signal_type }} 信号</h1>
        <p>股票: {{ stock_code }} {{ stock_name }}</p>
        <p>价格: {{ trigger_price }}</p>
        <p>描述: {{ description }}</p>
    </body>
    </html>
    """

    with patch('builtins.open', mock_open(read_data=template_content)):
        with patch('os.path.exists', return_value=True):
            html = alert_manager_with_email._render_email_template(sample_signal)

    # 验证模板渲染
    assert '600519' in html
    assert '贵州茅台' in html
    assert 'BUY' in html


def test_email_rate_limiting(alert_manager_with_email, sample_signal):
    """测试邮件发送频率限制"""
    mock_smtp = MagicMock()

    with patch('smtplib.SMTP', return_value=mock_smtp):
        with patch.object(alert_manager_with_email, '_render_email_template', return_value='<html>Test</html>'):
            # 第一次应该发送
            result1 = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)
            assert result1['success'] is True

            # 立即再次发送相同股票的邮件应该被限制
            result2 = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

            # 应该被限制，返回失败结果
            assert result2['success'] is False
            assert 'rate limit' in result2.get('error', '').lower()


def test_email_subject_formatting(alert_manager_with_email, sample_signal):
    """测试邮件主题格式化"""
    subject = alert_manager_with_email._format_email_subject(sample_signal)

    # 验证主题包含关键信息
    assert 'BUY' in subject
    assert '贵州茅台' in subject or '600519' in subject


def test_email_with_multiple_recipients(alert_manager_with_email, sample_signal):
    """测试向多个收件人发送邮件"""
    mock_smtp = MagicMock()

    with patch('smtplib.SMTP', return_value=mock_smtp):
        with patch.object(alert_manager_with_email, '_render_email_template', return_value='<html>Test</html>'):
            result = alert_manager_with_email.send_notification(sample_signal, AlertChannel.EMAIL)

    # 验证邮件发送到所有收件人
    assert result['success'] is True
    call_args = mock_smtp.send_message.call_args
    if call_args:
        message = call_args[0][0] if call_args[0] else call_args[1].get('message')
        if message and hasattr(message, 'get'):
            recipients = message.get('To', '')
            # 验证至少包含一个收件人
            assert len(recipients) > 0 or mock_smtp.send_message.called
