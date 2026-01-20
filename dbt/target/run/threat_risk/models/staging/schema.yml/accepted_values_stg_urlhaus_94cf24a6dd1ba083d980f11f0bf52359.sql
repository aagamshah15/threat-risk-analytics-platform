select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        url_status as value_field,
        count(*) as n_records

    from "threat_risk"."staging"."stg_urlhaus"
    group by url_status

)

select *
from all_values
where value_field not in (
    'online','offline','unknown'
)



      
    ) dbt_internal_test