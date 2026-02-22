# Compose files
COMPOSE_BASE = -f docker-compose.yml
COMPOSE_P2   = -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml
COMPOSE_P3   = -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml -f infra/orchestration/docker-compose.phase3.yml
COMPOSE_P4   = -f docker-compose.yml -f infra/streaming/docker-compose.phase2.yml -f infra/orchestration/docker-compose.phase3.yml -f infra/consumption/docker-compose.phase4.yml

.PHONY: up run run-p2 up-p2 dbt dbt-p2 verify verify-p2 logs logs-p2 down down-p2 reset reset-p2 psql docs docs-serve up-p3 init-p3 run-p3-hello run-p3 run-p3-backfill verify-p3 show-p3-latest logs-p3 down-p3 reset-p3 demo-p3 up-p4 init-p4 run-p4 verify-p4 logs-p4 down-p4 reset-p4 demo-p4

RUN_DATE ?= $(shell date +%F)
MAX_KAFKA_LAG ?= 10000
MAX_INGEST_LAG_MINUTES ?= 15
MIN_ROWS_PER_RUN_DATE ?= 1
MAX_DAILY_CHANGE_RATIO ?= 20.0

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
# Phase 3 (orchestration + observability) targets
# ----------------------------

up-p3:
	docker compose $(COMPOSE_P3) up -d --build

init-p3:
	docker compose $(COMPOSE_P3) run --rm prefect-cli prefect work-pool create local-process --type process || true

run-p3-hello:
	docker compose $(COMPOSE_P3) run --rm prefect-cli python orchestration/flows/hello_flow.py

run-p3:
	docker compose $(COMPOSE_P3) run --rm prefect-cli python -c "from orchestration.flows.p3_pipeline_flow import p3_pipeline_flow; p3_pipeline_flow(run_date='$(RUN_DATE)', max_kafka_lag=int('$(MAX_KAFKA_LAG)'), max_ingest_lag_minutes=int('$(MAX_INGEST_LAG_MINUTES)'), min_rows_per_run_date=int('$(MIN_ROWS_PER_RUN_DATE)'), max_daily_change_ratio=float('$(MAX_DAILY_CHANGE_RATIO)'))"

run-p3-backfill:
ifndef BACKFILL_START
	$(error BACKFILL_START is not set. Use: make run-p3-backfill BACKFILL_START=YYYY-MM-DD BACKFILL_END=YYYY-MM-DD)
endif
ifndef BACKFILL_END
	$(error BACKFILL_END is not set. Use: make run-p3-backfill BACKFILL_START=YYYY-MM-DD BACKFILL_END=YYYY-MM-DD)
endif
	docker compose $(COMPOSE_P3) run --rm prefect-cli python -c "from orchestration.flows.p3_pipeline_flow import p3_pipeline_flow; p3_pipeline_flow(backfill_start='$(BACKFILL_START)', backfill_end='$(BACKFILL_END)', run_date='$(BACKFILL_START)', max_kafka_lag=int('$(MAX_KAFKA_LAG)'), max_ingest_lag_minutes=int('$(MAX_INGEST_LAG_MINUTES)'), min_rows_per_run_date=int('$(MIN_ROWS_PER_RUN_DATE)'), max_daily_change_ratio=float('$(MAX_DAILY_CHANGE_RATIO)'))"

verify-p3:
	@echo "== Prefect UI =="
	@echo "http://localhost:4200"
	@echo "== Prefect services =="
	docker compose $(COMPOSE_P3) ps prefect-server prefect-worker
	@echo "== Recent artifacts =="
	ls -lah artifacts/p3_runs || true

show-p3-latest:
	@latest_dir=$$(ls -1dt artifacts/p3_runs/* 2>/dev/null | head -n 1); \
	if [ -z "$$latest_dir" ]; then \
	  echo "No Phase 3 artifacts found."; \
	  exit 0; \
	fi; \
	echo "Latest artifact: $$latest_dir"; \
	if [ -f "$$latest_dir/summary.md" ]; then \
	  echo "== summary.md =="; \
	  cat "$$latest_dir/summary.md"; \
	else \
	  echo "summary.md not found in $$latest_dir"; \
	fi

logs-p3:
	docker compose $(COMPOSE_P3) logs -f --tail=100 prefect-server prefect-worker

down-p3:
	docker compose $(COMPOSE_P3) down

reset-p3:
	docker compose $(COMPOSE_P3) down -v

demo-p3: up-p3 init-p3 run-p3
	@echo "Open Prefect UI: http://localhost:4200"

# ----------------------------
# Phase 4 (consumption + reliability hardening)
# ----------------------------

up-p4:
	docker compose $(COMPOSE_P4) up -d --build

init-p4:
	docker compose $(COMPOSE_P4) run --rm prefect-cli prefect work-pool create local-process --type process || true

run-p4:
	docker compose $(COMPOSE_P4) run --rm prefect-cli python -c "from orchestration.flows.p3_pipeline_flow import p3_pipeline_flow; p3_pipeline_flow(run_date='$(RUN_DATE)', max_kafka_lag=int('$(MAX_KAFKA_LAG)'), max_ingest_lag_minutes=int('$(MAX_INGEST_LAG_MINUTES)'), min_rows_per_run_date=int('$(MIN_ROWS_PER_RUN_DATE)'), max_daily_change_ratio=float('$(MAX_DAILY_CHANGE_RATIO)'))"

verify-p4:
	@echo "== Phase 4 URLs =="
	@echo "Prefect UI:   http://localhost:4200"
	@echo "Redpanda UI:  http://localhost:8080"
	@echo "API docs:     http://localhost:8000/docs"
	@echo "Dashboard:    http://localhost:8501"
	@echo "== API health =="
	curl -s http://localhost:8000/health || true

logs-p4:
	docker compose $(COMPOSE_P4) logs -f --tail=100 api dashboard prefect-server prefect-worker

down-p4:
	docker compose $(COMPOSE_P4) down

reset-p4:
	docker compose $(COMPOSE_P4) down -v

demo-p4: up-p4 init-p4 run-p4 verify-p4
	@echo "Open dashboard: http://localhost:8501"


# ----------------------------
# Utilities
# ----------------------------

psql:
	docker exec -it $$(docker compose $(COMPOSE_BASE) ps -q postgres) psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

docs-serve:
	python3 -m http.server 8080 --directory dbt/target
