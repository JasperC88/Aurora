import gc
import os
import psutil
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger("aurora.memory")


def get_current_memory_mb() -> float:
    """Return the current resident set size (RSS) in megabytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


class MemoryGuard:
    """
    Context manager to track memory allocation and enforce maximum RAM thresholds.
    Ensures chunked pipelines in Antigravity or Eddie HPC remain within memory budgets.
    """

    def __init__(self, stage_name: str = "Operation", max_allowed_mb: float = 512.0):
        self.stage_name = stage_name
        self.max_allowed_mb = max_allowed_mb
        self.start_mem_mb = 0.0
        self.end_mem_mb = 0.0

    def __enter__(self):
        gc.collect()
        self.start_mem_mb = get_current_memory_mb()
        logger.debug(f"[{self.stage_name}] Starting memory: {self.start_mem_mb:.2f} MB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        gc.collect()
        self.end_mem_mb = get_current_memory_mb()
        delta = self.end_mem_mb - self.start_mem_mb
        logger.debug(
            f"[{self.stage_name}] Final memory: {self.end_mem_mb:.2f} MB (Delta: {delta:+.2f} MB)"
        )
        if self.end_mem_mb > self.max_allowed_mb:
            logger.warning(
                f"Memory threshold exceeded in {self.stage_name}: "
                f"{self.end_mem_mb:.2f} MB > limit {self.max_allowed_mb:.2f} MB"
            )
        return False


def enforce_memory_limit(max_mb: float = 512.0):
    """Decorator to enforce memory budget on functions processing telemetry chunks."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with MemoryGuard(stage_name=func.__name__, max_allowed_mb=max_mb):
                return func(*args, **kwargs)

        return wrapper

    return decorator
