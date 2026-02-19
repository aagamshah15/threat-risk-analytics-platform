import os
import json
import time
import uuid
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from kafka import KafkaConsumer
from minio import Minio
import psycopg2
from psycopg2.extras import execute_values

BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "redpanda:9092")
TOPIC = os.getenv("TOPIC", "threat.urlhaus.events")
GROUP_ID = os.getenv("GROUP_ID", "threat-risk-consumer")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "bronze")
MINIO_PREFIX = os.getenv("MINIO_PREFIX", "urlhaus/events")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DB", "postgres")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
BATCH_SECONDS = int(os.getenv("BATCH_SECONDS", "5"))

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP,
    group_id=GROUP_ID,
    auto_offset_reset="earliest",
    enable_auto_commit=False,  # commit only after sinks succeed
    value_deserializer=lambda b: json.loads(b.decode("utf-8")),
)

minio = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

def ensure_bucket(bucket: str):
    if not minio.bucket_exists(bucket):
        minio.make_bucket(bucket)
        print(f"[consumer] created bucket: {bucket}")

def write_jsonl_to_minio(records: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    dt = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")
    batch_id = uuid.uuid4().hex
    key = f"{MINIO_PREFIX}/dt={dt}/hour={hour}/batch_{batch_id}.jsonl"

    lines = []
    for r in records:
        r["_consumer_ingested_at"] = now.isoformat()
        lines.append(json.dumps(r))

    data = ("\n".join(lines) + "\n").encode("utf-8")
    minio.put_object(
        MINIO_BUCKET,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type="application/json",
    )
    return key

def pg_connect():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )

UPSERT_SQL = """
INSERT INTO raw.urlhaus_events (
  event_id, event_time, ingested_at, source, url, feed, payload,
  _consumer_ingested_at, _kafka_topic, _kafka_partition, _kafka_offset
)
VALUES %s
ON CONFLICT (event_id) DO UPDATE SET
  ingested_at = EXCLUDED.ingested_at,
  payload = EXCLUDED.payload,
  _consumer_ingested_at = EXCLUDED._consumer_ingested_at,
  _kafka_topic = EXCLUDED._kafka_topic,
  _kafka_partition = EXCLUDED._kafka_partition,
  _kafka_offset = EXCLUDED._kafka_offset
;
"""

def normalize_record(r: Dict[str, Any]) -> Tuple:
    payload = r.get("payload", {})
    url = payload.get("url") if isinstance(payload, dict) else None
    feed = payload.get("feed") if isinstance(payload, dict) else None

    # Fallback safety: if event_time missing, use ingested_at
    event_time = r.get("event_time") or r.get("ingested_at")
    ingested_at = r.get("ingested_at") or datetime.now(timezone.utc).isoformat()

    return (
        r.get("event_id"),
        event_time,
        ingested_at,
        r.get("source") or "urlhaus",
        url,
        feed,
        json.dumps(payload),
        r.get("_consumer_ingested_at") or datetime.now(timezone.utc).isoformat(),
        r.get("_kafka_topic"),
        r.get("_kafka_partition"),
        r.get("_kafka_offset"),
    )

def upsert_to_postgres(records: List[Dict[str, Any]]):
    with pg_connect() as conn:
        with conn.cursor() as cur:
            values = [normalize_record(r) for r in records]
            execute_values(cur, UPSERT_SQL, values, page_size=1000)
        conn.commit()

print(f"[consumer] starting | bootstrap={BOOTSTRAP} topic={TOPIC} group={GROUP_ID}")
print(f"[consumer] minio | endpoint={MINIO_ENDPOINT} bucket={MINIO_BUCKET} prefix={MINIO_PREFIX}")
print(f"[consumer] postgres | host={PG_HOST} db={PG_DB} user={PG_USER}")
print(f"[consumer] batching | size={BATCH_SIZE} seconds={BATCH_SECONDS}")

ensure_bucket(MINIO_BUCKET)

buffer: List[Dict[str, Any]] = []
last_flush = time.time()

while True:
    msg_pack = consumer.poll(timeout_ms=1000)
    now = time.time()

    for _tp, msgs in msg_pack.items():
        for m in msgs:
            val = m.value
            val["_kafka_topic"] = m.topic
            val["_kafka_partition"] = m.partition
            val["_kafka_offset"] = m.offset
            buffer.append(val)

    should_flush = (len(buffer) >= BATCH_SIZE) or (buffer and (now - last_flush) >= BATCH_SECONDS)

    if should_flush:
        try:
            key = write_jsonl_to_minio(buffer)
            upsert_to_postgres(buffer)
            consumer.commit()

            print(f"[consumer] wrote {len(buffer)} -> s3://{MINIO_BUCKET}/{key} AND upserted raw.urlhaus_events; committed offsets")
            buffer.clear()
            last_flush = now

        except Exception as e:
            print(f"[consumer] ERROR during flush: {type(e).__name__}: {e}")
            time.sleep(2)

