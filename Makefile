run-app:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	celery -A app.tasks worker --loglevel=info -c 2

create-db:
	bash init_db.sh create-db

create-user:
	bash init_db.sh create-user

create-vector-extension:
	bash init_db.sh create-vector-extension

remove-user:
	bash init_db.sh remove-user

remove-db:
	bash init_db.sh remove-db

init-db: create-db create-vector-extension create-user

db-bash:
	PGPASSWORD=$(PSQL_ADMIN_PASSWORD) psql -h $(DB_HOST) -U $(PSQL_ADMIN) -p $(DB_PORT) -d $(DB_NAME)

#### Dockerize
APP_IMAGE?=image-similarity:latest
DB_IMAGE?=image-similarity-db:latest

docker-app-image:
	docker build -t ${APP_IMAGE} --rm=true --force-rm=true .

bash-app-image:
	docker run --rm -it ${APP_IMAGE} /bin/bash

run-compose:
	docker compose up

stop-compose:
	docker compose down