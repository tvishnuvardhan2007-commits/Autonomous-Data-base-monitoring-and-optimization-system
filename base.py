from __future__ import annotations
from typing import Any, Protocol

class CollectorError(RuntimeError):
    """A safe, user-displayable database collection failure."""

class DatabaseCollector(Protocol):
    def collect(self) -> dict[str, Any]: ...
    def close(self) -> None: ...
