{{ 
  config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge'
  ) 
}}

with base as (
  select
    event_id,
    event_time,
    ingested_at,
    source,
    url,
    feed
  from {{ ref('stg_urlhaus_events') }}

  {% if is_incremental() %}
    -- Lookback window handles late arrivals / replays
    where ingested_at >= (
      select coalesce(max(ingested_at), '1970-01-01'::timestamptz) from {{ this }}
    ) - interval '48 hours'
  {% endif %}
)

select * from base

