
    
    

select
    vendor_key as unique_field,
    count(*) as n_records

from "threat_risk"."marts"."dim_vendor"
where vendor_key is not null
group by vendor_key
having count(*) > 1


