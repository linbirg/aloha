"""Aloha 日志模块

统一使用 lib/logger 的日志功能。

使用方式:
    from aloha.lib import logger
    logger.LOG_INFO(f"你好 {name}")
"""

import sys
from aloha.lib.logger import logger as _logger_instance, _LoggerProxy

# 初始化全局日志
_logger_instance.set_output_level("INFO")
_logger_instance.set_log_file(sys.stderr, {})


class _AlohaLogger:
    """Aloha 日志包装类"""

    def __init__(self, name: str = "aloha"):
        self._proxy = _LoggerProxy(_logger_instance)
        self._name = name

    def LOG_DEBUG(self, msg: str):
        self._proxy.DEBUG(msg)

    def LOG_TRACE(self, msg: str):
        self._proxy.TRACE(msg)

    def LOG_INFO(self, msg: str):
        self._proxy.INFO(msg)

    def LOG_ANNOUNCE(self, msg: str):
        self._proxy.ANNOUNCE(msg)

    def LOG_WARNING(self, msg: str):
        self._proxy.WARNING(msg)

    def LOG_FATAL(self, msg: str):
        self._proxy.FATAL(msg)


# 创建默认日志实例
logger = _AlohaLogger("aloha")


__all__ = ["logger"]
