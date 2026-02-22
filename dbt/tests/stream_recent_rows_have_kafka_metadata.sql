-- Fail only when recent streaming rows are missing Kafka lineage metadata.
select
  event_id,
  ingested_at,
  _kafka_topic,
  _kafka_partition,
  _kafka_offset
from raw.urlhaus_events
where ingested_at >= now() - interval '1 day'
  and (
    _kafka_topic is null
    or _kafka_partition is null
    or _kafka_offset is null
  )
