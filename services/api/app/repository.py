from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AnalyticsRepository:
    conn: Any

    def health(self) -> dict[str, Any]:
        with self.conn.cursor() as cur:
            cur.execute("select 1 as ok")
            row = cur.fetchone()
        return {"db_ok": bool(row and row[0] == 1)}

    def pipeline_summary(self) -> dict[str, Any]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                with stream as (
                  select
                    count(*) as stream_events_total,
                    max(ingested_at) as latest_stream_ingested_at,
                    extract(epoch from (now() - max(ingested_at))) / 60.0 as stream_ingest_lag_minutes,
                    extract(epoch from (now() - max(_consumer_ingested_at))) / 60.0 as consumer_heartbeat_lag_minutes,
                    coalesce(sum(case when _kafka_offset is not null then 1 else 0 end), 0) as rows_with_kafka_metadata
                  from raw.urlhaus_events
                ),
                kev as (
                  select
                    count(*) as kev_rows_total,
                    count(distinct cve_id) as kev_unique_cves,
                    max(date_day) as latest_kev_date
                  from marts.fact_kev
                ),
                threats as (
                  select
                    count(*) as threat_rows_total,
                    max(event_time) as latest_event_time
                  from marts.fct_urlhaus_threat_events
                )
                select
                  stream.stream_events_total,
                  stream.latest_stream_ingested_at,
                  round(coalesce(stream.stream_ingest_lag_minutes, 1e9)::numeric, 2) as stream_ingest_lag_minutes,
                  round(coalesce(stream.consumer_heartbeat_lag_minutes, 1e9)::numeric, 2) as consumer_heartbeat_lag_minutes,
                  stream.rows_with_kafka_metadata,
                  kev.kev_rows_total,
                  kev.kev_unique_cves,
                  kev.latest_kev_date,
                  threats.threat_rows_total,
                  threats.latest_event_time
                from stream, kev, threats
                """
            )
            row = cur.fetchone()

        return {
            "stream_events_total": int(row[0] or 0),
            "latest_stream_ingested_at": row[1].isoformat() if row[1] else None,
            "stream_ingest_lag_minutes": float(row[2] or 0.0),
            "consumer_heartbeat_lag_minutes": float(row[3] or 0.0),
            "rows_with_kafka_metadata": int(row[4] or 0),
            "kev_rows_total": int(row[5] or 0),
            "kev_unique_cves": int(row[6] or 0),
            "latest_kev_date": row[7].isoformat() if row[7] else None,
            "threat_rows_total": int(row[8] or 0),
            "latest_event_time": row[9].isoformat() if row[9] else None,
        }

    def threat_event_trends(self, days: int) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                select
                  date_trunc('day', event_time)::date as day,
                  count(*) as event_count,
                  count(distinct url) as unique_urls
                from marts.fct_urlhaus_threat_events
                where event_time >= now() - (%s || ' days')::interval
                group by 1
                order by 1
                """,
                (days,),
            )
            rows = cur.fetchall()

        return [
            {
                "day": row[0].isoformat(),
                "event_count": int(row[1]),
                "unique_urls": int(row[2]),
            }
            for row in rows
        ]

    def kev_risk_summary(self) -> dict[str, Any]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                with base as (
                  select
                    count(*) as kev_total,
                    count(distinct cve_id) as unique_cves,
                    min(date_added) as first_added,
                    max(date_added) as latest_added,
                    count(*) filter (where due_date < current_date) as overdue_count
                  from marts.fact_kev
                ),
                top_vendors as (
                  select coalesce(dp.vendor_project, 'unknown') as vendor, count(*) as cve_count
                  from marts.fact_kev fk
                  left join marts.dim_product dp on fk.product_key = dp.product_key
                  group by dp.vendor_project
                  order by 2 desc, 1
                  limit 5
                )
                select
                  base.kev_total,
                  base.unique_cves,
                  base.first_added,
                  base.latest_added,
                  base.overdue_count,
                  coalesce(
                    json_agg(json_build_object('vendor', top_vendors.vendor, 'cve_count', top_vendors.cve_count))
                      filter (where top_vendors.vendor is not null),
                    '[]'::json
                  ) as top_vendors
                from base
                left join top_vendors on true
                group by 1,2,3,4,5
                """
            )
            row = cur.fetchone()

        return {
            "kev_total": int(row[0] or 0),
            "unique_cves": int(row[1] or 0),
            "first_added": row[2].isoformat() if row[2] else None,
            "latest_added": row[3].isoformat() if row[3] else None,
            "overdue_count": int(row[4] or 0),
            "top_vendors": row[5] or [],
        }

    def top_malicious_hosts(self, days: int, limit: int) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                select
                  coalesce(
                    nullif(
                      split_part(regexp_replace(url, '^https?://', ''), '/', 1),
                      ''
                    ),
                    'unknown'
                  ) as host,
                  count(*) as event_count
                from marts.fct_urlhaus_threat_events
                where event_time >= now() - (%s || ' days')::interval
                group by 1
                order by 2 desc, 1
                limit %s
                """,
                (days, limit),
            )
            rows = cur.fetchall()

        return [{"host": row[0], "event_count": int(row[1])} for row in rows]

    def stream_lag_trends(self, hours: int) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                select
                  date_trunc('hour', ingested_at) as bucket_hour,
                  round(avg(extract(epoch from (ingested_at - event_time)))::numeric, 2) as avg_event_delay_seconds,
                  count(*) as samples
                from raw.urlhaus_events
                where ingested_at >= now() - (%s || ' hours')::interval
                group by 1
                order by 1
                """,
                (hours,),
            )
            rows = cur.fetchall()

        return [
            {
                "bucket_hour": row[0].isoformat(),
                "avg_event_delay_seconds": float(row[1] or 0.0),
                "samples": int(row[2]),
            }
            for row in rows
        ]
