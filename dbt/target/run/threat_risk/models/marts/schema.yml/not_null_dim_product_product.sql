select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select product
from "threat_risk"."marts"."dim_product"
where product is null



      
    ) dbt_internal_test