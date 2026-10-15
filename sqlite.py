from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import time

from .base import CollectorError

class SQLiteCollector:
    """Read-only local SQLite metadata collector."""
    engine = "sqlite"

    def __init__(self, path: str, timeout_seconds: int = 4):
        self.path = str(Path(path).expanduser().resolve())
        self.timeout_seconds = max(1, min(int(timeout_seconds), 10))

    def collect(self) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            uri = Path(self.path).as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=self.timeout_seconds)
            try:
                cur = conn.cursor()
                cur.execute("PRAGMA database_list")
                dbs = cur.fetchall()
                cur.execute("SELECT sqlite_version()")
                version = cur.fetchone()[0]
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [r[0] for r in cur.fetchall()]
                cur.execute("PRAGMA page_count"); page_count = cur.fetchone()[0]
                cur.execute("PRAGMA page_size"); page_size = cur.fetchone()[0]
            finally:
                conn.close()
            return {
                "engine": self.engine, "source": "live", "database": self.path,
                "version": version, "collected_at": datetime.now(timezone.utc).isoformat(),
                "collector_latency_ms": round((time.perf_counter()-started)*1000, 2),
                "table_count": len(tables), "tables": tables[:100],
                "page_count": page_count, "page_size_bytes": page_size,
                "database_bytes": page_count * page_size,
                "connection_model": "embedded; no server connection counters",
            }
        except Exception as exc:
            raise CollectorError(f"SQLite collection failed ({type(exc).__name__}). Check that the file exists and is readable.") from exc

    def close(self) -> None:
        return None
