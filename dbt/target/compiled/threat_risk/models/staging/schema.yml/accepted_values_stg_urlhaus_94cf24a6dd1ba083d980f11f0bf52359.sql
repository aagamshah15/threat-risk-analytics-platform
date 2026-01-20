
    
    

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


