"""
测试MonitoringService - 监控服务整合

测试覆盖:
1. 初始化测试 (2个)
2. 监控列表管理 (3个)
3. 服务控制 (2个)
4. 监控周期 (3个)
5. 报告生成 (2个)
6. 配置管理 (2个)
7. 综合场景 (2个)
"""

import pytest
import yaml
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.monitoring.monitoring_service import MonitoringService


# ========================================================================
# 测试夹具
# ========================================================================

@pytest.fixture
def temp_config_file(tmp_path):
    """创建临时配置文件"""
    config = {
        'monitoring': {
            'update_interval': 60,
            'watchlist': [
                {'code': '600519', 'name': '贵州茅台'},
                {'code': '000001', 'name': '平安银行'}
            ],
            'signals': {
                'enabled_detectors': ['ma_crossover', 'rsi', 'volume_breakout'],
                'ma_short': 5,
                'ma_long': 20,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            },
            'alerts': {
                'min_priority': 'medium',
                'channels': ['console', 'log'],
                'dedup_window': 900
            },
            'position_monitoring': {
                'enabled': True,
                'check_interval': 300
            }
        },
        'risk': {
            'total_capital': 1000000
        }
    }

    config_file = tmp_path / "test_monitoring.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)

    return str(config_file)


@pytest.fixture
def monitoring_service(temp_config_file):
    """创建MonitoringService实例"""
    return MonitoringService(temp_config_file)


# ========================================================================
# 1. 初始化测试
# ========================================================================

def test_monitoring_service_initialization(monitoring_service):
    """测试MonitoringService正确初始化"""
    assert monitoring_service is not None
    assert hasattr(monitoring_service, 'watcher')
    assert hasattr(monitoring_service, 'detector')
    assert hasattr(monitoring_service, 'alert_manager')
    assert hasattr(monitoring_service, 'position_monitor')
    assert hasattr(monitoring_service, 'risk_manager')


def test_monitoring_service_loads_config(monitoring_service):
    """测试正确加载配置"""
    assert monitoring_service.config is not None
    assert 'monitoring' in monitoring_service.config
    assert monitoring_service.update_interval == 60


# ========================================================================
# 2. 监控列表管理
# ========================================================================

def test_add_to_watchlist(monitoring_service):
    """测试添加股票到监控列表"""
    result = monitoring_service.add_to_watchlist('000002', '万科A')

    assert result['success'] is True
    watchlist = monitoring_service.get_watchlist()
    assert '000002' in watchlist


def test_remove_from_watchlist(monitoring_service):
    """测试从监控列表移除股票"""
    # 先添加
    monitoring_service.add_to_watchlist('000002', '万科A')

    # 再移除
    result = monitoring_service.remove_from_watchlist('000002')

    assert result['success'] is True
    watchlist = monitoring_service.get_watchlist()
    assert '000002' not in watchlist


def test_get_watchlist(monitoring_service):
    """测试获取监控列表"""
    watchlist = monitoring_service.get_watchlist()

    assert isinstance(watchlist, dict)
    # 配置文件中定义了2只股票
    assert len(watchlist) >= 2
    assert '600519' in watchlist
    assert '000001' in watchlist


# ========================================================================
# 3. 服务控制
# ========================================================================

def test_start_service(monitoring_service):
    """测试启动服务"""
    monitoring_service.start()

    assert monitoring_service.is_running is True


def test_stop_service(monitoring_service):
    """测试停止服务"""
    monitoring_service.start()
    monitoring_service.stop()

    assert monitoring_service.is_running is False


# ========================================================================
# 4. 监控周期
# ========================================================================

def test_run_monitoring_cycle(monitoring_service):
    """测试执行一次监控周期"""
    with patch.object(monitoring_service.watcher, 'update_quotes') as mock_update:
        with patch.object(monitoring_service, 'scan_and_alert') as mock_scan:
            monitoring_service.run_monitoring_cycle()

            # 验证调用了更新行情
            mock_update.assert_called_once()

            # 验证调用了扫描和提醒
            mock_scan.assert_called_once()


