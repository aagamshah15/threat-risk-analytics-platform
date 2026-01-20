with src as (
  select *
  from raw.urlhaus_recent
),
clean as (
  select
    nullif(trim(url), '') as url,
    nullif(trim(url_status), '') as url_status,
    nullif(trim(host), '') as host,
    date_added,
    nullif(trim(threat), '') as threat,
    nullif(trim(tags), '') as tags,
    nullif(trim(urlhaus_link), '') as urlhaus_link,
    nullif(trim(reporter), '') as reporter,
    larted,
    source_url,
    run_date,
    ingested_at
  from src
)
select * from clean