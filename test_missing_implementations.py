import os
import sqlite3
import tempfile
import pytest

from app_ext.collectors.factory import create_collector
from app_ext.collectors.base import CollectorError
from app_ext.collectors.sqlite import SQLiteCollector
from app_ext.storage import Store
from app_ext.anomaly_detection import score_history, rule_baseline
from app_ext.optimization import propose_index, approve_proposal
from app_ext.security import require_api_token
from fastapi import HTTPException

def test_sqlite_collector_read_only_snapshot():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        con = sqlite3.connect(f.name)
        con.execute("CREATE TABLE demo(id INTEGER PRIMARY KEY)")
        con.execute("INSERT INTO demo DEFAULT VALUES")
        con.commit(); con.close()
        data = SQLiteCollector(f.name).collect()
        assert data["source"] == "live"
        assert data["table_count"] == 1
        assert data["database_bytes"] > 0

def test_factory_engine_support_and_sqlserver_explained():
    assert create_collector("sqlite", "/tmp/example.db").engine == "sqlite"
    with pytest.raises(CollectorError, match="SQL Server collector is not included"):
        create_collector("sqlserver", "mssql://localhost/db")

def test_store_persists_snapshots_and_audit():
    with tempfile.TemporaryDirectory() as d:
        s = Store(os.path.join(d, "store.db"))
        s.register_target("t1", "demo", "sqlite", "DEMO_DSN", "2026-01-01T00:00:00Z")
        snap = {"collected_at":"2026-01-01T00:00:00Z","source":"live","connections":3}
        s.save_snapshot("t1", snap)
        assert s.history("t1")[0]["connections"] == 3
        assert s.list_targets()[0]["id"] == "t1"
        assert s.audit_events(10)[0]["action"] == "target_registered"

def test_rules_and_ml_insufficient_data():
    assert rule_baseline({"latency_ms":800})[0]["feature"] == "latency_ms"
    result = score_history([], {"latency_ms":10,"cpu_pct":10,"connections":1})
    assert result["ml_status"] == "insufficient_data"

def test_index_proposal_is_review_only():
    p = propose_index("db1", "orders", "customer_id", "query scans orders by customer_id")
    assert "CREATE INDEX CONCURRENTLY" in p.sql_preview
    with pytest.raises(ValueError):
        propose_index("db1", "orders; DROP TABLE x", "id", "bad input")
    with pytest.raises(PermissionError):
        approve_proposal(p, "operator", False)
    approved = approve_proposal(p, "operator", True)
    assert approved["executed"] is False

def test_bearer_token_fails_closed_in_production(monkeypatch):
    monkeypatch.setenv("APP_MODE", "production")
    monkeypatch.delenv("API_TOKEN", raising=False)
    with pytest.raises(HTTPException) as e:
        require_api_token(None)
    assert e.value.status_code == 503
