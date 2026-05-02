"""
WhisperFlow — Centralized Logger
Rotating file handler + console output with configurable levels.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_logger_initialized = False


def setup_logger(
    name: str = "WhisperFlow",
    log_dir: Path = None,
    level: str = "INFO",
) -> logging.Logger:
    """
    Configure and return the application logger.
    Uses a rotating file handler (max 5 MB, 3 backups) and console output.
    """
    global _logger_initialized

    logger = logging.getLogger(name)

    if _logger_initialized:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "whisperflow.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger_initialized = True
    return logger


def get_logger(module_name: str = None) -> logging.Logger:
    """Get a child logger for a specific module."""
    base = logging.getLogger("WhisperFlow")
    if module_name:
        return base.getChild(module_name)
    return base
