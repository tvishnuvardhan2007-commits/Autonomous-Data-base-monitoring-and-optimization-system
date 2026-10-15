"""Versioned, reproducible anomaly scoring with a transparent rule baseline."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

MODEL_VERSION = "isolation-forest-v1"
FEATURES = ("latency_ms", "cpu_pct", "connections")

def rule_baseline(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("latency_ms", 600, "high", "Query latency exceeds 600 ms."),
        ("cpu_pct", 85, "critical", "CPU utilization exceeds 85%."),
        ("connections", 80, "high", "Connection count exceeds 80."),
    ]
    findings = []
    for key, threshold, severity, message in checks:
        value = snapshot.get(key)
        if value is not None and float(value) >= threshold:
            findings.append({"feature":key,"value":float(value),"threshold":threshold,
                             "severity":severity,"message":message,"method":"rule-baseline",
                             "model_version":MODEL_VERSION})
    return findings

def score_history(history: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any]:
    """Fit only on prior history. Returns a safe 'insufficient_data' result until 30 rows."""
    baseline = rule_baseline(current)
    usable = [r for r in history if all(isinstance(r.get(k), (int,float)) for k in FEATURES)]
    result: dict[str, Any] = {
        "model_version": MODEL_VERSION, "features": list(FEATURES),
        "rule_findings": baseline, "ml_status": "insufficient_data",
        "ml_anomaly": None, "ml_score": None,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    if len(usable) < 30 or not all(isinstance(current.get(k), (int,float)) for k in FEATURES):
        return result
    try:
        from sklearn.ensemble import IsolationForest
        x = [[float(row[k]) for k in FEATURES] for row in usable[-500:]]
        model = IsolationForest(n_estimators=150, contamination="auto", random_state=42)
        model.fit(x)
        vector = [[float(current[k]) for k in FEATURES]]
        pred = int(model.predict(vector)[0])
        score = float(model.decision_function(vector)[0])
        result.update({"ml_status":"scored","ml_anomaly":pred == -1,"ml_score":round(score,6)})
    except ImportError:
        result["ml_status"] = "dependency_missing"
    except Exception as exc:
        result["ml_status"] = f"scoring_error:{type(exc).__name__}"
    return result
