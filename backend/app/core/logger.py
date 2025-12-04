"""
Logging configuration using Loguru
"""

import logging
import sys

from loguru import logger

from app.core.settings import settings


# Intercept SQLAlchemy logs and route to loguru
class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect to Loguru"""

    def emit(self, record):
        # Map SQLAlchemy INFO logs to Loguru DEBUG
        if record.name.startswith("sqlalchemy") and record.levelname == "INFO":
            level = "DEBUG"
        else:
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # type: ignore
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Configure loguru logger with console and file outputs"""

    # Remove default handler
    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
            # "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
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
            # "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        ),
        level=settings.log_settings.FILE_LEVEL,
        # enqueue=True,
    )

    logger.add(
        settings.log_settings.validated_dir_path / "errors_{time:YYYY-MM-DD}.log",
        rotation=f"{settings.log_settings.FILE_ROTATION_MB} MB",
        retention=f"{settings.log_settings.FILE_RETENTION_DAYS * 3} days",
        compression="zip",
        format=(
            # "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        ),
        level="ERROR",
        # enqueue=True,
    )

    # Intercept everything from standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.DEBUG, force=True)

    # Remove all handlers from root logger and add our interceptor
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(logging.DEBUG)

    # Configure all known loggers to use our handler
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith(("uvicorn", "fastapi", "sqlalchemy")):
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers = []
            logging_logger.propagate = True

    # Map SQLAlchemy INFO to DEBUG after logging is configured
    class SQLAlchemyFilter(logging.Filter):
        def filter(self, record):
            # Map SQLAlchemy INFO logs to DEBUG level
            if record.name.startswith("sqlalchemy") and record.levelname == "INFO":
                record.levelname = "DEBUG"
                record.levelno = logging.DEBUG
            return True

    # Add filter to SQLAlchemy loggers
    for logger_name in ["sqlalchemy.engine", "sqlalchemy.pool"]:
        logging.getLogger(logger_name).addFilter(SQLAlchemyFilter())

    logger.info("Logging configured successfully")

    return logger
