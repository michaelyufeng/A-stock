"""
AlertManager - 提醒管理器

功能:
1. 提醒规则管理（添加、删除、更新）
2. 信号匹配检测
3. 多渠道通知（控制台、日志、邮件、微信）
4. 冷却期管理（防止重复提醒）
5. 提醒历史记录
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import yaml

from src.monitoring.signal_detector import Signal

logger = logging.getLogger(__name__)


class AlertChannel(Enum):
    """提醒渠道枚举"""
    CONSOLE = "console"
    LOG = "log"
    EMAIL = "email"
    WECHAT = "wechat"


@dataclass
class AlertRule:
    """提醒规则数据类"""
    rule_id: str
    name: str
    stock_codes: List[str]  # 关注的股票代码列表
    signal_types: List[str]  # 关注的信号类型 ['BUY', 'SELL', 'WARNING', 'INFO']
    categories: List[str]  # 关注的信号类别 ['technical', 'risk', 'price', 'volume']
    min_priority: str  # 最低优先级 'low', 'medium', 'high', 'critical'
    channels: List[AlertChannel]  # 通知渠道
    enabled: bool = True
    cooldown_minutes: int = 60  # 冷却期（分钟）


class AlertManager:
    """提醒管理器 - 管理提醒规则和发送通知"""

    # 优先级权重
    PRIORITY_WEIGHTS = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }

    def __init__(self, config_path: str = 'config/risk_rules.yaml'):
        """
        初始化提醒管理器

        Args:
            config_path: 配置文件路径
        """
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.last_alert_time: Dict[str, datetime] = {}  # {rule_id-stock_code: timestamp}

        # 加载配置
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 提取提醒相关配置
            alerts_config = config.get('alerts', {})
            self.default_cooldown_minutes = alerts_config.get('default_cooldown_minutes', 60)
            self.max_history_days = alerts_config.get('max_history_days', 30)

            logger.info(f"Loaded alert config: cooldown={self.default_cooldown_minutes}min")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self.default_cooldown_minutes = 60
            self.max_history_days = 30
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.default_cooldown_minutes = 60
            self.max_history_days = 30

    # ========================================================================
    # 规则管理
    # ========================================================================

    def add_rule(self, rule: AlertRule) -> Dict[str, Any]:
        """
        添加提醒规则

        Args:
            rule: AlertRule对象

        Returns:
            {'success': bool, 'message': str}
        """
        if rule.rule_id in self.rules:
            return {
                'success': False,
                'message': f'Rule {rule.rule_id} already exists'
            }

        self.rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id} - {rule.name}")

        return {
            'success': True,
            'message': f'Rule {rule.rule_id} added successfully'
        }

    def remove_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        移除提醒规则

        Args:
            rule_id: 规则ID

        Returns:
            {'success': bool, 'message': str}
        """
        if rule_id not in self.rules:
            return {
                'success': False,
                'message': f'Rule {rule_id} not found'
            }

        del self.rules[rule_id]
        logger.info(f"Removed alert rule: {rule_id}")

        return {
            'success': True,
            'message': f'Rule {rule_id} removed successfully'
        }

    def update_rule(self, rule_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新提醒规则

        Args:
            rule_id: 规则ID
            **kwargs: 要更新的字段

        Returns:
            {'success': bool, 'message': str}
        """
        if rule_id not in self.rules:
            return {
                'success': False,
                'message': f'Rule {rule_id} not found'
            }

        rule = self.rules[rule_id]

        # 更新允许的字段
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        logger.info(f"Updated alert rule: {rule_id}")

        return {
            'success': True,
            'message': f'Rule {rule_id} updated successfully'
        }

    def get_all_rules(self) -> List[AlertRule]:
        """
        获取所有提醒规则

        Returns:
            规则列表
        """
        return list(self.rules.values())

    # ========================================================================
    # 信号匹配
    # ========================================================================

    def check_signal_matches(self, signal: Signal, rule: AlertRule) -> bool:
        """
        检查信号是否匹配规则

        Args:
            signal: Signal对象
            rule: AlertRule对象

        Returns:
            是否匹配
        """
        # 规则是否启用
        if not rule.enabled:
            return False

        # 检查股票代码
        if rule.stock_codes and signal.stock_code not in rule.stock_codes:
            return False

        # 检查信号类型
        if rule.signal_types and signal.signal_type not in rule.signal_types:
            return False

        # 检查信号类别
        if rule.categories and signal.category not in rule.categories:
            return False

        # 检查优先级
        signal_priority_weight = self.PRIORITY_WEIGHTS.get(signal.priority, 0)
        min_priority_weight = self.PRIORITY_WEIGHTS.get(rule.min_priority, 0)

        if signal_priority_weight < min_priority_weight:
            return False

        return True

    def _is_in_cooldown(self, rule_id: str, stock_code: str, cooldown_minutes: int) -> bool:
        """
        检查是否在冷却期内

        Args:
            rule_id: 规则ID
            stock_code: 股票代码
            cooldown_minutes: 冷却期（分钟）

        Returns:
            是否在冷却期
        """
        key = f"{rule_id}-{stock_code}"

        if key not in self.last_alert_time:
            return False

        last_time = self.last_alert_time[key]
        elapsed = (datetime.now() - last_time).total_seconds() / 60

        return elapsed < cooldown_minutes

    def _update_cooldown(self, rule_id: str, stock_code: str):
        """
        更新冷却期时间

        Args:
            rule_id: 规则ID
            stock_code: 股票代码
        """
        key = f"{rule_id}-{stock_code}"
        self.last_alert_time[key] = datetime.now()

    # ========================================================================
    # 通知发送
    # ========================================================================

    def send_notification(self, signal: Signal, channel: AlertChannel) -> Dict[str, Any]:
        """
        发送通知

        Args:
            signal: Signal对象
            channel: 通知渠道

        Returns:
            发送结果
        """
        try:
            if channel == AlertChannel.CONSOLE:
                self._send_console_notification(signal)
            elif channel == AlertChannel.LOG:
                self._send_log_notification(signal)
            elif channel == AlertChannel.EMAIL:
                self._send_email_notification(signal)
            elif channel == AlertChannel.WECHAT:
                self._send_wechat_notification(signal)

            return {'success': True, 'channel': channel.value}

        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {e}")
            return {'success': False, 'channel': channel.value, 'error': str(e)}

    def _send_console_notification(self, signal: Signal):
        """发送控制台通知"""
        # 根据信号类型选择颜色标记
        type_icons = {
            'BUY': '🟢',
            'SELL': '🔴',
            'WARNING': '🟡',
            'INFO': '🔵'
        }

        priority_icons = {
            'low': '➖',
            'medium': '➕',
            'high': '❗',
            'critical': '‼️'
        }

        icon = type_icons.get(signal.signal_type, '●')
        priority_icon = priority_icons.get(signal.priority, '')

        print(f"\n{icon} [{signal.signal_type}] {priority_icon} {signal.stock_code} {signal.stock_name}")
        print(f"   {signal.description}")
        print(f"   价格: ¥{signal.trigger_price:.2f} | 时间: {signal.timestamp.strftime('%H:%M:%S')}")
        print(f"   类别: {signal.category} | 优先级: {signal.priority}")

    def _send_log_notification(self, signal: Signal):
        """发送日志通知"""
        log_msg = (
            f"ALERT: [{signal.signal_type}] {signal.stock_code} {signal.stock_name} - "
            f"{signal.description} @ ¥{signal.trigger_price:.2f} "
            f"(priority: {signal.priority})"
        )

        if signal.priority == 'critical':
            logger.critical(log_msg)
        elif signal.priority == 'high':
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def _send_email_notification(self, signal: Signal):
        """发送邮件通知（待实现）"""
        logger.warning(f"Email notification not implemented yet for {signal.stock_code}")
        # TODO: 实现邮件通知
        pass

    def _send_wechat_notification(self, signal: Signal):
        """发送微信通知（待实现）"""
        logger.warning(f"WeChat notification not implemented yet for {signal.stock_code}")
        # TODO: 实现微信通知
        pass

    # ========================================================================
    # 信号处理
    # ========================================================================

    def process_signal(self, signal: Signal) -> Dict[str, Any]:
        """
        处理单个信号

        Args:
            signal: Signal对象

        Returns:
            处理结果
        """
        triggered_rules = []

        for rule_id, rule in self.rules.items():
            # 检查信号是否匹配规则
            if not self.check_signal_matches(signal, rule):
                continue

            # 检查冷却期
            if self._is_in_cooldown(rule_id, signal.stock_code, rule.cooldown_minutes):
                logger.debug(f"Rule {rule_id} in cooldown for {signal.stock_code}")
                continue

            # 发送通知
            for channel in rule.channels:
                self.send_notification(signal, channel)

            # 更新冷却期
            self._update_cooldown(rule_id, signal.stock_code)

            # 记录历史
            self._record_alert(signal, rule_id)

            triggered_rules.append(rule_id)

        return {
            'triggered': len(triggered_rules) > 0,
            'rule_ids': triggered_rules,
            'signal': signal
        }

    def process_signals(self, signals: List[Signal]) -> List[Dict[str, Any]]:
        """
        批量处理信号

        Args:
            signals: Signal列表

        Returns:
            处理结果列表
        """
        results = []

        for signal in signals:
            result = self.process_signal(signal)
            results.append(result)

        return results

    # ========================================================================
    # 提醒历史
    # ========================================================================

    def _record_alert(self, signal: Signal, rule_id: str):
        """
        记录提醒历史

        Args:
            signal: Signal对象
            rule_id: 触发的规则ID
        """
        record = {
            'timestamp': datetime.now(),
            'stock_code': signal.stock_code,
            'stock_name': signal.stock_name,
            'signal_type': signal.signal_type,
            'description': signal.description,
            'trigger_price': signal.trigger_price,
            'priority': signal.priority,
            'rule_id': rule_id
        }

        self.alert_history.append(record)

    def get_alert_history(
        self,
        stock_code: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询提醒历史

        Args:
            stock_code: 股票代码过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制

        Returns:
            历史记录列表
        """
        filtered = self.alert_history

        # 按股票代码过滤
        if stock_code:
            filtered = [r for r in filtered if r['stock_code'] == stock_code]

        # 按时间范围过滤
        if start_time:
            filtered = [r for r in filtered if r['timestamp'] >= start_time]

        if end_time:
            filtered = [r for r in filtered if r['timestamp'] <= end_time]

        # 按时间倒序排列
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)

        # 限制返回数量
        return filtered[:limit]

    def clear_old_history(self, days: int = 30):
        """
        清理旧的提醒历史

        Args:
            days: 保留最近N天的记录
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        original_count = len(self.alert_history)
        self.alert_history = [
            r for r in self.alert_history
            if r['timestamp'] > cutoff_time
        ]

        removed_count = original_count - len(self.alert_history)

        if removed_count > 0:
            logger.info(f"Cleared {removed_count} old alert records (older than {days} days)")
