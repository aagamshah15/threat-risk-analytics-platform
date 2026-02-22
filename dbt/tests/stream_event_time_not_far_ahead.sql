-- Catch malformed timestamps where event_time is unrealistically ahead of ingest time.
select
  event_id,
  event_time,
  ingested_at
from raw.urlhaus_events
where event_time is not null
  and ingested_at is not null
  and event_time > ingested_at + interval '10 minutes'
