import pytest
from pathlib import Path
from src.core.logger import get_logger, setup_logger


class TestLogger:
    def test_get_logger(self):
        """测试获取logger实例"""
        logger = get_logger(__name__)
        assert logger is not None

    def test_logger_name(self):
        """测试logger名称"""
        logger = get_logger("test_module")
        # loguru logger不直接暴露name属性，但可以验证它能工作
        logger.info("Test message")

    def test_multiple_loggers_same_name(self):
        """测试同名logger是否相同"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        # loguru返回同一个logger实例
        assert logger1 is logger2

    def test_log_levels(self):
        """测试不同日志级别"""
        logger = get_logger("test_levels")
        # 验证不会抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logger_creates_log_dir(self, tmp_path):
        """测试setup_logger创建日志目录"""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir), force=True)
        assert log_dir.exists()
