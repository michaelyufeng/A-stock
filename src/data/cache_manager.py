"""缓存管理器模块"""
from pathlib import Path
from typing import Any, Optional
from diskcache import Cache as DiskCache
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器（基于diskcache）"""

    def __init__(self):
        """初始化缓存管理器"""
        config = ConfigManager()
        cache_config = config.get('data.cache', {})

        # 缓存目录
        cache_dir = cache_config.get('directory', './data/cache')
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # 是否启用缓存
        self._enabled = cache_config.get('enabled', True)

        # 初始化磁盘缓存
        self._cache = DiskCache(cache_dir)

        # 默认TTL配置
        self._default_ttl = cache_config.get('ttl', {})

        logger.info(f"Cache manager initialized: dir={cache_dir}, enabled={self._enabled}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        if not self._enabled:
            logger.debug(f"Cache disabled, returning default for key: {key}")
            return default

        try:
            value = self._cache.get(key, default=default)
            if value != default:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示不过期

        Returns:
            是否设置成功
        """
        if not self._enabled:
            logger.debug(f"Cache disabled, skipping set for key: {key}")
            return False

        try:
            self._cache.set(key, value, expire=ttl)
            logger.debug(f"Cache set: {key} (ttl={ttl})")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if not self._enabled:
            logger.debug(f"Cache disabled, skipping delete for key: {key}")
            return False

        try:
            result = self._cache.delete(key)
            logger.debug(f"Cache delete: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        if not self._enabled:
            logger.debug("Cache disabled, skipping clear")
            return False

        try:
            self._cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_ttl(self, data_type: str) -> Optional[int]:
        """
        获取指定数据类型的默认TTL

        Args:
            data_type: 数据类型 ('realtime', 'daily', 'financial')

        Returns:
            TTL秒数，如果不存在返回None
        """
        ttl = self._default_ttl.get(data_type)
        logger.debug(f"Get TTL for {data_type}: {ttl}")
        return ttl

    def __del__(self):
        """清理资源（关闭cache）"""
        if hasattr(self, '_cache'):
            try:
                self._cache.close()
                logger.debug("Cache closed")
            except Exception as e:
                logger.error(f"Error closing cache: {e}")
