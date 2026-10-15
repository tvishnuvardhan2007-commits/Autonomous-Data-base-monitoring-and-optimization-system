from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
import time

from .base import CollectorError

class PostgreSQLCollector:
    """Read-only PostgreSQL telemetry. Requires psycopg[binary]."""
    engine = "postgresql"

    def __init__(self, dsn: str, timeout_seconds: int = 4):
        if not dsn or not dsn.startswith(("postgres://", "postgresql://")):
            raise ValueError("A PostgreSQL DSN is required.")
        self.dsn = dsn
        self.timeout_seconds = max(1, min(int(timeout_seconds), 10))

    def collect(self) -> dict[str, Any]:
        try:
            import psycopg
            from psycopg.rows import dict_row
            started = time.perf_counter()
            with psycopg.connect(
                self.dsn, connect_timeout=self.timeout_seconds,
                options=f"-c statement_timeout={self.timeout_seconds * 1000}",
                row_factory=dict_row,
                application_name="db-sentinel-monitor",
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT current_database() AS database_name,
                               current_user AS username,
                               (SELECT count(*) FROM pg_stat_activity
                                WHERE datname = current_database()) AS connections,
                               (SELECT setting::int FROM pg_settings
                                WHERE name = 'max_connections') AS max_connections,
                               (SELECT count(*) FROM pg_stat_activity
                                WHERE datname = current_database() AND state = 'active') AS active_queries,
                               (SELECT count(*) FROM pg_stat_activity
                                WHERE datname = current_database()
                                  AND wait_event_type IS NOT NULL) AS waiting_queries,
                               (SELECT COALESCE(sum(blks_hit),0) FROM pg_stat_database
                                WHERE datname = current_database()) AS cache_hits,
                               (SELECT COALESCE(sum(blks_read),0) FROM pg_stat_database
                                WHERE datname = current_database()) AS disk_reads,
                               (SELECT COALESCE(sum(deadlocks),0) FROM pg_stat_database
                                WHERE datname = current_database()) AS deadlocks,
                               (SELECT COALESCE(sum(xact_commit+xact_rollback),0)
                                FROM pg_stat_database WHERE datname = current_database()) AS transactions
                    """)
                    row = dict(cur.fetchone())
                    # Optional extension. Failure here does not invalidate core metrics.
                    slow_queries = []
                    try:
                        cur.execute("""
                            SELECT left(query, 500) AS query, calls,
                                   round(total_exec_time::numeric, 2) AS total_ms,
                                   round(mean_exec_time::numeric, 2) AS mean_ms, rows
                            FROM pg_stat_statements
                            WHERE dbid = (SELECT oid FROM pg_database
                                          WHERE datname = current_database())
                            ORDER BY total_exec_time DESC LIMIT 5
                        """)
                        slow_queries = [dict(r) for r in cur.fetchall()]
                    except Exception:
                        conn.rollback()
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            max_conn = max(1, int(row.get("max_connections") or 1))
            hits, reads = int(row.get("cache_hits") or 0), int(row.get("disk_reads") or 0)
            return {
                "engine": self.engine, "source": "live", "database": row["database_name"],
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "collector_latency_ms": elapsed_ms,
                "connections": int(row.get("connections") or 0),
                "max_connections": max_conn,
                "connection_utilization_pct": round(100 * int(row.get("connections") or 0) / max_conn, 2),
                "active_queries": int(row.get("active_queries") or 0),
                "waiting_queries": int(row.get("waiting_queries") or 0),
                "cache_hit_ratio_pct": round(100 * hits / (hits + reads), 2) if hits + reads else None,
                "disk_reads": reads, "deadlocks": int(row.get("deadlocks") or 0),
                "transactions": int(row.get("transactions") or 0),
                "slow_queries": slow_queries,
            }
        except ImportError as exc:
            raise CollectorError("Install psycopg[binary] to collect PostgreSQL metrics.") from exc
        except Exception as exc:
            # Do not echo DSNs or exception strings that may contain secrets.
            raise CollectorError(f"PostgreSQL collection failed ({type(exc).__name__}). Check network, permissions, and timeout.") from exc

    def close(self) -> None:
        return None
