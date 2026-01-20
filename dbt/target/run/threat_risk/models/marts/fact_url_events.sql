
  
    

  create  table "threat_risk"."marts"."fact_url_events__dbt_tmp"
  
  
    as
  
  (
    select
  md5(coalesce(url,'')) as url_key,
  run_date as date_day,
  url_status,
  threat,
  tags,
  date_added,
  reporter,
  larted
from "threat_risk"."staging"."stg_urlhaus"
where url is not null
  );
  