from __future__ import annotations

import os

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app


def _dsn() -> str:
    return os.getenv("API_TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or ""


def test_health_and_summary_against_real_postgres() -> None:
    dsn = _dsn()
    if not dsn:
        pytest.skip("Set API_TEST_DATABASE_URL or DATABASE_URL to run integration test.")

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("create schema if not exists raw")
            cur.execute("create schema if not exists marts")
            cur.execute(
                """
                create table if not exists raw.urlhaus_events (
                  event_id text primary key,
                  event_time timestamptz,
                  ingested_at timestamptz,
                  source text,
                  url text,
                  feed text,
                  payload jsonb,
                  _consumer_ingested_at timestamptz,
                  _kafka_topic text,
                  _kafka_partition int,
                  _kafka_offset bigint,
                  inserted_at timestamptz default now()
                )
                """
            )
            cur.execute(
                """
                create table if not exists marts.fct_urlhaus_threat_events (
                  event_id text,
                  event_time timestamptz,
                  ingested_at timestamptz,
                  source text,
                  url text,
                  feed text
                )
                """
            )
            cur.execute(
                """
                create table if not exists marts.fact_kev (
                  cve_id text,
                  date_day date,
                  date_added date
                )
                """
            )
            cur.execute("truncate raw.urlhaus_events")
            cur.execute("truncate marts.fct_urlhaus_threat_events")
            cur.execute("truncate marts.fact_kev")

            cur.execute(
                """
                insert into raw.urlhaus_events (
                  event_id, event_time, ingested_at, source, url, feed, payload,
                  _consumer_ingested_at, _kafka_topic, _kafka_partition, _kafka_offset
                )
                values (
                  'evt-1', now() - interval '2 minutes', now() - interval '1 minute',
                  'urlhaus', 'http://mal.example', 'urlhaus', '{}'::jsonb,
                  now() - interval '1 minute', 'threat.urlhaus.events', 0, 10
                )
                """
            )
            cur.execute(
                """
                insert into marts.fct_urlhaus_threat_events
                  (event_id, event_time, ingested_at, source, url, feed)
                values
                  ('evt-1', now() - interval '2 minutes', now() - interval '1 minute', 'urlhaus', 'http://mal.example', 'urlhaus')
                """
            )
            cur.execute(
                """
                insert into marts.fact_kev (cve_id, date_day, date_added)
                values ('CVE-2099-0001', current_date, current_date)
                """
            )
        conn.commit()

    client = TestClient(app)

    health = client.get("/health")
    summary = client.get("/v1/pipeline/summary")

    assert health.status_code == 200
    assert health.json()["db_ok"] is True

    assert summary.status_code == 200
    body = summary.json()
    assert body["stream_events_total"] >= 1
    assert body["kev_rows_total"] >= 1
    assert body["threat_rows_total"] >= 1
