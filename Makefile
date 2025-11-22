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

ipython:
	docker-compose exec app ipython

logs:
	docker-compose logs -f

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

check-hypertables:
	@echo "Checking TimescaleDB hypertables..."
	docker-compose exec postgres psql -U crewcarbon -d carbon_mrv -c "\d+ sensor_measurements"
	docker-compose exec postgres psql -U crewcarbon -d carbon_mrv -c "SELECT * FROM timescaledb_information.hypertables;"

check-regular-tables:
	@echo "Checking regular PostgreSQL tables..."
	docker-compose exec postgres psql -U crewcarbon -d carbon_mrv -c "\dt"


run-ph-pipeline:
	docker-compose exec app python scripts/ph_sensor_pipeline.py

run-ph-pipeline-logs:
	docker-compose exec app python scripts/ph_sensor_pipeline.py 2>&1 | tee pipeline.log

