"""配置管理器模块"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器（单例模式）"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """加载所有配置文件"""
        config_dir = Path(__file__).parent.parent.parent / 'config'

        # 加载主配置
        config_file = config_dir / 'config.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

        # 加载策略配置
        strategies_file = config_dir / 'strategies.yaml'
        if strategies_file.exists():
            with open(strategies_file, 'r', encoding='utf-8') as f:
                self._config['strategies'] = yaml.safe_load(f) or {}

        # 加载风控规则
        risk_rules_file = config_dir / 'risk_rules.yaml'
        if risk_rules_file.exists():
            with open(risk_rules_file, 'r', encoding='utf-8') as f:
                self._config['risk_rules'] = yaml.safe_load(f) or {}

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键，支持 'data.provider' 格式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
