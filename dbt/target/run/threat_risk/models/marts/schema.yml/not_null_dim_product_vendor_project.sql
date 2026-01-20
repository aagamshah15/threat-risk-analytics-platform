select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select vendor_project
from "threat_risk"."marts"."dim_product"
where vendor_project is null



      
    ) dbt_internal_test