# Website monitoring service

## How it works
Infrastructure includes following:
- Kafka cloud cluster;
- Redis cloud cluster;
- PostgreSQL cloud cluster;
- Celery workers for periodic tasks execution;
- CLI client to add/remove tasks;
- application that consumes monitoring reports;
- PgAdmin — web-client for PostgreSQL (port 15432);
- Redis-commander — web-client for Redis (port 8081);
- Flower — web-client to check Celery tasks progress (port 8888);
- Portainer — web-client for Docker (port 9000).

Periodic tasks are created by users via CLI and are launching by **Celery** according to their periodicity.
Tasks make requests to specified websites, generate reports about checking and put 
the reports into defined topic on **Kafka**. Another application reads logs from the topic and 
transfers them to table on **PostgreSQL**.  
Celery tasks are coordinating by **Redis**.  

## First launch
### Preparation
**Kafka**, **Redis** and **PostgreSQL** clusters should be up anywhere. 
Other services can be up on any machine and require environment settings 
that must be read from _.env_ file. Execute `cp .env.example .env` and fill values 
in the new _.env_ file. Variables will be automatically load into environment after start.

> Settings _KAFKA_SSL_CAFILE_, _KAFKA_SSL_CERTFILE_, _KAFKA_KEYFILE_ expect absolute paths 
> to files WITHIN container. Considered container based on _monitor_app_ image (look Dockerfile).

Also, infrastruture requires few volumes for metadata storage. 
To keep data from **PgAdmin** and **Portainer** create volumes via 
`docker volume create monitor_pgadmin` and `docker volume create monitor_portainer`.  

### Start
> Make sure that you have started **Kafka**, **Redis** and **PostgreSQL** clusters in cloud

The only command to launch the prepared infrastructure is `docker-compose up -d`.


## CLI client
The client serves to manipulate monitoring tasks. Execute `python src/monitoring.py --help` 
to get information about available commands. To call description and list of parameters 
for specified command call the command with only `--help` parameter.

Example of task creation:
```
python src/monitoring.py add Google https://google.com --periodicity 45 --http-method PUT 
--headers "{\"Content-Type\": \"multipart/form-data\", \"X-Content-Type-Options\": \"nosniff\"}"
```

> Carefully watch output of commands  

## Development
To launch the infrastructure locally execute `docker-compose -f docker-compose.dev.yaml up -d`.  
For local development there are additional containers for **Kafka**, **Zookeeper**, **Redis**
and **PostgreSQL**.  

> Don't mix environment variables for these services and for new ones in _.env_ file!  

To run tests change directory to _src_ and execute `pytest` or call `pytest src/test_cases.py` from root.

## Miscellaneous
After start previously launched tasks will continue scheduled execution.

After any settings update all touched containers must be recreated via `docker-compose up -d` to apply new settings.  

## Troubleshooting
Search every error in containers logs by command `docker-compose logs` and _service_name_ at the end.
Also, don't forget to check containers' health on **Portainer**.
