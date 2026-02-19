
    
    



select ingested_at
from "threat_risk"."marts"."fct_urlhaus_threat_events"
where ingested_at is null


