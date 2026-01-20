with src as (
  select *
  from raw.kev
),
clean as (
  select
    nullif(trim(cve_id), '') as cve_id,
    nullif(trim(vendor_project), '') as vendor_project,
    nullif(trim(product), '') as product,
    nullif(trim(vulnerability_name), '') as vulnerability_name,
    date_added,
    short_description,
    required_action,
    due_date,
    notes,
    source_url,
    run_date,
    ingested_at
  from src
)
select * from clean