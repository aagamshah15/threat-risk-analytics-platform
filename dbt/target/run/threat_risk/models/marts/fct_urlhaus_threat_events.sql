
      -- back compat for old kwarg name
  
  
        
            
            
        
    

    

    merge into "threat_risk"."marts"."fct_urlhaus_threat_events" as DBT_INTERNAL_DEST
        using "fct_urlhaus_threat_events__dbt_tmp021157991362" as DBT_INTERNAL_SOURCE
        on (
                DBT_INTERNAL_SOURCE.event_id = DBT_INTERNAL_DEST.event_id
            )

    
    when matched then update set
        "event_id" = DBT_INTERNAL_SOURCE."event_id","event_time" = DBT_INTERNAL_SOURCE."event_time","ingested_at" = DBT_INTERNAL_SOURCE."ingested_at","source" = DBT_INTERNAL_SOURCE."source","url" = DBT_INTERNAL_SOURCE."url","feed" = DBT_INTERNAL_SOURCE."feed"
    

    when not matched then insert
        ("event_id", "event_time", "ingested_at", "source", "url", "feed")
    values
        ("event_id", "event_time", "ingested_at", "source", "url", "feed")


  