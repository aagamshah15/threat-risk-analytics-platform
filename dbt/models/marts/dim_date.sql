with dates as (
  select distinct run_date as d from {{ ref('stg_kev') }}
  union
  select distinct run_date as d from {{ ref('stg_urlhaus') }}
),
final as (
  select
    d as date_day,
    extract(year from d)::int as year,
    extract(month from d)::int as month,
    extract(day from d)::int as day
  from dates
)
select * from final

