

with base as (
  select
    event_id,
    event_time,
    ingested_at,
    source,
    url,
    feed
  from "threat_risk"."staging"."stg_urlhaus_events"

  
    -- Lookback window handles late arrivals / replays
    where ingested_at >= (
      select coalesce(max(ingested_at), '1970-01-01'::timestamptz) from "threat_risk"."marts"."fct_urlhaus_threat_events"
    ) - interval '48 hours'
  
)

select * from base