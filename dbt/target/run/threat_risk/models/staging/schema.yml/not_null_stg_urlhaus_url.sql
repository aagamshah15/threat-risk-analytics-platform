select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select url
from "threat_risk"."staging"."stg_urlhaus"
where url is null



      
    ) dbt_internal_test