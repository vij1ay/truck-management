"""
Logging configuration for the Transport Management System.

Features:
- Rotating file handler with configurable max size and backup count
- Console handler for development
- Structured log format with timestamps
- Different log levels per environment
"""

import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Log configuration constants
LOG_DIR = Path("logs")
LOG_FILE = "app.log"
MAX_LOG_SIZE = 20 * 1024 * 1024  # 20 MB
BACKUP_COUNT = 100  # Maximum 100 log files

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(trace_id)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


trace_id_ctx_var: ContextVar[str] = ContextVar("trace_id", default="-")


class TraceIdFilter(logging.Filter):
    """Inject request trace ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - thin wrapper
        record.trace_id = trace_id_ctx_var.get("-")
        return True


def set_trace_id(trace_id: str):
    """Set the current trace ID in a context variable."""
    return trace_id_ctx_var.set(trace_id)


def get_trace_id() -> str:
    """Get the current trace ID (\"-\" if none is set)."""
    return trace_id_ctx_var.get("-")


def reset_trace_id(token) -> None:
    """Reset the trace ID context to a previous token."""
    trace_id_ctx_var.reset(token)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> logging.Logger:
    """
    Configure and return the root application logger.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        log_file: Log file name (default: app.log)
        enable_console: Enable console output
        enable_file: Enable file output
    
    Returns:
        Configured root logger
    """
    # Use defaults if not specified
    log_dir = log_dir or LOG_DIR
    log_file = log_file or LOG_FILE
    
    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the root logger for the app
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter and trace filter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    trace_filter = TraceIdFilter()
    
    # File handler with rotation
    if enable_file:
        file_path = log_dir / log_file
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # File captures all levels
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        logger.addHandler(file_handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        console_handler.addFilter(trace_filter)
        logger.addHandler(console_handler)

    # Ensure logger itself also applies trace filter (covers any future handlers)
    logger.addFilter(trace_filter)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (e.g., "app.services.auth")
    
    Returns:
        Logger instance for the module
    
    Usage:
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("This is an info message")
    """
    return logging.getLogger(name)


# Initialize the root app logger on module import
_root_logger: Optional[logging.Logger] = None


def init_logger(debug: bool = False) -> logging.Logger:
    """
    Initialize the application logger.
    
    Should be called once at application startup.
    
    Args:
        debug: Enable debug mode with more verbose logging
    
    Returns:
        Configured root logger
    """
    global _root_logger
    
    log_level = "DEBUG" if debug else "INFO"
    _root_logger = setup_logging(
        log_level=log_level,
        enable_console=True,
        enable_file=True,
    )
    
    _root_logger.info(f"Logger initialized with level: {log_level}")
    _root_logger.info(f"Log directory: {LOG_DIR.absolute()}")
    _root_logger.info(f"Max log file size: {MAX_LOG_SIZE / (1024*1024):.0f} MB")
    _root_logger.info(f"Max backup files: {BACKUP_COUNT}")
    
    return _root_logger


def get_root_logger() -> logging.Logger:
    """Get the root application logger, initializing if necessary."""
    global _root_logger
    if _root_logger is None:
        _root_logger = init_logger()
    return _root_logger


# Convenience logging functions for quick access
class AppLogger:
    """
    Convenience class for application-wide logging.
    
    Usage:
        from app.core.logger import AppLogger
        AppLogger.info("User logged in", user_id="123")
    """
    
    @staticmethod
    def _get_logger() -> logging.Logger:
        return get_root_logger()
    
    @staticmethod
    def debug(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().debug(full_message)
    
    @staticmethod
    def info(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().info(full_message)
    
    @staticmethod
    def warning(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().warning(full_message)
    
    @staticmethod
    def error(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().error(full_message)
    
    @staticmethod
    def critical(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().critical(full_message)
    
    @staticmethod
    def exception(message: str, **kwargs):
        extra = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra}" if extra else message
        AppLogger._get_logger().exception(full_message)
