{{ config(materialized='view') }}

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
  from {{ source('raw', 'urlhaus_events') }}
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

