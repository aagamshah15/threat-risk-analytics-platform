select
  md5(coalesce(url,'')) as url_key,
  url,
  host
from (
  select distinct url, host
  from {{ ref('stg_urlhaus') }}
  where url is not null
) u

