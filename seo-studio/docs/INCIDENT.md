# Incident Response Playbook

This document outlines the procedure for responding to incidents in the SEO Studio application.

## Roles & Responsibilities

-   **Incident Commander (IC):** The person responsible for coordinating the response.
-   **Communications Lead (CL):** Responsible for communicating status to stakeholders.
-   **Technical Lead (TL):** The primary technical resource for diagnosing and resolving the issue.

## Incident Response Lifecycle

### 1. Detection & Alerting

-   Incidents are detected via automated monitoring (Prometheus/Grafana alerts, Sentry errors) or manual reports.
-   An alert is fired in the on-call channel (e.g., Slack, PagerDuty).

### 2. Triage & Assessment (First 5 Minutes)

-   The on-call engineer acknowledges the alert and assumes the role of Incident Commander.
-   **Goal:** Assess the impact. Is this a critical, user-facing outage? Is it a background job failure?
-   **Key Tools:**
    -   **System Health Dashboard:** Check API latency, error rates, and queue depths.
    -   **Logs:** Search logs by `request_id` or filter by `level:error`.

### 3. Containment & Mitigation (5-15 Minutes)

-   **Goal:** Stop the bleeding. This is not the time for a root cause analysis.
-   **Possible Actions:**
    -   **Rollback:** If the incident was caused by a recent deployment, the first action should be to roll back to the previous stable version.
    -   **Toggle a Feature Flag:** If the incident is tied to a new feature, disable it via the `/panel/system/flags` dashboard.
    -   **Scale Up Resources:** If the issue is due to load (e.g., growing queues), scale up the affected worker or web services.
    -   **Engage Circuit Breaker:** Manually open the circuit breaker for a failing external provider.
    -   **Restart Services:** A graceful restart of a service (`docker compose restart <service>`) can sometimes resolve transient issues.

### 4. Diagnosis & Resolution

-   Once the immediate impact is contained, the TL can begin a deeper investigation.
-   **Goal:** Identify the root cause and implement a permanent fix.
-   This may involve debugging, code changes, and deploying a hotfix.

### 5. Post-Incident Review

-   All incidents, regardless of severity, must have a post-mortem.
-   The review should be blameless and focus on identifying systemic issues.
-   **Action Items:** Create tickets for any follow-up work (e.g., adding more tests, improving monitoring, fixing the underlying bug).

## Common Incident Scenarios

### Scenario: High Error Rate on API

1.  **Triage:** Check the Health Dashboard for which endpoints are failing.
2.  **Containment:** If caused by a recent deploy, **rollback**.
3.  **Diagnosis:** Check logs for the failing endpoints. Is it a database error? A bug in the code? An issue with an external service?
4.  **Resolution:** Deploy a hotfix.

### Scenario: Celery Queues Growing Rapidly

1.  **Triage:** Identify the affected queue on the Health Dashboard.
2.  **Containment:** Scale up the workers for that queue: `docker compose up -d --scale <worker_service>=10`.
3.  **Diagnosis:** Check worker logs. Are tasks failing and being re-queued? Is there a poison pill message? Is a downstream service (DB, Redis, external API) slow?
4.  **Resolution:** If a task is failing repeatedly, consider purging the queue (`celery -A seo_studio purge -Q <queue_name>`) after inspecting the messages. Fix the underlying task code.
