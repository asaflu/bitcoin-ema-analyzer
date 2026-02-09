"""
Logging configuration for the application.
"""

import logging
import sys
from config import LOG_FORMAT, LOG_LEVEL


def setup_logger(name: str = "bitcoin_db", level: str = LOG_LEVEL) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


# Default logger instance
logger = setup_logger()
