from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.main import app, get_repository


class FakeRepo:
    def health(self) -> dict[str, Any]:
        return {"db_ok": True}

    def pipeline_summary(self) -> dict[str, Any]:
        return {
            "stream_events_total": 12,
            "latest_stream_ingested_at": "2026-02-22T12:00:00+00:00",
            "stream_ingest_lag_minutes": 1.2,
            "consumer_heartbeat_lag_minutes": 0.8,
            "rows_with_kafka_metadata": 12,
            "kev_rows_total": 20,
            "kev_unique_cves": 20,
            "latest_kev_date": "2026-02-22",
            "threat_rows_total": 12,
            "latest_event_time": "2026-02-22T11:58:00+00:00",
        }

    def threat_event_trends(self, days: int) -> list[dict[str, Any]]:
        return [{"day": "2026-02-21", "event_count": days, "unique_urls": 2}]

    def kev_risk_summary(self) -> dict[str, Any]:
        return {
            "kev_total": 20,
            "unique_cves": 20,
            "first_added": "2026-01-01",
            "latest_added": "2026-02-22",
            "overdue_count": 3,
            "top_vendors": [{"vendor": "apache", "cve_count": 4}],
        }

    def top_malicious_hosts(self, days: int, limit: int) -> list[dict[str, Any]]:
        return [{"host": "evil.example", "event_count": limit + days}]

    def stream_lag_trends(self, hours: int) -> list[dict[str, Any]]:
        return [{"bucket_hour": "2026-02-22T12:00:00+00:00", "avg_event_delay_seconds": 9.5, "samples": hours}]


def _override_repo():
    yield FakeRepo()


def test_health_endpoint() -> None:
    app.dependency_overrides[get_repository] = _override_repo
    client = TestClient(app)
    resp = client.get("/health")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db_ok": True}


def test_pipeline_summary_contract() -> None:
    app.dependency_overrides[get_repository] = _override_repo
    client = TestClient(app)
    resp = client.get("/v1/pipeline/summary")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {
        "stream_events_total",
        "latest_stream_ingested_at",
        "stream_ingest_lag_minutes",
        "consumer_heartbeat_lag_minutes",
        "rows_with_kafka_metadata",
        "kev_rows_total",
        "kev_unique_cves",
        "latest_kev_date",
        "threat_rows_total",
        "latest_event_time",
    }


def test_trends_query_param_validation() -> None:
    app.dependency_overrides[get_repository] = _override_repo
    client = TestClient(app)
    valid = client.get("/v1/trends/threat-events?days=30")
    invalid = client.get("/v1/trends/threat-events?days=0")
    app.dependency_overrides.clear()

    assert valid.status_code == 200
    assert valid.json()["days"] == 30
    assert invalid.status_code == 422
