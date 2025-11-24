Crew Carbon Ingest

Use the following command to spin up a bash shell:
`docker-compose exec app bash`

Inside the shell type:
`python`


Use the following command to recreate all tables from scratch

`docker-compose exec app python src/ingest/create_tables.py`


Step 1:
Build Container

`docker-compose build`

Step 2:
Start Services

`docker-compose up -d`

Step 3:
Run `create_tables.py` to reset the database tables and recreate the base tables

    `docker-compose exec app python src/ingest/create_tables.py`

Step 4:
Run `run_data_pipeline.py` the raw data transformation pipelines

`docker-compose exec app python src/ingest/run_data_pipeline.py`

Step 5:
Run the `run_mrv_pipeline.py` to create the CO2 removal dataset
    `docker-compose exec app python src/ingest/run_mrv_pipeline.py`

This step will create/update the following table:
``

Step 6:
Run 
`docker-compose down`