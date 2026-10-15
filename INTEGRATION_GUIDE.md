# Delta ZIP: new implementation only

This archive intentionally excludes files already present in the GitHub repository:
`app/main.py`, `app/static/*`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`,
`README.md`, existing tests, and existing documentation are not duplicated.

## Contents and what each adds

- `app_ext/collectors/`: read-only collectors for PostgreSQL, MySQL/MariaDB, and SQLite.
- `app_ext/storage.py`: persistent SQLite storage for registered targets, metric snapshots, recommendations, and audit events.
- `app_ext/security.py`: bearer-token FastAPI dependency that fails closed in production if the token is missing.
- `app_ext/anomaly_detection.py`: transparent threshold baseline plus versioned IsolationForest scoring after at least 30 historical rows.
- `app_ext/optimization.py`: safe index proposal generator and approval record. It does not execute SQL.
- `tests_delta/`: tests for the new modules.
- `requirements-additions.txt`: only dependencies not present in the existing repository.
- `.github/workflows/delta-tests.yml`: separate CI workflow for delta-module tests.
- `INTEGRATION_GUIDE.md`: this guide.

## Additive install

Extract the ZIP into the repository root. These paths are new; do not replace existing files. In the project venv:

```powershell
python -m pip install -r requirements-additions.txt
python -m pytest -q tests_delta
```

The modules are deliberately namespaced under `app_ext` so they don't overwrite your current `app` package. The current `app/main.py` is still demo-oriented; the new modules must be wired into its endpoints to replace sample fleet data. That integration is not silently done by copying these files.

## Wire live collection into the existing API

Use the existing `/api/connect` endpoint as the place to register a target, but do not store a raw DSN or password in the target table. Store only an environment-variable name in `dsn_env_key`; put the actual DSN in the deployment's secret/environment configuration. Example:

```python
from app_ext.collectors import create_collector, CollectorError
from app_ext.storage import Store
from app_ext.anomaly_detection import score_history

store = Store()
# In a protected metrics endpoint:
# target = next(t for t in store.list_targets() if t["id"] == target_id)
# dsn = os.environ[target["dsn_env_key"]]
# snapshot = create_collector(target["engine"], dsn).collect()
# store.save_snapshot(target_id, snapshot)
# result = score_history(store.history(target_id), snapshot)
```

Protect all sensitive endpoints using FastAPI dependency injection, e.g. `Depends(require_api_token)`. The current frontend has no login/token-entry UI, so do not set `API_TOKEN` for browser use until a secure authenticated frontend or reverse proxy supplies it.

## Known scope boundary

SQL Server's collector is not included because `pyodbc` requires an OS-level SQL Server ODBC driver and environment-specific setup. The current UI contains SQL Server demo fleet entries; keep those marked demo/unverified until a compatible adapter and integration tests are added. No module in this archive executes remediation SQL automatically.