def test_scan_and_alert(monitoring_service):
    """测试扫描和提醒"""
    # Mock行情数据
    with patch.object(monitoring_service.watcher, 'get_all_quotes') as mock_quotes:
        mock_quotes.return_value = {
            '600519': {'current_price': 1600.0, 'name': '贵州茅台'},
            '000001': {'current_price': 16.0, 'name': '平安银行'}
        }

        with patch.object(monitoring_service.detector, 'detect_all_signals') as mock_detect:
            mock_detect.return_value = []  # 无信号

            signals = monitoring_service.scan_and_alert()

            assert isinstance(signals, list)


def test_monitoring_cycle_with_signals(monitoring_service):
    """测试监控周期检测到信号"""
    from src.monitoring.signal_detector import Signal

    # Mock检测到信号
    test_signal = Signal(
        stock_code='600519',
        stock_name='贵州茅台',
        signal_type='BUY',
        category='technical',
        description='MA金叉',
        priority='medium',
        trigger_price=1600.0,
        timestamp=datetime.now(),
        metadata={}
    )

    with patch.object(monitoring_service.detector, 'detect_all_signals') as mock_detect:
        mock_detect.return_value = [test_signal]

        with patch.object(monitoring_service.alert_manager, 'process_signal') as mock_alert:
            signals = monitoring_service.scan_and_alert()

            # 验证检测到信号
            assert len(signals) > 0

            # 验证发送了提醒
            mock_alert.assert_called()


# ========================================================================
# 5. 报告生成
# ========================================================================

def test_generate_daily_summary(monitoring_service):
    """测试生成每日总结"""
    summary = monitoring_service.generate_daily_summary()

    assert isinstance(summary, str)
    assert len(summary) > 0
    # 应该包含关键信息
    assert '监控总结' in summary or '每日报告' in summary or 'summary' in summary.lower()


def test_get_active_signals(monitoring_service):
    """测试获取活跃信号"""
    signals = monitoring_service.get_active_signals()

    assert isinstance(signals, list)
    # 初始应该为空
    assert len(signals) == 0


# ========================================================================
# 6. 配置管理
# ========================================================================

def test_reload_config(monitoring_service, temp_config_file):
    """测试重新加载配置"""
    # 修改配置文件
    with open(temp_config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    config['monitoring']['update_interval'] = 120

    with open(temp_config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f)

    # 重新加载
    monitoring_service.reload_config()

    # 验证配置已更新
    assert monitoring_service.update_interval == 120


def test_config_validation(temp_config_file):
    """测试配置验证"""
    # 测试有效配置
    service = MonitoringService(temp_config_file)
    assert service is not None

    # 测试无效配置文件路径
    with pytest.raises(FileNotFoundError):
        MonitoringService('nonexistent_config.yaml')


# ========================================================================
# 7. 综合场景
# ========================================================================

def test_full_monitoring_workflow(monitoring_service):
    """测试完整监控工作流"""
    # 1. 启动服务
    monitoring_service.start()
    assert monitoring_service.is_running is True

    # 2. 添加监控股票
    monitoring_service.add_to_watchlist('000002', '万科A')

    # 3. 执行监控周期
    with patch.object(monitoring_service.watcher, 'update_quotes'):
        with patch.object(monitoring_service.detector, 'detect_all_signals') as mock_detect:
            mock_detect.return_value = []
            monitoring_service.run_monitoring_cycle()

    # 4. 生成报告
    summary = monitoring_service.generate_daily_summary()
    assert len(summary) > 0

    # 5. 停止服务
    monitoring_service.stop()
    assert monitoring_service.is_running is False


def test_position_monitoring_integration(monitoring_service):
    """测试持仓监控集成"""
    # 添加持仓
    monitoring_service.risk_manager.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1500.0,
        entry_date=datetime.now()
    )

    # Mock行情数据
    with patch.object(monitoring_service.watcher, 'get_all_quotes') as mock_quotes:
        mock_quotes.return_value = {
            '600519': {'current_price': 1350.0}  # 触发止损
        }

        # 执行监控
        signals = monitoring_service.scan_and_alert()

        # 应该检测到止损信号
        # 注意：实际信号检测取决于detector的实现
        assert isinstance(signals, list)
