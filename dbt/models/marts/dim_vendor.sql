select
  md5(coalesce(vendor_project, '')) as vendor_key,
  vendor_project
from (
  select distinct vendor_project
  from {{ ref('stg_kev') }}
  where vendor_project is not null
) v

