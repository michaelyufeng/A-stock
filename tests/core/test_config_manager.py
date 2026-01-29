import pytest
from pathlib import Path
from src.core.config_manager import ConfigManager


class TestConfigManager:
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_load_config(self):
        """测试加载配置文件"""
        config = ConfigManager()
        assert config.config is not None
        assert 'data' in config.config
        assert 'ai' in config.config

    def test_get_value(self):
        """测试获取配置值"""
        config = ConfigManager()
        provider = config.get('data.provider')
        assert provider == 'akshare'

    def test_get_nested_value(self):
        """测试获取嵌套配置值"""
        config = ConfigManager()
        cache_ttl = config.get('data.cache.ttl.realtime')
        assert cache_ttl == 60

    def test_get_default_value(self):
        """测试获取默认值"""
        config = ConfigManager()
        value = config.get('non.existent.key', default='default_value')
        assert value == 'default_value'

    def test_get_section(self):
        """测试获取整个配置节"""
        config = ConfigManager()
        ai_config = config.get('ai')
        assert isinstance(ai_config, dict)
        assert ai_config['provider'] == 'deepseek'
