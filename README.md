# Autonomous DB Monitoring & Optimization Platform

A responsive dark dashboard for a database monitoring project, based on the supplied UI references. It demonstrates a monitored database fleet, telemetry charts, workload simulation, anomaly feed, optimization recommendations, and an audit trail.

## Features

- Fleet health cards for PostgreSQL, MySQL, SQL Server, and SQLite demo targets.
- Live-refreshing telemetry chart UI (refreshes every 5 seconds).
- Workload simulator for baseline, slow query, CPU spike, connection flood, and lock contention scenarios.
- Demo anomaly feed and explainable advisory recommendations.
- Recommendation approve-for-review / dismiss actions and audit logging.
- Target registration form that explicitly labels new targets as **unverified**.
- Responsive layout for desktop and mobile.
- FastAPI endpoints, Docker build, Compose configuration, and CI test workflow.

## Run locally (Windows PowerShell)

From the extracted project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open:
- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## Run with Docker

```bash
docker compose up --build
```

Open http://127.0.0.1:8000. Stop with `docker compose down`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Deploy on Render

1. Push this project to a GitHub repository.
2. In Render choose **New → Web Service** and connect the repository.
3. Select **Docker** as the runtime (uses the included `Dockerfile`).
4. Deploy. Render detects the container port 8000 from the Dockerfile.
5. Open the generated service URL and test `/api/health`.

## Important implementation limits

- The UI intentionally includes sample fleet entries and illustrative telemetry. They are **not live measurements**.
- The workload simulator generates deterministic scenario metrics to demonstrate UI behavior; it does not stress a real database.
- The connect form does not save passwords and does not attempt a remote database login. A new target is marked `UNVERIFIED`.
- The anomaly list uses illustrative rule/scenario flags; no trained Isolation Forest model is bundled in this version.
- Recommendations are advice only. Approving one records human approval for review; it does **not** run SQL. Rollback is a preview-only action.
- No authentication is configured. Do not expose the demo publicly with sensitive data.
- Before production use, implement engine-specific least-privilege collectors, secret management, authenticated access, real metrics, model validation, and audited/approved change execution.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service health |
| GET | `/api/fleet` | Fleet overview |
| GET | `/api/metrics` | Demo telemetry series |
| GET | `/api/anomalies` | Anomaly feed |
| GET | `/api/recommendations` | Optimization advisory |
| POST | `/api/workload` | Simulate a scenario |
| POST | `/api/connect` | Register an unverified target |
| POST | `/api/actions` | Approve for review, dismiss, or preview rollback |
| GET | `/api/audit` | Audit trail |

## Repository integration

Copy the project contents into the root of your repository, keeping your presentation files. Ensure `.env` and `.venv` are not committed. Review changes, commit to a feature branch, and open a pull request before merging.
