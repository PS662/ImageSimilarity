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