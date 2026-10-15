# Production Readiness Roadmap

## Current status

This repository currently demonstrates a database-monitoring dashboard. Fleet entries and telemetry are illustrative, workload scenarios are simulated, database registration does not authenticate to a database, and recommendations do not execute SQL.

Do not connect this demo to sensitive production systems or expose it publicly until the security and operational controls below are implemented and reviewed.

## Release-blocking requirements

- [ ] **Authentication and authorization:** protect the UI and every API endpoint; define operator and administrator roles.
- [ ] **Browser and network security:** replace permissive CORS with an explicit allowlist (or remove CORS when the UI and API are same-origin); add appropriate security headers and request limits.
- [ ] **Real database collectors:** implement engine-specific collectors using dedicated least-privilege accounts, connection timeouts, and bounded queries. Distinguish live, stale, missing, and simulated measurements.
- [ ] **Secrets:** use platform-managed secrets or a secret manager. Never log credentials or include them in audit events.
- [ ] **Persistent state:** store audit events, targets, recommendations, and history in durable storage with migrations and retention policies.
- [ ] **ML validation:** version the model and feature pipeline; evaluate against representative held-out data; document precision, recall, and false-positive rates; monitor drift; compare against a simple threshold baseline.
- [ ] **Safe remediation:** keep SQL execution disabled until there is a policy engine, explicit authorization, least-privilege executor, statement timeouts, plan validation, rollback strategy, and emergency kill switch.
- [ ] **Reliability testing:** add integration tests against real database containers, authorization tests, malformed-input tests, load tests, and failure/recovery tests.
- [ ] **Operations:** configure structured logs, metrics, alerting, backup/restore procedures, dependency and container scanning, and incident-response documentation.

## Minimum acceptance criteria

1. A collector reads metrics from a disposable test database and records source and collection timestamp.
2. Invalid credentials, unreachable hosts, timeouts, and unsupported engines fail safely without leaking secrets.
3. Tests verify unauthenticated access is denied for protected endpoints and unauthorized users cannot change settings.
4. Restarting the service does not erase audit history or registered targets.
5. Anomaly detection is evaluated on held-out data and compared with a simple baseline.
6. No remediation runs without policy checks and explicit authorization; failures are audited and recoverable.
7. A clean deployment passes CI, security checks, and documented smoke tests.

Passing this checklist is a prerequisite for a production review, not a guarantee of production readiness.
