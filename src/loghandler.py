"""Simplify use of logging."""

import logging
from enum import Enum


class LogLevel(Enum):
    """Available log levels."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


def set_log_format(logger: logging.Logger) -> None:
    """Set the log format for given logger."""
    new_formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for handler in logger.handlers:
        handler.setFormatter(new_formatter)


def set_loglevel(logger: logging.Logger, level: LogLevel) -> None:
    """Set the log level for your logger."""
    logger.setLevel(level.value)
    set_log_format(logger)


def setup_logger(name: str) -> logging.Logger:
    """Setups a logger to use in your modules."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Prevents forwarding to root logger
    logger.propagate = False

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Add formatter to ch
    ch.setFormatter(formatter)
    # Add ch to logger
    logger.addHandler(ch)

    return logger


def modify_scapy_log() -> None:
    """Customize the scappy logger."""
    # Modify logger for scappy
    scapy_logger = logging.getLogger("scapy.runtime")
    scapy_logger.setLevel(logging.INFO)  # Log-Level anpassen

    # New handler with custom formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    scapy_logger.addHandler(handler)

    # Deactivate forwarding to root logger
    scapy_logger.propagate = False
