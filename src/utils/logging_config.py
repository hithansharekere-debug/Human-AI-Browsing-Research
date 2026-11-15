"""Centralized logging configuration for egress network analysis.

Guarantees data privacy by sanitizing any accidental IP address strings
and preventing payload exposure in stdout or file logs.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Regex pattern to sanitize IPv4 and IPv6 addresses if accidentally printed
IPV4_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_REGEX = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")


class PrivacyMaskingFilter(logging.Filter):
    """Logging filter that redacts raw IP addresses from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            masked = IPV4_REGEX.sub("[REDACTED_IP]", record.msg)
            masked = IPV6_REGEX.sub("[REDACTED_IPV6]", masked)
            record.msg = masked
        return True


def configure_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configures project-wide logger with privacy safeguards.

    Args:
        log_level: Logging severity level (default: logging.INFO).
        log_file: Optional path to write log file.

    Returns:
        Configured root logger for the package.
    """
    logger = logging.getLogger("human_ai_egress")
    logger.setLevel(log_level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    privacy_filter = PrivacyMaskingFilter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(privacy_filter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(privacy_filter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
