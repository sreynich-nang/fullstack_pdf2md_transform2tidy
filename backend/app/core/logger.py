"""
Logging Configuration
"""
import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from typing import Optional

from app.core.config import settings


def setup_logger(name: str = "app") -> logging.Logger:
    """Setup application logger"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with custom format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Console formatter
    console_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with JSON format
    log_dir = settings.get_path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.INFO)
    
    # JSON formatter for file logs
    json_format = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(json_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger, defaulting to the root app logger."""
    return setup_logger(name or "app")


# Global logger instance
logger = get_logger()