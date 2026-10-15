from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_fleet_has_demo_targets():
    response = client.get("/api/fleet")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 4
    assert data["demo_data"] is True

def test_workload_scenario_creates_metric_and_audit():
    response = client.post("/api/workload", json={"scenario":"slow_query"})
    assert response.status_code == 200
    assert response.json()["metric"]["latency_ms"] == 1250
    assert client.get("/api/audit").json()["items"]

def test_connect_does_not_store_credentials():
    response = client.post("/api/connect", json={
        "label":"Test database","engine":"PostgreSQL 16","host":"localhost",
        "port":5432,"database":"testdb","username":"demo","password":"secret"
    })
    assert response.status_code == 200
    assert response.json()["credentials_saved"] is False
    assert "secret" not in str(client.get("/api/audit").json())
