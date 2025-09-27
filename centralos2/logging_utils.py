"""Logging utilities."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import LoggingConfig


def configure_logging(cfg: LoggingConfig) -> Path:
    cfg.directory.mkdir(parents=True, exist_ok=True)
    log_path = cfg.directory / "centralos.log"

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, cfg.level.upper(), logging.INFO))

    # Clear default handlers if already configured
    logger.handlers = []

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(log_path, maxBytes=cfg.max_bytes, backupCount=cfg.backup_count)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bleak").setLevel(logging.INFO)

    logger.debug("Logging configured at %s", log_path)
    return log_path
