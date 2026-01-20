select
  md5(coalesce(url,'')) as url_key,
  run_date as date_day,
  url_status,
  threat,
  tags,
  date_added,
  reporter,
  larted
from {{ ref('stg_urlhaus') }}
where url is not null

