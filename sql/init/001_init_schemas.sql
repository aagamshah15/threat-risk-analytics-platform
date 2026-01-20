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

