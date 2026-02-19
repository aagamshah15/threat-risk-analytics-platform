# Compose files
COMPOSE_BASE = -f docker-compose.yml
COMPOSE_P2   = -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml

.PHONY: up run run-p2 up-p2 dbt dbt-p2 verify verify-p2 logs logs-p2 down down-p2 reset reset-p2 psql docs docs-serve

# ----------------------------
# Phase 1 (batch) targets
# ----------------------------

up:
	docker compose $(COMPOSE_BASE) up -d --build

run:
	docker compose $(COMPOSE_BASE) up -d --build
	docker compose $(COMPOSE_BASE) run --rm elt
	docker compose $(COMPOSE_BASE) run --rm dbt

dbt:
	docker compose $(COMPOSE_BASE) run --rm dbt dbt build

verify:
	@echo "== Postgres marts tables =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "\dt marts.*"
	@echo "== Row counts (marts) =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select 'fact_kev' as table, count(*) from marts.fact_kev union all select 'fact_url_events', count(*) from marts.fact_url_events;"
	@echo "== Sample checks =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select vendor_project, count(*) cnt from marts.dim_vendor group by 1 order by 2 desc limit 10;"
	@echo "== dbt test (fast) =="
	docker compose $(COMPOSE_BASE) run --rm dbt dbt test

docs:
	docker compose $(COMPOSE_BASE) run --rm dbt dbt docs generate
	@echo "dbt docs generated under dbt/target (local)."

# Safe down (keeps volumes)
down:
	docker compose $(COMPOSE_BASE) down

# Destructive reset (wipes volumes)
reset:
	docker compose $(COMPOSE_BASE) down -v


# ----------------------------
# Phase 2 (streaming + incremental) targets
# ----------------------------

up-p2:
	docker compose $(COMPOSE_P2) up -d --build

run-p2:
	docker compose $(COMPOSE_P2) up -d --build
	docker compose $(COMPOSE_P2) run --rm elt
	docker compose $(COMPOSE_P2) run --rm dbt dbt build

dbt-p2:
	docker compose $(COMPOSE_P2) run --rm dbt dbt build

verify-p2:
	@echo "== Postgres raw table (streaming) =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "\dt raw.*"
	@echo "== Row counts (raw + incremental fact) =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select 'raw.urlhaus_events' as table, count(*) from raw.urlhaus_events union all select 'marts.fct_urlhaus_threat_events', count(*) from marts.fct_urlhaus_threat_events;"
	@echo "== Latest ingested_at =="
	docker exec -it threat-risk-platform-postgres-1 psql -U app -d threat_risk -c "select max(ingested_at) as latest_ingested_at from raw.urlhaus_events;"
	@echo "== dbt test =="
	docker compose $(COMPOSE_P2) run --rm dbt dbt test

logs:
	docker compose $(COMPOSE_BASE) logs -f --tail=100

logs-p2:
	docker compose $(COMPOSE_P2) logs -f --tail=100

down-p2:
	docker compose $(COMPOSE_P2) down

reset-p2:
	docker compose $(COMPOSE_P2) down -v


# ----------------------------
# Utilities
# ----------------------------

psql:
	docker exec -it $$(docker compose $(COMPOSE_BASE) ps -q postgres) psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

docs-serve:
	python3 -m http.server 8080 --directory dbt/target

