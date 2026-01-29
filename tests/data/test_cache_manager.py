import pytest
import time
from src.data.cache_manager import CacheManager


class TestCacheManager:
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = CacheManager()
        cache.set('test_key', 'test_value')
        result = cache.get('test_key')
        assert result == 'test_value'

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        cache = CacheManager()
        result = cache.get('nonexistent_key')
        assert result is None

    def test_get_with_default(self):
        """测试获取不存在的键返回默认值"""
        cache = CacheManager()
        result = cache.get('nonexistent_key', default='default_value')
        assert result == 'default_value'

    def test_delete(self):
        """测试删除缓存"""
        cache = CacheManager()
        cache.set('test_key', 'test_value')
        cache.delete('test_key')
        result = cache.get('test_key')
        assert result is None

    def test_clear(self):
        """测试清空缓存"""
        cache = CacheManager()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_ttl_expiration(self):
        """测试TTL过期"""
        cache = CacheManager()
        cache.set('test_key', 'test_value', ttl=1)  # 1秒过期
        time.sleep(1.5)
        result = cache.get('test_key')
        assert result is None
