.PHONY: help up down shell python ipython logs db-shell run-pipeline test clean

help:
	@echo "Crew Carbon MRV - Local Development"
	@echo "===================================="
	@echo "up            - Start containers"
	@echo "down          - Stop containers"
	@echo "shell         - Open bash shell in app container"
	@echo "python        - Open Python REPL in app container"
	@echo "db-shell      - Open PostgreSQL shell"
	@echo "test          - Run tests"
	@echo "clean         - Remove all data and containers"
	@echo "run-all-pipelines -Create or recreate tables and ingest data then calc MRV"

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

test:
	docker-compose exec app pytest tests/ -v

clean:
	docker-compose down -v
	rm -rf data/staging/* data/validated/* data/output/*
	@echo "Cleaned up!"

run-all-pipelines:
	@echo "     ██████ ██████  ███████ ██     ██      ██████  █████  ██████  ██████   ██████  ███    ██ "
	@echo "    ██      ██   ██ ██      ██     ██     ██      ██   ██ ██   ██ ██   ██ ██    ██ ████   ██ "
	@echo "    ██      ██████  █████   ██  █  ██     ██      ███████ ██████  ██████  ██    ██ ██ ██  ██ "
	@echo "    ██      ██   ██ ██      ██ ███ ██     ██      ██   ██ ██   ██ ██   ██ ██    ██ ██  ██ ██ "
	@echo "     ██████ ██   ██ ███████  ███ ███       ██████ ██   ██ ██   ██ ██████   ██████  ██   ████ "
	@echo "Building Container..."
	docker-compose up -d
	@echo "Starting complete data pipeline..."
	@echo "Step 1: Creating tables..."
	docker-compose exec app python src/ingest/create_tables.py
	@echo "Step 2: Running data pipeline..."
	docker-compose exec app python src/ingest/run_data_pipeline.py
	@echo "Step 3: Running MRV calculations..."
	docker-compose exec app python src/ingest/run_mrv_pipeline.py
	@echo "✓ Pipeline complete!"