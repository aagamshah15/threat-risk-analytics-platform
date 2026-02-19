select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select url
from "threat_risk"."marts"."fct_urlhaus_threat_events"
where url is null



      
    ) dbt_internal_test