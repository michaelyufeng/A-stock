"""
MonitoringService - 监控服务整合

功能:
1. 整合所有监控组件（RealTimeWatcher, SignalDetector, AlertManager, PositionMonitor）
2. 提供统一的监控服务接口
3. 配置驱动的监控系统
4. 完整的监控循环
5. 生成每日总结报告
"""

import logging
import yaml
from typing import Dict, List, Optional
from datetime import datetime
import time

from src.monitoring.realtime_watcher import RealTimeWatcher
from src.monitoring.signal_detector import SignalDetector, Signal
from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.position_monitor import PositionMonitor
from src.risk.risk_manager import RiskManager


logger = logging.getLogger(__name__)


class MonitoringService:
    """监控服务 - 整合所有监控组件"""

    def __init__(self, config_path: str):
        """
        初始化监控服务

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)

        # 服务状态
        self.is_running = False

        # 提取配置
        monitoring_config = self.config.get('monitoring', {})
        risk_config = self.config.get('risk', {})

        self.update_interval = monitoring_config.get('update_interval', 60)
        self.watchlist_config = monitoring_config.get('watchlist', [])
        self.signals_config = monitoring_config.get('signals', {})
        self.alerts_config = monitoring_config.get('alerts', {})
        self.position_config = monitoring_config.get('position_monitoring', {})

        # 活跃信号记录
        self.active_signals: List[Signal] = []
        self.signal_history: List[Dict] = []

        # 初始化组件
        self._initialize_components(risk_config)

        logger.info(f"MonitoringService initialized with config: {config_path}")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def _initialize_components(self, risk_config: Dict):
        """初始化所有监控组件"""
        # 1. 创建RiskManager
        total_capital = risk_config.get('total_capital', 1_000_000)
        self.risk_manager = RiskManager(total_capital=total_capital)

        # 2. 创建RealTimeWatcher
        watchlist = [
            {'code': item['code'], 'name': item['name']}
            for item in self.watchlist_config
        ]
        self.watcher = RealTimeWatcher(
            stock_list=watchlist,
            update_interval=self.update_interval
        )

        # 3. 创建SignalDetector
        self.detector = SignalDetector(risk_manager=self.risk_manager)

        # 配置检测器参数
        signals_config = self.signals_config
        if 'ma_short' in signals_config:
            self.detector.ma_short = signals_config['ma_short']
        if 'ma_long' in signals_config:
            self.detector.ma_long = signals_config['ma_long']
        if 'rsi_oversold' in signals_config:
            self.detector.rsi_oversold = signals_config['rsi_oversold']
        if 'rsi_overbought' in signals_config:
            self.detector.rsi_overbought = signals_config['rsi_overbought']

        # 4. 创建AlertManager
        self.alert_manager = AlertManager()

        # 配置默认提醒规则
        self._setup_default_alert_rules()

        # 5. 创建PositionMonitor
        self.position_monitor = PositionMonitor(
            risk_manager=self.risk_manager,
            signal_detector=self.detector
        )

        logger.info("All monitoring components initialized")

    def _setup_default_alert_rules(self):
        """设置默认提醒规则"""
        alerts_config = self.alerts_config
        min_priority = alerts_config.get('min_priority', 'medium')
        channels_config = alerts_config.get('channels', ['console', 'log'])

        # 转换渠道配置
        channels = []
        for ch in channels_config:
            if ch == 'console':
                channels.append(AlertChannel.CONSOLE)
            elif ch == 'log':
                channels.append(AlertChannel.LOG)
            elif ch == 'email':
                channels.append(AlertChannel.EMAIL)
            elif ch == 'wechat':
                channels.append(AlertChannel.WECHAT)

        # 创建默认规则
        default_rule = AlertRule(
            rule_id='default_monitoring',
            name='默认监控规则',
            stock_codes=[],  # 所有股票
            signal_types=['BUY', 'SELL', 'WARNING'],
            categories=['technical', 'risk', 'price', 'volume'],
            min_priority=min_priority,
            channels=channels,
            enabled=True,
            cooldown_minutes=alerts_config.get('dedup_window', 900) // 60
        )

        self.alert_manager.add_rule(default_rule)

        logger.info(f"Default alert rule created: min_priority={min_priority}")

    # ========================================================================
    # 服务控制
    # ========================================================================

    def start(self):
        """启动监控服务"""
        self.is_running = True
        logger.info("Monitoring service started")

    def stop(self):
        """停止监控服务"""
        self.is_running = False
        logger.info("Monitoring service stopped")

    def reload_config(self):
        """重新加载配置"""
        try:
            self.config = self._load_config(self.config_path)

            # 更新参数
            monitoring_config = self.config.get('monitoring', {})
            self.update_interval = monitoring_config.get('update_interval', 60)

            logger.info("Configuration reloaded")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")

    # ========================================================================
    # 监控列表管理
    # ========================================================================

    def add_to_watchlist(self, stock_code: str, stock_name: str) -> Dict:
        """
        添加股票到监控列表

        Args:
            stock_code: 股票代码
            stock_name: 股票名称

        Returns:
            操作结果
        """
        result = self.watcher.add_stock(stock_code, stock_name)

        logger.info(f"Added to watchlist: {stock_code} {stock_name}")

        return {
            'success': True,
            'message': f'Added {stock_code} to watchlist'
        }

    def remove_from_watchlist(self, stock_code: str) -> Dict:
        """
        从监控列表移除股票

        Args:
            stock_code: 股票代码

        Returns:
            操作结果
        """
        result = self.watcher.remove_stock(stock_code)

        logger.info(f"Removed from watchlist: {stock_code}")

        return {
            'success': True,
            'message': f'Removed {stock_code} from watchlist'
        }

    def get_watchlist(self) -> Dict[str, str]:
        """
        获取监控列表

        Returns:
            {stock_code: stock_name}
        """
        return self.watcher.get_watchlist()

    # ========================================================================
    # 监控循环
    # ========================================================================

    def run_monitoring_cycle(self):
        """执行一次完整的监控周期"""
        try:
            # 1. 更新实时行情
            logger.debug("Updating quotes...")
            self.watcher.update_quotes()

            # 2. 扫描和提醒
            logger.debug("Scanning for signals...")
            signals = self.scan_and_alert()

            # 3. 监控持仓（如果启用）
            if self.position_config.get('enabled', True):
                logger.debug("Monitoring positions...")
                self._monitor_positions()

            logger.info(f"Monitoring cycle completed, {len(signals)} signals detected")

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    def scan_and_alert(self) -> List[Signal]:
        """
        扫描信号并发送提醒

        Returns:
            检测到的信号列表
        """
        all_signals = []

        # 获取所有行情
        quotes = self.watcher.get_all_quotes()

        # 扫描每只股票
        watchlist = self.get_watchlist()

        for stock_code in watchlist.keys():
            # 检测信号
            signals = self.detector.detect_all_signals(stock_code)

            if signals:
                all_signals.extend(signals)

                # 发送提醒
                for signal in signals:
                    self.alert_manager.process_signal(signal)

                    # 记录活跃信号
                    self._record_signal(signal)

        return all_signals

    def _monitor_positions(self):
        """监控持仓"""
        # 获取持仓列表
        positions = self.risk_manager.get_all_positions()

        if not positions:
            logger.debug("No positions to monitor")
            return

        # 获取行情
        quotes = self.watcher.get_all_quotes()

        # 过滤出持仓股票的行情
        position_quotes = {
            code: quotes[code]
            for code in positions.keys()
            if code in quotes
        }

        # 监控持仓风险
        signals = self.position_monitor.monitor_positions(position_quotes)

        if signals:
            logger.info(f"Position monitoring detected {len(signals)} risk signals")

            # 发送提醒
            for signal in signals:
                self.alert_manager.process_signal(signal)
                self._record_signal(signal)

    def _record_signal(self, signal: Signal):
        """记录信号"""
        # 添加到活跃信号列表
        self.active_signals.append(signal)

        # 添加到历史记录
        self.signal_history.append({
            'timestamp': signal.timestamp,
            'stock_code': signal.stock_code,
            'stock_name': signal.stock_name,
            'signal_type': signal.signal_type,
            'description': signal.description,
            'priority': signal.priority
        })

        # 限制历史记录大小
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

    # ========================================================================
    # 报告生成
    # ========================================================================

    def generate_daily_summary(self) -> str:
        """
        生成每日总结报告

        Returns:
            总结报告文本
        """
        lines = []
        lines.append("=" * 60)
        lines.append("  每日监控总结")
        lines.append("=" * 60)
        lines.append("")

        # 基本信息
        lines.append(f"日期: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"服务状态: {'运行中' if self.is_running else '已停止'}")
        lines.append("")

        # 监控统计
        watchlist = self.get_watchlist()
        lines.append("【监控统计】")
        lines.append(f"监控股票数: {len(watchlist)} 只")

        # 今日信号统计
        today_signals = [
            s for s in self.signal_history
            if s['timestamp'].date() == datetime.now().date()
        ]

        lines.append(f"今日信号数: {len(today_signals)} 个")

        if today_signals:
            # 按类型统计
            buy_count = sum(1 for s in today_signals if s['signal_type'] == 'BUY')
            sell_count = sum(1 for s in today_signals if s['signal_type'] == 'SELL')
            warning_count = sum(1 for s in today_signals if s['signal_type'] == 'WARNING')

            lines.append(f"  买入信号: {buy_count} 个")
            lines.append(f"  卖出信号: {sell_count} 个")
            lines.append(f"  预警信号: {warning_count} 个")

        lines.append("")

        # 持仓信息
        positions = self.risk_manager.get_all_positions()
        lines.append("【持仓信息】")
        lines.append(f"持仓数量: {len(positions)} 只")

        if positions:
            # 组合健康评估
            health = self.position_monitor.assess_portfolio_health()
            lines.append(f"风险级别: {health['risk_level'].upper()}")
            lines.append(f"总盈亏: ¥{health['total_profit_loss']:,.2f} ({health['total_profit_loss_pct']:+.2%})")

            if health['warnings']:
                lines.append("\n⚠️  风险提示:")
                for warning in health['warnings'][:5]:  # 最多显示5条
                    lines.append(f"  - {warning}")

        lines.append("")

        # 活跃信号
        if self.active_signals:
            lines.append("【活跃信号】")
            # 显示最近5个信号
            recent_signals = sorted(
                self.active_signals,
                key=lambda x: x.timestamp,
                reverse=True
            )[:5]

            for signal in recent_signals:
                lines.append(f"  [{signal.priority}] {signal.stock_name}: {signal.description}")

        lines.append("")
        lines.append(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_active_signals(self) -> List[Signal]:
        """
        获取活跃信号

        Returns:
            活跃信号列表
        """
        return self.active_signals.copy()

    # ========================================================================
    # 主运行循环
    # ========================================================================

    def run(self):
        """
        运行监控服务（持续运行）

        用于生产环境的持续监控
        """
        self.start()

        logger.info(f"Monitoring service running with {self.update_interval}s interval")

        try:
            while self.is_running:
                # 执行监控周期
                self.run_monitoring_cycle()

                # 等待下一次更新
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()

        except Exception as e:
            logger.error(f"Monitoring service error: {e}")
            self.stop()
            raise

    def run_once(self):
        """
        运行一次监控（用于测试和手动触发）

        Returns:
            检测到的信号列表
        """
        logger.info("Running single monitoring cycle")

        self.run_monitoring_cycle()

        return self.get_active_signals()
