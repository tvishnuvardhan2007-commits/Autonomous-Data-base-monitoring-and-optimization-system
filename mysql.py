from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, unquote
import time

from .base import CollectorError

class MySQLCollector:
    """Read-only MySQL/MariaDB collector. Requires PyMySQL."""
    engine = "mysql"

    def __init__(self, dsn: str, timeout_seconds: int = 4):
        parsed = urlparse(dsn)
        if parsed.scheme not in {"mysql", "mysql+pymysql", "mariadb"}:
            raise ValueError("A mysql:// or mariadb:// DSN is required.")
        self.settings = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": parsed.path.lstrip("/"),
            "connect_timeout": max(1, min(int(timeout_seconds), 10)),
            "read_timeout": max(1, min(int(timeout_seconds), 10)),
            "write_timeout": max(1, min(int(timeout_seconds), 10)),
            "cursorclass": None,
            "autocommit": True,
        }

    def collect(self) -> dict[str, Any]:
        try:
            import pymysql
            started = time.perf_counter()
            cfg = dict(self.settings)
            cfg.pop("cursorclass", None)
            with pymysql.connect(**cfg) as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Threads_running','Questions','Slow_queries','Innodb_row_lock_waits')")
                    status = {r["Variable_name"]: int(r["Value"]) for r in cur.fetchall()}
                    cur.execute("SHOW VARIABLES LIKE 'max_connections'")
                    row = cur.fetchone()
                    max_conn = int(row["Value"]) if row else 1
                    cur.execute("SELECT DATABASE() AS database_name, VERSION() AS version")
                    info = cur.fetchone()
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            connections = status.get("Threads_connected", 0)
            return {
                "engine": self.engine, "source": "live", "database": info["database_name"],
                "version": info["version"], "collected_at": datetime.now(timezone.utc).isoformat(),
                "collector_latency_ms": elapsed, "connections": connections,
                "max_connections": max_conn,
                "connection_utilization_pct": round(100 * connections / max(1, max_conn), 2),
                "active_queries": status.get("Threads_running", 0),
                "waiting_queries": status.get("Innodb_row_lock_waits", 0),
                "slow_queries_count": status.get("Slow_queries", 0),
                "transactions_or_questions": status.get("Questions", 0),
            }
        except ImportError as exc:
            raise CollectorError("Install PyMySQL to collect MySQL metrics.") from exc
        except Exception as exc:
            raise CollectorError(f"MySQL collection failed ({type(exc).__name__}). Check network, permissions, and timeout.") from exc

    def close(self) -> None:
        return None
