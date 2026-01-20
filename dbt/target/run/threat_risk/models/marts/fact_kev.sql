
  
    

  create  table "threat_risk"."marts"."fact_kev__dbt_tmp"
  
  
    as
  
  (
    select
  md5(coalesce(cve_id,'')) as cve_key,
  md5(coalesce(vendor_project,'') || '|' || coalesce(product,'')) as product_key,
  run_date as date_day,
  cve_id,
  vulnerability_name,
  date_added,
  due_date,
  required_action,
  notes
from "threat_risk"."staging"."stg_kev"
where cve_id is not null
  );
  