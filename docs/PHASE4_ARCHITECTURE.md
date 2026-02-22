# Phase 4 Architecture: Consumption + Reliability Hardening

Phase 4 extends the existing Phase 1/2/3 platform with a serving and demo consumption layer.

## Additions

1. FastAPI Serving Layer (`services/api`)
- Read-only API over `raw` + `marts` schemas
- Endpoints:
  - `GET /health`
  - `GET /v1/pipeline/summary`
  - `GET /v1/trends/threat-events`
  - `GET /v1/risk/kev-summary`
- Additional helper endpoints for dashboard:
  - `GET /v1/trends/stream-lag`
  - `GET /v1/threat/top-hosts`

2. Streamlit Demo Layer (`services/dashboard`)
- Recruiter-focused pages:
  - Pipeline health
  - Stream freshness/lag trends
  - Top malicious URLs/hosts
  - KEV highlights
- Consumes FastAPI, not direct DB access.

3. Reliability Hardening
- Explicit bootstrap DDL for `raw.urlhaus_events`
- Stronger dbt source/model tests
- dbt freshness checks on streaming source
- Additional singular tests for stream metadata integrity

4. CI gates (`.github/workflows/ci.yml`)
- Lint (`ruff`) on new services
- dbt build + source freshness + targeted tests
- API unit tests + integration test path

## Compose Topology

Phase 4 runs as an overlay on top of existing Phase 3 compose files:

- base: `docker-compose.yml`
- phase2: `infra/streaming/docker-compose.phase2.yml`
- phase3: `infra/orchestration/docker-compose.phase3.yml`
- phase4: `infra/consumption/docker-compose.phase4.yml`

This keeps existing Phase 1/2/3 targets working unchanged.
