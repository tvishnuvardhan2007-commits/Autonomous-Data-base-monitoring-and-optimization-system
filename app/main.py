from __future__ import annotations
import os, time, random, statistics
from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_TITLE = "Autonomous DB Monitoring & Optimization Platform"
app = FastAPI(title=APP_TITLE, version="1.0.0", description="Database telemetry, explainable anomaly detection, and reviewed optimization advice.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

STARTED = time.time()
AUDIT: list[dict[str, Any]] = []
ANOMALIES: list[dict[str, Any]] = [
    {"id":"anom-001","type":"HIGH_QUERY_LATENCY","severity":"warning","title":"Elevated query latency","details":"Demo telemetry shows query latency above the configured threshold.","score":-0.52,"status":"OPEN","created_at":datetime.now(timezone.utc).isoformat()},
    {"id":"anom-002","type":"LOCK_CONTENTION","severity":"critical","title":"Possible lock contention","details":"Simulated workload indicates concurrent transactions waiting on row locks. Verify with engine-native lock views.","score":-0.0664,"status":"OPEN","created_at":datetime.now(timezone.utc).isoformat()}
]
METRICS = [
    {"time":"05:31:32 PM","latency_ms":640,"cpu_pct":71,"connections":72},
    {"time":"05:32:32 PM","latency_ms":652,"cpu_pct":72.4,"connections":72},
    {"time":"05:33:32 PM","latency_ms":665,"cpu_pct":73.8,"connections":72},
    {"time":"05:34:32 PM","latency_ms":679,"cpu_pct":75.2,"connections":72},
    {"time":"05:35:32 PM","latency_ms":691,"cpu_pct":76.6,"connections":72},
    {"time":"05:36:32 PM","latency_ms":704,"cpu_pct":78.1,"connections":72},
]
FLEET = [
    {"id":"db-prod-commerce","name":"Production E-Commerce DBMS","engine":"PostgreSQL 16","database":"ecommerce_prod","host":"127.0.0.1","port":5432,"status":"HEALTHY","cpu_pct":None,"latency_ms":None,"connections":None,"source":"demo"},
    {"id":"db-analytics","name":"Analytics & Data Warehouse DBMS","engine":"MySQL 8","database":"analytics_dw","host":"10.0.2.15","port":3306,"status":"WARNING","cpu_pct":78.1,"latency_ms":704,"connections":72,"source":"demo"},
    {"id":"db-orders","name":"Order Processing DBMS","engine":"SQL Server","database":"orders_demo","host":"demo-sqlserver.local","port":1433,"status":"HEALTHY","cpu_pct":None,"latency_ms":None,"connections":None,"source":"demo"},
    {"id":"db-reporting","name":"Reporting Sandbox","engine":"SQLite","database":"reporting_demo.db","host":"local-file","port":0,"status":"HEALTHY","cpu_pct":None,"latency_ms":None,"connections":None,"source":"demo"},
    {"id":"db-customer","name":"Production Customer DBMS","engine":"PostgreSQL 16","database":"monitoring_db","host":"localhost","port":5432,"status":"CONNECTED","cpu_pct":None,"latency_ms":None,"connections":None,"source":"unverified"},
]
RECOMMENDATIONS = [
    {"id":"rec-001","title":"Review transaction deadlock and row-lock contention","severity":"high","category":"Concurrency","sql":"-- Review active locks and blocked sessions using engine-native views.\n-- Do not terminate sessions without operator approval.","reason":"The demo workload simulator flagged possible lock contention.","status":"RECOMMENDED"},
    {"id":"rec-002","title":"Investigate high-latency query candidates","severity":"medium","category":"Query tuning","sql":"-- Capture EXPLAIN / EXPLAIN ANALYZE for the slow query in a safe environment.\n-- Validate candidate indexes against workload and write overhead.","reason":"Demo latency is above the configured 600 ms threshold.","status":"RECOMMENDED"},
    {"id":"rec-003","title":"Review connection pool sizing","severity":"medium","category":"Capacity","sql":"-- Compare active/idle connections with max_connections and pool settings.\n-- Prefer application pool tuning over raising limits blindly.","reason":"Simulated connection count is near the configured warning threshold.","status":"RECOMMENDED"},
]

def audit(action: str, details: str, status: str = "RECORDED"):
    AUDIT.insert(0, {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "executed_by": "operator", "details": details, "status": status})
    del AUDIT[100:]

@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/static/index.html", encoding="utf-8") as f:
        return f.read()

@app.get("/api/health")
def health():
    return {"status":"ok","service":APP_TITLE,"uptime_seconds":round(time.time()-STARTED,1),"mode":os.getenv("APP_MODE","demo"),"timestamp":datetime.now(timezone.utc).isoformat()}

@app.get("/api/fleet")
def fleet():
    return {"items":FLEET,"summary":{"healthy":sum(x["status"]=="HEALTHY" for x in FLEET),"warning":sum(x["status"]=="WARNING" for x in FLEET),"critical":sum(x["status"]=="CRITICAL" for x in FLEET),"connected":sum(x["status"]=="CONNECTED" for x in FLEET)},"demo_data":True}

@app.get("/api/metrics")
def metrics():
    return {"items":METRICS,"updated_at":datetime.now(timezone.utc).isoformat(),"demo_data":True}

@app.get("/api/anomalies")
def anomalies():
    return {"items":ANOMALIES,"open_count":sum(a["status"]=="OPEN" for a in ANOMALIES),"demo_data":True}

@app.get("/api/recommendations")
def recommendations():
    return {"items":RECOMMENDATIONS,"note":"Recommendations are advisory. SQL is not executed automatically."}

class WorkloadRequest(BaseModel):
    scenario: str = Field(pattern="^(baseline|slow_query|cpu_spike|connection_flood|lock_contention)$")

@app.post("/api/workload")
def workload(req: WorkloadRequest):
    now = datetime.now(timezone.utc).strftime("%I:%M:%S %p")
    scenarios = {
        "baseline": (120, 34, 18, "NORMAL_LOAD", "Baseline workload is within demo thresholds.", "info"),
        "slow_query": (1250, 48, 25, "HIGH_QUERY_LATENCY", "Simulated slow query exceeds latency threshold. Capture an execution plan and inspect indexes.", "warning"),
        "cpu_spike": (310, 92, 31, "CPU_SPIKE", "Simulated CPU utilization is high. Identify top CPU queries before changing configuration.", "critical"),
        "connection_flood": (280, 62, 95, "CONNECTION_FLOOD", "Connection count is elevated. Inspect pool usage and idle sessions.", "warning"),
        "lock_contention": (860, 67, 44, "LOCK_CONTENTION", "Possible transaction lock contention. Inspect blockers and deadlock logs.", "critical"),
    }
    latency, cpu, conn, kind, message, severity = scenarios[req.scenario]
    METRICS.append({"time":now,"latency_ms":latency,"cpu_pct":cpu,"connections":conn})
    del METRICS[:-12]
    if req.scenario != "baseline":
        ANOMALIES.insert(0, {"id":f"anom-{int(time.time()*1000)}","type":kind,"severity":severity,"title":kind.replace("_"," ").title(),"details":message,"score":round(random.uniform(-0.75,-0.05),4),"status":"OPEN","created_at":datetime.now(timezone.utc).isoformat()})
        del ANOMALIES[30:]
    audit("WORKLOAD_SIMULATION", f"Scenario={req.scenario}; latency={latency}ms; cpu={cpu}%; connections={conn}", "SIMULATED")
    return {"scenario":req.scenario,"metric":{"time":now,"latency_ms":latency,"cpu_pct":cpu,"connections":conn},"anomaly":None if req.scenario=="baseline" else {"type":kind,"severity":severity,"message":message},"message":message,"demo_data":True}

class ConnectRequest(BaseModel):
    label: str = Field(min_length=2, max_length=80)
    engine: str = Field(pattern="^(PostgreSQL 16|MySQL 8|SQLite)$")
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=0, le=65535)
    database: str = Field(min_length=1, max_length=120)
    username: str = Field(default="", max_length=120)
    password: str = Field(default="", max_length=500)

