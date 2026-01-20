
  
    

  create  table "threat_risk"."marts"."dim_vendor__dbt_tmp"
  
  
    as
  
  (
    select
  md5(coalesce(vendor_project, '')) as vendor_key,
  vendor_project
from (
  select distinct vendor_project
  from "threat_risk"."staging"."stg_kev"
  where vendor_project is not null
) v
  );
  