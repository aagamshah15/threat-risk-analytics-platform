select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select run_date
from "threat_risk"."staging"."stg_kev"
where run_date is null



      
    ) dbt_internal_test