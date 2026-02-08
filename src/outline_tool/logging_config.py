"""
Logging configuration for Outline Tool.

This module centralizes logging setup so every layer can use consistent loggers.
"""

from __future__ import annotations

import logging
import logging.config
from typing import Any


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        level: Root logging level (e.g., "DEBUG", "INFO").
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "standard"}
        },
        "root": {"handlers": ["console"], "level": level},
    }
    logging.config.dictConfig(config)