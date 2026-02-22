# Phase 4 Troubleshooting

## API returns 500 on startup

Check if Postgres is healthy and tables exist:

```bash
docker compose -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml -f infra/orchestration/docker-compose.phase3.yml -f infra/consumption/docker-compose.phase4.yml ps
```

If database was reset, rerun pipeline once:

```bash
make run-p4
```

## Dashboard shows API unavailable

Check API health:

```bash
curl http://localhost:8000/health
```

If unhealthy, inspect API logs:

```bash
make logs-p4
```

## dbt freshness failures

Streaming freshness depends on recent rows in `raw.urlhaus_events`.
If producer/consumer is down, freshness checks will fail by design.

Check stream services:

```bash
docker compose -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml ps redpanda producer consumer
```

## Integration test skipped locally

`services/api/tests/test_api_integration.py` only runs when one of these env vars is set:

- `API_TEST_DATABASE_URL`
- `DATABASE_URL`

Example:

```bash
API_TEST_DATABASE_URL=postgresql://app:app@localhost:5432/threat_risk pytest -q services/api/tests/test_api_integration.py
```
