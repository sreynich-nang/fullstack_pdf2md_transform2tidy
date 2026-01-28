"""
Timing Utilities
"""
import time
from contextlib import contextmanager
from typing import Optional

from app.core.logger import logger


class Timer:
    """Simple timer class"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Stop the timer and return elapsed time"""
        self.end_time = time.time()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """Get elapsed time"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else time.time()
        return round(end - self.start_time, 3)


@contextmanager
def log_timing(stage: str, file_id: Optional[str] = None):
    """
    Context manager for timing and logging operations
    
    Usage:
        with log_timing("extraction", file_id="abc123"):
            # ... do work ...
    """
    start = time.time()
    extra = {"file_id": file_id} if file_id else {}
    
    logger.info(f"Starting {stage}", extra=extra)
    
    try:
        yield
    except Exception as e:
        duration = time.time() - start
        logger.error(
            f"Failed {stage} after {duration:.3f}s: {str(e)}",
            extra={**extra, "duration_seconds": duration, "error": str(e)}
        )
        raise
    else:
        duration = time.time() - start
        logger.info(
            f"Completed {stage} in {duration:.3f}s",
            extra={**extra, "duration_seconds": duration}
        )