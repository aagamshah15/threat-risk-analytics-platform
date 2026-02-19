select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select source
from "threat_risk"."raw"."urlhaus_events"
where source is null



      
    ) dbt_internal_test