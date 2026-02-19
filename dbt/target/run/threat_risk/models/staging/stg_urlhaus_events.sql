
  create view "threat_risk"."staging"."stg_urlhaus_events__dbt_tmp"
    
    
  as (
    

with src as (
  select
    event_id,
    event_time,
    ingested_at,
    source,
    url,
    feed,
    payload,
    _consumer_ingested_at,
    _kafka_topic,
    _kafka_partition,
    _kafka_offset,
    inserted_at
  from "threat_risk"."raw"."urlhaus_events"
)

select
  event_id,
  event_time,
  ingested_at,
  source,
  url,
  feed,
  payload,
  inserted_at
from src
  );