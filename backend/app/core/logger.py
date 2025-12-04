"""
Logging configuration using Loguru
"""

import sys

from loguru import logger

from app.core.settings import settings


def setup_logging():
    """Configure loguru logger with console and file outputs"""

    # Remove default handler
    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=settings.log_settings.STREAM_LEVEL,
    )

    logger.add(
        settings.log_settings.validated_dir_path / "app_{time:YYYY-MM-DD}.log",
        rotation=f"{settings.log_settings.FILE_ROTATION_MB} MB",
        retention=f"{settings.log_settings.FILE_RETENTION_DAYS} days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - "
            "{message}"
        ),
        level=settings.log_settings.FILE_LEVEL,
        enqueue=True,
    )

    logger.add(
        settings.log_settings.validated_dir_path / "errors_{time:YYYY-MM-DD}.log",
        rotation=f"{settings.log_settings.FILE_ROTATION_MB} MB",
        retention=f"{settings.log_settings.FILE_RETENTION_DAYS * 3} days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - "
            "{message}"
        ),
        level="ERROR",
        enqueue=True,
    )

    logger.info("Logging configured successfully")

    return logger
