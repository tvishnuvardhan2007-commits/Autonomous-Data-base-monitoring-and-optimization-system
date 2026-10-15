"""Read-only engine-specific database telemetry collectors."""
from .base import CollectorError
from .factory import create_collector

__all__ = ["CollectorError", "create_collector"]
