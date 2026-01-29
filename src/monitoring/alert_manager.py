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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import time
from jinja2 import Environment, FileSystemLoader, select_autoescape

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
        self._email_rate_limiter: Dict[str, datetime] = {}  # {stock_code: last_email_time}

        # 加载配置
        self._load_config(config_path)

        # 初始化Jinja2模板环境
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _load_config(self, config_path: str):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 提取提醒相关配置
            alerts_config = config.get('alerts', {})
            self.default_cooldown_minutes = alerts_config.get('default_cooldown_minutes', 60)
            self.max_history_days = alerts_config.get('max_history_days', 30)

            # 加载邮件配置
            self.email_config = alerts_config.get('email', {})
            self._load_email_env_vars()

            logger.info(f"Loaded alert config: cooldown={self.default_cooldown_minutes}min")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self.default_cooldown_minutes = 60
            self.max_history_days = 30
            self.email_config = {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.default_cooldown_minutes = 60
            self.max_history_days = 30
            self.email_config = {}

    def _load_email_env_vars(self):
        """从环境变量加载敏感邮件配置"""
        from dotenv import load_dotenv
        load_dotenv()

        # 替换配置中的环境变量占位符
        if 'sender' in self.email_config:
            sender = self.email_config['sender']
            if isinstance(sender, str) and sender.startswith('${') and sender.endswith('}'):
                env_var = sender[2:-1]
                self.email_config['sender'] = os.getenv(env_var, '')

        if 'sender_password' in self.email_config:
            password = self.email_config['sender_password']
            if isinstance(password, str) and password.startswith('${') and password.endswith('}'):
                env_var = password[2:-1]
                self.email_config['sender_password'] = os.getenv(env_var, '')

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
        """
        发送邮件通知

        Args:
            signal: Signal对象

        Raises:
            Exception: 邮件发送失败时抛出异常
        """
        # 检查邮件配置
        if not self.email_config:
            logger.error("Email configuration not found")
            raise ValueError("Email configuration not found")

        # 检查必需的配置项
        required_fields = ['smtp_server', 'smtp_port', 'sender', 'sender_password', 'recipients']
        for field in required_fields:
            if field not in self.email_config or not self.email_config[field]:
                logger.error(f"Missing email config field: {field}")
                raise ValueError(f"Missing email config field: {field}")

        # 检查发送频率限制
        if self._is_email_rate_limited(signal.stock_code):
            logger.info(f"Email rate limited for {signal.stock_code}")
            raise ValueError(f"Email rate limited for {signal.stock_code}")

        # 获取配置参数
        smtp_server = self.email_config['smtp_server']
        smtp_port = self.email_config['smtp_port']
        sender = self.email_config['sender']
        sender_password = self.email_config['sender_password']
        recipients = self.email_config['recipients']
        use_tls = self.email_config.get('use_tls', True)
        max_retries = self.email_config.get('max_retries', 3)
        retry_delay = self.email_config.get('retry_delay', 1)

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = ', '.join(recipients) if isinstance(recipients, list) else recipients
        msg['Subject'] = self._format_email_subject(signal)

        # 渲染HTML内容
        html_content = self._render_email_template(signal)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # 重试机制发送邮件
        last_error = None
        for attempt in range(max_retries):
            try:
                # 连接SMTP服务器
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

                if use_tls:
                    server.starttls()

                # 登录
                server.login(sender, sender_password)

                # 发送邮件
                server.send_message(msg)

                # 关闭连接
                server.quit()

                # 更新发送频率限制
                self._update_email_rate_limit(signal.stock_code)

                logger.info(f"Email sent successfully for {signal.stock_code} (attempt {attempt + 1})")
                return

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                raise  # 认证错误不重试

            except (smtplib.SMTPException, OSError, ConnectionError) as e:
                last_error = e
                logger.warning(f"Email sending failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Email sending failed after {max_retries} attempts")
                    raise last_error

            except Exception as e:
                logger.error(f"Unexpected error sending email: {e}")
                raise

    def _format_email_subject(self, signal: Signal) -> str:
        """
        格式化邮件主题

        Args:
            signal: Signal对象

        Returns:
            格式化后的邮件主题
        """
        subject_template = self.email_config.get(
            'subject_template',
            '[A股监控] {signal_type} - {stock_name}'
        )

        return subject_template.format(
            signal_type=signal.signal_type,
            stock_code=signal.stock_code,
            stock_name=signal.stock_name,
            priority=signal.priority
        )

    def _render_email_template(self, signal: Signal) -> str:
        """
        渲染邮件HTML模板

        Args:
            signal: Signal对象

        Returns:
            渲染后的HTML内容
        """
        try:
            template = self.jinja_env.get_template('email_alert.html')

            html_content = template.render(
                signal_type=signal.signal_type,
                stock_code=signal.stock_code,
                stock_name=signal.stock_name,
                description=signal.description,
                priority=signal.priority,
                trigger_price=signal.trigger_price,
                timestamp=signal.timestamp,
                category=signal.category,
                metadata=signal.metadata,
                now=datetime.now()
            )

            return html_content

        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            # 返回简单的文本版本
            return self._render_fallback_email(signal)

    def _render_fallback_email(self, signal: Signal) -> str:
        """
        渲染备用的简单邮件模板

        Args:
            signal: Signal对象

        Returns:
            简单的HTML内容
        """
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">A股交易信号提醒</h2>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>信号类型:</strong> {signal.signal_type}</p>
                <p><strong>股票代码:</strong> {signal.stock_code}</p>
                <p><strong>股票名称:</strong> {signal.stock_name}</p>
                <p><strong>触发价格:</strong> ¥{signal.trigger_price:.2f}</p>
                <p><strong>优先级:</strong> {signal.priority}</p>
                <p><strong>描述:</strong> {signal.description}</p>
                <p><strong>时间:</strong> {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p style="color: #999; font-size: 12px;">
                本提醒仅供参考，不构成投资建议。股市有风险，投资需谨慎。
            </p>
        </body>
        </html>
        """

    def _is_email_rate_limited(self, stock_code: str) -> bool:
        """
        检查邮件发送是否超出频率限制

        Args:
            stock_code: 股票代码

        Returns:
            是否被限制
        """
        rate_limit_seconds = self.email_config.get('rate_limit_seconds', 300)

        if stock_code not in self._email_rate_limiter:
            return False

        last_time = self._email_rate_limiter[stock_code]
        elapsed = (datetime.now() - last_time).total_seconds()

        return elapsed < rate_limit_seconds

    def _update_email_rate_limit(self, stock_code: str):
        """
        更新邮件发送时间记录

        Args:
            stock_code: 股票代码
        """
        self._email_rate_limiter[stock_code] = datetime.now()

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
