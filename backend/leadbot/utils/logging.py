"""Shared logging configuration for API and workers."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_app_logging(*, log_level: str = "INFO", log_file: str = "logs/leady-api.log") -> None:
    """Configure root logging with a rotating file handler.

    This is idempotent and safe to call multiple times.
    """

    root_logger = logging.getLogger()
    if getattr(root_logger, "_leady_logging_configured", False):
        return

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.setLevel(log_level.upper())
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    setattr(root_logger, "_leady_logging_configured", True)
