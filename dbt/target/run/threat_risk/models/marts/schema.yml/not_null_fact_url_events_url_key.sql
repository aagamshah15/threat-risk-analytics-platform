select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select url_key
from "threat_risk"."marts"."fact_url_events"
where url_key is null



      
    ) dbt_internal_test