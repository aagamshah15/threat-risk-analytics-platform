# Phase 4 Recruiter Demo Path

## Goal
Show end-to-end data engineering capability: ingestion, streaming, orchestration, serving API, and stakeholder dashboard.

## One-command startup

```bash
make demo-p4
```

This command:
1. Starts full stack (Phase 1 + 2 + 3 + 4 services)
2. Initializes Prefect work pool
3. Runs the orchestrated pipeline flow once
4. Prints key URLs and API health

## Demo script (5-10 minutes)

1. Open Prefect UI: `http://localhost:4200`
- Show latest flow run and task states.

2. Open API docs: `http://localhost:8000/docs`
- Call:
  - `/health`
  - `/v1/pipeline/summary`
  - `/v1/trends/threat-events`
  - `/v1/risk/kev-summary`

3. Open dashboard: `http://localhost:8501`
- Page: Pipeline Health
- Page: Stream Freshness/Lag Trends
- Page: Top Malicious URLs/Hosts
- Page: KEV Highlights

4. Mention reliability controls
- dbt source freshness and data tests
- CI quality gates
- idempotent stream ingestion and replayable bronze storage

## Shutdown

```bash
make down-p4
```

Destructive cleanup:

```bash
make reset-p4
```
