
    
    

select
    vendor_project as unique_field,
    count(*) as n_records

from "threat_risk"."marts"."dim_vendor"
where vendor_project is not null
group by vendor_project
having count(*) > 1


