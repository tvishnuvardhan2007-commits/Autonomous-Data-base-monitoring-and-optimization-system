"""Durable SQLite storage for registered targets, snapshots, recommendations, and audit events."""
from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from typing import Any

class Store:
    def __init__(self, path: str | None = None):
        self.path = path or os.getenv("MONITOR_STORE_PATH", "data/monitor_store.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS targets(
              id TEXT PRIMARY KEY, label TEXT NOT NULL, engine TEXT NOT NULL,
              dsn_env_key TEXT NOT NULL, created_at TEXT NOT NULL,
              enabled INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS snapshots(
              id INTEGER PRIMARY KEY AUTOINCREMENT, target_id TEXT NOT NULL,
              collected_at TEXT NOT NULL, source TEXT NOT NULL, payload TEXT NOT NULL,
              FOREIGN KEY(target_id) REFERENCES targets(id)
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_target_time ON snapshots(target_id,collected_at);
            CREATE TABLE IF NOT EXISTS recommendations(
              id TEXT PRIMARY KEY, target_id TEXT NOT NULL, status TEXT NOT NULL,
              payload TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events(
              id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              actor TEXT NOT NULL, action TEXT NOT NULL, target_id TEXT,
              outcome TEXT NOT NULL, details TEXT NOT NULL
            );
            """)

    def register_target(self, target_id: str, label: str, engine: str, dsn_env_key: str, created_at: str):
        if not dsn_env_key.isidentifier():
            raise ValueError("dsn_env_key must be an environment variable name.")
        with self._conn() as c:
            c.execute("INSERT INTO targets(id,label,engine,dsn_env_key,created_at) VALUES(?,?,?,?,?)",
                      (target_id,label,engine,dsn_env_key,created_at))
        self.audit("system", "target_registered", target_id, "UNVERIFIED",
                   {"label":label,"engine":engine,"dsn_env_key":dsn_env_key})

    def list_targets(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute("SELECT id,label,engine,dsn_env_key,created_at,enabled FROM targets ORDER BY created_at DESC")]

    def save_snapshot(self, target_id: str, snapshot: dict[str, Any]):
        with self._conn() as c:
            c.execute("INSERT INTO snapshots(target_id,collected_at,source,payload) VALUES(?,?,?,?)",
                      (target_id,snapshot["collected_at"],snapshot.get("source","live"),json.dumps(snapshot, default=str)))

    def history(self, target_id: str, limit: int = 100):
        if not 1 <= limit <= 1000: raise ValueError("limit must be 1..1000")
        with self._conn() as c:
            rows = c.execute("SELECT payload FROM snapshots WHERE target_id=? ORDER BY id DESC LIMIT ?",(target_id,limit)).fetchall()
        return [json.loads(r["payload"]) for r in reversed(rows)]

    def audit(self, actor: str, action: str, target_id: str | None, outcome: str, details: dict[str, Any]):
        with self._conn() as c:
            c.execute("INSERT INTO audit_events(actor,action,target_id,outcome,details) VALUES(?,?,?,?,?)",
                      (actor,action,target_id,outcome,json.dumps(details, default=str)))

    def audit_events(self, limit: int = 100):
        if not 1 <= limit <= 1000: raise ValueError("limit must be 1..1000")
        with self._conn() as c:
            rows = c.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [{**dict(r),"details":json.loads(r["details"])} for r in rows]
