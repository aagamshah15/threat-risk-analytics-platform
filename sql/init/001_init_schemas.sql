CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Raw tables (landing)
CREATE TABLE IF NOT EXISTS raw.kev (
  cve_id TEXT,
  vendor_project TEXT,
  product TEXT,
  vulnerability_name TEXT,
  date_added DATE,
  short_description TEXT,
  required_action TEXT,
  due_date DATE,
  notes TEXT,
  source_url TEXT,
  ingested_at TIMESTAMPTZ DEFAULT now(),
  run_date DATE
);

CREATE TABLE IF NOT EXISTS raw.urlhaus_recent (
  url TEXT,
  url_status TEXT,
  host TEXT,
  date_added TIMESTAMPTZ,
  threat TEXT,
  tags TEXT,
  urlhaus_link TEXT,
  reporter TEXT,
  larted BOOLEAN,
  source_url TEXT,
  ingested_at TIMESTAMPTZ DEFAULT now(),
  run_date DATE
);

CREATE TABLE IF NOT EXISTS raw.urlhaus_events (
  event_id TEXT PRIMARY KEY,
  event_time TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source TEXT NOT NULL,
  url TEXT,
  feed TEXT,
  payload JSONB,
  _consumer_ingested_at TIMESTAMPTZ,
  _kafka_topic TEXT,
  _kafka_partition INTEGER,
  _kafka_offset BIGINT,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_urlhaus_events_ingested_at
  ON raw.urlhaus_events (ingested_at);

CREATE INDEX IF NOT EXISTS idx_raw_urlhaus_events_event_time
  ON raw.urlhaus_events (event_time);