@app.post("/api/connect")
def connect(req: ConnectRequest):
    # Avoid implying a live connection: this demo stores no credentials and does not attempt a remote login.
    audit("CONNECTION_REQUEST", f"Requested target {req.label} ({req.engine}) at {req.host}:{req.port}; credentials were not stored.", "NEEDS_DRIVER_SETUP")
    FLEET.append({"id":f"db-user-{int(time.time())}","name":req.label,"engine":req.engine,"database":req.database,"host":req.host,"port":req.port,"status":"UNVERIFIED","cpu_pct":None,"latency_ms":None,"connections":None,"source":"unverified"})
    return {"status":"UNVERIFIED","message":"Target saved as unverified. This demo does not test credentials or collect engine-native metrics. Configure a secure engine-specific connector before treating it as live.","credentials_saved":False}

class ActionRequest(BaseModel):
    recommendation_id: str
    action: str = Field(pattern="^(approve|dismiss|rollback_preview)$")

@app.post("/api/actions")
def action(req: ActionRequest):
    rec = next((r for r in RECOMMENDATIONS if r["id"] == req.recommendation_id), None)
    if not rec: raise HTTPException(404, "Recommendation not found")
    if req.action == "approve":
        # Explicitly record approval only; do not execute SQL.
        rec["status"] = "APPROVED FOR MANUAL REVIEW"
        audit("RECOMMENDATION_APPROVED", f"{rec['title']} approved for manual review; no SQL executed.", "APPROVED")
        return {"status":rec["status"],"message":"Approval recorded. No database change was executed."}
    if req.action == "dismiss":
        rec["status"] = "DISMISSED"
        audit("RECOMMENDATION_DISMISSED", rec["title"], "DISMISSED")
        return {"status":"DISMISSED","message":"Recommendation dismissed."}
    audit("ROLLBACK_PREVIEW", "Rollback workflow preview requested; no action taken.", "PREVIEW_ONLY")
    return {"status":"PREVIEW_ONLY","message":"Rollback is a preview only. No database change was executed."}

@app.get("/api/audit")
def audit_trail():
    return {"items":AUDIT}

@app.get("/api/config")
def config():
    return {"app_title":APP_TITLE,"refresh_seconds":5,"demo_mode":True,"features":["fleet overview","telemetry charts","workload simulator","anomaly feed","recommendations","audit trail","connect target form"],"safety":"No SQL is automatically executed."}
