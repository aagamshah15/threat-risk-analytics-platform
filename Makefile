.PHONY: up run verify docs down logs psql

up:
	docker compose up -d --build

run:
	docker compose up -d --build
	docker compose run --rm elt
	docker compose run --rm dbt

verify:
	@echo "== Postgres marts tables =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "\dt marts.*"
	@echo "== Row counts (marts) =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select 'fact_kev' as table, count(*) from marts.fact_kev union all select 'fact_url_events', count(*) from marts.fact_url_events;"
	@echo "== Sample checks =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select vendor_project, count(*) cnt from marts.dim_vendor group by 1 order by 2 desc limit 10;"
	@echo "== dbt test (fast) =="
	docker compose run --rm dbt dbt test

docs:
	docker compose run --rm dbt dbt docs generate
	@echo "dbt docs generated under dbt/target (local)."

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

psql:
	docker exec -it $$(docker compose ps -q postgres) psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

docs-serve:
	python3 -m http.server 8080 --directory dbt/target

