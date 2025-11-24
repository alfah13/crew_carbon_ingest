.PHONY: help up down shell python ipython logs db-shell run-pipeline test clean

help:
	@echo "Crew Carbon MRV - Local Development"
	@echo "===================================="
	@echo "up            - Start containers"
	@echo "down          - Stop containers"
	@echo "shell         - Open bash shell in app container"
	@echo "python        - Open Python REPL in app container"
	@echo "ipython       - Open IPython shell in app container"
	@echo "logs          - View container logs"
	@echo "db-shell      - Open PostgreSQL shell"
	@echo "run-pipeline  - Run full ingestion -> QAQC -> MRV pipeline"
	@echo "test          - Run tests"
	@echo "clean         - Remove all data and containers"

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Jupyter: http://localhost:8888"
	@echo "PostgreSQL: localhost:5432"

down:
	docker-compose down

shell:
	docker-compose exec app bash

python:
	docker-compose exec app python

db-shell:
	docker-compose exec postgres psql -U crewcarbon -d carbon_mrv

run-pipeline:
	docker-compose exec app python scripts/run_pipeline.py

test:
	docker-compose exec app pytest tests/ -v

clean:
	docker-compose down -v
	rm -rf data/staging/* data/validated/* data/output/*
	@echo "Cleaned up!"

setup-db:
	docker-compose exec postgres psql -U crewcarbon -d carbon_mrv -f /docker-entrypoint-initdb.d/01_init_timescale.sql
	@echo "✓ Database tables created (regular + hypertables)"

run-all-pipelines:
	@echo "     ██████ ██████  ███████ ██     ██      ██████  █████  ██████  ██████   ██████  ███    ██ "
	@echo "    ██      ██   ██ ██      ██     ██     ██      ██   ██ ██   ██ ██   ██ ██    ██ ████   ██ "
	@echo "    ██      ██████  █████   ██  █  ██     ██      ███████ ██████  ██████  ██    ██ ██ ██  ██ "
	@echo "    ██      ██   ██ ██      ██ ███ ██     ██      ██   ██ ██   ██ ██   ██ ██    ██ ██  ██ ██ "
	@echo "     ██████ ██   ██ ███████  ███ ███       ██████ ██   ██ ██   ██ ██████   ██████  ██   ████ "
	@echo "Starting complete data pipeline..."
	@echo "Step 1: Creating tables..."
	docker-compose exec app python src/ingest/create_tables.py
	@echo "Step 2: Running data pipeline..."
	docker-compose exec app python src/ingest/run_data_pipeline.py
	@echo "Step 3: Running MRV calculations..."
	docker-compose exec app python src/ingest/run_mrv_pipeline.py
	@echo "✓ Pipeline complete!"