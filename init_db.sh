#!/bin/bash

check_env_var() {
  local var_name="$1"
  if [[ -z "${!var_name}" ]]; then
    echo "Error: Environment variable '$var_name' is not set!"
    exit 1
  fi
}

required_env_vars=(
  "PSQL_ADMIN"
  "PSQL_ADMIN_PASSWORD"
  "DB_NAME"
  "DB_HOST"
  "DB_PORT"
  "DB_USER"
  "DB_PASSWORD"
)

for var in "${required_env_vars[@]}"; do
  check_env_var "$var"
done

echo "Database Vars: $DB_HOST PORT: $DB_PORT"

DB_ADMIN_USER=${PSQL_ADMIN}
DB_ADMIN_PASSWORD=${PSQL_ADMIN_PASSWORD}

DB_NAME=${DB_NAME}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

TEST_USER=${DB_USER}
TEST_PASSWORD=${DB_PASSWORD}

export PGPASSWORD=${DB_ADMIN_PASSWORD}

# Function to check if database exists
check_db_exists() {
  psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';"
}

# Function to check if user exists
check_user_exists() {
  psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$TEST_USER';"
}

# Function to create database and user with grants
create_db() {
  if [[ $(check_db_exists) != "1" ]]; then
    echo "Database $DB_NAME does not exist. Creating..."
    createdb -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" "$DB_NAME"
    if [[ $? -ne 0 ]]; then
      echo "Failed to create database $DB_NAME. Exiting."
      exit 1
    fi
    echo "Database $DB_NAME created successfully."
  else
    echo "Database $DB_NAME already exists."
  fi
}

# Function to create user and grant permissions
create_user() {
  if [[ $(check_user_exists) != "1" ]]; then
    echo "User $TEST_USER does not exist. Creating..."
    psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d postgres -c "CREATE USER $TEST_USER WITH PASSWORD '$TEST_PASSWORD';"
    echo "User $TEST_USER created successfully."
  else
    echo "User $TEST_USER already exists."
  fi

  echo "Granting privileges to $TEST_USER..."
  psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d "$DB_NAME" <<SQL
GRANT CONNECT ON DATABASE $DB_NAME TO $TEST_USER;
GRANT USAGE ON SCHEMA public TO $TEST_USER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $TEST_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $TEST_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $TEST_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $TEST_USER;
GRANT ALL PRIVILEGES ON SCHEMA public TO $TEST_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $TEST_USER;
SQL
  echo "Privileges granted successfully."
}

# Function to enable pgvector and create embeddings table
create_vector_extension() {
  echo "Enabling pgvector extension in $DB_NAME..."
  psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
  if [[ $? -ne 0 ]]; then
    echo "Failed to enable pgvector extension. Exiting."
    exit 1
  fi
  echo "pgvector extension enabled successfully."
}

# Function to remove user
remove_user() {
  echo "Removing user $TEST_USER..."
  psql -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" -d postgres -c "DROP USER IF EXISTS $TEST_USER;"
  echo "User $TEST_USER removed successfully."
}

# Function to drop the database
remove_db() {
  echo "Removing database $DB_NAME..."
  dropdb -h "$DB_HOST" -U "$DB_ADMIN_USER" -p "$DB_PORT" "$DB_NAME"
  echo "Database $DB_NAME removed successfully."
}

# Parse command-line arguments
case $1 in
  create-db)
    create_db
    ;;
  create-user)
    create_user
    ;;
  create-vector-extension)
    create_vector_extension
    ;;
  remove-user)
    remove_user
    ;;
  remove-db)
    remove_db
    ;;
  *)
    echo "Usage: $0 {create-db|create-user|create-vector-extension|remove-user|remove-db}"
    exit 1
    ;;
esac
