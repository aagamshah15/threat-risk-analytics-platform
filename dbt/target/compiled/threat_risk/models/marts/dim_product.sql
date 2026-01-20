select
  md5(coalesce(vendor_project,'') || '|' || coalesce(product,'')) as product_key,
  md5(coalesce(vendor_project,'')) as vendor_key,
  vendor_project,
  product
from (
  select distinct vendor_project, product
  from "threat_risk"."staging"."stg_kev"
  where vendor_project is not null and product is not null
) p