.PHONY: up run down logs psql

up:
	docker compose up -d --build

run:
	docker compose up -d --build
	docker compose run --rm elt
	docker compose run --rm dbt

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

psql:
	docker exec -it $$(docker compose ps -q postgres) psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

