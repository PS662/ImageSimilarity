set -e

echo "Initializing the PostgreSQL database..."

/docker-entrypoint.sh postgres &

until pg_isready -h localhost -p 5432; do
  echo "Waiting for database to be ready..."
  sleep 2
done

bash /docker-entrypoint-initdb.d/init_db.sh create-db
bash /docker-entrypoint-initdb.d/init_db.sh create-vector-extension
bash /docker-entrypoint-initdb.d/init_db.sh create-user

wait
