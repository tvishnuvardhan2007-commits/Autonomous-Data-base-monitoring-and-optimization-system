from __future__ import annotations
from .base import CollectorError

def create_collector(engine: str, dsn: str, timeout_seconds: int = 4):
    """Build a supported collector. SQL Server requires a separate ODBC adapter."""
    normalized = engine.strip().lower().replace(" ", "")
    if normalized in {"postgres", "postgresql", "postgresql16"}:
        from .postgres import PostgreSQLCollector
        return PostgreSQLCollector(dsn, timeout_seconds)
    if normalized in {"mysql", "mysql8", "mariadb"}:
        from .mysql import MySQLCollector
        return MySQLCollector(dsn, timeout_seconds)
    if normalized in {"sqlite", "sqlite3"}:
        from .sqlite import SQLiteCollector
        return SQLiteCollector(dsn, timeout_seconds)
    if normalized in {"sqlserver", "mssql"}:
        raise CollectorError("SQL Server collector is not included in this delta. It needs pyodbc plus a compatible OS ODBC driver.")
    raise CollectorError(f"Unsupported database engine: {engine}")
