"""日志模块"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from src.core.config_manager import ConfigManager


_logger_initialized = False
_logger_cache = {}


def setup_logger(log_dir: Optional[str] = None, force: bool = False) -> None:
    """
    设置全局logger

    Args:
        log_dir: 日志目录路径
        force: 是否强制重新初始化
    """
    global _logger_initialized

    if _logger_initialized and not force:
        return

    # 如果强制重新初始化，先移除所有handlers
    if force or not _logger_initialized:
        logger.remove()

    # 加载配置
    config = ConfigManager()
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO')
    log_format = log_config.get('format',
                                 "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                                 "<level>{level: <8}</level> | "
                                 "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                                 "<level>{message}</level>")

    # 控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True
    )

    # 文件输出
    if log_dir is None:
        log_files = log_config.get('files', {})
        app_log = log_files.get('app', './logs/app.log')
        error_log = log_files.get('error', './logs/error.log')
    else:
        log_dir_path = Path(log_dir)
        app_log = log_dir_path / 'app.log'
        error_log = log_dir_path / 'error.log'

    # 确保日志目录存在
    Path(app_log).parent.mkdir(parents=True, exist_ok=True)
    Path(error_log).parent.mkdir(parents=True, exist_ok=True)

    # 应用日志
    logger.add(
        app_log,
        format=log_format,
        level='DEBUG',
        rotation=log_config.get('rotation', '100 MB'),
        retention=log_config.get('retention', '30 days'),
        compression='zip',
        encoding='utf-8'
    )

    # 错误日志
    logger.add(
        error_log,
        format=log_format,
        level='ERROR',
        rotation=log_config.get('rotation', '100 MB'),
        retention=log_config.get('retention', '30 days'),
        compression='zip',
        encoding='utf-8'
    )

    _logger_initialized = True


def get_logger(name: str):
    """
    获取logger实例

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    if not _logger_initialized:
        setup_logger()

    # 缓存相同名称的logger
    if name not in _logger_cache:
        _logger_cache[name] = logger.bind(name=name)

    return _logger_cache[name]


# 模块级别logger
log = get_logger(__name__)
