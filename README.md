Crew Carbon Ingest

Use the following command to spin up a bash shell:
`docker-compose exec app bash`

Inside the shell type:
`python`


Use the following command to recreate all tables from scratch

`docker-compose exec app python src/ingest/create_tables.py`