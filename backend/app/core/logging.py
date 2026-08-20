"""Structured logging setup, shared by the API process and Celery workers."""
import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    # Quiet noisy third-party loggers by default.
    for noisy in ("httpx", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
