"""日志工具模块 - 提供彩色日志输出，零依赖实现

支持彩色终端输出和文件日志记录，使用ANSI转义码实现。
"""

import sys
import os
import logging
from datetime import datetime
from typing import Optional


# ANSI颜色代码
class Colors:
    """ANSI终端颜色常量"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # 前景色
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # 背景色
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class ColorFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # 日志级别对应的颜色
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BG_RED + Colors.WHITE,
    }

    # 日志级别对应的前缀
    LEVEL_PREFIX = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO ",
        logging.WARNING: "WARN ",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "FATAL",
    }

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color:
            color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
            prefix = self.LEVEL_PREFIX.get(record.levelno, "?????")
            message = record.getMessage()
            # 带时间戳的格式
            timestamp = datetime.now().strftime("%H:%M:%S")
            return f"{Colors.DIM}{timestamp}{Colors.RESET} {color}{Colors.BOLD}{prefix}{Colors.RESET} {message}"
        else:
            return super().format(record)


def get_logger(
    name: str = "netbridge",
    level: int = logging.INFO,
    enable_file: bool = False,
    log_dir: Optional[str] = None,
) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        enable_file: 是否启用文件日志
        log_dir: 日志文件目录，默认为 ~/.netbridge/logs

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter(use_color=True))
    logger.addHandler(console_handler)

    # 文件handler（可选）
    if enable_file:
        if log_dir is None:
            log_dir = os.path.expanduser("~/.netbridge/logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(
            log_dir,
            f"netbridge_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger


# 便捷函数
def info(msg: str) -> None:
    """输出INFO级别日志"""
    get_logger().info(msg)


def warning(msg: str) -> None:
    """输出WARNING级别日志"""
    get_logger().warning(msg)


def error(msg: str) -> None:
    """输出ERROR级别日志"""
    get_logger().error(msg)


def debug(msg: str) -> None:
    """输出DEBUG级别日志"""
    get_logger().debug(msg)


def success(msg: str) -> None:
    """输出成功信息（绿色）"""
    print(f"{Colors.GREEN}{Colors.BOLD}  OK{Colors.RESET} {msg}")


def fail(msg: str) -> None:
    """输出失败信息（红色）"""
    print(f"{Colors.RED}{Colors.BOLD}FAIL{Colors.RESET} {msg}")


def status(msg: str) -> None:
    """输出状态信息（蓝色）"""
    print(f"{Colors.BLUE}{Colors.BOLD} >>>{Colors.RESET} {msg}")


def highlight(msg: str) -> None:
    """输出高亮信息"""
    print(f"{Colors.CYAN}{Colors.BOLD}{msg}{Colors.RESET}")


def dim(msg: str) -> None:
    """输出暗色信息"""
    print(f"{Colors.DIM}{msg}{Colors.RESET}")


def colored_text(text: str, color: str) -> str:
    """给文本添加颜色

    Args:
        text: 原始文本
        color: ANSI颜色代码

    Returns:
        带颜色标记的文本
    """
    return f"{color}{text}{Colors.RESET}"
