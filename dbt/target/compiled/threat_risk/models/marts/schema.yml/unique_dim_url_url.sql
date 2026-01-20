
    
    

select
    url as unique_field,
    count(*) as n_records

from "threat_risk"."marts"."dim_url"
where url is not null
group by url
having count(*) > 1


