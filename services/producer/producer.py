import os
import json
import time
import hashlib
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer

# ------------------------------------------------------------------------------
# Configuration (via env vars)
# ------------------------------------------------------------------------------

BOOTSTRAP = os.getenv("BOOTSTRAP_SERVERS", "redpanda:9092")
TOPIC = os.getenv("TOPIC", "threat.urlhaus.events")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "300"))

URLHAUS_TEXT_RECENT = os.getenv(
    "URLHAUS_RECENT_URLS",
    "https://urlhaus.abuse.ch/downloads/text_recent/",
)

# ------------------------------------------------------------------------------
# Kafka producer
# ------------------------------------------------------------------------------

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def event_id_for_url(url: str) -> str:
    """
    Stable event_id for a URL.
    Using SHA256(url) is sufficient for Phase 2.
    """
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

def fetch_recent_urls() -> list[str]:
    """
    Fetch the URLhaus 'text_recent' feed.
    Lines starting with '#' are comments.
    """
    resp = requests.get(
        URLHAUS_TEXT_RECENT,
        headers={"User-Agent": "threat-risk-platform-phase2/1.0"},
        timeout=30,
    )
    resp.raise_for_status()

    urls = []
    for line in resp.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls

# ------------------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------------------

print(f"[producer] starting | bootstrap={BOOTSTRAP} topic={TOPIC}")
print(f"[producer] polling URLhaus text_recent: {URLHAUS_TEXT_RECENT} every {POLL_SECONDS}s")

# Keep track of recently sent event_ids to avoid re-sending the same URLs
seen = set()
MAX_SEEN = 50_000  # bounded memory; safe because downstream is idempotent

while True:
    try:
        now = datetime.now(timezone.utc).isoformat()
        urls = fetch_recent_urls()

        sent = 0
        for url in urls:
            eid = event_id_for_url(url)
            if eid in seen:
                continue

            event = {
                "schema_version": 1,
                "source": "urlhaus",
                "event_id": eid,
                "event_time": now,      # feed has no per-URL timestamp
                "ingested_at": now,
                "payload": {
                    "url": url,
                    "feed": "text_recent",
                },
            }

            producer.send(TOPIC, event)
            sent += 1

            seen.add(eid)
            if len(seen) > MAX_SEEN:
                # reset to prevent unbounded memory growth
                seen.clear()

        producer.flush()
        print(f"[producer] fetched {len(urls)} urls, sent {sent} new")

    except Exception as e:
        print(f"[producer] ERROR: {type(e).__name__}: {e}")

    time.sleep(POLL_SECONDS)

